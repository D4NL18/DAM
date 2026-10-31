def get_calendar_notes_prompt() -> str:
    """Regras do domínio de calendário, notas/lembretes e wishlist (P-1108 / P-0501)."""
    return (
        "### GOOGLE CALENDAR CRUD:\n"
        "- To create an appointment use `agendar_evento`. To cancel/delete use `excluir_evento`. To reschedule/modify use `editar_evento` (NEVER use `agendar_evento` for edits to avoid duplicates).\n\n"
        "### REMINDERS RULE (SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR):\n"
        "- When listing reminders: show ONLY reminders scheduled for TODAY. Call `listar_lembretes_pendentes` with apenas_hoje=True.\n"
        "- Future reminders MUST NOT appear unless the user explicitly asks for all future reminders (apenas_hoje=False).\n"
        "- If none for today: 'Nenhuma tarefa pendente para hoje'.\n\n"
        "### NOTES & WISHLIST DATABASE PERSISTENCE (MANDATORY):\n"
        "- NEVER pretend to save a note or wishlist item in conversation memory without calling the database persistence tool!\n"
        "- For personal notes, quotes, lists, or information to remember: ALWAYS call `criar_anotacao` to save in Firestore (`information_notes`), `buscar_anotacoes` to list/search, `atualizar_anotacao` to edit, or `excluir_anotacao` to delete.\n"
        "- For wishlist items, products to buy, PC parts/components, hardware, or store links: ALWAYS call `adicionar_item_wishlist` (passing `moeda='USD'` if in dollars or `'BRL'` if in reais) to persist in Firestore (`wishlist`), `consultar_wishlist` to list/search, `atualizar_item_wishlist` to update, `marcar_item_wishlist_comprado` when purchased, or `remover_item_wishlist` to delete.\n"
        "- When the user asks about saved items, PC parts, wishlist, or notes, ALWAYS call `consultar_wishlist` and/or `buscar_anotacoes` to fetch the real records from the database.\n"
    )
