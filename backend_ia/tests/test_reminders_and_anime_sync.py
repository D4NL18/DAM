import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from services.user_context import UserContext
from services.tools.notes_tool import (
    _reset_mock_storage,
    _obter_todos_itens,
    criar_lembrete,
    criar_anotacao,
    listar_lembretes_pendentes,
)
from services.tools.anime_tracker_tool import (
    _MEMORY_WATCHLIST,
    _reset_memory_watchlist,
    _format_timestamp_br,
    _renovar_proximos_episodios_expirados,
)
from services.briefing_service import (
    _obter_info_animes_briefing,
    TZ_BRASILIA,
)

@pytest.fixture(autouse=True)
def setup_teardown():
    _reset_mock_storage()
    _reset_memory_watchlist()
    UserContext.set_user("daniel", "5511999999999")
    yield
    _reset_mock_storage()
    _reset_memory_watchlist()


class TestRemindersDefaultToToday:
    """Testes para P-0419 e P-0420: Lembretes filtrados para hoje por padrão e tags limpas."""

    def test_listar_lembretes_pendentes_padrao_apenas_hoje(self):
        """P-0419: Sem argumentos, listar_lembretes_pendentes deve retornar estritamente os lembretes de hoje."""
        hoje_str = datetime.now(TZ_BRASILIA).strftime("%Y-%m-%d")
        data_hoje = f"{hoje_str} 10:00"
        data_futura = "2026-11-23 09:00"

        criar_lembrete(titulo="Pagar Claro Hoje", data_hora_lembrete=data_hoje, tags=["contas"])
        criar_lembrete(titulo="Pagar pré-pago Claro", data_hora_lembrete=data_futura, tags=["financas", "claro"])

        # Chamada sem argumentos (default apenas_hoje=True)
        resultado = listar_lembretes_pendentes()

        assert "Pagar Claro Hoje" in resultado
        assert "Pagar pré-pago Claro" not in resultado
        assert "2026-11-23" not in resultado

    def test_listar_lembretes_pendentes_explicitamente_todos(self):
        """P-0419: Com apenas_hoje=False, deve retornar todos os lembretes pendentes futuros."""
        hoje_str = datetime.now(TZ_BRASILIA).strftime("%Y-%m-%d")
        data_hoje = f"{hoje_str} 10:00"
        data_futura = "2026-11-23 09:00"

        criar_lembrete(titulo="Tarefa de Hoje", data_hora_lembrete=data_hoje)
        criar_lembrete(titulo="Pagar pré-pago Claro", data_hora_lembrete=data_futura)

        resultado = listar_lembretes_pendentes(apenas_hoje=False)

        assert "Tarefa de Hoje" in resultado
        assert "Pagar pré-pago Claro" in resultado
        assert "2026-11-23 09:00" in resultado

    def test_listar_lembretes_pendentes_sem_lembretes_hoje(self):
        """P-0419: Se houver apenas lembretes futuros, chamada padrão retorna que não há lembretes para hoje."""
        data_futura = "2026-11-23 09:00"
        criar_lembrete(titulo="Lembrete Distante", data_hora_lembrete=data_futura)

        resultado = listar_lembretes_pendentes()

        assert "Nenhum lembrete pendente para hoje" in resultado
        assert "Lembrete Distante" not in resultado

    def test_criar_lembrete_higienizacao_tags_malformadas(self):
        """P-0420: String com array literal de tags deve ser convertida em lista limpa."""
        tags_sujas = "['financas', 'claro', 'recorrente']"
        retorno = criar_lembrete(
            titulo="Pagar pré-pago Claro",
            data_hora_lembrete="2026-11-23 09:00",
            tags=tags_sujas
        )

        assert "[#financas #claro #recorrente]" in retorno
        assert "['financas'" not in retorno
        assert "#['financas'" not in retorno

        # Verifica como foi persistido
        itens = _obter_todos_itens()
        assert len(itens) == 1
        assert itens[0]["tags"] == ["financas", "claro", "recorrente"]

    def test_criar_anotacao_higienizacao_tags_malformadas(self):
        """P-0420: Anotação com tags em lista suja também deve ser higienizada."""
        tags_sujas = ["['ideias'", "'dam']"]
        retorno = criar_anotacao(
            titulo="Ideia de Feature",
            conteudo="Anotação de teste",
            tags=tags_sujas
        )

        assert "[#ideias #dam]" in retorno
        itens = _obter_todos_itens()
        assert len(itens) == 1
        assert itens[0]["tags"] == ["ideias", "dam"]

    def test_listar_lembretes_pendentes_formato_brasileiro_hoje(self):
        """P-0419: Lembrete gravado com formato brasileiro DD/MM/YYYY deve ser reconhecido para hoje."""
        hoje_dt = datetime.now(TZ_BRASILIA)
        hoje_br = hoje_dt.strftime("%d/%m/%Y")
        data_br = f"{hoje_br} às 14:30"
        data_amanha = (hoje_dt + timedelta(days=1)).strftime("%d/%m/%Y") + " 10:00"

        criar_lembrete(titulo="Consulta Médica Hoje", data_hora_lembrete=data_br)
        criar_lembrete(titulo="Tarefa de Amanhã", data_hora_lembrete=data_amanha)

        resultado = listar_lembretes_pendentes()
        assert "Consulta Médica Hoje" in resultado
        assert "Tarefa de Amanhã" not in resultado

    def test_prompts_contem_regra_absoluta_lembretes(self):
        """P-0419: Valida que system_base e briefing_rules contêm a regra mandatória de lembretes."""
        from services.prompts.system_base import get_system_base_prompt
        from services.prompts.briefing_rules import get_briefing_prompt

        base_prompt = get_system_base_prompt("2026-09-09 10:00")
        briefing_prompt = get_briefing_prompt()

        assert "SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR" in base_prompt
        assert "SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR" in briefing_prompt



class TestAnimeTrackerDynamicSync:
    """Testes para P-0421: Renovação dinâmica de próximos episódios e seleção do lançamento de domingo."""

    def test_briefing_animes_seleciona_proximo_de_domingo(self):
        """P-0421: Quando não há anime hoje (quarta-feira), o próximo lançamento DEVE ser o de domingo."""
        tz_br = TZ_BRASILIA
        # Quarta-feira 09/09/2026 às 08:00
        dt_quarta = datetime(2026, 9, 9, 8, 0, tzinfo=tz_br)

        # Domingo 13/09/2026 às 05:00 (timestamp UTC correspondente)
        dt_domingo_05h = datetime(2026, 9, 13, 5, 0, tzinfo=tz_br)
        airing_domingo_05h = int(dt_domingo_05h.astimezone(timezone.utc).timestamp())

        # Domingo 13/09/2026 às 12:00
        dt_domingo_12h = datetime(2026, 9, 13, 12, 0, tzinfo=tz_br)
        airing_domingo_12h = int(dt_domingo_12h.astimezone(timezone.utc).timestamp())

        # Quinta-feira 15/10/2026 às 12:00
        dt_quinta_out = datetime(2026, 10, 15, 12, 0, tzinfo=tz_br)
        airing_quinta_out = int(dt_quinta_out.astimezone(timezone.utc).timestamp())

        # Anime 1: Seihantai (assistindo, domingo 05h)
        _MEMORY_WATCHLIST["210031"] = {
            "anilist_id": 210031,
            "titulo_principal": "Seihantai na Kimi to Boku 2nd Season",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 10,
            "proximo_episodio": {
                "episodio": 11,
                "airing_at": airing_domingo_05h,
                "data_formatada": "Domingo, 13/09/2026 às 05:00",
                "tempo_restante_segundos": 334800
            }
        }

        # Anime 2: Mushoku Tensei III (assistindo, domingo 12h)
        _MEMORY_WATCHLIST["178789"] = {
            "anilist_id": 178789,
            "titulo_principal": "Mushoku Tensei III: Isekai Ittara Honki Dasu",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 11,
            "proximo_episodio": {
                "episodio": 12,
                "airing_at": airing_domingo_12h,
                "data_formatada": "Domingo, 13/09/2026 às 12:00",
                "tempo_restante_segundos": 360000
            }
        }

        # Anime 3: Seishun Buta Yarou (planejo_assistir, 15/10/2026)
        _MEMORY_WATCHLIST["199340"] = {
            "anilist_id": 199340,
            "titulo_principal": "Seishun Buta Yarou wa Dear Friend no Yume wo Minai",
            "status_usuario": "planejo_assistir",
            "ultimo_episodio_visto": 0,
            "proximo_episodio": {
                "episodio": 1,
                "airing_at": airing_quinta_out,
                "data_formatada": "Quinta-feira, 15/10/2026 às 12:00",
                "tempo_restante_segundos": 3000000
            }
        }

        with patch("services.briefing_service.firebase.db", None):
            resumo = _obter_info_animes_briefing(dt_quarta)

        assert "Nenhum episódio novo dos seus animes hoje" in resumo
        assert "Seihantai na Kimi to Boku 2nd Season" in resumo
        assert "Domingo, 13/09/2026 às 05:00" in resumo
        assert "Seishun Buta Yarou" not in resumo
        assert "15/10/2026" not in resumo

    def test_renovacao_autonoma_de_episodios_expirados(self):
        """P-0421: Se o anime em assistindo tiver episódio expirado no passado, renova via AniList."""
        tz_br = TZ_BRASILIA
        # Data do briefing: Quarta 09/09/2026
        dt_quarta = datetime(2026, 9, 9, 8, 0, tzinfo=tz_br)
        # Episódio antigo expirado: Domingo 06/09/2026 (no passado)
        dt_passado = datetime(2026, 9, 6, 12, 0, tzinfo=tz_br)
        airing_passado = int(dt_passado.astimezone(timezone.utc).timestamp())

        # Novo episódio que a API do AniList deve retornar: Domingo 13/09/2026
        dt_novo = datetime(2026, 9, 13, 12, 0, tzinfo=tz_br)
        airing_novo = int(dt_novo.astimezone(timezone.utc).timestamp())

        _MEMORY_WATCHLIST["178789"] = {
            "anilist_id": 178789,
            "titulo_principal": "Mushoku Tensei III",
            "status_usuario": "assistindo",
            "ultimo_episodio_visto": 10,
            "proximo_episodio": {
                "episodio": 11,
                "airing_at": airing_passado,
                "data_formatada": "Domingo, 06/09/2026 às 12:00",
                "tempo_restante_segundos": -200000
            }
        }

        # Mock da API AniList retornando o novo episódio
        mock_anilist_data = {
            "MediaListCollection": {
                "lists": [
                    {
                        "name": "Watching",
                        "entries": [
                            {
                                "status": "CURRENT",
                                "progress": 11,
                                "media": {
                                    "id": 178789,
                                    "title": {"romaji": "Mushoku Tensei III", "english": None},
                                    "status": "RELEASING",
                                    "episodes": 24,
                                    "nextAiringEpisode": {
                                        "episode": 12,
                                        "airingAt": airing_novo,
                                        "timeUntilAiring": 360000
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        }

        with patch("services.tools.anime_tracker_tool._consultar_anilist_graphql", return_value=mock_anilist_data), \
             patch("services.briefing_service.firebase.db", None), \
             patch("services.tools.anime_tracker_tool.firebase.db", None):
            resumo = _obter_info_animes_briefing(dt_quarta)

        assert "Mushoku Tensei III" in resumo
        assert "Ep. 12" in resumo
        assert "13/09/2026" in resumo
