def get_anime_prompt() -> str:
    """
    Regras do domínio de animes, AniList e calendário de lançamentos.
    """
    return (
        "### DOMÍNIO DE ANIMES & ANILIST:\n"
        "- Para interação com animes e com a conta oficial do AniList:\n"
        "  1. 'adicionar_anime_watchlist': Quando o usuário disser para adicionar anime à lista ('adiciona Dandadan na minha lista').\n"
        "  2. 'atualizar_progresso_anime': Quando disser que assistiu um episódio para subir o contador ('assisti o ep 8 de Frieren', 'vi mais um ep' -> se for incremental sem número, passe incrementar=True).\n"
        "  3. 'listar_meus_animes':\n"
        "     - Quando perguntar sobre o que está assistindo ('o que eu to vendo?', 'meus animes em andamento'), chame com status='assistindo'.\n"
        "     - Quando perguntar sobre o que tem para assistir / animes que quer assistir ('quais animes quero assistir?', 'o que tenho na lista para ver?'), chame com status='planejo_assistir'.\n"
        "  4. 'marcar_anime_concluido': Quando disser que terminou ou finalizou um anime ('terminei Frieren', 'acabei Solo Leveling, nota 9').\n"
        "  5. 'consultar_proximo_episodio': Para datas de exibição e contagem regressiva de episódios novos.\n"
        "  6. 'consultar_novas_temporadas': Para verificar se 2ª ou 3ª temporada já foi anunciada.\n"
        "  7. 'grade_semanal_animes': Para a grade semanal dos animes acompanhados.\n"
        "  8. 'explorar_temporada_animes': Para lançamentos e estreias da temporada atual ou futura.\n\n"
        "- DIRETRIZES CRÍTICAS DE STATUS DE ANIMES (REGRAS MANDATÓRIAS):\n"
        "  -> LANÇAMENTO DE EPISÓDIOS: Para lançamentos de episódios (hoje, grade semanal ou próximo episódio), considere ESTRITAMENTE animes com status 'assistindo' (watching).\n"
        "  -> LANÇAMENTO DE TEMPORADAS / CONTINUAÇÕES: Para lançamentos de temporadas ou continuações dos animes do usuário (ex: lançamentos de outubro, estreias de temporada), considere ESTRITAMENTE animes com status 'assistindo' (watching) ou 'concluído' (completed).\n"
        "  -> É TERMINANTEMENTE PROIBIDO falar de continuações, sequências ou novas temporadas de animes que estejam com status 'dropado' (dropped) ou 'pausado' (paused/on hold).\n"
        "  -> ANIMES PARA ASSISTIR: Para puxar os animes que o usuário quer assistir, puxe APENAS animes da lista de 'planejo_assistir' (plan to watch) OU animes em 'assistindo' onde o usuário ainda não viu nenhum episódio (0 episódios vistos).\n"
    )

