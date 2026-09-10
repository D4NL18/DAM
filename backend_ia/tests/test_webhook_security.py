import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings

class TestWebhookSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "DamBot2026SecureKey!"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"

    def test_secops_blocks_sql_injection_in_apikey(self):
        """Injeção SQL no header de autenticação deve ser bloqueada com 401"""
        malicious_headers = {"apikey": "' OR '1'='1"}
        response = self.client.post("/api/whatsapp/webhook", json={"test": "hack"}, headers=malicious_headers)
        self.assertEqual(response.status_code, 401)

    def test_secops_blocks_invalid_token(self):
        """Tentativa de acesso com token aleatório deve retornar 401"""
        headers = {"apikey": "invalid_token_attempt"}
        response = self.client.post("/api/whatsapp/webhook", json={"test": "data"}, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_secops_blocks_spoofed_jid_domain(self):
        """JID com número do usuário embutido em domínio falso deve ser rejeitado"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        # Tentativa de spoofing colocando o número alvo como domínio ou canal
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "attacker@5511987654321.com",
                    "fromMe": False,
                    "id": "HACK_001"
                },
                "message": {"conversation": "exploit"}
            }
        }
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

    def test_secops_blocks_group_spoofing(self):
        """Mesmo com número no ID do grupo, deve ser rejeitado"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321-1600000000@g.us",
                    "fromMe": False,
                    "id": "HACK_002"
                },
                "message": {"conversation": "hack no grupo"}
            }
        }
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

    def test_secops_survives_malformed_nested_json(self):
        """Payload truncado ou aninhado maliciosamente não deve estourar 500"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        payload = {"event": "messages.upsert", "data": "invalid_type_string_instead_of_dict"}
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

    @patch("routers.webhook.WhatsAppService.get_base64_from_media_message")
    def test_secops_blocks_media_download_for_unauthorized_user(self, mock_get_media):
        """Usuário não autorizado enviando mídia jamais deve acionar requisições à Evolution API"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5521999999999@s.whatsapp.net",
                    "fromMe": False,
                    "id": "UNAUTH_IMG_001"
                },
                "messageType": "imageMessage",
                "message": {
                    "imageMessage": {
                        "mimetype": "image/jpeg"
                    }
                }
            }
        }
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")
        self.assertEqual(response.json().get("reason"), "unauthorized_user")
        # Garante que NENHUMA requisição de download de mídia foi disparada
        mock_get_media.assert_not_called()

    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.ChatRepository.get_recent_history")
    def test_secops_handles_corrupt_base64_in_ai_service(self, mock_history, mock_model_cls):
        """Base64 corrompido maliciosamente não deve derrubar o serviço com exceção não tratada"""
        from services.ai_service import AIService
        mock_history.return_value = []
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Falha de processamento tratada."
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_model_cls.return_value = mock_model

        # Base64 corrompido com caracteres inválidos
        corrupt_b64 = "!!!NotAValidBase64String###%%%"
        result = AIService.process_message(
            remote_jid="5511987654321@s.whatsapp.net",
            user_text="Teste de payload corrompido",
            media_base64=corrupt_b64,
            media_mimetype="image/jpeg"
        )
        # O sistema deve capturar a exceção e retornar a resposta amigável de fallback
        self.assertIn("Desculpe", result)

if __name__ == '__main__':
    unittest.main()

