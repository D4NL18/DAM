def get_translation_rules_prompt() -> str:
    """Universal multimodal translator rules (US-10)."""
    return (
        "### UNIVERSAL MULTIMODAL TRANSLATOR (US-10):\n"
        "- Integrated with Google Cloud Translation for precise any-to-any language translations.\n"
        "- Text translation: always call `traduzir_conteudo(texto=..., idioma_destino=..., idioma_origem=...)`.\n"
        "- Image translation: OCR the visual text, then pass to `traduzir_conteudo`.\n"
        "- Audio translation: transcribe spoken content, then call `traduzir_conteudo`.\n"
        "- ABSOLUTE RULE: Translation responses must ALWAYS be delivered as text in WhatsApp. Present results cleanly for easy reading and copying.\n"
    )
