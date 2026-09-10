def get_anime_prompt() -> str:
    """Anime domain rules for AniList integration and release tracking."""
    return (
        "### ANIME & ANILIST DOMAIN:\n"
        "- Tool routing:\n"
        "  1. `adicionar_anime_watchlist`: Add anime to personal list.\n"
        "  2. `atualizar_progresso_anime`: Update episode progress (use incrementar=True for +1 without specific number).\n"
        "  3. `listar_meus_animes`: List user's anime — status='assistindo' for currently watching, status='planejo_assistir' for plan-to-watch.\n"
        "  4. `marcar_anime_concluido`: Mark anime as completed with optional rating.\n"
        "  5. `consultar_proximo_episodio`: Next episode date and countdown.\n"
        "  6. `consultar_novas_temporadas`: Check for announced sequels/new seasons.\n"
        "  7. `grade_semanal_animes`: Weekly release schedule of tracked anime.\n"
        "  8. `explorar_temporada_animes`: Explore current/future season releases.\n\n"
        "- CRITICAL STATUS RULES:\n"
        "  -> Episode releases: consider ONLY anime with status 'assistindo' (watching).\n"
        "  -> Season/sequel releases: consider ONLY 'assistindo' or 'concluído' (completed).\n"
        "  -> FORBIDDEN: never mention sequels for 'dropado' (dropped) or 'pausado' (paused) anime.\n"
        "  -> Plan-to-watch: show ONLY anime from 'planejo_assistir' list or 'assistindo' with 0 episodes watched.\n"
    )
