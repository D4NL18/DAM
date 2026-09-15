import pytest
from unittest.mock import patch, MagicMock
from services.ai_service import AIService
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user():
    UserContext.set_user("daniel", "5511999999999")


class TestAIServiceResilience:
    """Suíte de testes para resiliência e auto-healing da IA contra MALFORMED_FUNCTION_CALL (P-1108)."""

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_auto_healing_retry_when_malformed_function_call_occurs(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-1108: Quando o modelo com tools=None falha com finish_reason=10 (MALFORMED_FUNCTION_CALL)
        ou lança ValueError ao acessar response.text, o AIService deve acionar o Auto-Healing
        com o catálogo completo de ferramentas e retornar a resposta com sucesso.
        """
        # Mock do primeiro modelo (tentativa normal com tools=None ou restritas)
        first_model = MagicMock()
        first_chat = MagicMock()
        first_response = MagicMock()
        first_candidate = MagicMock()
        first_candidate.finish_reason = 10  # MALFORMED_FUNCTION_CALL
        first_response.candidates = [first_candidate]
        type(first_response).text = property(lambda self: (_ for _ in ()).throw(ValueError("Invalid operation: finish_reason: 10")))
        first_chat.send_message.return_value = first_response
        first_model.start_chat.return_value = first_chat

        # Mock do segundo modelo (fallback/auto-healing com todas as tools)
        fallback_model = MagicMock()
        fallback_chat = MagicMock()
        fallback_response = MagicMock()
        fallback_candidate = MagicMock()
        fallback_candidate.finish_reason = 1  # STOP
        fallback_response.candidates = [fallback_candidate]
        fallback_response.text = "Agendei seu compromisso para sábado às 19h no Google Calendar!"
        fallback_chat.send_message.return_value = fallback_response
        fallback_model.start_chat.return_value = fallback_chat

        # Alterna entre o primeiro modelo e o fallback
        mock_genai_model.side_effect = [first_model, fallback_model]

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Alguma frase que causou malformed call inesperada"
        )

        assert result == "Agendei seu compromisso para sábado às 19h no Google Calendar!"
        # Verifica se o fallback foi invocado com ferramentas e auto-calling
        assert mock_genai_model.call_count == 2
        fallback_call_kwargs = mock_genai_model.call_args_list[1][1]
        assert fallback_call_kwargs.get("tools") is not None
        assert len(fallback_call_kwargs.get("tools")) > 10

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_casual_chat_without_error_returns_cleanly(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """Conversas casuais funcionam com tools=None sem acionar retentativa."""
        model = MagicMock()
        chat = MagicMock()
        response = MagicMock()
        candidate = MagicMock()
        candidate.finish_reason = 1  # STOP
        response.candidates = [candidate]
        response.text = "Olá! Como posso ajudar você hoje?"
        chat.send_message.return_value = response
        model.start_chat.return_value = chat

        mock_genai_model.return_value = model

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Olá DAM, tudo bem?"
        )

        assert result == "Olá! Como posso ajudar você hoje?"
        assert mock_genai_model.call_count == 1
        call_kwargs = mock_genai_model.call_args[1]
        assert call_kwargs.get("tools") is None
