import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

class TestFinanceSecOps:
    """Testes ofensivos de segurança (SecOps) para os novos endpoints de finanças."""

    def test_xss_injection_in_transaction_description(self):
        """SecOps: Tenta injetar script malicioso na descrição da transação."""
        mock_db = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "sec-tx-1"
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        malicious_payload = {
            "description": "<script>alert('xss')</script>Compra Teste",
            "amount": 99.90,
            "category": "Lazer",
            "type": "expense_variable",
            "paymentMethod": "Cartão de Crédito Pessoal",
            "owner": "<img src=x onerror=alert(1)>"
        }

        with patch("config.firebase.db", mock_db):
            response = client.post("/api/v1/finance/transactions", json=malicious_payload, headers={"X-User-Id": "daniel"})
            assert response.status_code in [200, 201]
            data = response.json()
            # O sistema deve armazenar e tratar o payload sem quebrar a API nem executar código
            assert data["id"] == "sec-tx-1"
            assert "script" in data["description"]

    def test_multi_tenant_isolation_idor_prevention(self):
        """SecOps / IDOR: Usuário lari não pode ver transações do usuário daniel."""
        mock_db = MagicMock()
        
        doc_daniel = MagicMock()
        doc_daniel.id = "tx_daniel_secret"
        doc_daniel.to_dict.return_value = {
            "description": "Gasto Confidencial Daniel",
            "amount": 5000.0,
            "category": "Casa",
            "type": "expense_fixed",
            "date": "2026-04-01T12:00:00Z",
            "userId": "daniel"
        }

        doc_lari = MagicMock()
        doc_lari.id = "tx_lari_public"
        doc_lari.to_dict.return_value = {
            "description": "Gasto Lari",
            "amount": 100.0,
            "category": "Farmácia",
            "type": "expense_variable",
            "date": "2026-04-01T12:00:00Z",
            "userId": "lari"
        }

        mock_db.collection.return_value.stream.return_value = [doc_daniel, doc_lari]

        with patch("config.firebase.db", mock_db):
            # Requisição feita por Lari
            res_lari = client.get("/api/v1/finance/dashboard?year=2026&month=4", headers={"X-User-Id": "lari"})
            assert res_lari.status_code == 200
            data_lari = res_lari.json()
            
            # Garante que Lari só enxerga o seu gasto e total de R$ 100
            assert data_lari["totalSpent"] == 100.0
            tx_ids = [t["id"] for t in data_lari["transactions"]]
            assert "tx_daniel_secret" not in tx_ids
            assert "tx_lari_public" in tx_ids

    def test_sql_nosql_injection_in_category_filter(self):
        """SecOps: Injeção de operadores NoSQL na query param de categoria."""
        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = []

        with patch("config.firebase.db", mock_db):
            # Tenta operador NoSQL ou SQL injection no parâmetro category
            malicious_cat = "{$ne: null}' OR '1'='1"
            response = client.get(f"/api/v1/finance/dashboard?year=2026&month=4&category={malicious_cat}", headers={"X-User-Id": "daniel"})
            assert response.status_code == 200
            data = response.json()
            # Nenhum registro indevido é retornado
            assert data["transactions"] == []
