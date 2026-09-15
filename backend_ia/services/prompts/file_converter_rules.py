def get_file_converter_prompt() -> str:
    """Regras de conversão e gerenciamento de arquivos US-09 (P-1108)."""
    return (
        "### FILE CONVERSION (US-09):\n"
        "- Full file conversion hub: PDF↔Word, Images→PDF, merge/split PDF, image format conversion, PDF text extraction.\n"
        "- Use `gerenciar_arquivos` for all file operations.\n"
    )
