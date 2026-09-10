import logging
from typing import Optional
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)

FLAG_MAP = {
    "pt": "🇧🇷/🇵🇹",
    "en": "🇺🇸/🇬🇧",
    "es": "🇪🇸",
    "fr": "🇫🇷",
    "de": "🇩🇪",
    "it": "🇮🇹",
    "ja": "🇯🇵",
    "zh": "🇨🇳",
    "ru": "🇷🇺",
    "ko": "🇰🇷",
    "ar": "🇸🇦",
    "nl": "🇳🇱"
}

def traduzir_conteudo(
    texto: str,
    idioma_destino: str = "pt",
    idioma_origem: Optional[str] = None
) -> str:
    """
    Translate text, image-extracted text, or audio transcripts using Google Cloud Translation.

    Args:
        texto: Text to translate.
        idioma_destino: Target language code/name (default 'pt').
        idioma_origem: Source language if known (default auto-detect).
    """
    if not texto or not texto.strip():
        return "⚠️ Texto vazio. Por favor, informe o conteúdo que deseja traduzir."

    res = TranslationService.translate_text(
        text=texto,
        target_language=idioma_destino,
        source_language=idioma_origem
    )

    if res.get("status") == "error":
        return f"❌ Erro na tradução: {res.get('message', 'Falha no processamento.')}"

    src_code = res.get("source_language", "auto").upper()
    tgt_code = res.get("target_language", "pt").upper()
    translated = res.get("translated_text", "")
    src_flag = FLAG_MAP.get(src_code.lower(), "")
    tgt_flag = FLAG_MAP.get(tgt_code.lower(), "")

    flag_str = f" ({src_code} {src_flag} ➔ {tgt_code} {tgt_flag})" if src_flag or tgt_flag else f" ({src_code} ➔ {tgt_code})"

    return (
        f"🌐 **Tradução{flag_str}:**\n\n"
        f"{translated}\n"
    )
