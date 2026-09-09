import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

class TestFinanceTrends:
    """Testes TDD para FG-07: Evolução Temporal de Gastos & Receitas."""

    def test_get_finance_trends_empty(self):
        """P-014, P-016: Quando não há transações, retorna totais 0 e sem período anterior."""
        with patch("config.firebase.db", None):
            response = client.get("/api/v1/finance/trends?period=12m", headers={"X-User-Id": "daniel"})
            assert response.status_code == 200
            data = response.json()
            assert data["period"] == "12m"
            assert data["totalIncome"] == 0.0
            assert data["totalExpenses"] == 0.0
            assert data["periodBalance"] == 0.0
            assert data["comparison"]["hasPreviousPeriod"] is False
            assert len(data["series"]) == 12

    def test_get_finance_trends_aggregation(self):
        """P-015, P-016: Agregação correta de receitas e gastos mês a mês em ordem cronológica."""
        mock_db = MagicMock()

        # Doc 1: Receita em Março de 2026 (R$ 50.000)
        doc1 = MagicMock()
        doc1.id = "tx1"
        doc1.to_dict.return_value = {
            "description": "Faturamento",
            "amount": 50000.0,
            "type": "income",
            "date": "2026-03-10T10:00:00Z",
            "userId": "daniel"
        }

        # Doc 2: Gasto em Março de 2026 (R$ 20.000)
        doc2 = MagicMock()
        doc2.id = "tx2"
        doc2.to_dict.return_value = {
            "description": "Despesas Gerais",
            "amount": 20000.0,
            "type": "expense_variable",
            "date": "2026-03-15T10:00:00Z",
            "userId": "daniel"
        }

        # Doc 3: Receita em Abril de 2026 (R$ 60.000)
        doc3 = MagicMock()
        doc3.id = "tx3"
        doc3.to_dict.return_value = {
            "description": "Faturamento Abril",
            "amount": 60000.0,
            "type": "income",
            "date": "2026-04-05T10:00:00Z",
            "userId": "daniel"
        }

        mock_db.collection.return_value.stream.return_value = [doc1, doc2, doc3]

        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/trends?period=12m", headers={"X-User-Id": "daniel"})
            assert response.status_code == 200
            data = response.json()
            assert data["totalIncome"] == 110000.0
            assert data["totalExpenses"] == 20000.0
            assert data["periodBalance"] == 90000.0
            assert len(data["series"]) == 12

            # Encontra março e abril na série
            mar_item = next((s for s in data["series"] if s["month"] == 3 and s["year"] == 2026), None)
            abr_item = next((s for s in data["series"] if s["month"] == 4 and s["year"] == 2026), None)

            if mar_item:
                assert mar_item["income"] == 50000.0
                assert mar_item["expenses"] == 20000.0
                assert mar_item["balance"] == 30000.0

            if abr_item:
                assert abr_item["income"] == 60000.0
                assert abr_item["expenses"] == 0.0

    def test_get_finance_trends_periods_lengths(self):
        """P-014: Valida suporte a períodos 3m, 6m e 12m."""
        with patch("config.firebase.db", None):
            res_3m = client.get("/api/v1/finance/trends?period=3m", headers={"X-User-Id": "daniel"})
            assert res_3m.status_code == 200
            assert len(res_3m.json()["series"]) == 3

            res_6m = client.get("/api/v1/finance/trends?period=6m", headers={"X-User-Id": "daniel"})
            assert res_6m.status_code == 200
            assert len(res_6m.json()["series"]) == 6

            res_12m = client.get("/api/v1/finance/trends?period=12m", headers={"X-User-Id": "daniel"})
            assert res_12m.status_code == 200
            assert len(res_12m.json()["series"]) == 12

    def test_get_finance_trends_user_isolation(self):
        """P-020: Isolamento estrito de dados entre usuários."""
        mock_db = MagicMock()
        doc_daniel = MagicMock()
        doc_daniel.to_dict.return_value = {
            "description": "Receita Daniel",
            "amount": 75000.0,
            "type": "income",
            "date": "2026-04-01T10:00:00Z",
            "userId": "daniel"
        }

        doc_lari = MagicMock()
        doc_lari.to_dict.return_value = {
            "description": "Receita Lari",
            "amount": 40000.0,
            "type": "income",
            "date": "2026-04-01T10:00:00Z",
            "userId": "lari"
        }

        mock_db.collection.return_value.stream.return_value = [doc_daniel, doc_lari]

        with patch("config.firebase.db", mock_db):
            res_daniel = client.get("/api/v1/finance/trends?period=6m", headers={"X-User-Id": "daniel"})
            assert res_daniel.json()["totalIncome"] == 75000.0

            res_lari = client.get("/api/v1/finance/trends?period=6m", headers={"X-User-Id": "lari"})
            assert res_lari.json()["totalIncome"] == 40000.0
