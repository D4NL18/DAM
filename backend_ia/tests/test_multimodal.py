import unittest
import base64
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from services.ai_service import AIService
from services.whatsapp_service import WhatsAppService

class TestMultimodalIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "DamBot2026SecureKey!"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"
        self.headers = {"apikey": "DamBot2026SecureKey!"}

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_receives_image_message_with_inline_base64(self, mock_save_log, mock_process):
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

    @patch("routers.webhook.WhatsAppService.get_base64_from_media_message")
    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_downloads_image_when_not_in_payload(self, mock_save_log, mock_process, mock_get_media):
        """Cenário real da Evolution API: payload NÃO contém base64 inline."""
        dummy_b64 = base64.b64encode(b"real_photo_bytes").decode("utf-8")
        mock_get_media.return_value = {
            "base64": f"data:image/jpeg;base64,{dummy_b64}",
            "mimetype": "image/jpeg"
        }

        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "IMG_REAL_001"
                },
                "messageType": "imageMessage",
                "message": {
                    "imageMessage": {
                        "caption": "Olha essa foto",
                        "mimetype": "image/jpeg",
                        "url": "https://mmg.whatsapp.net/d/f/..."
                    }
                }
            }
        }

        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "processing")
        
        # Deve ter buscado ativamente na Evolution API
        mock_get_media.assert_called_once()
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        self.assertEqual(args[0], "5511987654321@s.whatsapp.net")
        self.assertEqual(args[1], "Olha essa foto")
        self.assertIsNotNone(args[2])
        self.assertEqual(args[3], "image/jpeg")

    @patch("routers.webhook.WhatsAppService.get_base64_from_media_message")
    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_downloads_audio_when_not_in_payload(self, mock_save_log, mock_process, mock_get_media):
        """Cenário real da Evolution API para áudio gravado."""
        dummy_audio_b64 = base64.b64encode(b"real_voice_bytes").decode("utf-8")
        mock_get_media.return_value = {
            "base64": dummy_audio_b64,
            "mimetype": "audio/ogg; codecs=opus"
        }

        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321@s.whatsapp.net",
                    "fromMe": False,
                    "id": "AUD_REAL_001"
                },
                "messageType": "audioMessage",
                "message": {
                    "audioMessage": {
                        "mimetype": "audio/ogg; codecs=opus",
                        "seconds": 5
                    }
                }
            }
        }

        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        mock_get_media.assert_called_once()
        mock_process.assert_called_once()
        args = mock_process.call_args[0]
        self.assertEqual(args[0], "5511987654321@s.whatsapp.net")
        self.assertEqual(args[2], dummy_audio_b64)
        # O MIME type de áudio deve ser normalizado para audio/ogg
        self.assertEqual(args[3], "audio/ogg")

    @patch("services.whatsapp_service.requests.post")
    def test_whatsapp_service_get_base64_from_media_message_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "base64": "data:image/jpeg;base64,abc123xyz",
            "mimetype": "image/jpeg"
        }
        mock_post.return_value = mock_resp

        result = WhatsAppService.get_base64_from_media_message("MSG_123")
        self.assertIsNotNone(result)
        self.assertEqual(result.get("base64"), "data:image/jpeg;base64,abc123xyz")
        self.assertEqual(result.get("mimetype"), "image/jpeg")

    @patch("services.whatsapp_service.requests.post")
    def test_whatsapp_service_get_base64_from_media_message_failure(self, mock_post):
        mock_post.side_effect = Exception("Evolution timeout")
        result = WhatsAppService.get_base64_from_media_message("MSG_FAIL")
        self.assertIsNone(result)

    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.ChatRepository.get_recent_history")
    def test_ai_service_processes_multimodal_image_with_data_uri_prefix(self, mock_history, mock_model_cls):
        mock_history.return_value = []
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Identifiquei R$ 150 na nota fiscal."
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_model_cls.return_value = mock_model

        raw_bytes = b"test_image_data_bytes_123"
        dummy_b64 = base64.b64encode(raw_bytes).decode("utf-8")
        # Base64 contendo prefixo data URI e quebras de linha
        data_uri_b64 = f"data:image/jpeg;base64,\n{dummy_b64}\n"

        resposta = AIService.process_message(
            remote_jid="5511987654321@s.whatsapp.net",
            user_text="Analise a nota fiscal",
            media_base64=data_uri_b64,
            media_mimetype="image/jpeg"
        )

        self.assertEqual(resposta, "Identifiquei R$ 150 na nota fiscal.")
        mock_chat.send_message.assert_called_once()
        call_content = mock_chat.send_message.call_args[0][0]
        self.assertIsInstance(call_content, list)
        self.assertEqual(call_content[0]["mime_type"], "image/jpeg")
        # Os bytes decodificados devem bater exatamente com o original
        self.assertEqual(call_content[0]["data"], raw_bytes)

    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.ChatRepository.get_recent_history")
    def test_ai_service_processes_audio_with_codec_mimetype_normalization(self, mock_history, mock_model_cls):
        mock_history.return_value = []
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Transcrição do áudio."
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_model_cls.return_value = mock_model

        raw_audio_bytes = b"fake_audio_stream_data"
        dummy_audio_b64 = base64.b64encode(raw_audio_bytes).decode("utf-8")

        resposta = AIService.process_message(
            remote_jid="5511987654321@s.whatsapp.net",
            user_text="Transcreva o áudio",
            media_base64=dummy_audio_b64,
            media_mimetype="audio/ogg; codecs=opus"
        )

        self.assertEqual(resposta, "Transcrição do áudio.")
        mock_chat.send_message.assert_called_once()
        call_content = mock_chat.send_message.call_args[0][0]
        # MIME type deve ser normalizado para audio/ogg no envio para o Gemini
        self.assertEqual(call_content[0]["mime_type"], "audio/ogg")
        self.assertEqual(call_content[0]["data"], raw_audio_bytes)

if __name__ == "__main__":
    unittest.main()

