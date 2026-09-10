import pytest
from services.tools_dispatcher import ToolsDispatcher
from services.prompts.prompt_composer import PromptComposer
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user():
    UserContext.set_user("daniel", "5571991269995")


class TestToolsDispatcher:
    def test_casual_conversation_returns_none_tools(self):
        """CA-01 & P-1101: Mensagens de conversa casual retornam tools=None para zero overhead."""
        frases_casuais = [
            "Olá!",
            "Bom dia DAM, tudo bem?",
            "Boa noite!",
            "Obrigado pela ajuda",
            "Quem é você?",
            "Valeu demais!",
            "Qual é a capital da França?",
            "Conta uma piada"
        ]
        for frase in frases_casuais:
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is None, f"Esperava None para frase casual: '{frase}'"

    def test_finance_intent_returns_only_finance_tools(self):
        """CA-01: Mensagens de finanças retornam estritamente ferramentas financeiras."""
        frases_financeiras = [
            "Gastei 50 reais no almoço",
            "Comprei um livro por 89,90",
            "Quanto gastei esse mês?",
            "Resumo de despesas da semana"
        ]
        for frase in frases_financeiras:
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is not None
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert any("gasto" in name for name in tool_names), f"Faltou tool de gasto para '{frase}'"
            assert not any("anime" in name for name in tool_names)
            assert not any("rota" in name for name in tool_names)

    def test_transit_intent_returns_only_maps_tools(self):
        """CA-01: Mensagens de trânsito retornam apenas ferramentas de mapas/rotas."""
        frases_transito = [
            "Como tá o trânsito pra Barra?",
            "Qual o tempo de percurso até o aeroporto?",
            "Que horas devo sair para chegar às 15h?"
        ]
        for frase in frases_transito:
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is not None
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert any("rota" in name or "horario_saida" in name for name in tool_names)
            assert not any("gasto" in name for name in tool_names)

    def test_calendar_intent_returns_calendar_tools(self):
        """CA-01: Mensagens de agenda retornam ferramentas de calendário/lembretes."""
        tools = ToolsDispatcher.resolve_tools("O que eu tenho agendado para hoje?")
        assert tools is not None
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert any("agenda" in name or "lembrete" in name for name in tool_names)

    def test_media_context_returns_vision_and_converter_tools(self):
        """P-1101: Quando houver imagem ou documento, ferramentas adequadas são carregadas."""
        tools = ToolsDispatcher.resolve_tools("Analise esta imagem enviada pelo usuário.", has_media=True)
        assert tools is not None
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert any("gasto" in name or "cardapio" in name or "arquivos" in name for name in tool_names)


class TestPromptComposerModularity:
    def test_core_prompt_is_concise(self):
        """P-1102: System prompt padrão sem domínios específicos deve ser conciso."""
        prompt = PromptComposer.compose_system_instruction(domains=[])
        assert "Você é o DAM" in prompt
        assert "PRECISÃO TEMPORAL" in prompt
        # Regras pesadas não devem estar presentes se não solicitadas
        assert "Dietbox" not in prompt
        assert "Anilist" not in prompt

    def test_on_demand_domain_injection(self):
        """P-1102: Injeta regras de domínio apenas quando explicitamente solicitadas."""
        prompt_fin = PromptComposer.compose_system_instruction(domains=["finance"])
        assert "FINANCEIRO" in prompt_fin or "despesas" in prompt_fin.lower()
        assert "Dietbox" not in prompt_fin

        prompt_nutri = PromptComposer.compose_system_instruction(domains=["nutrition"])
        assert "Dietbox" in prompt_nutri or "substituição" in prompt_nutri.lower()
