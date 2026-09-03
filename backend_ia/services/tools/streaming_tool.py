import logging
import os
import re
import json
import urllib.request
import urllib.parse
import unicodedata
from typing import Optional, Dict, Any, List
from config.settings import settings
from config import firebase

logger = logging.getLogger(__name__)

# Cache em memória para requisições frequentes
_STREAMING_CACHE: Dict[str, Dict[str, Any]] = {}

# Catálogo embutido inteligente de títulos populares no Brasil
CATALOGO_EMBUTIDO: Dict[str, Dict[str, Any]] = {
    "interestelar": {
        "titulo": "Interestelar (Interstellar)",
        "ano": 2014,
        "tipo": "Filme",
        "stream": ["Max", "Prime Video"],
        "rent": ["Apple TV+", "Google Play Filmes", "Prime Video"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "oppenheimer": {
        "titulo": "Oppenheimer",
        "ano": 2023,
        "tipo": "Filme",
        "stream": ["Telecine", "Globoplay", "Prime Video"],
        "rent": ["Apple TV+", "Google Play Filmes", "YouTube"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "barbie": {
        "titulo": "Barbie",
        "ano": 2023,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Prime Video", "Google Play Filmes"]
    },
    "duna": {
        "titulo": "Duna (Dune: Part One)",
        "ano": 2021,
        "tipo": "Filme",
        "stream": ["Max", "Prime Video"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "duna 2": {
        "titulo": "Duna: Parte 2 (Dune: Part Two)",
        "ano": 2024,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "vingadores ultimato": {
        "titulo": "Vingadores: Ultimato (Avengers: Endgame)",
        "ano": 2019,
        "tipo": "Filme",
        "stream": ["Disney+"],
        "rent": [],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "homem aranha sem volta para casa": {
        "titulo": "Homem-Aranha: Sem Volta Para Casa",
        "ano": 2021,
        "tipo": "Filme",
        "stream": ["Netflix", "Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "the batman": {
        "titulo": "The Batman",
        "ano": 2022,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "batman": {
        "titulo": "Batman (1989)",
        "ano": 1989,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "o poderoso chefao": {
        "titulo": "O Poderoso Chefão (The Godfather)",
        "ano": 1972,
        "tipo": "Filme",
        "stream": ["Paramount+", "Netflix"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "matrix": {
        "titulo": "Matrix (The Matrix)",
        "ano": 1999,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "top gun maverick": {
        "titulo": "Top Gun: Maverick",
        "ano": 2022,
        "tipo": "Filme",
        "stream": ["Paramount+", "Netflix"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "avatar o caminho da agua": {
        "titulo": "Avatar: O Caminho da Água",
        "ano": 2022,
        "tipo": "Filme",
        "stream": ["Disney+"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "tropa de elite": {
        "titulo": "Tropa de Elite",
        "ano": 2007,
        "tipo": "Filme",
        "stream": ["Globoplay", "Netflix"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "cidade de deus": {
        "titulo": "Cidade de Deus",
        "ano": 2002,
        "tipo": "Filme",
        "stream": ["Max", "Globoplay", "Netflix"],
        "rent": ["Apple TV+"],
        "buy": ["Apple TV+"]
    },
    "o auto da compadecida": {
        "titulo": "O Auto da Compadecida",
        "ano": 2000,
        "tipo": "Filme",
        "stream": ["Globoplay"],
        "rent": [],
        "buy": []
    },
    "shrek": {
        "titulo": "Shrek",
        "ano": 2001,
        "tipo": "Filme",
        "stream": ["Netflix", "Prime Video", "Max"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "harry potter": {
        "titulo": "Harry Potter e a Pedra Filosofal",
        "ano": 2001,
        "tipo": "Filme",
        "stream": ["Max"],
        "rent": ["Apple TV+", "Prime Video", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "senhor dos aneis": {
        "titulo": "O Senhor dos Anéis: A Sociedade do Anel",
        "ano": 2001,
        "tipo": "Filme",
        "stream": ["Max", "Prime Video"],
        "rent": ["Apple TV+", "Google Play Filmes"],
        "buy": ["Apple TV+", "Google Play Filmes"]
    },
    "breaking bad": {
        "titulo": "Breaking Bad",
        "ano": 2008,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": ["Apple TV+"]
    },
    "stranger things": {
        "titulo": "Stranger Things",
        "ano": 2016,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "the last of us": {
        "titulo": "The Last of Us",
        "ano": 2023,
        "tipo": "Série",
        "stream": ["Max"],
        "rent": [],
        "buy": []
    },
    "game of thrones": {
        "titulo": "Game of Thrones",
        "ano": 2011,
        "tipo": "Série",
        "stream": ["Max"],
        "rent": [],
        "buy": ["Apple TV+"]
    },
    "a casa do dragao": {
        "titulo": "A Casa do Dragão (House of the Dragon)",
        "ano": 2022,
        "tipo": "Série",
        "stream": ["Max"],
        "rent": [],
        "buy": []
    },
    "the boys": {
        "titulo": "The Boys",
        "ano": 2019,
        "tipo": "Série",
        "stream": ["Prime Video"],
        "rent": [],
        "buy": []
    },
    "o urso": {
        "titulo": "O Urso (The Bear)",
        "ano": 2022,
        "tipo": "Série",
        "stream": ["Disney+"],
        "rent": [],
        "buy": []
    },
    "the bear": {
        "titulo": "The Bear (O Urso)",
        "ano": 2022,
        "tipo": "Série",
        "stream": ["Disney+"],
        "rent": [],
        "buy": []
    },
    "succession": {
        "titulo": "Succession",
        "ano": 2018,
        "tipo": "Série",
        "stream": ["Max"],
        "rent": [],
        "buy": []
    },
    "round 6": {
        "titulo": "Round 6 (Squid Game)",
        "ano": 2021,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "squid game": {
        "titulo": "Squid Game (Round 6)",
        "ano": 2021,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "peaky blinders": {
        "titulo": "Peaky Blinders",
        "ano": 2013,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "ted lasso": {
        "titulo": "Ted Lasso",
        "ano": 2020,
        "tipo": "Série",
        "stream": ["Apple TV+"],
        "rent": [],
        "buy": []
    },
    "ruptura": {
        "titulo": "Ruptura (Severance)",
        "ano": 2022,
        "tipo": "Série",
        "stream": ["Apple TV+"],
        "rent": [],
        "buy": []
    },
    "severance": {
        "titulo": "Severance (Ruptura)",
        "ano": 2022,
        "tipo": "Série",
        "stream": ["Apple TV+"],
        "rent": [],
        "buy": []
    },
    "fallout": {
        "titulo": "Fallout",
        "ano": 2024,
        "tipo": "Série",
        "stream": ["Prime Video"],
        "rent": [],
        "buy": []
    },
    "yellowstone": {
        "titulo": "Yellowstone",
        "ano": 2018,
        "tipo": "Série",
        "stream": ["Paramount+", "Netflix"],
        "rent": [],
        "buy": []
    },
    "arcane": {
        "titulo": "Arcane: League of Legends",
        "ano": 2021,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "the office": {
        "titulo": "The Office (US)",
        "ano": 2005,
        "tipo": "Série",
        "stream": ["Netflix", "Prime Video", "Max"],
        "rent": [],
        "buy": []
    },
    "friends": {
        "titulo": "Friends",
        "ano": 1994,
        "tipo": "Série",
        "stream": ["Max"],
        "rent": [],
        "buy": []
    },
    "better call saul": {
        "titulo": "Better Call Saul",
        "ano": 2015,
        "tipo": "Série",
        "stream": ["Netflix"],
        "rent": [],
        "buy": []
    },
    "the mandalorian": {
        "titulo": "The Mandalorian",
        "ano": 2019,
        "tipo": "Série",
        "stream": ["Disney+"],
        "rent": [],
        "buy": []
    },
    "loki": {
        "titulo": "Loki",
        "ano": 2021,
        "tipo": "Série",
        "stream": ["Disney+"],
        "rent": [],
        "buy": []
    },
    "os outros": {
        "titulo": "Os Outros",
        "ano": 2023,
        "tipo": "Série",
        "stream": ["Globoplay"],
        "rent": [],
        "buy": []
    },
    "sob pressao": {
        "titulo": "Sob Pressão",
        "ano": 2017,
        "tipo": "Série",
        "stream": ["Globoplay"],
        "rent": [],
        "buy": []
    }
}

def _normalizar(texto: str) -> str:
    """Remove acentuação, pontuação e espaços extras para busca inteligente."""
    if not texto:
        return ""
    sem_acentos = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('utf-8')
    limpo = re.sub(r'[^a-z0-9 ]', ' ', sem_acentos.lower())
    return re.sub(r'\s+', ' ', limpo).strip()

def _filtra_por_tipo(tipo_item: str, tipo_desejado: str) -> bool:
    """Verifica se o tipo do item corresponde ao filtro desejado (filme, serie, todos)."""
    tipo_d = _normalizar(tipo_desejado)
    if not tipo_d or tipo_d in ["todos", "tudo", "qualquer"]:
        return True
    tipo_i = _normalizar(tipo_item)
    if "filme" in tipo_d and "filme" in tipo_i:
        return True
    if "seri" in tipo_d and "seri" in tipo_i:
        return True
    return False

def _buscar_catalogo_embutido(titulo_norm: str, tipo_midia: str = "todos") -> Optional[Dict[str, Any]]:
    """Busca aproximada ou exata no catálogo embutido de títulos populares."""
    # 1. Match exato na chave
    if titulo_norm in CATALOGO_EMBUTIDO:
        entry = CATALOGO_EMBUTIDO[titulo_norm]
        if _filtra_por_tipo(entry.get("tipo", ""), tipo_midia):
            return entry

    # 2. Match parcial
    for chave, item in CATALOGO_EMBUTIDO.items():
        if not _filtra_por_tipo(item.get("tipo", ""), tipo_midia):
            continue
        if chave in titulo_norm or titulo_norm in chave:
            return item

    # 3. Match de palavras-chave individuais (>= 4 caracteres)
    palavras = [p for p in titulo_norm.split() if len(p) >= 4]
    for p in palavras:
        for chave, item in CATALOGO_EMBUTIDO.items():
            if not _filtra_por_tipo(item.get("tipo", ""), tipo_midia):
                continue
            if p in chave.split():
                return item

    return None

def _buscar_tmdb(titulo: str, tipo_midia: str, api_key: str) -> Optional[Dict[str, Any]]:
    """Consulta a API do The Movie Database (TMDB) para obter provedores de streaming no Brasil."""
    try:
        endpoint = "multi"
        if "filme" in tipo_midia.lower():
            endpoint = "movie"
        elif "seri" in tipo_midia.lower():
            endpoint = "tv"

        query_encoded = urllib.parse.quote(titulo)
        url_search = f"https://api.themoviedb.org/3/search/{endpoint}?api_key={api_key}&query={query_encoded}&language=pt-BR&page=1"
        
        req = urllib.request.Request(url_search, headers={"User-Agent": "DAMBot/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])

        if not results:
            return None

        primeiro = results[0]
        media_type = primeiro.get("media_type", "movie" if endpoint == "movie" else "tv")
        if media_type not in ["movie", "tv"]:
            media_type = "movie"

        tmdb_id = primeiro.get("id")
        nome_oficial = primeiro.get("title") or primeiro.get("name") or titulo
        data_lancamento = primeiro.get("release_date") or primeiro.get("first_air_date") or ""
        ano = int(data_lancamento.split("-")[0]) if data_lancamento and data_lancamento[:4].isdigit() else None

        url_providers = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/watch/providers?api_key={api_key}"
        req_p = urllib.request.Request(url_providers, headers={"User-Agent": "DAMBot/1.0"})
        with urllib.request.urlopen(req_p, timeout=5) as resp_p:
            data_p = json.loads(resp_p.read().decode("utf-8"))
            providers_br = data_p.get("results", {}).get("BR", {})

        def _normalizar_provedor(p_name: str) -> str:
            if not p_name:
                return ""
            p_lower = p_name.strip().lower()
            if p_lower in ["disney plus", "disney+"]:
                return "Disney+"
            if p_lower in ["amazon prime video", "prime video"]:
                return "Prime Video"
            if p_lower in ["hbo max", "max"]:
                return "Max"
            return p_name

        stream_list = [_normalizar_provedor(p.get("provider_name")) for p in providers_br.get("flatrate", []) if p.get("provider_name")]
        rent_list = [_normalizar_provedor(p.get("provider_name")) for p in providers_br.get("rent", []) if p.get("provider_name")]
        buy_list = [_normalizar_provedor(p.get("provider_name")) for p in providers_br.get("buy", []) if p.get("provider_name")]

        return {
            "titulo": nome_oficial,
            "ano": ano,
            "tipo": "Série" if media_type == "tv" else "Filme",
            "stream": stream_list,
            "rent": rent_list,
            "buy": buy_list,
            "origem": "TMDB"
        }
    except Exception as e:
        logger.warning(f"Falha ao consultar TMDB para '{titulo}': {e}")
        return None

def _obter_cache_firestore(cache_key: str) -> Optional[Dict[str, Any]]:
    """Recupera resultado em cache do Firestore se disponível."""
    if firebase.db is None:
        return None
    try:
        doc = firebase.db.collection("streaming_cache").document(cache_key).get()
        if doc.exists:
            return doc.to_dict()
    except Exception as e:
        logger.warning(f"Erro ao ler cache do Firestore: {e}")
    return None

def _salvar_cache_firestore(cache_key: str, data: Dict[str, Any]):
    """Armazena resultado no Firestore se disponível."""
    if firebase.db is None:
        return
    try:
        firebase.db.collection("streaming_cache").document(cache_key).set(data)
    except Exception as e:
        logger.warning(f"Erro ao gravar cache no Firestore: {e}")

def _formatar_resposta(dados: Dict[str, Any]) -> str:
    """Formata os dados encontrados em mensagem elegante para o WhatsApp."""
    titulo = dados.get("titulo", "Título")
    ano = f" ({dados['ano']})" if dados.get("ano") else ""
    tipo = dados.get("tipo", "Mídia")

    linhas = [
        f"🎬 *Onde Assistir: {titulo}*{ano} • _{tipo}_",
        ""
    ]

    tem_algum = False

    if dados.get("stream"):
        tem_algum = True
        linhas.append("📺 *Assinatura (Streaming incluso):*")
        for plat in dados["stream"]:
            linhas.append(f"  • {plat}")
        linhas.append("")

    if dados.get("rent"):
        tem_algum = True
        linhas.append("💳 *Aluguel Digital:*")
        for plat in dados["rent"]:
            linhas.append(f"  • {plat}")
        linhas.append("")

    if dados.get("buy"):
        tem_algum = True
        linhas.append("🛍️ *Compra Digital:*")
        for plat in dados["buy"]:
            linhas.append(f"  • {plat}")
        linhas.append("")

    if not tem_algum:
        linhas.append("ℹ️ _Atualmente não há plataformas de streaming confirmadas com este título no catálogo brasileiro._")
        linhas.append("Ele pode estar disponível em mídia física, em exibição nos cinemas ou aguardando renovação de direitos.")
    else:
        linhas.append("💡 _Os catálogos dos serviços de streaming no Brasil podem sofrer alterações sem aviso prévio._")

    return "\n".join(linhas).strip()

def onde_assistir(titulo: str, tipo_midia: str = "todos") -> str:
    """
    Identifica em quais plataformas de streaming no Brasil o filme ou série está disponível.
    Distingue entre Assinatura (Stream plano), Aluguel (Rent) e Compra (Buy).
    
    Args:
        titulo: Nome do filme ou série a consultar.
        tipo_midia: 'filme', 'serie' ou 'todos'. Padrão é 'todos'.
    """
    if not titulo or not titulo.strip():
        return "Por favor, informe o nome de um filme ou série para saber onde assistir."

    titulo_limpo = titulo.strip()
    norm = _normalizar(titulo_limpo)
    cache_key = f"{norm}_{_normalizar(tipo_midia)}"

    # 1. Verifica cache em memória
    if cache_key in _STREAMING_CACHE:
        return _formatar_resposta(_STREAMING_CACHE[cache_key])

    # 2. Verifica cache no Firestore
    dados_firestore = _obter_cache_firestore(cache_key)
    if dados_firestore:
        _STREAMING_CACHE[cache_key] = dados_firestore
        return _formatar_resposta(dados_firestore)

    # 3. Consulta API do TMDB se houver chave configurada
    api_key = getattr(settings, "TMDB_API_KEY", "") or os.getenv("TMDB_API_KEY", "")
    dados = None
    if api_key:
        dados = _buscar_tmdb(titulo_limpo, tipo_midia, api_key)

    # 4. Fallback no Catálogo Embutido
    if not dados:
        dados = _buscar_catalogo_embutido(norm, tipo_midia)

    # 5. Salva em Cache e retorna
    if dados:
        _STREAMING_CACHE[cache_key] = dados
        _salvar_cache_firestore(cache_key, dados)
        return _formatar_resposta(dados)

    return (
        f"🔍 Não localizamos plataformas de streaming confirmadas para *'{titulo_limpo}'* no Brasil no momento.\n"
        f"Verifique se o nome está correto ou tente buscar pelo título original em inglês."
    )
