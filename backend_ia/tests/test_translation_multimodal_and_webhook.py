import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app
from services.whatsapp_service import WhatsAppService
from routers.webhook import process_and_reply

client = TestClient(app)

class TestTranslationMultimodalAndWebhook:
    def test_post_translate_api_endpoint(self):
        """Endpoint REST /api/translate retorna status 200 com payload estruturado."""
        with patch("services.translation_service.TranslationService.translate_text") as mock_trans:
            mock_trans.return_value = {
                "status": "success",
                "original_text": "Hello world",
                "translated_text": "Olá mundo",
                "source_language": "en",
                "target_language": "pt",
                "characters_count": 11,
                "provider": "google_cloud_translation_v2"
            }

            response = client.post("/api/translate", json={
                "text": "Hello world",
                "target_language": "pt"
            })

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["translated_text"] == "Olá mundo"
            assert data["source_language"] == "en"

    def test_get_translate_usage_endpoint(self):
        """Endpoint REST /api/translate/usage retorna dados de FinOps da cota."""
        response = client.get("/api/translate/usage")
        assert response.status_code == 200
        data = response.json()
        assert "characters_used" in data
        assert "monthly_limit" in data
        assert data["monthly_limit"] == 500000

    @patch("routers.webhook.WhatsAppService.send_text")
    @patch("routers.webhook.WhatsAppService.send_voice_note")
    @patch("routers.webhook.ChatRepository.save_log")
    @patch("routers.webhook.AIService.process_message")
    def test_webhook_translation_always_sends_text_for_audio_input(
        self,
        mock_process,
        mock_save_log,
        mock_send_voice,
        mock_send_text
    ):
        """
        P-1003: Requisito estrito do usuário:
        'As traduções devem ser de qualquer lingua para qualquer lingua e ser enviada sempre em formato de texto.'
        Quando o usuário envia um áudio pedindo tradução, o DAM DEVE enviar a resposta em formato de TEXTO
        e NUNCA como mensagem de voz sintetizada.
        """
        import asyncio
        mock_process.return_value = "🌐 **Tradução (EN -> PT):**\nBom dia, como você está?"

        # Simula recebimento de áudio com comando de tradução
        asyncio.run(process_and_reply(
            remote_jid="5571991269995@s.whatsapp.net",
            text="Traduza o que eu disse neste áudio para o português",
            media_base64="dGVzdGU=",
            media_mimetype="audio/ogg"
        ))

        # Garante que send_text foi chamado com a tradução
        mock_send_text.assert_called_once()
        args, _ = mock_send_text.call_args
        assert args[0] == "5571991269995@s.whatsapp.net"
        assert "Tradução" in args[1]

        # Garante que send_voice_note NÃO foi chamado!
        mock_send_voice.assert_not_called()
