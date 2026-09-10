import pytest
from unittest.mock import patch, MagicMock
from services.user_context import UserContext
from services.briefing_service import (
    montar_resumo_matinal,
    enviar_briefing_matinal,
    obter_preferencias_briefing,
    configurar_preferencias_briefing,
    consultar_preferencias_briefing,
    _reset_briefing_preferences,
    _reset_briefing_memory
)
from services.tools.vehicle_tool import (
    consultar_status_veiculo,
    cadastrar_ou_atualizar_veiculo,
    acionar_travas_veiculo,
    _reset_memory_vehicles
)
from services.tools.clash_of_clans_tool import consultar_clash_of_clans
from services.tools.anime_tracker_tool import listar_meus_animes
from services.tools.gift_curator_tool import (
    salvar_ideia_presente,
    consultar_ideias_presente,
    _reset_mock_gift_db
)

@pytest.fixture(autouse=True)
def clean_state():
    _reset_briefing_preferences()
    _reset_briefing_memory()
    _reset_memory_vehicles()
    _reset_mock_gift_db()
    UserContext.set_user("daniel")
    yield
    _reset_briefing_preferences()
    _reset_briefing_memory()
    _reset_memory_vehicles()
    _reset_mock_gift_db()
    UserContext.set_user("daniel")

class TestUserFeaturesAndBriefingIsolation:

    @patch("services.briefing_service.consultar_agenda")
    @patch("services.briefing_service.listar_lembretes_pendentes")
    @patch("services.briefing_service._obter_jogos_furia_hoje")
    @patch("services.briefing_service._obter_animes_lancando_hoje")
    def test_briefing_daniel_default_topics(self, mock_animes, mock_furia, mock_notes, mock_agenda):
        UserContext.set_user("daniel")
        mock_agenda.return_value = "• 10:00 - Reunião"
        mock_notes.return_value = "• Pagar luz"
        mock_furia.return_value = [{"time_a": "FURIA", "time_b": "MOUZ", "horario": "15:00", "campeonato": "Major", "hora_int": 15}]
        mock_animes.return_value = [{"titulo": "Jujutsu Kaisen", "episodio": 12, "horario": "14:00"}]

        resumo = montar_resumo_matinal(user_id="daniel")
        assert "Bom dia!" in resumo
        assert "Compromissos de Hoje" in resumo
        assert "Tarefas & Lembretes" in resumo
        assert "Jogos da FURIA (CS2)" in resumo
        assert "Animes de Hoje" in resumo
        assert "Saúde & Bem-Estar" not in resumo

    @patch("services.briefing_service.consultar_agenda")
    @patch("services.briefing_service.listar_lembretes_pendentes")
    @patch("services.briefing_service._obter_resumo_saude_briefing")
    def test_briefing_lari_default_topics(self, mock_saude, mock_notes, mock_agenda):
        UserContext.set_user("lari")
        mock_agenda.return_value = "• 09:00 - Pilates"
        mock_notes.return_value = "• Tomar vitamina"
        mock_saude.return_value = "• Passos: 8.420 | Calorias: 420 kcal"

        resumo = montar_resumo_matinal(user_id="lari")
        assert "Bom dia!" in resumo
        assert "Compromissos de Hoje" in resumo
        assert "Tarefas & Lembretes" in resumo
        assert "Saúde & Bem-Estar" in resumo
        # Lari não deve ter FURIA, Animes nem Clash no briefing padrão
        assert "Jogos da FURIA" not in resumo
        assert "Animes de Hoje" not in resumo
        assert "Clash of Clans" not in resumo

    def test_configurar_preferencias_briefing_horario_e_topicos(self):
        UserContext.set_user("lari")
        # Altera horário para 07:15 e adiciona tópico veiculo
        msg = configurar_preferencias_briefing(
            horario="07:15",
            adicionar_topicos=["veiculo"]
        )
        assert "07:15" in msg
        assert "veiculo" in msg

        prefs = obter_preferencias_briefing("lari")
        assert prefs["horario"] == "07:15"
        assert "veiculo" in prefs["topicos"]

        # Consulta configuração
        consulta = consultar_preferencias_briefing()
        assert "07:15" in consulta
        assert ("User" in consulta or "Lari" in consulta)

    def test_vehicle_isolation_daniel_vs_lari(self):
        # Daniel possui Fiat Fastback de fábrica
        UserContext.set_user("daniel")
        status_daniel = consultar_status_veiculo()
        assert "Fiat Fastback" in status_daniel

        # Lari inicialmente não possui veículo cadastrado
        UserContext.set_user("lari")
        status_lari_vazio = consultar_status_veiculo()
        assert "você ainda não possui um veículo cadastrado" in status_lari_vazio

        # Lari cadastra o veículo dela
        cad_res = cadastrar_ou_atualizar_veiculo(modelo="Honda HR-V 2023", placa="BRA2E19")
        assert "Honda HR-V 2023" in cad_res
        assert ("User" in cad_res or "Lari" in cad_res)

        # Consulta novamente como Lari
        status_lari_atual = consultar_status_veiculo()
        assert "Honda HR-V 2023" in status_lari_atual
        assert "Fiat Fastback" not in status_lari_atual

        # Comandos de trava de Lari atuam no carro dela
        res_trava = acionar_travas_veiculo("destravar")
        assert "Portas do Honda HR-V 2023 foram destravadas" in res_trava

        # Daniel continua com seu Fiat Fastback intacto
        UserContext.set_user("daniel")
        status_daniel_pos = consultar_status_veiculo()
        assert "Fiat Fastback" in status_daniel_pos

    def test_clash_of_clans_guard_clause(self):
        UserContext.set_user("lari")
        res = consultar_clash_of_clans(tipo="raid")
        assert "não possui uma conta do Clash of Clans" in res

    def test_anime_watchlist_guard_clause(self):
        UserContext.set_user("lari")
        res = listar_meus_animes()
        assert "não possui uma lista de animes nem uma conta AniList" in res

    def test_gift_ideas_isolation(self):
        # Daniel salva uma ideia de presente surpresa para a Lari
        UserContext.set_user("daniel")
        salvar_ideia_presente(pessoa="Lari", relacao="Namorada", ideia="Viagem surpresa a Paris")

        ideias_daniel = consultar_ideias_presente()
        assert "Viagem surpresa a Paris" in ideias_daniel

        # Lari consulta suas ideias de presentes anotadas: NÃO deve ver a surpresa de Daniel
        UserContext.set_user("lari")
        ideias_lari = consultar_ideias_presente()
        assert "Viagem surpresa a Paris" not in ideias_lari

        # Lari salva uma ideia para a Mãe dela
        salvar_ideia_presente(pessoa="Mãe", relacao="Mãe", ideia="Livro de Receitas")
        ideias_lari_atual = consultar_ideias_presente()
        assert "Livro de Receitas" in ideias_lari_atual

        # Daniel não vê as ideias da Lari
        UserContext.set_user("daniel")
        ideias_daniel_atual = consultar_ideias_presente()
        assert "Livro de Receitas" not in ideias_daniel_atual