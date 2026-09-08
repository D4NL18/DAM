import unittest
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from services.ai_service import AIService

class TestMultimodalIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "DamBot2026SecureKey!"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"
        self.headers = {"apikey": "DamBot2026SecureKey!"}

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_receives_image_message(self, mock_save_log, mock_process):
        dummy_b64 = base64.b64encode(b"fake_image_bytes").decode("utf-8")
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "IMG_001"
                },
                "messageType": "imageMessage",
                "message": {
                    "imageMessage": {
                        "caption": "Nota do restaurante",
                        "mimetype": "image/jpeg"
                    },
                    "base64": dummy_b64
                }
            }
        }

        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "processing")
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        self.assertEqual(args[0], "5511987654321@s.whatsapp.net")
        self.assertEqual(args[1], "Nota do restaurante")
        self.assertEqual(args[2], dummy_b64)
        self.assertEqual(args[3], "image/jpeg")

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_receives_audio_message(self, mock_save_log, mock_process):
        dummy_audio_b64 = base64.b64encode(b"fake_audio_bytes").decode("utf-8")
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "AUD_001"
                },
                "messageType": "audioMessage",
                "message": {
                    "audioMessage": {
                        "mimetype": "audio/ogg; codecs=opus",
                        "seconds": 4
                    },
                    "base64": dummy_audio_b64
                }
            }
        }

        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "processing")
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        self.assertEqual(args[0], "5511987654321@s.whatsapp.net")
        self.assertEqual(args[2], dummy_audio_b64)
        self.assertEqual(args[3], "audio/ogg; codecs=opus")

    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.ChatRepository.get_recent_history")
    def test_ai_service_processes_multimodal_image(self, mock_history, mock_model_cls):
        mock_history.return_value = []
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Identifiquei R$ 150 na nota fiscal."
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_model_cls.return_value = mock_model

        dummy_b64 = base64.b64encode(b"test_image_data").decode("utf-8")
        resposta = AIService.process_message(
            remote_jid="5511987654321@s.whatsapp.net",
            user_text="Analise a nota fiscal",
            media_base64=dummy_b64,
            media_mimetype="image/jpeg"
        )

        self.assertEqual(resposta, "Identifiquei R$ 150 na nota fiscal.")
        mock_chat.send_message.assert_called_once()
        call_content = mock_chat.send_message.call_args[0][0]
        # Deve enviar uma lista contendo a parte binária da imagem e o texto
        self.assertIsInstance(call_content, list)
        self.assertEqual(len(call_content), 2)
        self.assertEqual(call_content[0]["mime_type"], "image/jpeg")
        self.assertIn("Analise a nota fiscal", call_content[1])

if __name__ == "__main__":
    unittest.main()
