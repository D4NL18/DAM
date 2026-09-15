import pytest
from services.tools_dispatcher import ToolsDispatcher
from services.prompts.prompt_composer import PromptComposer
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user():
    UserContext.set_user("daniel", "5511999999999")


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

    def test_natural_calendar_events_detection(self):
        """P-1108: Expressões naturais de compromissos ativam o domínio calendar_notes."""
        frases_naturais = [
            "Sabado tenho noite de jogos na casa de clara às 19h",
            "Amanhã tenho médico às 15h",
            "Sexta tenho aniversário da minha mãe",
            "Domingo vou ter almoço em família às 12:30",
            "Quarta tenho dentista",
            "Tenho reunião às 10h",
            "Marque uma consulta na quinta às 14h",
            "Anota um lembrete para comprar pão",
            "Lembre-se de tomar remédio às 20h"
        ]
        for frase in frases_naturais:
            domains = ToolsDispatcher.detect_domains(frase)
            assert "calendar_notes" in domains, f"Falhou em detectar calendar_notes na frase: '{frase}'"
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is not None, f"Esperava tools não None para: '{frase}'"
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert any("agenda" in name or "lembrete" in name for name in tool_names)

    def test_get_all_tools(self):
        """P-1108: ToolsDispatcher disponibiliza o catálogo completo de ferramentas para resiliência/auto-healing."""
        all_tools = ToolsDispatcher.get_all_tools()
        assert len(all_tools) > 20
        tool_names = [getattr(t, "__name__", str(t)) for t in all_tools]
        assert "agendar_evento" in tool_names
        assert "registrar_gasto" in tool_names
        assert "consultar_rota" in tool_names

    def test_media_context_returns_vision_and_converter_tools(self):
        """P-1101: Quando houver imagem ou documento, ferramentas adequadas são carregadas."""
        tools = ToolsDispatcher.resolve_tools("Analise esta imagem enviada pelo usuário.", has_media=True)
        assert tools is not None
        tool_names = [getattr(t, "__name__", str(t)) for t in tools]
        assert any("gasto" in name or "cardapio" in name or "arquivos" in name for name in tool_names)


class TestPromptComposerModularity:
    def test_core_prompt_is_concise(self):
        """P-1102 & P-1108: System prompt padrão sem domínios específicos deve ser conciso e livre de referências a tools."""
        prompt = PromptComposer.compose_system_instruction(domains=[])
        assert "You are DAM" in prompt or "Você é o DAM" in prompt
        assert "TIME PRECISION" in prompt or "PRECISÃO TEMPORAL" in prompt
        # Regras pesadas não devem estar presentes se não solicitadas
        assert "Dietbox" not in prompt
        assert "Anilist" not in prompt
        # P-1108: Não deve conter instruções literais de execução de ferramentas quando tools=None
        assert "`agendar_evento`" not in prompt
        assert "`salvar_video`" not in prompt
        assert "`gerenciar_arquivos`" not in prompt
        assert "`listar_lembretes_pendentes`" not in prompt

    def test_on_demand_domain_injection(self):
        """P-1102 & P-1108: Injeta regras de domínio apenas quando explicitamente solicitadas."""
        prompt_fin = PromptComposer.compose_system_instruction(domains=["finance"])
        assert "FINANCIAL" in prompt_fin or "FINANCEIRO" in prompt_fin or "despesas" in prompt_fin.lower()
        assert "Dietbox" not in prompt_fin

        prompt_nutri = PromptComposer.compose_system_instruction(domains=["nutrition"])
        assert "Dietbox" in prompt_nutri or "substituição" in prompt_nutri.lower() or "nutrition" in prompt_nutri.lower()

        prompt_cal = PromptComposer.compose_system_instruction(domains=["calendar_notes"])
        assert "agendar_evento" in prompt_cal
        assert "listar_lembretes_pendentes" in prompt_cal

        prompt_video = PromptComposer.compose_system_instruction(domains=["saved_videos"])
        assert "salvar_video" in prompt_video

        prompt_files = PromptComposer.compose_system_instruction(domains=["media_files"])
        assert "gerenciar_arquivos" in prompt_files

