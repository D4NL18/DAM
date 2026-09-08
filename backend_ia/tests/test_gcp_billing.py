"""
Testes Unitários — GCP Billing Tool & FinOps
"""
from unittest.mock import patch, MagicMock
from services.tools.gcp_billing_tool import consultar_gcp_billing

class TestGcpBillingTool:
    @patch("services.tools.gcp_billing_tool.firebase.db")
    def test_consultar_billing_sem_snapshot_mostra_arquitetura(self, mock_db):
        mock_db.collection.return_value.document.return_value.get.return_value.exists = False

        r = consultar_gcp_billing()
        assert "Google Cloud Platform" in r
        assert "bot-dam" in r
        assert "dam-server" in r
        assert "dam-backend" in r
        assert "Free Tier" in r

    @patch("services.tools.gcp_billing_tool.firebase.db")
    def test_consultar_billing_com_snapshot_exibe_valores(self, mock_db):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "cost_amount": 45.50,
            "budget_amount": 100.00,
            "currency": "BRL",
            "percentual": 45.5,
            "budget_name": "Orçamento Mensal",
            "updated_at": "2026-09-03T18:00:00Z"
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        r = consultar_gcp_billing()
        assert "BRL 45.50" in r
        assert "BRL 100.00" in r
        assert "45.5%" in r
        assert "Orçamento Mensal" in r
