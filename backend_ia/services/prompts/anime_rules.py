def get_anime_prompt() -> str:
    """
    Regras do domínio de animes, AniList e calendário de lançamentos.
    """
    return (
        "### DOMÍNIO DE ANIMES & ANILIST:\n"
        "- Para interação com animes e com a conta oficial do AniList:\n"
        "  1. 'adicionar_anime_watchlist': Quando o usuário disser para adicionar anime à lista ('adiciona Dandadan na minha lista').\n"
        "  2. 'atualizar_progresso_anime': Quando disser que assistiu um episódio para subir o contador ('assisti o ep 8 de Frieren', 'vi mais um ep' -> se for incremental sem número, passe incrementar=True).\n"
        "  3. 'listar_meus_animes': Quando perguntar sobre o que está assistindo ('o que eu to vendo?', 'meus animes em andamento'), chame com status='assistindo'.\n"
        "  4. 'marcar_anime_concluido': Quando disser que terminou ou finalizou um anime ('terminei Frieren', 'acabei Solo Leveling, nota 9').\n"
        "  5. 'consultar_proximo_episodio': Para datas de exibição e contagem regressiva de episódios novos.\n"
        "  6. 'consultar_novas_temporadas': Para verificar se 2ª ou 3ª temporada já foi anunciada.\n"
        "  7. 'grade_semanal_animes': Para a grade semanal dos animes acompanhados.\n"
        "  8. 'explorar_temporada_animes': Para lançamentos e estreias da temporada atual ou futura.\n"
    )
