import unittest
import json
from unittest.mock import patch, MagicMock
from services.tools.streaming_tool import onde_assistir, _normalizar, _STREAMING_CACHE, CATALOGO_EMBUTIDO
from config.settings import settings
from config import firebase

class TestFase14Streaming(unittest.TestCase):
    def setUp(self):
        _STREAMING_CACHE.clear()

    def test_normalizar_texto(self):
        self.assertEqual(_normalizar("Interestelar!"), "interestelar")
        self.assertEqual(_normalizar("Óppenheímer: 2023"), "oppenheimer 2023")
        self.assertEqual(_normalizar("  Stranger   Things  "), "stranger things")
        self.assertEqual(_normalizar(""), "")

    def test_titulo_vazio(self):
        res = onde_assistir("")
        self.assertIn("informe o nome de um filme ou série", res)
        res_space = onde_assistir("   ")
        self.assertIn("informe o nome de um filme ou série", res_space)

    def test_filme_catalogo_embutido_com_assinatura_aluguel_e_compra(self):
        # Interestelar possui streaming no Max/Prime Video e aluguel/compra na Apple TV+
        res = onde_assistir("Interestelar")
        self.assertIn("Interestelar", res)
        self.assertIn("Filme", res)
        self.assertIn("Assinatura", res)
        self.assertIn("Max", res)
        self.assertIn("Aluguel Digital", res)
        self.assertIn("Compra Digital", res)

    def test_serie_catalogo_embutido(self):
        res = onde_assistir("Breaking Bad", tipo_midia="serie")
        self.assertIn("Breaking Bad", res)
        self.assertIn("Série", res)
        self.assertIn("Netflix", res)

    def test_normalizacao_e_case_insensitive(self):
        res1 = onde_assistir("stranger things")
        res2 = onde_assistir("STRANGER THINGS!")
        self.assertIn("Netflix", res1)
        self.assertIn("Netflix", res2)

    def test_distincao_stream_rent_buy(self):
        res = onde_assistir("Oppenheimer")
        self.assertIn("Assinatura (Streaming incluso):", res)
        self.assertIn("Aluguel Digital:", res)
        self.assertIn("Compra Digital:", res)

    def test_filtro_tipo_midia(self):
        # The Bear é série
        res = onde_assistir("The Bear", tipo_midia="serie")
        self.assertIn("Disney+", res)

    def test_cache_em_memoria(self):
        # Primeira consulta popula o cache
        res1 = onde_assistir("Barbie")
        self.assertIn("Max", res1)
        self.assertTrue(len(_STREAMING_CACHE) > 0)
        
        # Segunda consulta deve vir do cache em memória
        with patch("services.tools.streaming_tool._buscar_catalogo_embutido") as mock_catalogo:
            res2 = onde_assistir("Barbie")
            self.assertEqual(res1, res2)
            mock_catalogo.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_integracao_tmdb_api(self, mock_urlopen):
        # Simula resposta da API TMDB (busca e providers)
        search_response = {
            "results": [
                {
                    "id": 550,
                    "title": "Clube da Luta",
                    "media_type": "movie",
                    "release_date": "1999-10-15"
                }
            ]
        }
        providers_response = {
            "results": {
                "BR": {
                    "flatrate": [{"provider_name": "Star+"}, {"provider_name": "Prime Video"}],
                    "rent": [{"provider_name": "Apple TV+"}],
                    "buy": [{"provider_name": "Google Play Filmes"}]
                }
            }
        }

        mock_resp1 = MagicMock()
        mock_resp1.read.return_value = json.dumps(search_response).encode("utf-8")
        mock_resp2 = MagicMock()
        mock_resp2.read.return_value = json.dumps(providers_response).encode("utf-8")

        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=mock_resp1)),
            MagicMock(__enter__=MagicMock(return_value=mock_resp2))
        ]

        with patch.object(settings, "TMDB_API_KEY", "dummy_tmdb_key"):
            res = onde_assistir("Clube da Luta Teste TMDB", tipo_midia="filme")
            self.assertIn("Clube da Luta", res)
            self.assertIn("Star+", res)
            self.assertIn("Prime Video", res)
            self.assertIn("Apple TV+", res)
            self.assertIn("Google Play Filmes", res)

    def test_titulo_nao_encontrado(self):
        res = onde_assistir("FilmeInexistenteComNomeAleatorio123456789")
        self.assertIn("Não localizamos plataformas de streaming confirmadas", res)

    def test_cache_firestore_mock(self):
        mock_db = MagicMock()
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "titulo": "Filme Cache Firestore",
            "ano": 2025,
            "tipo": "Filme",
            "stream": ["PlataformaX"],
            "rent": [],
            "buy": []
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch.object(firebase, "db", mock_db):
            res = onde_assistir("Filme Cache Firestore")
            self.assertIn("Filme Cache Firestore", res)
            self.assertIn("PlataformaX", res)

if __name__ == "__main__":
    unittest.main()
