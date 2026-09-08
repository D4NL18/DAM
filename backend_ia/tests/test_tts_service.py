import pytest
from unittest.mock import patch, MagicMock
from services.tts_service import TTSService
from services.whatsapp_service import WhatsAppService


class TestTTSServiceUnit:
    def setup_method(self):
        # Limpa cache do TTS antes de cada teste
        TTSService._cache.clear()

    def test_sanitize_text_for_speech_markdown_removal(self):
        markdown_text = (
            "# Relatório Matinal\n"
            "* Bom dia, **Daniel**! Seu dia será _produtivo_.\n"
            "- Compromisso: Reunião às ~09:00~ 10:00.\n"
            "Acesse o link: https://google.com para mais detalhes."
        )
        sanitized = TTSService.sanitize_text_for_speech(markdown_text)

        assert "#" not in sanitized
        assert "**" not in sanitized
        assert "*" not in sanitized
        assert "_" not in sanitized
        assert "~" not in sanitized
        assert "https://google.com" not in sanitized
        assert "o link compartilhado" in sanitized or "link" in sanitized
        assert "Bom dia, Daniel" in sanitized

    def test_sanitize_text_removes_code_blocks_and_excess_emojis(self):
        text = "Aqui está o código: ```python\nprint('hello')\n```. Tenha um ótimo dia! 🚀🔥🎉❤️"
        sanitized = TTSService.sanitize_text_for_speech(text)
        assert "print('hello')" not in sanitized
        assert "```" not in sanitized
        # Emojis removidos ou limpos para não gerar leitura robotizada
        assert "🚀" not in sanitized
        assert "Tenha um ótimo dia" in sanitized

    def test_should_reply_with_audio_audio_message(self):
        assert TTSService.should_reply_with_audio(
            incoming_text="Transcreva e responda ao áudio.",
            message_type="audioMessage"
        ) is True

    def test_should_reply_with_audio_explicit_voice_requests(self):
        assert TTSService.should_reply_with_audio("Pode me mandar em áudio?") is True
        assert TTSService.should_reply_with_audio("Responde por voz por favor") is True
        assert TTSService.should_reply_with_audio("Grave um áudio explicando") is True
        assert TTSService.should_reply_with_audio("Me manda áudio do resumo") is True
        assert TTSService.should_reply_with_audio("Fale para mim o cardápio") is True

    def test_should_reply_with_audio_regular_text_is_false(self):
        assert TTSService.should_reply_with_audio("Quanto gastei no mercado?") is False
        assert TTSService.should_reply_with_audio("Qual o trânsito até o trabalho?") is False
        assert TTSService.should_reply_with_audio("Bom dia assistente") is False

    @patch("services.tts_service.TTSService._gerar_audio_provedor")
    def test_synthesize_speech_and_caching(self, mock_gerar):
        mock_gerar.return_value = b"MOCK_AUDIO_BYTES_123"

        texto = "Olá, seu saldo no banco de horas é positivo."
        audio_bytes1 = TTSService.synthesize_speech(texto)
        assert audio_bytes1 == b"MOCK_AUDIO_BYTES_123"
        assert mock_gerar.call_count == 1

        # Segunda chamada para o mesmo texto deve vir do cache L1 FinOps sem chamar provedor
        audio_bytes2 = TTSService.synthesize_speech(texto)
        assert audio_bytes2 == b"MOCK_AUDIO_BYTES_123"
        assert mock_gerar.call_count == 1

    @patch("services.tts_service.TTSService._gerar_audio_provedor")
    def test_synthesize_speech_fallback_none_on_error(self, mock_gerar):
        mock_gerar.side_effect = Exception("TTS API quota exceeded")
        audio = TTSService.synthesize_speech("Texto qualquer")
        assert audio is None

    @patch("requests.post")
    def test_whatsapp_service_send_voice_note(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"status": "success", "message": "audio sent"}
        mock_post.return_value = mock_resp

        audio_bytes = b"FAKE_OGG_OPUS_AUDIO"
        res = WhatsAppService.send_voice_note("5511999999999@s.whatsapp.net", audio_bytes)
        assert res is not None
        assert res.get("status") == "success"

        # Verifica se chamou o endpoint sendWhatsAppAudio
        call_url = mock_post.call_args[0][0]
        assert "sendWhatsAppAudio" in call_url
        call_payload = mock_post.call_args[1]["json"]
        assert call_payload["number"] == "5511999999999@s.whatsapp.net"
        assert "audio" in call_payload

    @patch("routers.webhook.AIService.process_message")
    @patch("routers.webhook.WhatsAppService.send_voice_note")
    @patch("routers.webhook.WhatsAppService.send_text")
    @patch("routers.webhook.TTSService.synthesize_speech")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_process_and_reply_with_audio(
        self, mock_save, mock_tts, mock_send_text, mock_send_voice, mock_ai
    ):
        import asyncio
        from routers.webhook import process_and_reply

        mock_ai.return_value = "Seu dia terá 3 reuniões importantes."
        mock_tts.return_value = b"AUDIO_BYTES_RESULT"
        mock_send_voice.return_value = {"status": "ok"}

        # Simula resposta para mensagem de áudio
        asyncio.run(process_and_reply(
            remote_jid="5511999999999@s.whatsapp.net",
            text="Transcreva e responda ao áudio.",
            media_base64="dGVzdGU=",
            media_mimetype="audio/ogg"
        ))

        mock_tts.assert_called_once_with("Seu dia terá 3 reuniões importantes.")
        mock_send_voice.assert_called_once()
        mock_send_text.assert_not_called()

    @patch("routers.webhook.AIService.process_message")
    @patch("routers.webhook.WhatsAppService.send_voice_note")
    @patch("routers.webhook.WhatsAppService.send_text")
    @patch("routers.webhook.TTSService.synthesize_speech")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_fallback_to_text_when_tts_fails(
        self, mock_save, mock_tts, mock_send_text, mock_send_voice, mock_ai
    ):
        import asyncio
        from routers.webhook import process_and_reply

        mock_ai.return_value = "Seu dia terá 3 reuniões importantes."
        mock_tts.return_value = None  # Falha no TTS

        asyncio.run(process_and_reply(
            remote_jid="5511999999999@s.whatsapp.net",
            text="Transcreva e responda ao áudio.",
            media_base64="dGVzdGU=",
            media_mimetype="audio/ogg"
        ))

        mock_tts.assert_called_once()
        mock_send_voice.assert_not_called()
        mock_send_text.assert_called_once_with(
            "5511999999999@s.whatsapp.net",
            "Seu dia terá 3 reuniões importantes."
        )

    def test_should_reply_with_audio_converta_mensagem_para_audio(self):
        assert TTSService.should_reply_with_audio("converta essa mensagem para audio") is True
        assert TTSService.should_reply_with_audio("converta em áudio") is True
        assert TTSService.should_reply_with_audio("transforme isso em audio") is True
        assert TTSService.should_reply_with_audio("mande em audio") is True

    def test_quebrar_em_chunks_texto_longo(self):
        texto_longo = (
            "Bom dia! Aqui está o seu resumo matinal de hoje, sexta-feira, 4 de setembro. "
            "Nos seus compromissos do dia, você tem Trabalho às 8 horas e Fisioterapia às 13 e 20. "
            "Você não possui tarefas ou lembretes pendentes para hoje. "
            "Nos eSports, a FURIA joga hoje às 14 e 30 contra a Team Vitality. Tenha um excelente dia!"
        )
        chunks = TTSService._quebrar_em_chunks(texto_longo, max_chars=160)
        assert len(chunks) > 1
        for c in chunks:
            assert len(c) <= 160
            assert len(c.strip()) > 0


