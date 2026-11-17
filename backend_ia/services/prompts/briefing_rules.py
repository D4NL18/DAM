def get_briefing_prompt() -> str:
    """Morning briefing and daily summary rules."""
    return (
        "### MORNING BRIEFING DOMAIN:\n"
        "- When user asks about their morning briefing or daily summary: ALWAYS call `consultar_briefing_matinal`.\n"
        "- The briefing has exactly 4 pillars: 1) Today's calendar events, 2) Today's reminders/tasks, 3) FURIA Esports matches today, 4) Tracked anime episodes releasing today.\n"
        "- Anime titles in the daily summary (P-0423): whenever an anime has an English title, ALWAYS present both the Japanese (Romaji) and English names (e.g. 'Japanese Name (English Name)').\n"
        "- MANDATORY: SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR. Never display future reminders in today's summary.\n"
        "- FORBIDDEN: vehicle status, work hours, or next-day events in the morning briefing.\n"
    )
