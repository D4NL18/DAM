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


    def test_gemini_model_chain_constants_and_primary_model(self):
        """
        P-1111: AIService.GEMINI_MODEL_CHAIN deve ser exatamente
        ['gemini-flash-latest', 'gemini-3.8-flash', 'gemini-3.6-flash', 'gemini-3.5-flash']
        e AIService.PRIMARY_MODEL deve ser 'gemini-flash-latest'.
        """
        expected_chain = [
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
        ]
        assert hasattr(AIService, "GEMINI_MODEL_CHAIN")
        assert list(AIService.GEMINI_MODEL_CHAIN) == expected_chain
        assert getattr(AIService, "PRIMARY_MODEL", AIService.GEMINI_MODEL_CHAIN[0]) == "gemini-flash-latest"

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_primary_model_used_first_is_gemini_flash_latest(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-1111: Na execução normal de AIService.process_message, o primeiro modelo
        instanciado em genai.GenerativeModel utiliza model_name='gemini-flash-latest'.
        """
        model = MagicMock()
        chat = MagicMock()
        response = MagicMock()
        candidate = MagicMock()
        candidate.finish_reason = 1
        response.candidates = [candidate]
        response.text = "Resposta com modelo primário gemini-flash-latest"
        chat.send_message.return_value = response
        model.start_chat.return_value = chat
        mock_genai_model.return_value = model

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Bom dia!"
        )

        assert result == "Resposta com modelo primário gemini-flash-latest"
        assert mock_genai_model.call_count == 1
        first_call_kwargs = mock_genai_model.call_args_list[0][1]
        assert first_call_kwargs.get("model_name") == "gemini-flash-latest"

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_fallback_chain_order_when_primary_and_first_fallback_fail(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-1111: Se 'gemini-flash-latest' e 'gemini-3.8-flash' falharem ao enviar mensagem
        e 'gemini-3.6-flash' funcionar, devem ser feitas 3 chamadas a genai.GenerativeModel
        na ordem exata ['gemini-flash-latest', 'gemini-3.8-flash', 'gemini-3.6-flash'].
        """
        model_primary = MagicMock()
        chat_primary = MagicMock()
        chat_primary.send_message.side_effect = Exception("404 Model gemini-flash-latest not found")
        model_primary.start_chat.return_value = chat_primary

        model_fb1 = MagicMock()
        chat_fb1 = MagicMock()
        chat_fb1.send_message.side_effect = Exception("429 ResourceExhausted on gemini-3.8-flash")
        model_fb1.start_chat.return_value = chat_fb1

        model_fb2 = MagicMock()
        chat_fb2 = MagicMock()
        response_fb2 = MagicMock()
        candidate_fb2 = MagicMock()
        candidate_fb2.finish_reason = 1
        response_fb2.candidates = [candidate_fb2]
        response_fb2.text = "Respondido com sucesso pelo fallback gemini-3.6-flash!"
        chat_fb2.send_message.return_value = response_fb2
        model_fb2.start_chat.return_value = chat_fb2

        mock_genai_model.side_effect = [model_primary, model_fb1, model_fb2]

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Qual a previsão de hoje?"
        )

        assert result == "Respondido com sucesso pelo fallback gemini-3.6-flash!"
        assert mock_genai_model.call_count == 3
        called_models = [call[1].get("model_name") for call in mock_genai_model.call_args_list]
        assert called_models == [
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.6-flash",
        ]

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_fallback_reaches_last_model_gemini_3_5_flash_when_all_previous_fail(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-1111: Se os 3 primeiros modelos falharem, o AIService recorre ao último fallback
        'gemini-3.5-flash' na ordem exata da cadeia.
        """
        failing_models = []
        for name in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-3.6-flash"]:
            m = MagicMock()
            c = MagicMock()
            c.send_message.side_effect = Exception(f"Unavailable: {name}")
            m.start_chat.return_value = c
            failing_models.append(m)

        model_last = MagicMock()
        chat_last = MagicMock()
        response_last = MagicMock()
        candidate_last = MagicMock()
        candidate_last.finish_reason = 1
        response_last.candidates = [candidate_last]
        response_last.text = "Respondido pelo último fallback gemini-3.5-flash!"
        chat_last.send_message.return_value = response_last
        model_last.start_chat.return_value = chat_last

        mock_genai_model.side_effect = failing_models + [model_last]

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Teste de resiliência total da cadeia"
        )

        assert result == "Respondido pelo último fallback gemini-3.5-flash!"
        called_models = [call[1].get("model_name") for call in mock_genai_model.call_args_list]
        assert called_models == [
            "gemini-flash-latest",
            "gemini-3.8-flash",
            "gemini-3.6-flash",
            "gemini-3.5-flash",
        ]


    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_temperature_calibrated_to_zero_in_generation_config(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-0804: O modelo deve ser instanciado com generation_config contendo temperature=0.0
        para evitar ao máximo alucinações e manter a resposta estritamente no que foi pedido.
        """
        assert hasattr(AIService, "DEFAULT_GENERATION_CONFIG")
        assert AIService.DEFAULT_GENERATION_CONFIG.get("temperature") == 0.0

        model = MagicMock()
        chat = MagicMock()
        response = MagicMock()
        candidate = MagicMock()
        candidate.finish_reason = 1
        response.candidates = [candidate]
        response.text = "Olá!"
        chat.send_message.return_value = response
        model.start_chat.return_value = chat
        mock_genai_model.return_value = model

        AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Oi"
        )

        call_kwargs = mock_genai_model.call_args_list[0][1]
        gen_cfg = call_kwargs.get("generation_config")
        assert gen_cfg is not None
        assert gen_cfg.get("temperature") == 0.0

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_blocks_hallucinated_finance_registration_when_tool_not_called(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-0805: Se o usuário pedir para cadastrar algo no financeiro e o LLM fingir que cadastrou
        ('Pronto! Cadastrei seu gasto...') sem ter executado registrar_gasto/registrar_receita,
        o AIService deve bloquear a confirmação falsa e retornar um feedback de erro real avisando
        que NÃO foi cadastrado.
        """
        model = MagicMock()
        chat = MagicMock()
        fake_response = MagicMock()
        candidate = MagicMock()
        candidate.finish_reason = 1
        fake_response.candidates = [candidate]
        fake_response.text = "Pronto! Cadastrei o seu gasto de R$ 120,00 com Mercado no Cartão de Crédito Pessoal!"
        chat.send_message.return_value = fake_response
        model.start_chat.return_value = chat
        mock_genai_model.return_value = model

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Cadastra 120 reais de mercado no cartão de crédito pessoal"
        )

        # Não pode deixar passar a mentira de que cadastrou com sucesso
        assert "NÃO foi cadastrado" in result or "não foi gravad" in result.lower() or "não foi cadastrad" in result.lower()
        assert "❌" in result or "⚠️" in result

    @patch("services.ai_service.ConversationCacheService.get_cached_response", return_value=None)
    @patch("services.ai_service.ChatRepository.get_recent_history", return_value=[])
    @patch("services.ai_service.genai.GenerativeModel")
    def test_surfaces_real_tool_error_when_llm_hides_failure(
        self, mock_genai_model, mock_history, mock_cache
    ):
        """
        P-0805: Se registrar_gasto falhar (ex: banco indisponível ou erro ao salvar) durante o turno
        e o LLM tentar fingir que conseguiu cadastrar, o AIService deve exibir o erro real da tool.
        """
        from services.tools.finance_tool import registrar_gasto

        def side_effect_send_message(*args, **kwargs):
            # Simula a chamada automática da tool falhando por banco indisponível
            with patch("services.tools.finance_tool.firebase.db", None):
                registrar_gasto(
                    descricao="Farmácia",
                    valor=95.0,
                    categoria="Farmácia",
                    metodo_pagamento="Pix"
                )
            fake_ok = MagicMock()
            cand = MagicMock()
            cand.finish_reason = 1
            fake_ok.candidates = [cand]
            fake_ok.text = "Cadastrei com sucesso R$ 95,00 na categoria Farmácia!"
            return fake_ok

        model = MagicMock()
        chat = MagicMock()
        chat.send_message.side_effect = side_effect_send_message
        model.start_chat.return_value = chat
        mock_genai_model.return_value = model

        result = AIService.process_message(
            remote_jid="5511999999999@s.whatsapp.net",
            user_text="Cadastra 95 reais de farmácia no pix"
        )

        assert "banco de dados não está disponível" in result.lower() or "não foi cadastrado" in result.lower()
        assert "Cadastrei com sucesso" not in result

    def test_tools_dispatcher_routes_finance_registration_phrases_and_multiturn_cards(self):
        """
        P-0805: Frases com 'cadastra', 'lança', 'registra ... reais' e continuações de cartão
        ('no cartão pessoal') devem sempre carregar registrar_gasto e registrar_receita.
        """
        from services.tools_dispatcher import ToolsDispatcher

        frases = [
            "Cadastra 50 reais de mercado",
            "Lança R$ 80,00 da conta de luz",
            "Registra no financeiro 45 reais de uber",
            "Cadastra um gasto de 120 reais na farmácia",
        ]
        for frase in frases:
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is not None, f"Tools vieram None para '{frase}'"
            names = [getattr(t, "__name__", "") for t in tools]
            assert "registrar_gasto" in names, f"registrar_gasto ausente para '{frase}'"
            assert "registrar_receita" in names, f"registrar_receita ausente para '{frase}'"

        # Multi-turn: usuário responde apenas qual o cartão após pergunta anterior de finanças
        tools_followup = ToolsDispatcher.resolve_tools(
            "Foi no cartão pessoal",
            context_text="Cadastra 50 reais de mercado"
        )
        assert tools_followup is not None
        names_followup = [getattr(t, "__name__", "") for t in tools_followup]
        assert "registrar_gasto" in names_followup
