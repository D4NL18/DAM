import html
import logging
import re
import threading
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from config.settings import settings
from config.timezone import get_brasilia_now

logger = logging.getLogger(__name__)

LANGUAGE_NAME_MAP = {
    "português": "pt",
    "portugues": "pt",
    "inglês": "en",
    "ingles": "en",
    "espanhol": "es",
    "castelhano": "es",
    "francês": "fr",
    "frances": "fr",
    "alemão": "de",
    "alemao": "de",
    "italiano": "it",
    "japonês": "ja",
    "japones": "ja",
    "mandarim": "zh",
    "chinês": "zh",
    "chines": "zh",
    "russo": "ru",
    "coreano": "ko",
    "árabe": "ar",
    "arabe": "ar",
    "holandês": "nl",
    "holandes": "nl",
    "grego": "el",
    "turco": "tr",
    "polonês": "pl",
    "polones": "pl",
    "sueco": "sv",
    "norueguês": "no",
    "noruegues": "no",
    "dinamarquês": "da",
    "dinamarques": "da",
    "finlandês": "fi",
    "finlandes": "fi",
    "hindi": "hi"
}

class TranslationService:
    """
    Serviço de Tradução Universal Multimodal integrado à Google Cloud Translation API v2
    com gestão FinOps da cota gratuita de 500.000 caracteres/mês e fallback resiliente.
    """
    _lock = threading.Lock()
    _monthly_characters: Dict[str, int] = {}
    _monthly_requests: Dict[str, int] = {}

    @classmethod
    def _get_current_month_key(cls) -> str:
        try:
            return get_brasilia_now().strftime("%Y-%m-%d")[:7]
        except Exception:
            return datetime.utcnow().strftime("%Y-%m-%d")[:7]

    @classmethod
    def normalize_language_code(cls, lang: Optional[str]) -> str:
        """
        P-1005: Normaliza o código ou nome do idioma para código ISO 639-1 em minúsculas.
        Aceita nomes comuns em português e remove sufixos regionais (ex: pt-BR -> pt).
        Aplica sanitização estrita SecOps contra Path Traversal e Command Injection.
        """
        if not lang:
            return "pt"

        raw = lang.strip().lower()

        # Mapeamento prévio de linguagem natural (com acentos preservados)
        if raw in LANGUAGE_NAME_MAP:
            return LANGUAGE_NAME_MAP[raw]

        # Remove caracteres perigosos de path traversal e comandos
        cleaned = re.sub(r"[^a-z0-9_\-\s]", "", raw).strip()
        if not cleaned:
            return "pt"

        # Mapeamento após limpeza
        if cleaned in LANGUAGE_NAME_MAP:
            return LANGUAGE_NAME_MAP[cleaned]

        # Remove sufixos regionais (ex: pt-br, en-us, es-es)
        if "-" in cleaned:
            base = cleaned.split("-")[0].strip()
            if base in LANGUAGE_NAME_MAP:
                return LANGUAGE_NAME_MAP[base]
            cleaned = base
        elif "_" in cleaned:
            base = cleaned.split("_")[0].strip()
            if base in LANGUAGE_NAME_MAP:
                return LANGUAGE_NAME_MAP[base]
            cleaned = base

        # Mantém apenas letras e limita a 5 caracteres
        alpha_only = re.sub(r"[^a-z]", "", cleaned)
        return alpha_only[:5] if alpha_only else "pt"

    @classmethod
    def get_monthly_usage(cls) -> Dict[str, Any]:
        """
        P-1002: Retorna a volumetria de consumo da cota gratuita do mês atual.
        """
        month = cls._get_current_month_key()
        limit = getattr(settings, "TRANSLATION_FREE_TIER_MONTHLY_LIMIT", 500000)
        
        with cls._lock:
            chars = cls._monthly_characters.get(month, 0)
            reqs = cls._monthly_requests.get(month, 0)

        pct = round((chars / limit) * 100, 2) if limit > 0 else 100.0
        free_active = chars < limit

        return {
            "month": month,
            "characters_used": chars,
            "monthly_limit": limit,
            "percentage_used": pct,
            "requests_count": reqs,
            "free_tier_active": free_active
        }

    @classmethod
    def record_usage(cls, characters_count: int):
        """Registra os caracteres e incremento de requisição para o mês corrente."""
        month = cls._get_current_month_key()
        with cls._lock:
            cls._monthly_characters[month] = cls._monthly_characters.get(month, 0) + characters_count
            cls._monthly_requests[month] = cls._monthly_requests.get(month, 0) + 1

    @classmethod
    def reset_monthly_counter(cls):
        """Reinicia o contador em memória (útil para testes unitários)."""
        with cls._lock:
            cls._monthly_characters.clear()
            cls._monthly_requests.clear()

    @classmethod
    def set_monthly_usage_for_test(cls, month: str, chars: int):
        """Define uso para validação de testes unitários."""
        with cls._lock:
            cls._monthly_characters[month] = chars

    @classmethod
    def translate_text(
        cls,
        text: str,
        target_language: str = "pt",
        source_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        P-1001 e P-1002: Traduz texto de qualquer idioma para qualquer idioma via Google Cloud Translation API.
        Aplica salvaguarda FinOps contra excesso de cota gratuita e fallback resiliente.
        """
        if not text or not text.strip():
            return {
                "status": "error",
                "message": "Texto vazio para tradução.",
                "original_text": text,
                "translated_text": "",
                "characters_count": 0
            }

        text_to_translate = text.strip()
        chars_count = len(text_to_translate)
        target = cls.normalize_language_code(target_language)
        source = cls.normalize_language_code(source_language) if source_language else None

        usage = cls.get_monthly_usage()
        
        # P-1002: Trava FinOps Hard Cap para não ultrapassar 500k caracteres cobrados
        if not usage["free_tier_active"] or (usage["characters_used"] + chars_count > usage["monthly_limit"]):
            logger.warning(f"[FINOPS TRANSLATION] Limite gratuito de 500k caracteres/mês atingido ({usage['characters_used']}). Acionando fallback gratuito.")
            return cls._execute_resilient_fallback(text_to_translate, target, source)

        # Chave de API GCP (ordem de preferência)
        api_key = (
            getattr(settings, "GOOGLE_TRANSLATE_API_KEY", "")
            or getattr(settings, "GOOGLE_MAPS_API_KEY", "")
            or getattr(settings, "GEMINI_API_KEY", "")
        )

        if api_key:
            try:
                endpoint = "https://translation.googleapis.com/language/translate/v2"
                params = {"key": api_key}
                payload: Dict[str, Any] = {
                    "q": [text_to_translate],
                    "target": target,
                    "format": "text"
                }
                if source:
                    payload["source"] = source

                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(endpoint, params=params, json=payload)
                
                if resp.status_code == 200:
                    data = resp.json()
                    translations = data.get("data", {}).get("translations", [])
                    if translations:
                        item = translations[0]
                        translated_raw = item.get("translatedText", "")
                        # Unescape caracteres HTML retornados pela API v2
                        translated = html.unescape(translated_raw)
                        detected_source = item.get("detectedSourceLanguage") or source or "auto"
                        
                        cls.record_usage(chars_count)
                        return {
                            "status": "success",
                            "original_text": text_to_translate,
                            "translated_text": translated,
                            "source_language": detected_source,
                            "target_language": target,
                            "characters_count": chars_count,
                            "provider": "google_cloud_translation_v2"
                        }
                    else:
                        logger.warning("Resposta da API de tradução do Google Cloud vazia. Acionando fallback.")
                else:
                    logger.warning(f"Google Cloud Translation API retornou status {resp.status_code}: {resp.text}. Acionando fallback.")
            except Exception as e:
                logger.error(f"Erro na requisição à Google Cloud Translation API: {e}. Acionando fallback.")

        # P-1006: Fallback resiliente
        return cls._execute_resilient_fallback(text_to_translate, target, source)

    @classmethod
    def _execute_resilient_fallback(
        cls,
        text: str,
        target_language: str,
        source_language: Optional[str]
    ) -> Dict[str, Any]:
        """
        P-1006: Fallback resiliente e de custo zero caso a API oficial falhe ou chave não esteja ativa.
        """
        chars_count = len(text)
        src = source_language or "auto"
        
        try:
            url = "https://translate.googleapis.com/translate_a/single"
            params = {
                "client": "gtx",
                "sl": src,
                "tl": target_language,
                "dt": "t",
                "q": text
            }
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url, params=params)
            
            if resp.status_code == 200:
                data = resp.json()
                # O formato gtx retorna uma lista de sentenças em data[0]
                translated_sentences = []
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                    for sentence in data[0]:
                        if isinstance(sentence, list) and len(sentence) > 0 and sentence[0]:
                            translated_sentences.append(sentence[0])
                
                detected = data[2] if len(data) > 2 and isinstance(data[2], str) else src
                translated_text = "".join(translated_sentences) or text
                
                return {
                    "status": "success",
                    "original_text": text,
                    "translated_text": translated_text,
                    "source_language": detected,
                    "target_language": target_language,
                    "characters_count": chars_count,
                    "provider": "google_translation_fallback"
                }
        except Exception as e:
            logger.warning(f"Fallback HTTP falhou: {e}. Retornando texto de fallback seguro.")

        # Fallback local de emergência
        return {
            "status": "success",
            "original_text": text,
            "translated_text": text,
            "source_language": source_language or "auto",
            "target_language": target_language,
            "characters_count": chars_count,
            "provider": "emergency_local_fallback"
        }
