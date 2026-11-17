import pytest
from unittest.mock import patch, MagicMock
from services.tools.anime_tracker_tool import (
    consultar_meu_episodio_anime,
    adicionar_anime_watchlist,
    _reset_memory_watchlist
)
from services.tools_dispatcher import ToolsDispatcher
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user_and_memory():
    UserContext.set_user("daniel", "5511999999999")
    _reset_memory_watchlist()
    yield
    _reset_memory_watchlist()


class TestAnimeCurrentEpisode:
    """Suíte de testes para consultar 'qual ep eu tô' de um anime."""

    @patch("services.tools.anime_tracker_tool.firebase.db", None)
    def test_consultar_meu_episodio_anime_encontra_anime_e_retorna_progresso(self):
        """
        Ao perguntar 'qual ep eu tô de Solo Leveling', o sistema retorna diretamente
        o último episódio visto, total de episódios e o próximo a assistir.
        """
        # Adiciona na watchlist em memória
        with patch("services.tools.anime_tracker_tool._consultar_anilist_graphql") as mock_gql:
            mock_gql.return_value = {
                "Media": {
                    "id": 12345,
                    "title": {"romaji": "Solo Leveling", "english": "Solo Leveling: Arise"},
                    "format": "TV",
                    "status": "RELEASING",
                    "episodes": 12,
                    "nextAiringEpisode": {
                        "airingAt": 1788500000,
                        "timeUntilAiring": 7200,
                        "episode": 9
                    }
                }
            }
            adicionar_anime_watchlist("Solo Leveling", status="assistindo", ultimo_episodio_visto=8)

        # Consulta direta: qual ep eu tô
        res = consultar_meu_episodio_anime("Solo Leveling")

        assert "Solo Leveling" in res
        assert "Episódio 8" in res or "Ep. 8" in res
        assert "12" in res
        assert "Próximo" in res or "Episódio 9" in res

    @patch("services.tools.anime_tracker_tool.firebase.db", None)
    def test_consultar_meu_episodio_anime_busca_por_romaji_ou_ingles(self):
        """
        A busca pelo anime deve reconhecer títulos tanto em inglês quanto romaji.
        Ex: usuário pergunta 'qual ep eu to de frieren' para 'Sousou no Frieren'.
        """
        with patch("services.tools.anime_tracker_tool._consultar_anilist_graphql") as mock_gql:
            mock_gql.return_value = {
                "Media": {
                    "id": 5555,
                    "title": {"romaji": "Sousou no Frieren", "english": "Frieren: Beyond Journey's End"},
                    "format": "TV",
                    "status": "FINISHED",
                    "episodes": 28,
                    "nextAiringEpisode": None
                }
            }
            adicionar_anime_watchlist("Sousou no Frieren", status="assistindo", ultimo_episodio_visto=16)

        # Pergunta usando o nome ocidental popular 'frieren'
        res = consultar_meu_episodio_anime("frieren")

        assert "Frieren" in res or "Sousou no Frieren" in res
        assert "16" in res
        assert "28" in res

    @patch("services.tools.anime_tracker_tool.firebase.db", None)
    def test_consultar_meu_episodio_anime_nao_cadastrado_avisa_amigavelmente(self):
        """Se o anime não estiver na lista do usuário, avisa de forma útil e orienta a adicionar."""
        with patch("services.tools.anime_tracker_tool._consultar_anilist_graphql", return_value=None):
            res = consultar_meu_episodio_anime("Dragon Ball Daima")

        assert "não está na sua lista" in res.lower() or "não encontrado na sua watchlist" in res.lower()
        assert "Dragon Ball Daima" in res

    def test_tools_dispatcher_routes_qual_ep_eu_to_queries(self):
        """
        O ToolsDispatcher deve reconhecer variações da pergunta 'qual ep eu tô' e carregar
        as ferramentas de anime, incluindo 'consultar_meu_episodio_anime'.
        """
        frases = [
            "qual ep eu to de solo leveling?",
            "em qual episódio parei de frieren?",
            "qual o meu progresso em one piece?",
            "em que ep eu estou de jujutsu kaisen?",
            "quantos eps eu já vi de mushoku tensei?",
            "qual ep parei de chainsaw man"
        ]

        for frase in frases:
            tools = ToolsDispatcher.resolve_tools(frase)
            assert tools is not None, f"Dispatcher retornou None para '{frase}'"
            names = [getattr(t, "__name__", "") for t in tools]
            assert "consultar_meu_episodio_anime" in names, f"'consultar_meu_episodio_anime' ausente para '{frase}'"
