import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app

client = TestClient(app)

class TestFinanceDashboardV2:
    """Testes TDD para a feature FG-06: Dashboard Avançado de Gastos, Categorias e Cartões."""

    def test_get_dashboard_empty(self):
        """P-001 & P-004: Quando não há transações no banco, retorna saldos zerados."""
        with patch("config.firebase.db", None):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=4", headers={"X-User-Id": "daniel"})
            assert response.status_code == 200
            data = response.json()
            assert data["totalSpent"] == 0.0
            assert data["totalIncome"] == 0.0
            assert data["totalFixed"] == 0.0
            assert data["totalVariable"] == 0.0
            assert data["balance"] == 0.0
            assert data["transactions"] == []
            assert data["expensesByCategory"] == []

    def test_get_dashboard_with_aggregation_and_types(self):
        """P-003 & P-004: Valida agregação correta de despesas fixas, variáveis e receitas."""
        mock_db = MagicMock()
        
        # Transação 1: Despesa Variável (Carro - R$ 2823)
        doc1 = MagicMock()
        doc1.id = "tx1"
        doc1.to_dict.return_value = {
            "description": "Financiamento Song",
            "amount": 2823.00,
            "category": "Carro",
            "type": "expense_variable",
            "payment_method": "Cartão de Crédito Pessoal",
            "installment": "2/3",
            "owner": "Daniel",
            "date": "2026-04-01T10:00:00Z",
            "userId": "daniel"
        }

        # Transação 2: Despesa Fixa (Aluguel - R$ 1500)
        doc2 = MagicMock()
        doc2.id = "tx2"
        doc2.to_dict.return_value = {
            "description": "Aluguel",
            "amount": 1500.00,
            "category": "Casa",
            "type": "expense_fixed",
            "payment_method": "Cartão de Débito",
            "date": "2026-04-05T10:00:00Z",
            "userId": "daniel"
        }

        # Transação 3: Receita (Salário - R$ 10000)
        doc3 = MagicMock()
        doc3.id = "tx3"
        doc3.to_dict.return_value = {
            "description": "Salário",
            "amount": 10000.00,
            "category": "Receitas",
            "type": "income",
            "payment_method": "Pix",
            "date": "2026-04-05T08:00:00Z",
            "userId": "daniel"
        }

        # Transação 4: Outro mês (não deve entrar)
        doc4 = MagicMock()
        doc4.id = "tx4"
        doc4.to_dict.return_value = {
            "description": "Compra Antiga",
            "amount": 500.00,
            "category": "Lazer",
            "type": "expense_variable",
            "date": "2026-03-15T10:00:00Z",
            "userId": "daniel"
        }

        # Simula stream da coleção finances
        def mock_collection(name):
            col = MagicMock()
            if name == "finances":
                col.stream.return_value = [doc1, doc2, doc3, doc4]
            else:
                col.stream.return_value = []
            return col

        mock_db.collection.side_effect = mock_collection

        with patch("config.firebase.db", mock_db):
            response = client.get("/api/v1/finance/dashboard?year=2026&month=4", headers={"X-User-Id": "daniel"})
            assert response.status_code == 200
            data = response.json()
            
            assert data["totalIncome"] == 10000.00
            assert data["totalFixed"] == 1500.00
            assert data["totalVariable"] == 2823.00
            assert data["totalSpent"] == 4323.00
            assert data["balance"] == 5677.00 # 10000 - 4323
            
            # Filtro por tipo=expense_variable
            resp_var = client.get("/api/v1/finance/dashboard?year=2026&month=4&type=expense_variable", headers={"X-User-Id": "daniel"})
            assert resp_var.status_code == 200
            data_var = resp_var.json()
            assert len(data_var["transactions"]) == 1
            assert data_var["transactions"][0]["description"] == "Financiamento Song"

            # Aba tipo=total (todas as entradas na tabela, mas gráfico exibindo apenas o negativo/despesas)
            resp_total = client.get("/api/v1/finance/dashboard?year=2026&month=4&type=total", headers={"X-User-Id": "daniel"})
            assert resp_total.status_code == 200
            data_total = resp_total.json()
            assert len(data_total["transactions"]) == 3
            total_cats = [c["category"] for c in data_total["expensesByCategory"]]
            assert "Carro" in total_cats
            assert "Casa" in total_cats
            assert "Receitas" not in total_cats

    def test_transactions_crud(self):
        """P-005: Adição, edição e exclusão de transações."""
        mock_db = MagicMock()
        mock_doc_ref = MagicMock()
        mock_doc_ref.id = "new-tx-id"
        mock_db.collection.return_value.add.return_value = (None, mock_doc_ref)

        with patch("config.firebase.db", mock_db):
            # 1. Create (POST)
            create_payload = {
                "description": "Ração Gatos",
                "amount": 220.00,
                "category": "Gatos",
                "type": "expense_variable",
                "paymentMethod": "Cartão de Crédito Secundário",
                "date": "2026-04-01",
                "owner": "Daniel"
            }
            res_post = client.post("/api/v1/finance/transactions", json=create_payload, headers={"X-User-Id": "daniel"})
            assert res_post.status_code in [200, 201]
            created = res_post.json()
            assert created["description"] == "Ração Gatos"

            # 2. Update (PUT)
            update_payload = {
                "description": "Ração Gatos Premium",
                "amount": 250.00,
                "category": "Gatos",
                "type": "expense_variable",
                "paymentMethod": "Cartão de Crédito Secundário",
                "date": "2026-04-01"
            }
            res_put = client.put("/api/v1/finance/transactions/new-tx-id", json=update_payload, headers={"X-User-Id": "daniel"})
            assert res_put.status_code == 200

            # 3. Delete (DELETE)
            res_del = client.delete("/api/v1/finance/transactions/new-tx-id", headers={"X-User-Id": "daniel"})
            assert res_del.status_code == 200

    def test_categories_crud_and_defaults(self):
        """P-009, P-010, P-011: Retorno de categorias padrão, adição, renomeação e exclusão."""
        mock_db = MagicMock()
        # Inicialmente sem categorias no banco -> retorna defaults
        mock_db.collection.return_value.stream.return_value = []

        with patch("config.firebase.db", mock_db):
            # GET categories
            res_get = client.get("/api/v1/finance/categories", headers={"X-User-Id": "daniel"})
            assert res_get.status_code == 200
            cats = res_get.json()
            assert len(cats) >= 5
            cat_names = [c["name"] for c in cats]
            assert "Mercado" in cat_names
            assert "Carro" in cat_names

            # POST category
            new_cat = {"name": "Academia", "color": "#10B981"}
            res_post = client.post("/api/v1/finance/categories", json=new_cat, headers={"X-User-Id": "daniel"})
            assert res_post.status_code in [200, 201]

            # PUT category
            edit_cat = {"name": "CrossFit & Academia", "color": "#059669"}
            res_put = client.put("/api/v1/finance/categories/cat123", json=edit_cat, headers={"X-User-Id": "daniel"})
            assert res_put.status_code == 200

            # DELETE category
            res_del = client.delete("/api/v1/finance/categories/cat123", headers={"X-User-Id": "daniel"})
            assert res_del.status_code == 200

    def test_cards_crud_and_defaults(self):
        """P-012: Gestão de cartões com retorno inicial dos padrões."""
        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = []

        with patch("config.firebase.db", mock_db):
            # GET cards
            res_get = client.get("/api/v1/finance/cards", headers={"X-User-Id": "daniel"})
            assert res_get.status_code == 200
            cards = res_get.json()
            assert len(cards) >= 3
            card_names = [c["name"] for c in cards]
            assert any("Pessoal" in name for name in card_names)

            # POST card
            new_card = {"name": "XP Visa Infinite", "type": "credito"}
            res_post = client.post("/api/v1/finance/cards", json=new_card, headers={"X-User-Id": "daniel"})
            assert res_post.status_code in [200, 201]

            # PUT card
            edit_card = {"name": "XP Visa Infinite Principal", "type": "credito"}
            res_put = client.put("/api/v1/finance/cards/card123", json=edit_card, headers={"X-User-Id": "daniel"})
            assert res_put.status_code == 200

            # DELETE card
            res_del = client.delete("/api/v1/finance/cards/card123", headers={"X-User-Id": "daniel"})
            assert res_del.status_code == 200

    def test_multiuser_isolation(self):
        """P-013: Isolamento estrito entre usuários daniel e lari."""
        mock_db = MagicMock()
        doc_daniel = MagicMock()
        doc_daniel.id = "d1"
        doc_daniel.to_dict.return_value = {
            "description": "Gasto Daniel",
            "amount": 100.0,
            "type": "expense_variable",
            "category": "Lazer",
            "date": "2026-04-02",
            "userId": "daniel"
        }
        doc_lari = MagicMock()
        doc_lari.id = "l1"
        doc_lari.to_dict.return_value = {
            "description": "Gasto Lari",
            "amount": 200.0,
            "type": "expense_variable",
            "category": "Farmácia",
            "date": "2026-04-02",
            "userId": "lari"
        }

        mock_db.collection.return_value.stream.return_value = [doc_daniel, doc_lari]

        with patch("config.firebase.db", mock_db):
            res_daniel = client.get("/api/v1/finance/dashboard?year=2026&month=4", headers={"X-User-Id": "daniel"})
            txs_daniel = res_daniel.json()["transactions"]
            assert len(txs_daniel) == 1
            assert txs_daniel[0]["description"] == "Gasto Daniel"

            res_lari = client.get("/api/v1/finance/dashboard?year=2026&month=4", headers={"X-User-Id": "lari"})
            txs_lari = res_lari.json()["transactions"]
            assert len(txs_lari) == 1
            assert txs_lari[0]["description"] == "Gasto Lari"
