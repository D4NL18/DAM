import pytest
from unittest.mock import patch, MagicMock
from services.tools.translation_tool import traduzir_conteudo

class TestTranslationTool:
    @patch("services.tools.translation_tool.TranslationService.translate_text")
    def test_traduzir_conteudo_success_format(self, mock_translate):
        """P-1001 e P-1004: Tool formata a resposta amigável e legível para WhatsApp."""
        mock_translate.return_value = {
            "status": "success",
            "original_text": "Good morning",
            "translated_text": "Bom dia",
            "source_language": "en",
            "target_language": "pt",
            "characters_count": 12,
            "provider": "google_cloud_translation_v2"
        }

        output = traduzir_conteudo(texto="Good morning", idioma_destino="pt")

        assert "Bom dia" in output
        assert "Tradução" in output or "🌐" in output

    @patch("services.tools.translation_tool.TranslationService.translate_text")
    def test_traduzir_conteudo_with_custom_target(self, mock_translate):
        """P-1001: Tool suporta idiomas de destino customizados como francês ou japonês."""
        mock_translate.return_value = {
            "status": "success",
            "original_text": "Olá amigo",
            "translated_text": "Bonjour mon ami",
            "source_language": "pt",
            "target_language": "fr",
            "characters_count": 9,
            "provider": "google_cloud_translation_v2"
        }

        output = traduzir_conteudo(texto="Olá amigo", idioma_destino="francês")

        assert "Bonjour mon ami" in output

    def test_traduzir_conteudo_empty_string_handled(self):
        """Validação de texto em branco."""
        output = traduzir_conteudo(texto="   ")
        assert "vazio" in output.lower() or "informe" in output.lower()
