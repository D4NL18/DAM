import pytest
from unittest.mock import patch
from services.tools.anime_tracker_tool import (
    adicionar_anime_watchlist,
    consultar_proximo_episodio,
    listar_meus_animes,
    atualizar_progresso_anime,
    grade_semanal_animes,
    sincronizar_perfil_anilist,
    consultar_novas_temporadas,
    explorar_temporada_animes,
    _reset_memory_watchlist
)

class TestAnimeTracker:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        _reset_memory_watchlist()
        yield
        _reset_memory_watchlist()

    def test_adicionar_anime_titulo_vazio(self):
        res = adicionar_anime_watchlist("   ")
        assert "Erro: O nome do anime não pode ser vazio" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_adicionar_anime_com_proximo_episodio(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 12345,
                "title": {"romaji": "Solo Leveling", "english": "Solo Leveling", "native": ""},
                "format": "TV",
                "status": "RELEASING",
                "episodes": 12,
                "genres": ["Action"],
                "nextAiringEpisode": {
                    "airingAt": 1788500000,
                    "timeUntilAiring": 7200,
                    "episode": 9
                },
                "siteUrl": "https://anilist.co/anime/12345"
            }
        }
        res = adicionar_anime_watchlist("Solo Leveling", status="assistindo", ultimo_episodio_visto=8)
        assert "Anime Adicionado à sua Watchlist" in res
        assert "Solo Leveling" in res
        assert "Ep. 8" in res
        assert "Ep. 9" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_consultar_proximo_episodio_releasing(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 999,
                "title": {"romaji": "One Piece", "english": "One Piece"},
                "status": "RELEASING",
                "episodes": None,
                "nextAiringEpisode": {
                    "airingAt": 1788550000,
                    "timeUntilAiring": 86400,
                    "episode": 1120
                }
            }
        }
        res = consultar_proximo_episodio("One Piece")
        assert "Lançamento de Episódio" in res
        assert "1120" in res
        assert "Crunchyroll" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_consultar_proximo_episodio_finalizado(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 555,
                "title": {"romaji": "Frieren", "english": "Frieren: Beyond Journey's End"},
                "status": "FINISHED",
                "episodes": 28,
                "nextAiringEpisode": None
            }
        }
        res = consultar_proximo_episodio("Frieren")
        assert "Temporada Concluída" in res

    def test_listar_meus_animes_vazio(self):
        res = listar_meus_animes()
        assert "Sua lista de animes ainda está vazia" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_atualizar_progresso_anime(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 111,
                "title": {"romaji": "Chainsaw Man", "english": "Chainsaw Man"},
                "status": "FINISHED",
                "episodes": 12,
                "nextAiringEpisode": None
            }
        }
        adicionar_anime_watchlist("Chainsaw Man", "assistindo", 2)
        res = atualizar_progresso_anime("Chainsaw Man", 5)
        assert "Episódio 5" in res
        
        lista = listar_meus_animes()
        assert "Ep. 5/12" in lista

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_grade_semanal_animes(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 222,
                "title": {"romaji": "Demon Slayer", "english": "Demon Slayer"},
                "status": "RELEASING",
                "episodes": 8,
                "nextAiringEpisode": {
                    "airingAt": 1788500000,
                    "timeUntilAiring": 10000,
                    "episode": 4
                }
            }
        }
        adicionar_anime_watchlist("Demon Slayer")
        grade = grade_semanal_animes()
        assert "Grade Semanal de Lançamentos" in grade
        assert "Demon Slayer" in grade

    def test_sincronizar_perfil_anilist_sem_username(self):
        res = sincronizar_perfil_anilist(username="   ")
        assert "Nenhum nome de usuário do AniList informado" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_sincronizar_perfil_anilist_sucesso(self, mock_gql):
        mock_gql.return_value = {
            "MediaListCollection": {
                "lists": [
                    {
                        "name": "Watching",
                        "entries": [
                            {
                                "status": "CURRENT",
                                "progress": 14,
                                "score": 9.0,
                                "media": {
                                    "id": 5001,
                                    "title": {"romaji": "Jujutsu Kaisen Season 2", "english": "Jujutsu Kaisen Season 2"},
                                    "format": "TV",
                                    "status": "FINISHED",
                                    "episodes": 23,
                                    "nextAiringEpisode": None,
                                    "siteUrl": "https://anilist.co/anime/5001"
                                }
                            }
                        ]
                    },
                    {
                        "name": "Planning",
                        "entries": [
                            {
                                "status": "PLANNING",
                                "progress": 0,
                                "score": 0,
                                "media": {
                                    "id": 5002,
                                    "title": {"romaji": "Kaiju No. 8", "english": "Kaiju No. 8"},
                                    "format": "TV",
                                    "status": "RELEASING",
                                    "episodes": 12,
                                    "nextAiringEpisode": {
                                        "episode": 7,
                                        "airingAt": 1788520000,
                                        "timeUntilAiring": 12000
                                    },
                                    "siteUrl": "https://anilist.co/anime/5002"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        res = sincronizar_perfil_anilist("otaku_user")
        assert "Sincronização com AniList Concluída" in res
        assert "otaku_user" in res
        assert "Total de Animes Sincronizados: **2**" in res
        assert "Assistindo no momento: **1**" in res
        assert "Planejando assistir: **1**" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_consultar_novas_temporadas_com_sequel(self, mock_gql):
        mock_gql.return_value = {
            "Media": {
                "id": 100,
                "title": {"romaji": "Sousou no Frieren", "english": "Frieren"},
                "format": "TV",
                "status": "FINISHED",
                "relations": {
                    "edges": [
                        {
                            "relationType": "SEQUEL",
                            "node": {
                                "id": 101,
                                "title": {"romaji": "Sousou no Frieren Season 2", "english": "Frieren Season 2"},
                                "format": "TV",
                                "status": "NOT_YET_RELEASED",
                                "season": "FALL",
                                "seasonYear": 2026,
                                "startDate": {"year": 2026, "month": 10, "day": None},
                                "nextAiringEpisode": None,
                                "siteUrl": "https://anilist.co/anime/101"
                            }
                        }
                    ]
                }
            }
        }
        res = consultar_novas_temporadas("Frieren")
        assert "Novas Temporadas & Sequências" in res
        assert "Frieren Season 2" in res
        assert "Próxima Temporada" in res
        assert "Confirmado / Em Produção" in res

    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_explorar_temporada_animes(self, mock_gql):
        mock_gql.return_value = {
            "Page": {
                "media": [
                    {
                        "id": 301,
                        "title": {"romaji": "Chainsaw Man: Reze Arc", "english": "Chainsaw Man The Movie: Reze Arc"},
                        "format": "MOVIE",
                        "status": "NOT_YET_RELEASED",
                        "genres": ["Action", "Supernatural"],
                        "episodes": 1,
                        "nextAiringEpisode": None,
                        "startDate": {"year": 2026, "month": 12, "day": 15}
                    }
                ]
            }
        }
        res = explorar_temporada_animes("outono", 2026)
        assert "Destaques da Temporada de Outono 2026" in res
        assert "Chainsaw Man" in res
        assert "MOVIE" in res

    @patch("services.tools.anime_tracker_tool._salvar_entrada_anilist_remoto")
    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_atualizar_progresso_incrementar(self, mock_gql, mock_remoto):
        mock_gql.return_value = {
            "Media": {
                "id": 777,
                "title": {"romaji": "Dandadan", "english": "Dandadan"},
                "status": "RELEASING",
                "episodes": 12,
                "nextAiringEpisode": None
            }
        }
        mock_remoto.return_value = True

        adicionar_anime_watchlist("Dandadan", status="assistindo", ultimo_episodio_visto=3)
        res = atualizar_progresso_anime("Dandadan", incrementar=True)
        assert "Episódio 4" in res
        assert "Dandadan" in res

    @patch("services.tools.anime_tracker_tool._salvar_entrada_anilist_remoto")
    @patch("services.tools.anime_tracker_tool._consultar_anilist_graphql")
    def test_marcar_anime_concluido_com_nota(self, mock_gql, mock_remoto):
        from services.tools.anime_tracker_tool import marcar_anime_concluido
        mock_gql.return_value = {
            "Media": {
                "id": 888,
                "title": {"romaji": "Frieren", "english": "Frieren: Beyond Journey's End"},
                "episodes": 28,
                "siteUrl": "https://anilist.co/anime/888"
            }
        }
        mock_remoto.return_value = True

        adicionar_anime_watchlist("Frieren", status="assistindo", ultimo_episodio_visto=27)
        res = marcar_anime_concluido("Frieren", nota=10.0)
        assert "Anime Concluído" in res
        assert "28/28" in res
        assert "10.0/10" in res

    def test_listar_meus_animes_assistindo(self):
        from services.tools.anime_tracker_tool import _MEMORY_WATCHLIST
        _MEMORY_WATCHLIST["123"] = {
            "titulo_principal": "One Piece",
            "ultimo_episodio_visto": 1115,
            "total_episodios": None,
            "status_usuario": "assistindo"
        }
        res = listar_meus_animes(status="assistindo")
        assert "Animes que Você Está Assistindo no Momento" in res
        assert "One Piece" in res
        assert "Ep. 1115" in res

