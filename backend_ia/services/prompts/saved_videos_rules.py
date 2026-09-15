def get_saved_videos_prompt() -> str:
    """Regras do domínio de vídeos salvos (P-1108)."""
    return (
        "### SAVED VIDEOS (TIKTOK, INSTAGRAM, YOUTUBE):\n"
        "- Links to save: call `salvar_video` immediately, extracting subject into `descricao`, `titulo`, `categoria`.\n"
        "- Querying saved videos: use `consultar_videos_salvos`.\n"
        "- Marking watched: `marcar_video_assistido`. Removing: `remover_video_salvo`.\n"
    )
