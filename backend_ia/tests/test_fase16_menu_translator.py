import unittest
from unittest.mock import patch, MagicMock
from services.tools.menu_translator_tool import (
    traduzir_e_explicar_cardapio,
    _analise_local_gastronomica,
    _detectar_alergenos,
    _verificar_conflitos_alimentares
)
from config.settings import settings


class TestFase16MenuTranslator(unittest.TestCase):
    def test_traduzir_cardapio_vazio(self):
        resultado = traduzir_e_explicar_cardapio("")
        self.assertIn("Por favor, forneça o nome", resultado)

    def test_traduzir_boeuf_bourguignon_frances(self):
        resultado = traduzir_e_explicar_cardapio("Boeuf Bourguignon", idioma_origem="francês")
        self.assertIn("Boeuf Bourguignon", resultado)
        self.assertIn("Vinho tinto", resultado)
        self.assertIn("Cozimento lento", resultado)
        # Analogia brasileira
        self.assertTrue("picadinho" in resultado or "vaca atolada" in resultado)
        # Alérgenos
        self.assertIn("glúten", resultado.lower())

    def test_traduzir_confit_de_canard_tecnica_confit(self):
        resultado = traduzir_e_explicar_cardapio("Confit de Canard")
        self.assertIn("Confit", resultado)
        self.assertIn("pato", resultado.lower())
        self.assertIn("carne de lata", resultado.lower())

    def test_traduzir_carbonara_italiano(self):
        resultado = traduzir_e_explicar_cardapio("Spaghetti alla Carbonara", idioma_origem="italiano")
        self.assertIn("Carbonara", resultado)
        self.assertIn("Guanciale", resultado)
        self.assertIn("Pecorino", resultado)
        self.assertIn("glúten", resultado.lower())
        self.assertIn("ovos", resultado.lower())

    def test_traduzir_tonkatsu_japones(self):
        resultado = traduzir_e_explicar_cardapio("Tonkatsu", idioma_origem="japonês")
        self.assertIn("Tonkatsu", resultado)
        self.assertIn("Panko", resultado)
        self.assertIn("milanesa", resultado.lower())
        self.assertIn("glúten", resultado.lower())
        self.assertIn("soja", resultado.lower())

    def test_traduzir_wiener_schnitzel_alemao(self):
        resultado = traduzir_e_explicar_cardapio("Wiener Schnitzel", idioma_origem="alemão")
        self.assertIn("Schnitzel", resultado)
        self.assertIn("milanesa", resultado.lower())

    def test_traduzir_shepherds_pie_ingles_analogia_escondidinho(self):
        resultado = traduzir_e_explicar_cardapio("Shepherd's Pie", idioma_origem="inglês")
        self.assertIn("Shepherd's Pie", resultado)
        self.assertIn("escondidinho", resultado.lower())

    def test_alerta_restricao_vegano_com_carne(self):
        resultado = traduzir_e_explicar_cardapio(
            "Boeuf Bourguignon",
            restricoes_alimentares="vegano"
        )
        self.assertIn("CONFLITO DE RESTRIÇÃO ALIMENTAR", resultado)
        self.assertIn("NÃO é recomendado", resultado)
        self.assertIn("carne", resultado.lower())

    def test_alerta_restricao_celiaco_com_massa(self):
        resultado = traduzir_e_explicar_cardapio(
            "Spaghetti alla Carbonara",
            restricoes_alimentares="celíaco"
        )
        self.assertIn("CONFLITO DE RESTRIÇÃO ALIMENTAR", resultado)
        self.assertIn("glúten", resultado.lower())

    def test_alerta_restricao_intolerancia_lactose(self):
        resultado = traduzir_e_explicar_cardapio(
            "Cacio e Pepe",
            restricoes_alimentares="intolerante a lactose"
        )
        self.assertIn("CONFLITO DE RESTRIÇÃO ALIMENTAR", resultado)
        self.assertIn("pecorino", resultado.lower())

    def test_alerta_restricao_alergia_frutos_do_mar(self):
        resultado = traduzir_e_explicar_cardapio(
            "Pulpo a la Gallega",
            restricoes_alimentares="alergia a frutos do mar"
        )
        self.assertIn("CONFLITO DE RESTRIÇÃO ALIMENTAR", resultado)
        self.assertIn("polvo", resultado.lower())

    def test_compatibilidade_ratatouille_vegano(self):
        resultado = traduzir_e_explicar_cardapio(
            "Ratatouille",
            restricoes_alimentares="vegano"
        )
        self.assertIn("Compatibilidade com sua Restrição", resultado)
        self.assertIn("Não foram identificados conflitos", resultado)

    def test_prato_generico_com_tecnicas_culinarias(self):
        resultado = traduzir_e_explicar_cardapio(
            "Filet Mignon ao molho gorgonzola preparado sous-vide e flambado",
            idioma_origem="francês"
        )
        self.assertIn("Sous-vide", resultado)
        self.assertIn("gorgonzola", resultado.lower())
        self.assertIn("Flambagem", resultado)

    @patch("google.generativeai.GenerativeModel")
    def test_integracao_gemini_quando_disponivel(self, mock_genai_model):
        original_key = settings.GEMINI_API_KEY
        try:
            settings.GEMINI_API_KEY = "test_gemini_key_123"
            mock_instance = MagicMock()
            mock_response = MagicMock()
            mock_response.text = (
                "🍽️ **Guia Gastronômico de Cardápio:** Salada Niçoise\n\n"
                "🌍 **Origem Cultural / Idioma:** Francesa\n"
                "🥣 **Ingredientes Principais:** Atum, ovos, azeitonas, vagens\n"
                "👨‍🍳 **Modo de Preparo e Técnica Culinária:** Salada fresca composta montada\n"
                "🇧🇷 **Analogia Brasileira:** Lembra uma salada de maionese com atum de domingo\n"
                "⚠️ **Alérgenos Conhecidos:** Peixe, ovos\n"
                "🚨 **Alerta de Restrições:** Seguro."
            )
            mock_instance.generate_content.return_value = mock_response
            mock_genai_model.return_value = mock_instance

            resultado = traduzir_e_explicar_cardapio("Salada Nicoise Exotica")
            self.assertIn("Salada Niçoise", resultado)
            self.assertIn("Analogia Brasileira", resultado)
        finally:
            settings.GEMINI_API_KEY = original_key


if __name__ == "__main__":
    unittest.main()
