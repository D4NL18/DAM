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
    Traduz qualquer conteúdo em texto puro, texto extraído de imagens (OCR) ou transcrito de áudios
    para o idioma de destino solicitado utilizando a Google Cloud Translation API.
    A resposta é entregue estritamente em formato de texto legível.

    Args:
        texto: O texto que deve ser traduzido (digitado pelo usuário, extraído de imagem/placa/menu, ou transcrito de áudio).
        idioma_destino: Idioma de chegada (ex: 'pt', 'en', 'es', 'fr', 'de', 'ja' ou 'inglês', 'espanhol', 'japonês'). Padrão: 'pt'.
        idioma_origem: Idioma de partida, se conhecido. Se omitido, a detecção é feita automaticamente.

    Returns:
        Texto formatado contendo o idioma identificado e a tradução gerada.
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
