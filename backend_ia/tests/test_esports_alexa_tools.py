import unittest
import base64
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from services.tools.alexa_tool import acionar_rotina_alexa, falar_na_alexa

class TestFase5Tools(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "DamBot2026SecureKey!"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"

    @patch("routers.billing.WhatsAppService.send_text")
    def test_billing_alert_webhook_triggers_notification(self, mock_send_text):
        budget_data = {
            "budgetDisplayName": "DAM Cloud Budget",
            "costAmount": 85.50,
            "budgetAmount": 100.00,
            "currencyCode": "BRL"
        }
        encoded_data = base64.b64encode(json.dumps(budget_data).encode("utf-8")).decode("utf-8")
        pubsub_payload = {
            "message": {
                "data": encoded_data,
                "messageId": "PUB_001"
            }
        }

        response = self.client.post(
            "/api/billing-alert",
            json=pubsub_payload,
            headers={"apikey": "DamBot2026SecureKey!"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "alert_processed")
        mock_send_text.assert_called_once()
        sent_msg = mock_send_text.call_args[0][1]
        self.assertIn("Alerta de Orçamento GCP", sent_msg)
        self.assertIn("85.50", sent_msg)

    def test_acionar_rotina_alexa_modo_demo(self):
        settings.VOICE_MONKEY_API_TOKEN = ""
        resultado = acionar_rotina_alexa(rotina="Modo Cinema", ambiente="Sala")
        self.assertIn("Modo Cinema", resultado)
        self.assertIn("Sala", resultado)
        self.assertIn("acionada em modo simulação", resultado)

    @patch("urllib.request.urlopen")
    def test_acionar_rotina_alexa_com_voice_monkey(self, mock_urlopen):
        settings.VOICE_MONKEY_API_TOKEN = "test_vm_token_123"
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.read.return_value = b'{"data": [{"name": "Ligar Luzes", "id": "luzes-123"}]}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        resultado = acionar_rotina_alexa(rotina="Ligar Luzes", ambiente="Quarto")
        self.assertIn("Ligar Luzes", resultado)
        self.assertIn("sua Alexa", resultado)
        self.assertTrue(mock_urlopen.call_count >= 1)

    @patch("urllib.request.urlopen")
    def test_falar_na_alexa_com_voice_monkey(self, mock_urlopen):
        settings.VOICE_MONKEY_API_TOKEN = "test_vm_token_123"
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        resultado = falar_na_alexa(mensagem="O almoço está pronto", ambiente="Cozinha")
        self.assertIn("almoço está pronto", resultado)
        self.assertIn("Alexa está falando", resultado)
        mock_urlopen.assert_called_once()

if __name__ == "__main__":
    unittest.main()
