import pytest
from unittest.mock import patch, MagicMock
from services.translation_service import TranslationService

class TestTranslationService:
    def setup_method(self):
        TranslationService.reset_monthly_counter()

    def test_normalize_language_code_from_iso(self):
        """Valida que códigos ISO 639-1 são normalizados corretamente."""
        assert TranslationService.normalize_language_code("en") == "en"
        assert TranslationService.normalize_language_code("pt") == "pt"
        assert TranslationService.normalize_language_code("es") == "es"
        assert TranslationService.normalize_language_code("ja") == "ja"

    def test_normalize_language_code_from_regional_tags(self):
        """P-1005: Normaliza sufixos regionais como pt-BR ou en-US para o código base."""
        assert TranslationService.normalize_language_code("pt-BR") == "pt"
        assert TranslationService.normalize_language_code("en-US") == "en"
        assert TranslationService.normalize_language_code("es-ES") == "es"

    def test_normalize_language_code_from_natural_names(self):
        """P-1005: Aceita nomes de idiomas em português em linguagem natural."""
        assert TranslationService.normalize_language_code("português") == "pt"
        assert TranslationService.normalize_language_code("ingles") == "en"
        assert TranslationService.normalize_language_code("inglês") == "en"
        assert TranslationService.normalize_language_code("espanhol") == "es"
        assert TranslationService.normalize_language_code("francês") == "fr"
        assert TranslationService.normalize_language_code("alemão") == "de"
        assert TranslationService.normalize_language_code("italiano") == "it"
        assert TranslationService.normalize_language_code("japonês") == "ja"
        assert TranslationService.normalize_language_code("japones") == "ja"
        assert TranslationService.normalize_language_code("mandarim") == "zh"
        assert TranslationService.normalize_language_code("russo") == "ru"

    @patch("services.translation_service.httpx.Client")
    def test_translate_text_google_cloud_api_success(self, mock_httpx_cls):
        """P-1001: Tradução com sucesso via Google Cloud Translation API v2."""
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "translations": [
                    {
                        "translatedText": "Olá mundo, como você está?",
                        "detectedSourceLanguage": "en"
                    }
                ]
            }
        }
        mock_client.post.return_value = mock_resp

        result = TranslationService.translate_text(
            text="Hello world, how are you?",
            target_language="pt",
            source_language="en"
        )

        assert result["status"] == "success"
        assert result["translated_text"] == "Olá mundo, como você está?"
        assert result["source_language"] == "en"
        assert result["target_language"] == "pt"
        assert result["characters_count"] == len("Hello world, how are you?")
        assert result["provider"] == "google_cloud_translation_v2"

    @patch("services.translation_service.httpx.Client")
    def test_translate_text_auto_detect_source(self, mock_httpx_cls):
        """P-1001: Detecção automática do idioma de origem quando omitido."""
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "translations": [
                    {
                        "translatedText": "Onde fica a estação?",
                        "detectedSourceLanguage": "de"
                    }
                ]
            }
        }
        mock_client.post.return_value = mock_resp

        result = TranslationService.translate_text(
            text="Wo ist der Bahnhof?",
            target_language="pt",
            source_language=None
        )

        assert result["status"] == "success"
        assert result["translated_text"] == "Onde fica a estação?"
        assert result["source_language"] == "de"
        assert result["target_language"] == "pt"

    @patch("services.translation_service.httpx.Client")
    def test_translate_text_any_to_any(self, mock_httpx_cls):
        """P-1001: Suporte a tradução de qualquer língua para qualquer língua (ex: ES -> EN)."""
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__enter__.return_value = mock_client
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "translations": [
                    {
                        "translatedText": "Good morning my friend",
                        "detectedSourceLanguage": "es"
                    }
                ]
            }
        }
        mock_client.post.return_value = mock_resp

        result = TranslationService.translate_text(
            text="Buenos días mi amigo",
            target_language="en",
            source_language="es"
        )

        assert result["status"] == "success"
        assert result["translated_text"] == "Good morning my friend"
        assert result["source_language"] == "es"
        assert result["target_language"] == "en"

    def test_free_tier_character_limit_hard_cap(self):
        """P-1002: Trava de segurança FinOps para não exceder 500k caracteres/mês."""
        TranslationService.set_monthly_usage_for_test(month="2026-09", chars=500000)
        
        # Tentativa de chamada deve acionar o fallback ou rejeitar chamadas pagas
        usage = TranslationService.get_monthly_usage()
        assert usage["characters_used"] >= 500000
        assert usage["free_tier_active"] is False

    @patch("services.translation_service.httpx.Client")
    def test_resilient_fallback_on_api_error(self, mock_httpx_cls):
        """P-1006: Se a API falhar ou chave estiver ausente, aciona fallback resiliente."""
        mock_client = MagicMock()
        mock_httpx_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.side_effect = Exception("Google Cloud Translation API connection timeout")

        result = TranslationService.translate_text(
            text="Hello world",
            target_language="pt"
        )

        assert result["status"] == "success"
        assert result["translated_text"] != ""
        assert "fallback" in result["provider"]

    def test_empty_text_returns_error(self):
        """Valida que textos vazios são tratados defensivamente."""
        result = TranslationService.translate_text(text="   ", target_language="pt")
        assert result["status"] == "error"
        assert "vazio" in result["message"].lower()
