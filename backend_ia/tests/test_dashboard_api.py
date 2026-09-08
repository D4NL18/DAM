import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

class TestDashboardAPI:
    """Testes dos endpoints de Dashboard consumidos pelo Frontend Angular."""

    def test_cors_headers_present(self):
        """Verifica se os cabeçalhos de CORS estão configurados para o frontend."""
        response = client.options(
            "/api/v1/finance/monthly-summary",
            headers={
                "Origin": "https://bot-dam-72ef2.web.app",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code in [200, 204]
        assert "access-control-allow-origin" in response.headers

    def test_finance_monthly_summary_empty_state(self):
        """P-DASH-01: Quando não há transações no banco, retorna total 0 e listas vazias (sem mocks)."""
        with patch("config.firebase.db", None):
            response = client.get("/api/v1/finance/monthly-summary?year=2026&month=9")
            assert response.status_code == 200
            data = response.json()
            assert data["totalSpent"] == 0.0
            assert data["currency"] == "BRL"
            assert data["expensesByCategory"] == []
            assert data["recentTransactions"] == []

    def test_finance_monthly_summary_with_real_records(self):
        """P-DASH-01: Quando há transações no Firestore, agrupa categorias e soma total real."""
        mock_db = MagicMock()
        mock_doc1 = MagicMock()
        mock_doc1.to_dict.return_value = {
            "amount": 150.0,
            "category": "Alimentação",
            "description": "Mercado",
            "date": "2026-09-02",
            "created_at": "2026-09-02T12:00:00Z"
        }
        mock_doc1.id = "doc1"
        mock_doc2 = MagicMock()
        mock_doc2.to_dict.return_value = {
            "amount": 50.0,
            "category": "Transporte",
            "description": "Combustível",
            "date": "2026-09-03",
            "created_at": "2026-09-03T10:00:00Z"
        }
        mock_doc2.id = "doc2"

        mock_db.collection.return_value.stream.return_value = [mock_doc1, mock_doc2]

        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/monthly-summary?year=2026&month=9")
            assert response.status_code == 200
            data = response.json()
            assert data["totalSpent"] == 200.0
            assert len(data["expensesByCategory"]) == 2
            assert len(data["recentTransactions"]) == 2

    def test_health_summary_empty_state(self):
        """P-DASH-02: Quando não há métricas de saúde, retorna zerado sem mocks."""
        with patch("config.firebase.db", None):
            response = client.get("/api/v1/health/summary?startDate=2026-09-01&endDate=2026-09-03")
            assert response.status_code == 200
            data = response.json()
            assert data["stepCount"] == 0
            assert data["activeEnergyBurned"] == 0
            assert data["heartRateAvg"] == 0
            assert data["sleepHours"] == 0.0

    def test_health_summary_with_records(self):
        """P-DASH-02: Quando há métricas de saúde no Firestore, calcula médias reais."""
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.to_dict.return_value = {
            "data": {
                "metrics": [
                    {"name": "step_count", "data": [{"qty": 8500}]},
                    {"name": "active_energy", "data": [{"qty": 420}]},
                    {"name": "heart_rate", "data": [{"Avg": 72}]},
                    {"name": "sleep_analysis", "data": [{"total_sleep": 7.5}]}
                ]
            }
        }
        mock_db.collection.return_value.stream.return_value = [mock_doc]

        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/health/summary?startDate=2026-09-01&endDate=2026-09-03")
            assert response.status_code == 200
            data = response.json()
            assert data["stepCount"] == 8500
            assert data["activeEnergyBurned"] == 420
            assert data["heartRateAvg"] == 72
            assert data["sleepHours"] == 7.5

    def test_agenda_summary_empty_state(self):
        """P-DASH-03: Quando a agenda não possui eventos hoje, retorna lista vazia."""
        with patch("services.tools.calendar_tool._get_calendar_service", return_value=None):
            response = client.get("/api/v1/agenda")
            assert response.status_code == 200
            data = response.json()
            assert data["todayTotalEvents"] == 0
            assert data["totalMeetingHours"] == 0.0
            assert data["nextEvent"] is None
            assert data["upcomingEvents"] == []
