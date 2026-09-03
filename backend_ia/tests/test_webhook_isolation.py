import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings

class TestWebhookIsolation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "TEST_WEBHOOK_KEY"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"
        self.headers = {"apikey": "TEST_WEBHOOK_KEY"}

    def _build_payload(self, event="messages.upsert", remote_jid="5511987654321@s.whatsapp.net", text="Olá bot", from_me=False, message_id="MSG_123"):
        return {
            "event": event,
            "data": {
                "key": {
                    "remoteJid": remote_jid,
                    "fromMe": from_me,
                    "id": message_id
                },
                "message": {
                    "conversation": text
                }
            }
        }

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_ignores_non_upsert_events(self, mock_save_log, mock_process):
        payload = {"event": "presence.update", "data": {}}
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        mock_process.assert_not_called()
        mock_save_log.assert_not_called()

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_ignores_group_messages(self, mock_save_log, mock_process):
        payload = self._build_payload(remote_jid="120363025555555555@g.us", text="Mensagem no grupo")
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        mock_process.assert_not_called()
        mock_save_log.assert_not_called()

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_ignores_unauthorized_phone(self, mock_save_log, mock_process):
        payload = self._build_payload(remote_jid="5511911112222@s.whatsapp.net", text="Oi de um estranho")
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        mock_process.assert_not_called()
        mock_save_log.assert_not_called()

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_failsafe_when_allowed_phone_empty(self, mock_save_log, mock_process):
        settings.ALLOWED_PHONE_NUMBER = ""
        payload = self._build_payload(remote_jid="5511987654321@s.whatsapp.net", text="Oi")
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        mock_process.assert_not_called()
        mock_save_log.assert_not_called()

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_anti_loop_ignores_bot_responses(self, mock_save_log, mock_process):
        payload = self._build_payload(
            remote_jid="5511987654321@s.whatsapp.net", 
            text="Mensagem enviada pelo bot\u200b"
        )
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        mock_process.assert_not_called()
        mock_save_log.assert_not_called()

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_processes_valid_self_chat(self, mock_save_log, mock_process):
        payload = self._build_payload(
            remote_jid="5511987654321@s.whatsapp.net", 
            text="Guardei a chave na gaveta"
        )
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "processing")
        mock_save_log.assert_called_once()
        mock_process.assert_called_once_with("5511987654321@s.whatsapp.net", "Guardei a chave na gaveta", None, None)

if __name__ == '__main__':
    unittest.main()
