def get_calendar_notes_prompt() -> str:
    """Regras do domínio de calendário e notas/lembretes (P-1108)."""
    return (
        "### GOOGLE CALENDAR CRUD:\n"
        "- To create an appointment use `agendar_evento`. To cancel/delete use `excluir_evento`. To reschedule/modify use `editar_evento` (NEVER use `agendar_evento` for edits to avoid duplicates).\n\n"
        "### REMINDERS RULE (SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR):\n"
        "- When listing reminders: show ONLY reminders scheduled for TODAY. Call `listar_lembretes_pendentes` with apenas_hoje=True.\n"
        "- Future reminders MUST NOT appear unless the user explicitly asks for all future reminders (apenas_hoje=False).\n"
        "- If none for today: 'Nenhuma tarefa pendente para hoje'.\n"
    )
