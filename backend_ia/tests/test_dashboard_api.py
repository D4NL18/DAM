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

    def test_agenda_summary_with_real_reminders(self):
        """P-DASH-03: Separa ativos e histórico, ignora notas e recalcula recorrência."""
        mock_itens = [
            {
                "id": "rem-1",
                "tipo": "lembrete",
                "titulo": "Pagar fatura",
                "data_hora_lembrete": "2026-11-20 09:00",
                "status": "pendente"
            },
            {
                "id": "rem-2",
                "tipo": "lembrete",
                "titulo": "Exame de sangue",
                "data_hora_lembrete": "2026-09-01 08:00",
                "status": "concluido"
            },
            {
                "id": "rem-3",
                "tipo": "nota",
                "titulo": "Orçamento PC EUA",
                "conteudo": "Detalhes de preços"
            },
            {
                "id": "rem-4",
                "tipo": "lembrete",
                "titulo": "Aniversário de namoro",
                "data_hora_lembrete": "2026-09-25 00:00",
                "recorrencia": "mensal",
                "status": "pendente"
            }
        ]
        with patch("services.tools.calendar_tool._get_calendar_service", return_value=None), \
             patch("routers.dashboard._obter_todos_itens", return_value=mock_itens):
            response = client.get("/api/v1/agenda/summary")
            assert response.status_code == 200
            data = response.json()
            # rem-3 (nota) nunca entra
            # rem-1 (futuro) e rem-4 (recorrente avançado) entram em reminders (ativos)
            # rem-2 (concluido) entra em reminderHistory
            assert len(data["reminders"]) == 2
            assert data["reminders"][0]["text"] in ["Pagar fatura", "Aniversário de namoro"]
            assert data["reminders"][1]["text"] in ["Pagar fatura", "Aniversário de namoro"]
            # Verifica que a nota de PC não está em lugar nenhum
            todos_textos = [r["text"] for r in data["reminders"]] + [h["text"] for h in data["reminderHistory"]]
            assert "Orçamento PC EUA" not in todos_textos
            assert len(data["reminderHistory"]) == 1
            assert data["reminderHistory"][0]["text"] == "Exame de sangue"

    def test_toggle_agenda_reminder(self):
        """P-DASH-03: Marca ou desmarca lembrete."""
        mock_itens = [
            {
                "id": "rem-toggle-1",
                "tipo": "lembrete",
                "titulo": "Comprar pão",
                "data_hora_lembrete": "2026-10-25 10:00",
                "status": "pendente"
            }
        ]
        with patch("routers.dashboard._obter_todos_itens", return_value=mock_itens), \
             patch("routers.dashboard.concluir_lembrete") as mock_concluir:
            resp = client.post("/api/v1/agenda/reminders/rem-toggle-1/toggle")
            assert resp.status_code == 200
            assert resp.json()["status"] == "concluido"
            assert resp.json()["completed"] is True
            mock_concluir.assert_called_once_with("rem-toggle-1")


