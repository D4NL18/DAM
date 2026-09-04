import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from config import firebase
from config.settings import settings
from services.user_context import UserContext

logger = logging.getLogger(__name__)

ANILIST_API_URL = "https://graphql.anilist.co"

# Fallback em memória caso Firestore não esteja conectado
_MEMORY_WATCHLIST: Dict[str, Dict[str, Any]] = {}

def _reset_memory_watchlist():
    """Auxiliar para testes unitários."""
    _MEMORY_WATCHLIST.clear()

def _consultar_anilist_graphql(query: str, variables: dict, token: Optional[str] = None) -> Optional[dict]:
    """Executa uma query ou mutação GraphQL contra a API do AniList."""
    data_payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "DAM-Assistant/1.0"
    }
    tok = token or settings.ANILIST_ACCESS_TOKEN
    if tok:
        headers["Authorization"] = f"Bearer {tok.strip()}"

    req = urllib.request.Request(
        ANILIST_API_URL,
        data=data_payload,
        headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("data")
    except Exception as e:
        logger.error(f"Erro na requisição GraphQL AniList: {e}")
        return None

def _salvar_entrada_anilist_remoto(media_id: int, status: str, progress: int = 0, score: Optional[float] = None) -> bool:
    """
    Executa mutação oficial no AniList para salvar ou atualizar a entrada diretamente na conta do usuário no AniList.co.
    """
    if not settings.ANILIST_ACCESS_TOKEN:
        return False

    status_map = {
        "assistindo": "CURRENT",
        "current": "CURRENT",
        "planejo_assistir": "PLANNING",
        "planning": "PLANNING",
        "concluido": "COMPLETED",
        "completed": "COMPLETED",
        "pausado": "PAUSED",
        "paused": "PAUSED",
        "dropado": "DROPPED",
        "dropped": "DROPPED"
    }
    status_gql = status_map.get(status.lower(), "CURRENT")

    mutation = """
    mutation ($mediaId: Int, $status: MediaListStatus, $progress: Int, $score: Float) {
      SaveMediaListEntry (mediaId: $mediaId, status: $status, progress: $progress, score: $score) {
        id
        status
        progress
        score
      }
    }
    """
    variables = {
        "mediaId": int(media_id),
        "status": status_gql,
        "progress": int(progress)
    }
    if score is not None:
        variables["score"] = float(score)

    try:
        res = _consultar_anilist_graphql(mutation, variables)
        return res is not None and "SaveMediaListEntry" in res
    except Exception as e:
        logger.error(f"Erro ao salvar entrada remota no AniList: {e}")
        return False

def _format_timestamp_br(timestamp_epoch: int) -> str:
    """Converte timestamp UTC unix para data/hora amigável no fuso de Brasília (UTC-3)."""
    tz_br = timezone(timedelta(hours=-3))
    dt = datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc).astimezone(tz_br)
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_nome = dias_semana[dt.weekday()]
    return f"{dia_nome}, {dt.strftime('%d/%m/%Y às %H:%M')}"

def _calcular_tempo_restante(segundos_restantes: int) -> str:
    """Calcula string amigável de contagem regressiva (ex: '2 dias e 4 horas')."""
    if segundos_restantes <= 0:
        return "Disponível agora!"
    
    dias = segundos_restantes // 86400
    horas = (segundos_restantes % 86400) // 3600
    minutos = (segundos_restantes % 3600) // 60

    partes = []
    if dias > 0:
        partes.append(f"{dias} dia{'s' if dias > 1 else ''}")
    if horas > 0:
        partes.append(f"{horas} hora{'s' if horas > 1 else ''}")
    if minutos > 0 and dias == 0:
        partes.append(f"{minutos} min")

    return " em " + " e ".join(partes) if partes else " em instantes"


def sincronizar_perfil_anilist(username: Optional[str] = None) -> str:
    """
    Sincroniza a lista pessoal de animes diretamente do perfil público do AniList.
    Importa animes que você está assistindo (Watching) e planeja assistir (Planning),
    salvando no Firestore com progresso de episódios e datas de lançamento de novos episódios.

    Args:
        username (str, opcional): Nome de usuário no AniList. Se omitido, utiliza a configuração padrão do sistema.
    """
    user = (username or settings.ANILIST_USERNAME or "").strip()
    if not user:
        return (
            "⚠️ Nenhum nome de usuário do AniList informado.\n"
            "Você pode me dizer seu username dizendo: 'Meu perfil no AniList é fulano' "
            "ou salvando a variável ANILIST_USERNAME no .env."
        )

    graphql_query = """
    query ($userName: String) {
      MediaListCollection (userName: $userName, type: ANIME) {
        lists {
          name
          isCustomList
          entries {
            status
            progress
            score
            media {
              id
              title {
                romaji
                english
                native
              }
              format
              status
              episodes
              nextAiringEpisode {
                airingAt
                timeUntilAiring
                episode
              }
              siteUrl
            }
          }
        }
      }
    }
    """

    data = _consultar_anilist_graphql(graphql_query, {"userName": user})
    collection = data.get("MediaListCollection") if data else None

    if not collection or not collection.get("lists"):
        return f"Não encontrei listas de animes para o perfil '{user}' no AniList. Verifique se o username está correto e se o perfil é público."

    animes_assistindo = []
    animes_planejando = []
    total_sincronizados = 0

    for lst in collection["lists"]:
        for entry in lst.get("entries", []):
            media = entry.get("media")
            if not media:
                continue

            doc_id = str(media["id"])
            titulo_principal = media["title"]["romaji"] or media["title"]["english"] or "Anime"
            titulo_ingles = media["title"]["english"] or titulo_principal
            status_entry = entry.get("status", "CURRENT").upper()

            status_usuario = "assistindo"
            if status_entry in ["PLANNING"]:
                status_usuario = "planejo_assistir"
            elif status_entry in ["COMPLETED"]:
                status_usuario = "concluido"
            elif status_entry in ["PAUSED", "DROPPED"]:
                status_usuario = "pausado"

            proximo_ep = None
            if media.get("nextAiringEpisode"):
                nep = media["nextAiringEpisode"]
                proximo_ep = {
                    "episodio": nep["episode"],
                    "airing_at": nep["airingAt"],
                    "data_formatada": _format_timestamp_br(nep["airingAt"]),
                    "tempo_restante_segundos": nep["timeUntilAiring"]
                }

            anime_info = {
                "anilist_id": media["id"],
                "titulo_principal": titulo_principal,
                "titulo_ingles": titulo_ingles,
                "status_transmissao": media.get("status", "DESCONHECIDO"),
                "total_episodios": media.get("episodes"),
                "status_usuario": status_usuario,
                "ultimo_episodio_visto": int(entry.get("progress", 0)),
                "nota_usuario": entry.get("score"),
                "proximo_episodio": proximo_ep,
                "site_url": media.get("siteUrl"),
                "origem": "AniList Sync",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }

            # Salva na memória local
            _MEMORY_WATCHLIST[doc_id] = anime_info

            # Salva no Firestore
            if firebase.db is not None:
                try:
                    firebase.db.collection("anime_watchlist").document(doc_id).set(anime_info)
                except Exception as e:
                    logger.error(f"Erro ao salvar anime sincronizado no Firestore: {e}")

            total_sincronizados += 1

            if status_usuario == "assistindo":
                animes_assistindo.append(anime_info)
            elif status_usuario == "planejo_assistir":
                animes_planejando.append(anime_info)

    # Resumo formatado para WhatsApp
    linhas = [
        f"🔄 *Sincronização com AniList Concluída!*",
        f"👤 Perfil: **{user}**",
        f"📦 Total de Animes Sincronizados: **{total_sincronizados}**",
        f"• Assistindo no momento: **{len(animes_assistindo)}**",
        f"• Planejando assistir: **{len(animes_planejando)}**",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]

    # Destaque para animes que têm novos episódios chegando
    com_lancamento = [a for a in animes_assistindo if a.get("proximo_episodio")]
    if com_lancamento:
        linhas.append("\n🍿 *Próximos Episódios dos Seus Animes:*")
        for a in com_lancamento[:5]:
            pep = a["proximo_episodio"]
            tempo_str = _calcular_tempo_restante(pep["tempo_restante_segundos"])
            linhas.append(f"• **{a['titulo_principal']}** — Ep. {pep['episodio']} em {pep['data_formatada']} ({tempo_str})")

    linhas.append("\n💡 Agora você pode me perguntar a qualquer momento: *'Quando sai o próximo episódio dos meus animes?'* ou *'Qual a grade desta semana?'*.")
    return "\n".join(linhas)


def consultar_novas_temporadas(titulo_anime: str) -> str:
    """
    Pesquisa por continuações, sequências, filmes canônicos e novas temporadas de um anime via AniList.
    Identifica se uma 2ª ou 3ª temporada já foi anunciada, status de produção e datas de estreia.

    Args:
        titulo_anime (str): Nome do anime (ex: 'Frieren', 'Chainsaw Man', 'Solo Leveling', 'Jujutsu Kaisen').
    """
    titulo_busca = titulo_anime.strip()
    if not titulo_busca:
        return "Erro: Informe o nome do anime para consultar novas temporadas."

    graphql_query = """
    query ($search: String) {
      Media (search: $search, type: ANIME) {
        id
        title {
          romaji
          english
        }
        format
        status
        relations {
          edges {
            relationType
            node {
              id
              title {
                romaji
                english
              }
              format
              status
              season
              seasonYear
              startDate {
                year
                month
                day
              }
              nextAiringEpisode {
                episode
                airingAt
                timeUntilAiring
              }
              siteUrl
            }
          }
        }
      }
    }
    """

    data = _consultar_anilist_graphql(graphql_query, {"search": titulo_busca})
    media = data.get("Media") if data else None

    if not media:
        return f"Não encontrei o anime '{titulo_busca}' no banco de dados para verificar continuações."

    titulo_principal = media["title"]["romaji"] or media["title"]["english"] or titulo_busca
    relations = media.get("relations", {}).get("edges", [])

    # Filtra sequências, filmes ou spin-offs
    continuacoes = []
    for edge in relations:
        rel_type = edge.get("relationType")
        node = edge.get("node")
        if not node:
            continue

        if rel_type in ["SEQUEL", "ALTERNATIVE", "SIDE_STORY", "SPIN_OFF"]:
            continuacoes.append({
                "rel_type": rel_type,
                "node": node
            })

    linhas = [
        f"🎬 *Novas Temporadas & Sequências - {titulo_principal}*",
        f"━━━━━━━━━━━━━━━━━━━━━━"
    ]

    if not continuacoes:
        status_atual = media.get("status")
        if status_atual == "RELEASING":
            linhas.append(f"• A temporada atual de **{titulo_principal}** ainda está em exibição semanal.")
        else:
            linhas.append(f"• Até o momento, nenhuma nova temporada ou sequência oficial foi confirmada no AniList para **{titulo_principal}**.")
        return "\n".join(linhas)

    for item in continuacoes:
        node = item["node"]
        rel_tipo = {
            "SEQUEL": "➡️ Próxima Temporada / Sequência",
            "ALTERNATIVE": "🔄 Versão / Filme Alternativo",
            "SIDE_STORY": "📖 História Paralela / OVA",
            "SPIN_OFF": "⚡ Spin-Off"
        }.get(item["rel_type"], item["rel_type"])

        nome_rel = node["title"]["romaji"] or node["title"]["english"]
        formato = node.get("format", "TV")
        status_node = node.get("status", "Desconhecido")

        data_estreia = "Data a confirmar"
        sdate = node.get("startDate")
        if sdate and sdate.get("year"):
            y = sdate.get("year")
            m = f"/{sdate.get('month'):02d}" if sdate.get("month") else ""
            data_estreia = f"{y}{m}"
        elif node.get("season") and node.get("seasonYear"):
            data_estreia = f"{node.get('season')} {node.get('seasonYear')}"

        status_legivel = {
            "NOT_YET_RELEASED": "🟢 Confirmado / Em Produção (Aguardando estreia)",
            "RELEASING": "🔥 Lançando Atualmente (Em exibição)",
            "FINISHED": "✅ Já lançado"
        }.get(status_node, status_node)

        linhas.append(f"*{rel_tipo}:*")
        linhas.append(f"• **{nome_rel}** ({formato})")
        linhas.append(f"• Status: {status_legivel}")
        linhas.append(f"• Previsão de Estreia: **{data_estreia}**")

        nep = node.get("nextAiringEpisode")
        if nep:
            linhas.append(f"• Próximo Ep: Ep. {nep['episode']} em {_format_timestamp_br(nep['airingAt'])}")
        linhas.append("")

    return "\n".join(linhas).strip()


def explorar_temporada_animes(estacao: Optional[str] = None, ano: Optional[int] = None) -> str:
    """
    Explora os animes mais esperados e lançamentos de uma temporada específica (Inverno, Primavera, Verão, Outono).
    Se omitido, consulta a temporada atual ou próxima.

    Args:
        estacao (str, opcional): 'inverno'/'winter', 'primavera'/'spring', 'verao'/'summer', 'outono'/'fall'.
        ano (int, opcional): Ano de exibição (ex: 2026).
    """
    agora = datetime.now()
    ano_final = int(ano) if ano else agora.year

    # Mapeamento de estações
    estacao_norm = (estacao or "").strip().lower()
    if estacao_norm in ["inverno", "winter"]:
        season_gql = "WINTER"
        nome_pt = "Inverno"
    elif estacao_norm in ["primavera", "spring"]:
        season_gql = "SPRING"
        nome_pt = "Primavera"
    elif estacao_norm in ["verao", "verão", "summer"]:
        season_gql = "SUMMER"
        nome_pt = "Verão"
    elif estacao_norm in ["outono", "fall"]:
        season_gql = "FALL"
        nome_pt = "Outono"
    else:
        # Dedução pelo mês atual
        mes = agora.month
        if mes in [1, 2, 3]:
            season_gql = "WINTER"
            nome_pt = "Inverno"
        elif mes in [4, 5, 6]:
            season_gql = "SPRING"
            nome_pt = "Primavera"
        elif mes in [7, 8, 9]:
            season_gql = "SUMMER"
            nome_pt = "Verão"
        else:
            season_gql = "FALL"
            nome_pt = "Outono"

    graphql_query = """
    query ($season: MediaSeason, $seasonYear: Int) {
      Page (page: 1, perPage: 8) {
        media (season: $season, seasonYear: $seasonYear, type: ANIME, sort: [POPULARITY_DESC]) {
          id
          title {
            romaji
            english
          }
          format
          status
          genres
          episodes
          nextAiringEpisode {
            episode
            airingAt
          }
          startDate {
            year
            month
            day
          }
        }
      }
    }
    """

    data = _consultar_anilist_graphql(graphql_query, {"season": season_gql, "seasonYear": ano_final})
    media_list = data.get("Page", {}).get("media", []) if data else []

    if not media_list:
        return f"Não encontrei animes cadastrados para a temporada de {nome_pt} de {ano_final} no AniList."

    linhas = [
        f"🌸 *Destaques da Temporada de {nome_pt} {ano_final}*",
        f"━━━━━━━━━━━━━━━━━━━━━━"
    ]

    for idx, anime in enumerate(media_list, 1):
        nome = anime["title"]["romaji"] or anime["title"]["english"]
        generos = ", ".join(anime.get("genres", [])[:3])
        formato = anime.get("format", "TV")
        
        sdate = anime.get("startDate", {})
        data_str = "A confirmar"
        if sdate.get("day") and sdate.get("month"):
            data_str = f"{sdate['day']:02d}/{sdate['month']:02d}/{sdate.get('year', ano_final)}"
        elif sdate.get("month"):
            data_str = f"{sdate['month']:02d}/{sdate.get('year', ano_final)}"

        linhas.append(f"**{idx}. {nome}** ({formato})")
        if generos:
            linhas.append(f"  ↳ Gêneros: {generos}")
        linhas.append(f"  ↳ Estreia: {data_str}")

        nep = anime.get("nextAiringEpisode")
        if nep:
            linhas.append(f"  ↳ ⏰ Próximo: Ep. {nep['episode']} em {_format_timestamp_br(nep['airingAt'])}")
        linhas.append("")

    return "\n".join(linhas).strip()


def consultar_proximo_episodio(titulo: str) -> str:
    """
    Consulta quando sairá o próximo episódio de um anime em tempo real via AniList API.
    Informa número do episódio, dia da semana, horário no fuso de Brasília e contagem regressiva.

    Args:
        titulo (str): Nome do anime (ex: 'Solo Leveling', 'Jujutsu Kaisen', 'One Piece').
    """
    titulo_busca = titulo.strip()
    if not titulo_busca:
        return "Erro: Informe o nome do anime para consultar."

    # Verifica se o usuário tem esse anime na sua lista pessoal
    anime_salvo = None
    for item in _MEMORY_WATCHLIST.values():
        if titulo_busca.lower() in item.get("titulo_principal", "").lower() or titulo_busca.lower() in item.get("titulo_ingles", "").lower():
            anime_salvo = item
            break

    graphql_query = """
    query ($search: String) {
      Media (search: $search, type: ANIME) {
        id
        title {
          romaji
          english
        }
        status
        episodes
        nextAiringEpisode {
          airingAt
          timeUntilAiring
          episode
        }
        siteUrl
      }
    }
    """

    data = _consultar_anilist_graphql(graphql_query, {"search": titulo_busca})
    media = data.get("Media") if data else None

    if not media:
        if anime_salvo:
            pep = anime_salvo.get("proximo_episodio")
            if pep:
                return (
                    f"📺 *{anime_salvo['titulo_principal']}*\n"
                    f"• Próximo Episódio: **Episódio {pep['episodio']}**\n"
                    f"• Data de Lançamento: **{pep['data_formatada']}**\n"
                    f"• Seu progresso: Ep. {anime_salvo.get('ultimo_episodio_visto', 0)}\n"
                    f"• Transmissão: Crunchyroll"
                )
        return f"Não encontrei informações de lançamento para o anime '{titulo_busca}'. Verifique se o nome está correto."

    titulo_nome = media["title"]["romaji"] or media["title"]["english"] or titulo_busca
    nep = media.get("nextAiringEpisode")

    if nep:
        data_br = _format_timestamp_br(nep["airingAt"])
        tempo_str = _calcular_tempo_restante(nep["timeUntilAiring"])
        linhas = [
            f"🍿 *Lançamento de Episódio - {titulo_nome}*",
            "━━━━━━━━━━━━━━━━━━━━━━",
            f"• **Episódio:** {nep['episode']}",
            f"• **Data e Hora:** {data_br}",
            f"• **Contagem Regressiva:** {tempo_str}",
            f"• **Status:** Em exibição semanal (Simulcast)",
            f"• **Onde Assistir:** Crunchyroll / Plataformas parceiras"
        ]
        if anime_salvo:
            linhas.append(f"• **Seu Progresso Atual:** Parou no Ep. {anime_salvo.get('ultimo_episodio_visto', 0)}")
        return "\n".join(linhas)
    else:
        status_traduzido = {
            "FINISHED": "Temporada Concluída (todos os episódios já foram ao ar)",
            "NOT_YET_RELEASED": "Ainda não estreou (aguardando anúncio de data oficial de estreia)",
            "CANCELLED": "Cancelado"
        }.get(media.get("status"), media.get("status", "Sem episódios agendados"))

        total_ep = f" ({media.get('episodes')} episódios)" if media.get('episodes') else ""
        linhas = [
            f"ℹ️ *{titulo_nome}*{total_ep}",
            f"• Status Atual: **{status_traduzido}**",
            "No momento não há um próximo episódio agendado para exibição semanal."
        ]
        if anime_salvo:
            linhas.append(f"• Seu progresso registrado: Ep. {anime_salvo.get('ultimo_episodio_visto', 0)}/{media.get('episodes') or '?'}")
        return "\n".join(linhas)


def adicionar_anime_watchlist(
    titulo: str, 
    status: str = "assistindo", 
    ultimo_episodio_visto: int = 0
) -> str:
    """
    Busca um anime pelo título no AniList e salva na sua lista pessoal (Firestore).
    Armazena título oficial, total de episódios, status de transmissão e dados do próximo episódio.

    Args:
        titulo (str): Nome do anime (ex: 'Solo Leveling', 'Frieren', 'Demon Slayer').
        status (str): Status ('assistindo', 'planejo_assistir', 'concluido', 'pausado').
        ultimo_episodio_visto (int): Último episódio que você já assistiu.
    """
    titulo_busca = titulo.strip()
    if not titulo_busca:
        return "Erro: O nome do anime não pode ser vazio."

    graphql_query = """
    query ($search: String) {
      Media (search: $search, type: ANIME) {
        id
        title {
          romaji
          english
          native
        }
        format
        status
        episodes
        genres
        nextAiringEpisode {
          airingAt
          timeUntilAiring
          episode
        }
        siteUrl
      }
    }
    """

    data = _consultar_anilist_graphql(graphql_query, {"search": titulo_busca})
    media = data.get("Media") if data else None

    # Fallback caso API externa esteja instável
    if not media:
        doc_id = titulo_busca.lower().replace(" ", "_")
        anime_info = {
            "anilist_id": None,
            "titulo_principal": titulo_busca,
            "titulo_ingles": titulo_busca,
            "status_transmissao": "DESCONHECIDO",
            "total_episodios": None,
            "status_usuario": status.lower(),
            "ultimo_episodio_visto": int(ultimo_episodio_visto),
            "proximo_episodio": None,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    else:
        doc_id = str(media["id"])
        titulo_principal = media["title"]["romaji"] or media["title"]["english"] or titulo_busca
        titulo_ingles = media["title"]["english"] or titulo_principal
        
        proximo_ep = None
        if media.get("nextAiringEpisode"):
            nep = media["nextAiringEpisode"]
            proximo_ep = {
                "episodio": nep["episode"],
                "airing_at": nep["airingAt"],
                "data_formatada": _format_timestamp_br(nep["airingAt"]),
                "tempo_restante_segundos": nep["timeUntilAiring"]
            }

        anime_info = {
            "anilist_id": media["id"],
            "titulo_principal": titulo_principal,
            "titulo_ingles": titulo_ingles,
            "status_transmissao": media.get("status", "DESCONHECIDO"),
            "total_episodios": media.get("episodes"),
            "status_usuario": status.lower(),
            "ultimo_episodio_visto": int(ultimo_episodio_visto),
            "proximo_episodio": proximo_ep,
            "site_url": media.get("siteUrl"),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }

    # Salva em memória
    _MEMORY_WATCHLIST[doc_id] = anime_info

    # Salva no Firestore
    if firebase.db is not None:
        try:
            firebase.db.collection("anime_watchlist").document(doc_id).set(anime_info)
            logger.info(f"Anime '{anime_info['titulo_principal']}' salvo no Firestore.")
        except Exception as e:
            logger.error(f"Erro ao salvar anime no Firestore: {e}")

    # Sincronização remota direta na conta do AniList.co (se houver anilist_id e token)
    sincronizado_remoto = False
    if anime_info.get("anilist_id"):
        sincronizado_remoto = _salvar_entrada_anilist_remoto(
            media_id=anime_info["anilist_id"],
            status=status,
            progress=ultimo_episodio_visto
        )

    # Monta resposta amigável
    linhas = [
        f"🎌 *Anime Adicionado à sua Watchlist!*",
        f"• Título: **{anime_info['titulo_principal']}**"
    ]
    if anime_info.get("total_episodios"):
        linhas.append(f"• Total de Episódios: {anime_info['total_episodios']}")
    linhas.append(f"• Seu progresso: Parou no Ep. {ultimo_episodio_visto}")
    
    if sincronizado_remoto:
        linhas.append("• ☁️ *Sincronizado diretamente na sua conta do AniList.co!*")

    if anime_info.get("proximo_episodio"):
        pep = anime_info["proximo_episodio"]
        tempo_str = _calcular_tempo_restante(pep["tempo_restante_segundos"])
        linhas.append(f"⏰ *Próximo Lançamento:* Ep. {pep['episodio']} em **{pep['data_formatada']}** ({tempo_str})")
    elif anime_info.get("status_transmissao") == "FINISHED":
        linhas.append("✅ *Temporada Finalizada* (todos os episódios já foram lançados)")

    return "\n".join(linhas)


def listar_meus_animes(status: Optional[str] = None) -> str:
    """
    Lista os animes cadastrados na sua watchlist no banco de dados Firestore e sincronizados do AniList.
    Use esta ferramenta quando o usuário perguntar: 'o que eu estou vendo?', 'quais animes estou assistindo?',
    ou pedir para listar animes da watchlist.

    Args:
        status (str, opcional): Filtrar por status ('assistindo', 'planejo_assistir', 'concluido'). Default: None (ou 'assistindo' se for a intenção).
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()
    if user_id != "daniel":
        return f"ℹ️ {user_name}, você ainda não possui uma lista de animes nem uma conta AniList vinculada ao assistente."

    animes = list(_MEMORY_WATCHLIST.values())

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            db_animes = [d.to_dict() for d in docs]
            if db_animes:
                animes = db_animes
        except Exception as e:
            logger.error(f"Erro ao buscar animes no Firestore: {e}")

    if not animes:
        return "Sua lista de animes ainda está vazia. Diga: 'Sincronize meu perfil do AniList' ou 'Adicione Solo Leveling aos meus animes' para começar!"

    status_filtro = status.strip().lower() if status else None
    if status_filtro:
        animes = [a for a in animes if a.get("status_usuario", "").lower() == status_filtro]
        if not animes:
            return f"Você não possui animes com status '{status}' na sua lista."

    titulo_cabecalho = "📺 *Animes que Você Está Assistindo no Momento*" if status_filtro == "assistindo" else "📋 *Sua Lista de Animes (DAM & AniList)*"
    linhas = [
        titulo_cabecalho,
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]

    for a in animes:
        nome = a.get("titulo_principal", "Anime")
        visto = a.get("ultimo_episodio_visto", 0)
        total = a.get("total_episodios") or "?"
        status_u = a.get("status_usuario", "assistindo").capitalize()
        
        info_linha = f"• **{nome}** — Progresso: Ep. {visto}/{total}"
        if status_filtro != "assistindo":
            info_linha += f" ({status_u})"
        
        pep = a.get("proximo_episodio")
        if pep and isinstance(pep, dict):
            tempo_str = _calcular_tempo_restante(pep.get("tempo_restante_segundos", 0))
            info_linha += f"\n  ↳ ⏰ *Ep. {pep.get('episodio')}* em {pep.get('data_formatada', 'Breve')} ({tempo_str})"
        
        linhas.append(info_linha)

    return "\n".join(linhas)


def atualizar_progresso_anime(
    titulo: str, 
    episodio_visto: Optional[int] = None,
    incrementar: bool = False
) -> str:
    """
    Atualiza o último episódio que você assistiu de um determinado anime na sua lista e no AniList.co.
    Se episodio_visto não for informado ou se incrementar=True, avança 1 episódio (+1) a partir do último visto.

    Args:
        titulo (str): Nome do anime (ex: 'Mushoku Tensei', 'Solo Leveling', 'One Piece').
        episodio_visto (int, opcional): Número do episódio que você assistiu (ex: 11).
        incrementar (bool, opcional): Se True, avança 1 episódio em relação ao progresso atual.
    """
    titulo_busca = titulo.strip().lower()
    anime_encontrado_key = None
    anime_obj = None

    # Procura na memória
    for k, v in _MEMORY_WATCHLIST.items():
        if titulo_busca in v.get("titulo_principal", "").lower() or titulo_busca in v.get("titulo_ingles", "").lower():
            anime_encontrado_key = k
            anime_obj = v
            break

    # Procura no Firestore se não achou
    if not anime_obj and firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            for doc in docs:
                data = doc.to_dict()
                if titulo_busca in data.get("titulo_principal", "").lower() or titulo_busca in data.get("titulo_ingles", "").lower():
                    anime_encontrado_key = doc.id
                    anime_obj = data
                    break
        except Exception as e:
            logger.error(f"Erro ao buscar no Firestore: {e}")

    # Calcula o novo número de episódio
    if anime_obj:
        ultimo_atual = int(anime_obj.get("ultimo_episodio_visto", 0))
        if episodio_visto is None or incrementar:
            novo_ep = ultimo_atual + 1
        else:
            novo_ep = int(episodio_visto)
    else:
        novo_ep = int(episodio_visto) if episodio_visto is not None else 1
        return adicionar_anime_watchlist(titulo=titulo, status="assistindo", ultimo_episodio_visto=novo_ep)

    anime_obj["ultimo_episodio_visto"] = novo_ep
    anime_obj["status_usuario"] = "assistindo"
    anime_obj["updated_at"] = datetime.now(timezone.utc).isoformat()
    _MEMORY_WATCHLIST[anime_encontrado_key] = anime_obj

    if firebase.db is not None:
        try:
            firebase.db.collection("anime_watchlist").document(anime_encontrado_key).update({
                "ultimo_episodio_visto": novo_ep,
                "status_usuario": "assistindo",
                "updated_at": anime_obj["updated_at"]
            })
        except Exception as e:
            logger.error(f"Erro ao atualizar progresso no Firestore: {e}")

    # Sincronização remota no AniList.co
    sincronizado_remoto = False
    if anime_obj.get("anilist_id"):
        sincronizado_remoto = _salvar_entrada_anilist_remoto(
            media_id=anime_obj["anilist_id"],
            status="CURRENT",
            progress=novo_ep
        )

    remoto_str = " (sincronizado com seu perfil no AniList.co!)" if sincronizado_remoto else ""
    return f"✅ Progresso atualizado! Você agora está no **Episódio {novo_ep}** de **{anime_obj.get('titulo_principal')}**{remoto_str}."


def marcar_anime_concluido(titulo: str, nota: Optional[float] = None) -> str:
    """
    Marca um anime como concluído (COMPLETED) na sua lista pessoal e diretamente no seu perfil do AniList.co.
    Atualiza o número de episódios para o total da temporada e registra a nota que você deu (opcional).

    Args:
        titulo (str): Nome do anime (ex: 'Frieren', 'Chainsaw Man', 'Solo Leveling').
        nota (float, opcional): Nota pessoal de 0 a 10 dada ao anime.
    """
    titulo_busca = titulo.strip().lower()
    anime_encontrado_key = None
    anime_obj = None

    # Procura na memória
    for k, v in _MEMORY_WATCHLIST.items():
        if titulo_busca in v.get("titulo_principal", "").lower() or titulo_busca in v.get("titulo_ingles", "").lower():
            anime_encontrado_key = k
            anime_obj = v
            break

    # Procura no Firestore
    if not anime_obj and firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            for doc in docs:
                data = doc.to_dict()
                if titulo_busca in data.get("titulo_principal", "").lower() or titulo_busca in data.get("titulo_ingles", "").lower():
                    anime_encontrado_key = doc.id
                    anime_obj = data
                    break
        except Exception as e:
            logger.error(f"Erro ao buscar no Firestore: {e}")

    # Se não achou na lista local, busca no AniList
    if not anime_obj:
        graphql_query = """
        query ($search: String) {
          Media (search: $search, type: ANIME) {
            id
            title { romaji english }
            episodes
            siteUrl
          }
        }
        """
        data = _consultar_anilist_graphql(graphql_query, {"search": titulo_busca})
        media = data.get("Media") if data else None
        if not media:
            return f"Não encontrei o anime '{titulo}' para marcar como concluído."
        
        anime_encontrado_key = str(media["id"])
        anime_obj = {
            "anilist_id": media["id"],
            "titulo_principal": media["title"]["romaji"] or media["title"]["english"] or titulo,
            "titulo_ingles": media["title"]["english"] or titulo,
            "total_episodios": media.get("episodes"),
            "ultimo_episodio_visto": media.get("episodes") or 12,
            "status_usuario": "concluido"
        }

    total_eps = anime_obj.get("total_episodios") or anime_obj.get("ultimo_episodio_visto", 0)
    anime_obj["status_usuario"] = "concluido"
    if total_eps:
        anime_obj["ultimo_episodio_visto"] = int(total_eps)
    if nota is not None:
        anime_obj["nota_usuario"] = float(nota)
    anime_obj["updated_at"] = datetime.now(timezone.utc).isoformat()

    _MEMORY_WATCHLIST[anime_encontrado_key] = anime_obj

    if firebase.db is not None:
        try:
            update_data = {
                "status_usuario": "concluido",
                "ultimo_episodio_visto": anime_obj["ultimo_episodio_visto"],
                "updated_at": anime_obj["updated_at"]
            }
            if nota is not None:
                update_data["nota_usuario"] = float(nota)
            firebase.db.collection("anime_watchlist").document(anime_encontrado_key).set(anime_obj)
        except Exception as e:
            logger.error(f"Erro ao salvar conclusão no Firestore: {e}")

    # Sincronização remota no AniList.co
    sincronizado_remoto = False
    if anime_obj.get("anilist_id"):
        sincronizado_remoto = _salvar_entrada_anilist_remoto(
            media_id=anime_obj["anilist_id"],
            status="COMPLETED",
            progress=anime_obj["ultimo_episodio_visto"],
            score=nota
        )

    nome_final = anime_obj.get("titulo_principal", titulo)
    nota_str = f" | Sua Nota: ⭐ **{nota}/10**" if nota is not None else ""
    remoto_str = "\n☁️ *Status atualizado para COMPLETED na sua conta oficial do AniList.co!*" if sincronizado_remoto else ""

    return (
        f"🏆 *Parabéns! Anime Concluído!*\n"
        f"• Anime: **{nome_final}**\n"
        f"• Progresso Final: **{anime_obj['ultimo_episodio_visto']}/{total_eps or '?'} episódios**{nota_str}{remoto_str}"
    )


def grade_semanal_animes() -> str:
    """
    Monta a grade semanal de lançamentos de episódios dos animes que estão na sua lista.
    Organiza os animes por dia da semana (Segunda a Domingo) com o horário de lançamento no fuso de Brasília.
    """
    animes = list(_MEMORY_WATCHLIST.values())

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            db_animes = [d.to_dict() for d in docs]
            if db_animes:
                animes = db_animes
        except Exception as e:
            logger.error(f"Erro ao consultar Firestore: {e}")

    com_lancamento = [a for a in animes if a.get("proximo_episodio") and isinstance(a.get("proximo_episodio"), dict)]

    if not com_lancamento:
        return "Nenhum anime da sua lista possui episódios com data de lançamento agendada para os próximos dias."

    grade: Dict[str, List[str]] = {
        "Segunda-feira": [],
        "Terça-feira": [],
        "Quarta-feira": [],
        "Quinta-feira": [],
        "Sexta-feira": [],
        "Sábado": [],
        "Domingo": []
    }

    tz_br = timezone(timedelta(hours=-3))
    dias_nomes = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]

    for a in com_lancamento:
        pep = a["proximo_episodio"]
        airing_at = pep.get("airing_at")
        if airing_at:
            dt = datetime.fromtimestamp(airing_at, tz=timezone.utc).astimezone(tz_br)
            dia = dias_nomes[dt.weekday()]
            hora = dt.strftime("%H:%M")
            grade[dia].append(f"• **{a.get('titulo_principal')}** (Ep. {pep.get('episodio')}) às {hora}")

    linhas = [
        "📅 *Grade Semanal de Lançamentos dos Seus Animes*",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]

    tem_algum = False
    for dia, itens in grade.items():
        if itens:
            tem_algum = True
            linhas.append(f"\n🗓️ *{dia}*")
            linhas.extend(itens)

    if not tem_algum:
        return "Nenhum dos seus animes tem novos episódios programados para esta semana."

    return "\n".join(linhas)
