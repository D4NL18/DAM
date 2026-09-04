import hashlib
import logging
import re
import threading
import unicodedata
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, Optional

from config import firebase

logger = logging.getLogger(__name__)


class QueryVolatility(str, Enum):
    """Categorias semânticas de volatilidade das consultas (RN-CACHE-001)."""
    REALTIME_VOLATILE = "REALTIME_VOLATILE"          # Trânsito, rotas, travas (Bypass compulsório)
    STATE_CHANGING_ACTION = "STATE_CHANGING_ACTION"  # Ações de escrita/mutações (Bypass compulsório)
    CLASH_OF_CLANS = "CLASH_OF_CLANS"                # Reuso de resposta de guerra/raid
    CS2_ESPORTS = "CS2_ESPORTS"                      # Expiração dinâmica até 2h antes da partida
    STATIC_INFORMATIONAL = "STATIC_INFORMATIONAL"    # Nutrição, streaming, conversões, cardápios
    UNKNOWN = "UNKNOWN"                              # Não classificado (não cacheável por segurança)


class CacheEntry:
    """Representa um registro individual de cache de conversação."""
    def __init__(
        self,
        remote_jid: str,
        query_normalized: str,
        response_text: str,
        domain: QueryVolatility,
        created_at: datetime,
        expires_at: datetime,
        ttl_seconds: int
    ):
        self.remote_jid = remote_jid
        self.query_normalized = query_normalized
        self.response_text = response_text
        self.domain = domain
        self.created_at = created_at
        self.expires_at = expires_at
        self.ttl_seconds = ttl_seconds

    def is_expired(self, current_time: Optional[datetime] = None) -> bool:
        now = current_time or datetime.now()
        return now >= self.expires_at


class ConversationCacheService:
    """
    Serviço centralizado de Cache Semântico de Prompts e Conversas (PC-08).
    Garante drástica redução de tokens consumidos pelo Gemini respeitando
    a volatilidade e o isolamento estrito por usuário.
    """
    _l1_cache: Dict[str, CacheEntry] = {}
    _lock = threading.RLock()

    # Métricas acumuladas (RN-CACHE-006)
    _metrics = {
        "hits": 0,
        "misses": 0,
        "tokens_saved_estimated": 0
    }

    # Palavras-chave para forçar atualização em tempo real (RN-CACHE-004)
    FORCE_REFRESH_KEYWORDS = [
        "atualizar", "atualiza", "atualize", "forcar", "forçar",
        "tempo real", "ao vivo", "novamente", "de novo", "checar novamente"
    ]

    # Expressões regulares para roteamento semântico
    REGEX_REALTIME = re.compile(
        r"\b(transito|trânsito|rota|rotas|tempo de percurso|tempo de rota|tempo de viagem|"
        r"tempo ate|tempo até|horario de saida|horário de saída|horario para sair|horário para sair|"
        r"sair agora|trafego|tráfego|waze|maps|engarrafamento|transito agora|trânsito agora|"
        r"status do veiculo|status do veículo|nivel de combustivel|nível de combustível)\b",
        re.IGNORECASE
    )

    REGEX_ACTIONS = re.compile(
        r"\b(gastei|comprei|paguei|compra de|debito|débito|credito|crédito|pix de|enviar pix|"
        r"cria um lembrete|criar lembrete|crie um lembrete|cria uma nota|criar nota|crie uma nota|"
        r"anota ai|anota aí|anotar|lembrete para|agendar|agenda uma|agende uma|salvar senha|salve a senha|"
        r"tranca o carro|trancar o carro|destrancar o carro|fala na alexa|falar na alexa|"
        r"adicionar despesa|adiciona despesa|bater ponto|registrar ponto|ponto de entrada|ponto de saida|"
        r"dividir a conta|adicionar anime|adiciona anime|concluir anime|marcar como concluido)\b",
        re.IGNORECASE
    )

    REGEX_CLASH = re.compile(
        r"\b(clash|clash of clans|guerra de cla|guerra de clã|guerra de clas|guerra de clãs|"
        r"guerra no clash|guerra do clash|tenho guerra|estamos em guerra|ataque na guerra|"
        r"ataques na guerra|capital do cla|capital do clã|raid da capital|raid weekend|cwl|liga de guerra)\b",
        re.IGNORECASE
    )

    REGEX_CS2 = re.compile(
        r"\b(furia|cs2|counter-strike|counter strike|cs:go|jogo de cs|jogos de cs|partida de cs|"
        r"partidas de cs|proximo jogo da furia|próximo jogo da furia|quando a furia joga|"
        r"tem jogo de cs|jogos da furia|jogos do cs|faze|mibr|pain|imperial|vitality|navi|liquid|spirit)\b",
        re.IGNORECASE
    )

    REGEX_STATIC = re.compile(
        r"\b(onde assistir|onde posso assistir|tem na netflix|tem no prime|tem na max|"
        r"posso trocar|substituir|substituição|dietbox|lista de substituicao|lista de substituição|"
        r"calorias|quantos gramas|quantas gramas|converter|conversor|como fazer|ingredientes de|"
        r"cardapio|cardápio|ideia de presente|ideias de presente|presente para)\b",
        re.IGNORECASE
    )

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normaliza o texto da query (minúsculas, sem acentos, sem pontuações).
        """
        if not text:
            return ""
        # Remove acentos
        nfkd = unicodedata.normalize("NFKD", text)
        sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
        # Minúsculas e substituição de caracteres não-alfanuméricos por espaço
        limpo = re.sub(r"[^\w\s]", " ", sem_acento.lower())
        # Colapso de múltiplos espaços
        return " ".join(limpo.split()).strip()

    @classmethod
    def generate_cache_key(cls, remote_jid: str, query: str) -> str:
        """
        RN-CACHE-002 e RN-CACHE-003: Gera uma chave hash SHA-256 única
        garantindo isolamento por usuário (remote_jid) e normalização semântica.
        """
        norm_query = cls.normalize_text(query)
        raw_key = f"{remote_jid.strip().lower()}:{norm_query}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @classmethod
    def classify_query_volatility(cls, text: str) -> QueryVolatility:
        """
        RN-CACHE-001: Roteador de volatilidade semântica da consulta.
        """
        norm = cls.normalize_text(text)

        # 1. Trânsito / Mobilidade em tempo real (Prioridade Máxima: NUNCA CACHEAR)
        if cls.REGEX_REALTIME.search(norm):
            return QueryVolatility.REALTIME_VOLATILE

        # 2. Ações de escrita e mutação de estado (NUNCA CACHEAR)
        if cls.REGEX_ACTIONS.search(norm):
            return QueryVolatility.STATE_CHANGING_ACTION

        # 3. Clash of Clans (Guerra / Raids)
        if cls.REGEX_CLASH.search(norm):
            return QueryVolatility.CLASH_OF_CLANS

        # 4. Counter-Strike 2 / FURIA
        if cls.REGEX_CS2.search(norm):
            return QueryVolatility.CS2_ESPORTS

        # 5. Informativos Estáticos (Dietbox, Streaming, Conversões)
        if cls.REGEX_STATIC.search(norm):
            return QueryVolatility.STATIC_INFORMATIONAL

        return QueryVolatility.UNKNOWN

    @classmethod
    def calculate_cs2_ttl(
        cls,
        game_time: Optional[datetime],
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Demanda do Usuário: "No caso de jogo de cs, o cache pode ser até 2h antes do jogo
        pq dps pode mudar o horário".
        
        Regra:
        - Se game_time for None: retorna 7200s (2 horas padrão).
        - Se o jogo for em mais de 2 horas (diff > 7200s):
          O cache expira exatamente 2 horas antes do início da partida (diff - 7200s).
        - Se o jogo for em 2 horas ou menos (ou ao vivo):
          TTL = 0 (não cachear / bypass), permitindo capturar mudanças de horário e placar.
        """
        if not game_time:
            return 7200

        now = current_time or datetime.now()
        diff_seconds = (game_time - now).total_seconds()

        # Faltam 2 horas ou menos (ou jogo já começou)
        if diff_seconds <= 7200:
            return 0

        # O cache expira 2 horas antes do jogo
        ttl = int(diff_seconds - 7200)
        return max(0, ttl)

    @classmethod
    def extract_game_time_from_text(cls, text: str) -> Optional[datetime]:
        """
        Tenta extrair o datetime da próxima partida a partir da resposta de texto.
        Suporta formatos como:
        - "04/09/2026 às 14:30"
        - "Hoje às 18:00"
        - "Amanhã às 11:00"
        """
        now = datetime.now()
        
        # Formato explícito: DD/MM/YYYY às HH:MM
        match_full = re.search(r"(\d{2})/(\d{2})/(\d{4})\s+(?:às|as)\s+(\d{2}):(\d{2})", text, re.IGNORECASE)
        if match_full:
            d, m, y, h, mi = match_full.groups()
            try:
                return datetime(int(y), int(m), int(d), int(h), int(mi))
            except Exception:
                pass

        # Formato relativo: Hoje às HH:MM
        match_hoje = re.search(r"\bhoje\s+(?:às|as)\s+(\d{2}):(\d{2})", text, re.IGNORECASE)
        if match_hoje:
            h, mi = match_hoje.groups()
            try:
                return datetime(now.year, now.month, now.day, int(h), int(mi))
            except Exception:
                pass

        # Formato relativo: Amanhã às HH:MM
        match_amanha = re.search(r"\bamanh[aã]\s+(?:às|as)\s+(\d{2}):(\d{2})", text, re.IGNORECASE)
        if match_amanha:
            h, mi = match_amanha.groups()
            try:
                amanha = now + timedelta(days=1)
                return datetime(amanha.year, amanha.month, amanha.day, int(h), int(mi))
            except Exception:
                pass

        return None

    @classmethod
    def get_cached_response(cls, remote_jid: str, query: str) -> Optional[str]:
        """
        Recupera resposta em cache para a mensagem caso elegível e não expirada.
        """
        # Verifica se o usuário pediu forçamento de atualização
        norm_query = cls.normalize_text(query)
        for kw in cls.FORCE_REFRESH_KEYWORDS:
            if re.search(rf"\b{kw}\b", norm_query):
                logger.info(f"[CACHE] Forçamento de refresh detectado ('{kw}'). Ignorando cache.")
                return None

        # Roteamento de volatilidade
        volatility = cls.classify_query_volatility(query)
        if volatility in (QueryVolatility.REALTIME_VOLATILE, QueryVolatility.STATE_CHANGING_ACTION):
            return None

        cache_key = cls.generate_cache_key(remote_jid, query)
        now = datetime.now()

        # 1. Consulta L1 (Memória)
        with cls._lock:
            entry = cls._l1_cache.get(cache_key)
            if entry:
                if not entry.is_expired(now):
                    cls._record_hit(query, entry.response_text)
                    logger.info(f"[CACHE HIT L1] Reusando resposta para {remote_jid[:8]}... [{entry.domain}]")
                    return entry.response_text
                else:
                    # Expirado: remove de L1
                    del cls._l1_cache[cache_key]

        # 2. Consulta L2 (Firestore) se disponível
        try:
            if firebase.db is not None:
                doc = firebase.db.collection("conversation_cache").document(cache_key).get()
                if doc.exists:
                    data = doc.to_dict() or {}
                    expires_at_iso = data.get("expires_at")
                    if expires_at_iso:
                        expires_at = datetime.fromisoformat(expires_at_iso)
                        if now < expires_at:
                            resp = data.get("response_text", "")
                            cls._record_hit(query, resp)
                            # Repopula L1
                            entry = CacheEntry(
                                remote_jid=remote_jid,
                                query_normalized=norm_query,
                                response_text=resp,
                                domain=volatility,
                                created_at=datetime.fromisoformat(data.get("created_at", now.isoformat())),
                                expires_at=expires_at,
                                ttl_seconds=data.get("ttl_seconds", 3600)
                            )
                            with cls._lock:
                                cls._l1_cache[cache_key] = entry
                            logger.info(f"[CACHE HIT L2] Reusando resposta Firestore para {remote_jid[:8]}...")
                            return resp
        except Exception as e:
            logger.warning(f"[CACHE] Falha ao consultar L2 Firestore: {e}")

        # Cache Miss
        cls._record_miss()
        return None

    @classmethod
    def save_response(
        cls,
        remote_jid: str,
        query: str,
        response_text: str,
        custom_ttl: Optional[int] = None
    ) -> bool:
        """
        Salva uma resposta elegível no cache L1 e L2 com TTL apropriado.
        Retorna True se foi salva, ou False se não elegível.
        """
        if not response_text:
            return False

        volatility = cls.classify_query_volatility(query)

        # Regra inviolável: Trânsito e Ações nunca são salvas
        if volatility in (QueryVolatility.REALTIME_VOLATILE, QueryVolatility.STATE_CHANGING_ACTION):
            return False

        # Determinação do TTL em segundos
        now = datetime.now()

        if custom_ttl is not None:
            if custom_ttl <= 0:
                return False
            ttl_seconds = custom_ttl
        else:
            if volatility == QueryVolatility.CLASH_OF_CLANS:
                ttl_seconds = 3600  # 1 hora (mesmo dia / mesma fase de guerra)
            elif volatility == QueryVolatility.CS2_ESPORTS:
                # Extrai horário do jogo e calcula TTL dinâmico
                game_time = cls.extract_game_time_from_text(response_text)
                ttl_seconds = cls.calculate_cs2_ttl(game_time=game_time, current_time=now)
                if ttl_seconds <= 0:
                    logger.info("[CACHE] Jogo de CS2 a menos de 2h ou ao vivo. Cache desativado.")
                    return False
            elif volatility == QueryVolatility.STATIC_INFORMATIONAL:
                ttl_seconds = 43200  # 12 horas
            else:
                return False

        expires_at = now + timedelta(seconds=ttl_seconds)
        norm_query = cls.normalize_text(query)
        cache_key = cls.generate_cache_key(remote_jid, query)

        entry = CacheEntry(
            remote_jid=remote_jid,
            query_normalized=norm_query,
            response_text=response_text,
            domain=volatility,
            created_at=now,
            expires_at=expires_at,
            ttl_seconds=ttl_seconds
        )

        # 1. Grava em L1 (Memória)
        with cls._lock:
            cls._l1_cache[cache_key] = entry

        # 2. Grava em L2 (Firestore) de forma não-bloqueante/fail-safe
        try:
            if firebase.db is not None:
                firebase.db.collection("conversation_cache").document(cache_key).set({
                    "remote_jid": remote_jid,
                    "query_normalized": norm_query,
                    "response_text": response_text,
                    "domain": volatility.value,
                    "created_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "ttl_seconds": ttl_seconds
                }, merge=True)
        except Exception as e:
            logger.warning(f"[CACHE] Falha ao persistir no Firestore: {e}")

        logger.info(f"[CACHE STORED] Chave {cache_key[:8]} armazenada com TTL de {ttl_seconds}s [{volatility}]")
        return True

    @classmethod
    def _record_hit(cls, query: str, response: str):
        with cls._lock:
            cls._metrics["hits"] += 1
            # Estimativa de tokens economizados: ~4 caracteres por token no prompt + resposta + system instruction (~1000 tokens)
            tokens_saved = 1000 + (len(query) + len(response)) // 4
            cls._metrics["tokens_saved_estimated"] += tokens_saved

    @classmethod
    def _record_miss(cls):
        with cls._lock:
            cls._metrics["misses"] += 1

    @classmethod
    def get_metrics(cls) -> Dict[str, Any]:
        with cls._lock:
            return dict(cls._metrics)

    @classmethod
    def reset_metrics(cls):
        with cls._lock:
            cls._metrics = {
                "hits": 0,
                "misses": 0,
                "tokens_saved_estimated": 0
            }

    @classmethod
    def clear_cache(cls):
        """Limpa o cache em memória (usado principalmente em testes)."""
        with cls._lock:
            cls._l1_cache.clear()
