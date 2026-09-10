# Funcionalidade: Anime Tracker & Calendário AniList

## 1. Visão Geral
O **Anime Tracker** é a central de rastreamento de animes do DAM, integrada de forma bi-direcional à conta oficial do usuário no **AniList.co** (`Tonho123`) e persistida no Cloud Firestore (`anime_watchlist`).

A funcionalidade permite gerenciar listas de animes em exibição, atualizar episódios assistidos automaticamente, pesquisar novas temporadas/sequências e consultar datas de lançamentos de episódios no fuso horário brasileiro (America/Sao_Paulo).

## 2. Capacidades do Assistente
1. **Adicionar Anime à Watchlist (`adicionar_anime_watchlist`):**
   - Busca no GraphQL do AniList metadados oficiais (IDs, títulos romaji/english, episódios totais, status).
   - Salva localmente e sincroniza remotamente na conta AniList com status `CURRENT` ou `PLANNING`.
2. **Atualizar Progresso de Episódios (`atualizar_progresso_anime`):**
   - Suporta contagem absoluta ("assisti o ep 8") ou incremento relativo de +1 ("vi mais um ep").
   - Dispara mutação GraphQL `SaveMediaListEntry` refletindo o progresso em tempo real no site do AniList.
3. **Listar Animes em Andamento (`listar_meus_animes`):**
   - Filtra os animes em exibição com status `assistindo`.
   - Exibe barra de progresso (ex: `Ep. 10/12`) e contagem regressiva para o próximo episódio se houver transmissão agendada.
4. **Concluir Anime (`marcar_anime_concluido`):**
   - Ajusta progresso para o total máximo de episódios da temporada.
   - Registra nota pessoal informada pelo usuário (ex: nota 9.5).
   - Atualiza status para `COMPLETED` no Firestore e no perfil oficial do AniList.
5. **Calendário e Sequências (`consultar_proximo_episodio`, `consultar_novas_temporadas`, `explorar_temporada_animes`, `grade_semanal_animes`):**
   - Identifica sequências anunciadas, filmes e novas temporadas confirmadas na árvore de relações do AniList.
   - Mostra lançamentos sazonais da temporada atual (ex: Outono 2026).

## 3. Modelo de Dados (Firestore `anime_watchlist`)
- `anilist_id`: int
- `titulo_principal`: string
- `titulo_ingles`: string
- `status_transmissao`: string (RELEASING, FINISHED, NOT_YET_RELEASED)
- `total_episodios`: int / null
- `status_usuario`: string (assistindo, planejo_assistir, concluido, pausado)
- `ultimo_episodio_visto`: int
- `nota_usuario`: float (opcional)
- `proximo_episodio`: dict (episodio, airing_at, data_formatada, tempo_restante_segundos)
- `updated_at`: string ISO-8601
