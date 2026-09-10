"""
Testes Unitários (TDD) para GP-04.1: Correções e Aprimoramentos do Morning Briefing
Cobre as Regras de Negócio P-0410 a P-0418.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from services.user_context import UserContext
import services.briefing_service as briefing_service
from services.briefing_service import (
    montar_resumo_matinal,
    enviar_briefing_matinal,
    obter_preferencias_briefing,
    salvar_preferencias_briefing,
    _obter_info_animes_briefing,
    _obter_alertas_coc,
    _reset_briefing_memory,
    _reset_briefing_preferences,
    TZ_BRASILIA
)
from services.tools.notes_tool import (
    criar_lembrete,
    listar_lembretes_pendentes,
    _reset_mock_storage
)
from services.tools.anime_tracker_tool import (
    _reset_memory_watchlist,
    _MEMORY_WATCHLIST,
    listar_meus_animes,
    grade_semanal_animes
)
from services.tools.clash_of_clans_tool import (
    _verificar_raid_season,
    _verificar_clan_war
)


@pytest.fixture(autouse=True)
def setup_teardown():
    _reset_briefing_memory()
    _reset_briefing_preferences()
    _reset_mock_storage()
    _reset_memory_watchlist()
    UserContext.set_user("daniel", "5511999999999")
    yield
    _reset_briefing_memory()
    _reset_briefing_preferences()
    _reset_mock_storage()
    _reset_memory_watchlist()
    UserContext.set_user("daniel", "5511999999999")


# ==============================================================================
# STORY 1: LEMBRETES DO DIA & SANITIZAÇÃO DE TAGS (P-0410, P-0411)
# ==============================================================================
class TestStory1LembretesDoDia:

    def test_briefing_mostra_apenas_lembretes_de_hoje(self):
        """P-0410: Lembrete de hoje deve aparecer; lembrete de 75 dias depois NÃO deve."""
        hoje = datetime(2026, 9, 8, 8, 0, tzinfo=TZ_BRASILIA)
        data_hoje_str = "2026-09-08 09:00"
        data_futura_str = "2026-11-23 09:00"

        # Cria lembrete para hoje e outro para 75 dias no futuro
        criar_lembrete(titulo="Reunião de Alinhamento", data_hora_lembrete=data_hoje_str, tags=["trabalho"])
        criar_lembrete(titulo="Pagar pré-pago Claro", data_hora_lembrete=data_futura_str, tags=["financas", "claro"])

        # Monta o briefing para a data de hoje
        resumo = montar_resumo_matinal(data_alvo=hoje, user_id="daniel")

        # Verifica que o lembrete de hoje está presente
        assert "Reunião de Alinhamento" in resumo
        # Verifica categoricamente que o lembrete de 75 dias depois NÃO está presente
        assert "Pagar pré-pago Claro" not in resumo
        assert "2026-11-23" not in resumo

    def test_sanitizacao_de_tags_evita_arrays_aninhados(self):
        """P-0411: Tags não devem renderizar como #[['financas', 'claro']]."""
        hoje = datetime(2026, 9, 8, 8, 0, tzinfo=TZ_BRASILIA)
        
        # Simula item com tags em formato lista ou string
        criar_lembrete(
            titulo="Consulta Médica", 
            data_hora_lembrete="2026-09-08 14:00", 
            tags=["saude", "medico"]
        )

        resumo = montar_resumo_matinal(data_alvo=hoje, user_id="daniel")

        assert "Consulta Médica" in resumo
        assert "#['" not in resumo
        assert "[['" not in resumo
        assert "#saude" in resumo
        assert "#medico" in resumo

    def test_listar_lembretes_pendentes_com_filtro_apenas_hoje(self):
        """P-0410: Função de listar lembretes deve suportar filtrar pela data especificada."""
        data_hoje = "2026-09-08"
        criar_lembrete(titulo="Tarefa Hoje", data_hora_lembrete="2026-09-08 10:00")
        criar_lembrete(titulo="Tarefa Futura", data_hora_lembrete="2026-10-15 10:00")

        resultado = listar_lembretes_pendentes(apenas_hoje=True, data_referencia=data_hoje)
        assert "Tarefa Hoje" in resultado
        assert "Tarefa Futura" not in resultado


# ==============================================================================
# STORY 2: FILTROS DE STATUS DE ANIMES (P-0412, P-0413, P-0414)
# ==============================================================================
class TestStory2FiltrosAnimes:

    def test_lancamentos_episodio_apenas_para_watching(self):
        """P-0412: Apenas animes com status 'assistindo' devem constar em episódios de hoje e próximo."""
        dt_segunda = datetime(2026, 9, 14, 12, 0, tzinfo=TZ_BRASILIA)
        airing_segunda = int(dt_segunda.astimezone(timezone.utc).timestamp())

        dt_quinta = datetime(2026, 10, 15, 12, 0, tzinfo=TZ_BRASILIA)
        airing_quinta = int(dt_quinta.astimezone(timezone.utc).timestamp())

        # Anime em 'assistindo' que lança na segunda
        _MEMORY_WATCHLIST["anime_1"] = {
            "anilist_id": 101,
            "titulo_principal": "Anime de Segunda Ativo",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 5,
            "proximo_episodio": {
                "episodio": 6,
                "airing_at": airing_segunda,
                "data_formatada": "Segunda-feira, 14/09/2026 às 12:00",
                "tempo_restante_segundos": 500000
            }
        }

        # Seishun Buta Yarou com status 'planejo_assistir' (ou 'concluido')
        _MEMORY_WATCHLIST["anime_2"] = {
            "anilist_id": 102,
            "titulo_principal": "Seishun Buta Yarou wa Dear Friend no Yume wo Minai",
            "status_usuario": "planejo_assistir",
            "ultimo_episodio_visto": 0,
            "proximo_episodio": {
                "episodio": 1,
                "airing_at": airing_quinta,
                "data_formatada": "Quinta-feira, 15/10/2026 às 12:00",
                "tempo_restante_segundos": 3000000
            }
        }

        # Data de teste: terça-feira 08/09/2026
        dt_hoje = datetime(2026, 9, 8, 8, 0, tzinfo=TZ_BRASILIA)
        info_animes = _obter_info_animes_briefing(dt_hoje)

        # O próximo lançamento DEVE ser o anime ativo de segunda, e NÃO Seishun Buta Yarou!
        assert "Anime de Segunda Ativo" in info_animes
        assert "Seishun Buta Yarou" not in info_animes

    def test_animes_para_assistir_puxa_planning_ou_watching_sem_eps(self):
        """P-0414: Lista 'para assistir' deve incluir plan to watch ou watching com 0 eps."""
        _MEMORY_WATCHLIST["plan_1"] = {
            "titulo_principal": "Frieren Season 2",
            "status_usuario": "planejo_assistir",
            "ultimo_episodio_visto": 0,
            "total_episodios": 12
        }
        _MEMORY_WATCHLIST["watch_novo"] = {
            "titulo_principal": "Dandadan",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 0,
            "total_episodios": 12
        }
        _MEMORY_WATCHLIST["watch_em_andamento"] = {
            "titulo_principal": "One Piece",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 1080,
            "total_episodios": 1100
        }
        _MEMORY_WATCHLIST["concluido"] = {
            "titulo_principal": "Attack on Titan",
            "status_usuario": "concluido",
            "ultimo_episodio_visto": 80,
            "total_episodios": 80
        }

        # Consulta animes para assistir / começar
        resultado = listar_meus_animes(status="planejo_assistir")
        assert "Frieren Season 2" in resultado
        assert "Dandadan" in resultado
        # One Piece já tem 1080 eps vistos, não é para começar/assistir
        assert "One Piece" not in resultado
        assert "Attack on Titan" not in resultado

    def test_grade_semanal_animes_considera_apenas_watching(self):
        """P-0412: Grade semanal deve conter apenas animes em watching."""
        dt = datetime(2026, 9, 14, 12, 0, tzinfo=TZ_BRASILIA)
        airing = int(dt.astimezone(timezone.utc).timestamp())

        _MEMORY_WATCHLIST["dropped_anime"] = {
            "titulo_principal": "Anime Dropado",
            "status_usuario": "dropado",
            "proximo_episodio": {
                "episodio": 3,
                "airing_at": airing,
                "data_formatada": "Segunda-feira"
            }
        }
        _MEMORY_WATCHLIST["watching_anime"] = {
            "titulo_principal": "Anime Assistindo",
            "status_usuario": "assistindo",
            "proximo_episodio": {
                "episodio": 4,
                "airing_at": airing,
                "data_formatada": "Segunda-feira"
            }
        }

        grade = grade_semanal_animes()
        assert "Anime Assistindo" in grade
        assert "Anime Dropado" not in grade


# ==============================================================================
# STORY 3: CLASH OF CLANS ALERTAS CONCORRENTES & 0 ATAQUES (P-0415, P-0416)
# ==============================================================================
class TestStory3ClashOfClans:

    def test_verificar_raid_season_com_zero_ataques_membro_ausente(self):
        """P-0415: Se o jogador não consta em members durante season ongoing, tem 5 ataques disponíveis."""
        data_raid_ongoing = {
            "state": "ongoing",
            "members": [
                {"tag": "#OUTRO1", "attacks": 6, "attackLimit": 6}
            ]
        }
        player_tag = "#MEUTAG"
        # O jogador não atacou ainda na season em andamento
        alerta = _verificar_raid_season(data_raid_ongoing, player_tag)
        assert alerta is not None
        assert "Raid Weekend" in alerta or "Capital" in alerta
        assert "5" in alerta or "ataque" in alerta.lower()

    @patch("services.briefing_service._fetch_coc_data")
    @patch("services.briefing_service.settings")
    def test_obter_alertas_coc_mostra_ambos_cwl_e_raid(self, mock_settings, mock_fetch):
        """P-0416: Se houver CWL e Raid ativos com ataques pendentes, ambos devem constar no briefing."""
        mock_settings.COC_API_TOKEN = "fake_token"
        mock_settings.COC_CLAN_TAG = "#CLAN123"
        mock_settings.COC_PLAYER_TAG = "#PLAYER123"

        def mock_fetch_side_effect(endpoint):
            if "capitalraidseasons" in endpoint:
                return {
                    "items": [{
                        "state": "ongoing",
                        "members": []  # 0 ataques feitos
                    }]
                }
            elif "currentwar/leaguegroup" in endpoint:
                return {
                    "state": "inWar",
                    "rounds": [{"warTags": ["#WAR1"]}]
                }
            elif "clanwarleagues/wars" in endpoint:
                return {
                    "state": "inWar",
                    "clan": {
                        "tag": "#CLAN123",
                        "members": [{"tag": "#PLAYER123", "attacks": []}]  # 1 pendente
                    },
                    "opponent": {"name": "The Mens", "tag": "#OPP123"},
                    "attacksPerMember": 1
                }
            elif "currentwar" in endpoint:
                return {"state": "notInWar"}
            return {}

        mock_fetch.side_effect = mock_fetch_side_effect

        alertas = _obter_alertas_coc()
        # Ambos os alertas DEVEM estar presentes
        assert "Raid Weekend" in alertas
        assert "Liga de Guerras (CWL)" in alertas or "CWL" in alertas


# ==============================================================================
# STORY 4: DISPARO MULTI-USUÁRIO & ISOLAMENTO PARA LARI (P-0417, P-0418)
# ==============================================================================
class TestStory4MultiUserBriefing:

    @patch("services.briefing_service.WhatsAppService.send_text")
    def test_enviar_briefing_matinal_para_lari_usa_contexto_e_telefone_dela(self, mock_send):
        """P-0418: Envio para Lari usa o telefone dela e isola seus dados."""
        mock_send.return_value = {"status": "ok"}

        # Define preferências para Lari
        salvar_preferencias_briefing("lari", {
            "userId": "lari",
            "userName": "Lari",
            "horario": "07:30",
            "topicos": ["agenda", "lembretes", "saude"],
            "ativo": True
        })

        resultado = enviar_briefing_matinal(force=True, user_id="lari")
        assert "✅" in resultado or "sucesso" in resultado.lower()

        # Verifica se chamou WhatsAppService com o JID da Lari
        mock_send.assert_called_once()
        args, _ = mock_send.call_args
        remote_jid, texto_mensagem = args
        assert "5511888888888" in remote_jid
        # O briefing de Lari não deve ter animes nem clash por padrão
        assert "Clash of Clans" not in texto_mensagem
        assert "FURIA" not in texto_mensagem

    def test_montar_resumo_matinal_isola_user_context(self):
        """P-0418: Durante a montagem do resumo de Lari, dados de Daniel não vazam."""
        # Cria lembrete exclusivo para Daniel e outro para Lari
        UserContext.set_user("daniel", "5511999999999")
        criar_lembrete(titulo="Lembrete Exclusivo Daniel", data_hora_lembrete="2026-09-08 10:00")

        UserContext.set_user("lari", "5511888888888")
        criar_lembrete(titulo="Lembrete Exclusivo Lari", data_hora_lembrete="2026-09-08 11:00")

        # Gera o resumo para Lari
        hoje = datetime(2026, 9, 8, 8, 0, tzinfo=TZ_BRASILIA)
        resumo_lari = montar_resumo_matinal(data_alvo=hoje, user_id="lari")

        assert "Lembrete Exclusivo Lari" in resumo_lari
        assert "Lembrete Exclusivo Daniel" not in resumo_lari

    @patch("services.briefing_service.enviar_briefing_matinal")
    def test_verificar_e_disparar_briefings_agendados_por_horario(self, mock_enviar):
        """P-0417: Dispara para usuários que possuem o horário correspondente configurado."""
        salvar_preferencias_briefing("daniel", {
            "userId": "daniel",
            "horario": "08:00",
            "ativo": True
        })
        salvar_preferencias_briefing("lari", {
            "userId": "lari",
            "horario": "07:30",
            "ativo": True
        })

        mock_enviar.return_value = "Enviado com sucesso"

        from services.briefing_service import verificar_e_disparar_briefings_agendados

        # Disparo das 07:30 deve acionar APENAS Lari
        enviados_0730 = verificar_e_disparar_briefings_agendados(hora_minuto="07:30")
        assert "lari" in enviados_0730
        assert "daniel" not in enviados_0730

        mock_enviar.reset_mock()

        # Disparo das 08:00 deve acionar Daniel
        enviados_0800 = verificar_e_disparar_briefings_agendados(hora_minuto="08:00")
        assert "daniel" in enviados_0800
        assert "lari" not in enviados_0800

    @patch("services.briefing_service.enviar_briefing_matinal")
    def test_verificar_e_disparar_briefings_catchup_matinal(self, mock_enviar):
        """Dispara catch-up matinal caso o usuário tenha horário anterior e ainda não tenha recebido hoje."""
        salvar_preferencias_briefing("lari", {
            "userId": "lari",
            "horario": "06:00",
            "ativo": True
        })
        salvar_preferencias_briefing("daniel", {
            "userId": "daniel",
            "horario": "08:00",
            "ativo": True
        })

        mock_enviar.return_value = "✅ Enviado com sucesso"
        from services.briefing_service import verificar_e_disparar_briefings_agendados, _MEMORY_BRIEFING_LOGS
        _MEMORY_BRIEFING_LOGS.clear()

        # Às 06:15 com permitir_catchup=True, Lari (06:00) deve ser acionada via catch-up
        enviados = verificar_e_disparar_briefings_agendados(hora_minuto="06:15", permitir_catchup=True)
        assert "lari" in enviados
        assert "daniel" not in enviados

    @patch("services.briefing_service.WhatsAppService.send_text")
    def test_enviar_briefing_falha_evolution_api_nao_registra_sucesso(self, mock_send):
        """Se a Evolution API falhar (retornar None), não deve registrar sucesso nem idempotência."""
        mock_send.return_value = None
        from services.briefing_service import enviar_briefing_matinal, _MEMORY_BRIEFING_LOGS
        _MEMORY_BRIEFING_LOGS.clear()

        res = enviar_briefing_matinal(force=True, user_id="lari")
        assert "Erro" in res
        assert not any("lari" in k for k in _MEMORY_BRIEFING_LOGS)

