import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.api_core.exceptions import ResourceExhausted
import os
import time
import logging
from .settings import settings

logger = logging.getLogger(__name__)

db = None

DEFAULT_FIRESTORE_TIMEOUT = 4.0
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 300.0
_quota_cooldown_until: float = 0.0


def is_circuit_breaker_open() -> bool:
    """Indica se o circuit breaker do Firestore está aberto por cota 429 recente."""
    return time.monotonic() < _quota_cooldown_until


def trip_circuit_breaker(cooldown_seconds: float = CIRCUIT_BREAKER_COOLDOWN_SECONDS) -> None:
    """Abre o circuit breaker em memória por cooldown_seconds ao detectar erro 429."""
    global _quota_cooldown_until
    already_open = is_circuit_breaker_open()
    _quota_cooldown_until = time.monotonic() + max(0.0, cooldown_seconds)
    if not already_open:
        logger.warning(
            "Firestore 429 Quota exceeded detectado. Circuit breaker aberto por %.0fs (fail-fast em 0ms).",
            cooldown_seconds,
        )


def reset_circuit_breaker() -> None:
    """Reseta o circuit breaker em memória (útil para testes unitários)."""
    global _quota_cooldown_until
    _quota_cooldown_until = 0.0


def _is_quota_error(exc: Exception) -> bool:
    """Detecta se a exceção representa esgotamento de cota (HTTP 429 / RESOURCE_EXHAUSTED)."""
    if isinstance(exc, ResourceExhausted):
        return True
    if getattr(exc, "code", None) == 429:
        return True
    msg = str(exc).lower()
    return "quota exceeded" in msg or "resource_exhausted" in msg or "429" in msg


def _ensure_circuit_closed() -> None:
    if is_circuit_breaker_open():
        raise ResourceExhausted("Firestore circuit breaker active (429 quota cooldown)")


def _execute_resilient(func, *args, **kwargs):
    """Executa operação no Firestore com timeout curto, sem retry gRPC de 60s e circuit breaker."""
    _ensure_circuit_closed()
    kwargs.setdefault("retry", None)
    kwargs.setdefault("timeout", DEFAULT_FIRESTORE_TIMEOUT)
    try:
        return func(*args, **kwargs)
    except Exception as exc:
        if _is_quota_error(exc):
            trip_circuit_breaker()
        raise


def _create_resilient_stream(stream_fn, *args, **kwargs):
    """Envolve stream() do Firestore para aplicar timeout/retry=None e abrir o circuit breaker em 429."""
    _ensure_circuit_closed()
    kwargs.setdefault("retry", None)
    kwargs.setdefault("timeout", DEFAULT_FIRESTORE_TIMEOUT)

    def _guarded_generator():
        _ensure_circuit_closed()
        try:
            for item in stream_fn(*args, **kwargs):
                yield item
        except Exception as exc:
            if _is_quota_error(exc):
                trip_circuit_breaker()
            raise

    return _guarded_generator()


class ResilientQuery:
    """Proxy transparente para Query do Firestore com fail-fast e circuit breaker."""

    def __init__(self, raw_query):
        self._raw = raw_query

    def where(self, *args, **kwargs):
        return ResilientQuery(self._raw.where(*args, **kwargs))

    def order_by(self, *args, **kwargs):
        return ResilientQuery(self._raw.order_by(*args, **kwargs))

    def limit(self, *args, **kwargs):
        return ResilientQuery(self._raw.limit(*args, **kwargs))

    def limit_to_last(self, *args, **kwargs):
        return ResilientQuery(self._raw.limit_to_last(*args, **kwargs))

    def offset(self, *args, **kwargs):
        return ResilientQuery(self._raw.offset(*args, **kwargs))

    def select(self, *args, **kwargs):
        return ResilientQuery(self._raw.select(*args, **kwargs))

    def start_at(self, *args, **kwargs):
        return ResilientQuery(self._raw.start_at(*args, **kwargs))

    def start_after(self, *args, **kwargs):
        return ResilientQuery(self._raw.start_after(*args, **kwargs))

    def end_at(self, *args, **kwargs):
        return ResilientQuery(self._raw.end_at(*args, **kwargs))

    def end_before(self, *args, **kwargs):
        return ResilientQuery(self._raw.end_before(*args, **kwargs))

    def get(self, *args, **kwargs):
        return _execute_resilient(self._raw.get, *args, **kwargs)

    def stream(self, *args, **kwargs):
        return _create_resilient_stream(self._raw.stream, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._raw, name)


class ResilientDocumentReference:
    """Proxy transparente para DocumentReference do Firestore com fail-fast e circuit breaker."""

    def __init__(self, raw_doc):
        self._raw = raw_doc

    def get(self, *args, **kwargs):
        return _execute_resilient(self._raw.get, *args, **kwargs)

    def set(self, *args, **kwargs):
        return _execute_resilient(self._raw.set, *args, **kwargs)

    def create(self, *args, **kwargs):
        return _execute_resilient(self._raw.create, *args, **kwargs)

    def update(self, *args, **kwargs):
        return _execute_resilient(self._raw.update, *args, **kwargs)

    def delete(self, *args, **kwargs):
        return _execute_resilient(self._raw.delete, *args, **kwargs)

    def collection(self, *args, **kwargs):
        return ResilientCollectionReference(self._raw.collection(*args, **kwargs))

    def __getattr__(self, name):
        return getattr(self._raw, name)


class ResilientCollectionReference(ResilientQuery):
    """Proxy transparente para CollectionReference do Firestore com fail-fast e circuit breaker."""

    def document(self, *args, **kwargs):
        return ResilientDocumentReference(self._raw.document(*args, **kwargs))

    def add(self, *args, **kwargs):
        result = _execute_resilient(self._raw.add, *args, **kwargs)
        if isinstance(result, tuple) and len(result) == 2:
            return result[0], ResilientDocumentReference(result[1])
        return result


class ResilientWriteBatch:
    """Proxy transparente para WriteBatch do Firestore com desempacotamento de referências e circuit breaker."""

    def __init__(self, raw_batch):
        self._raw = raw_batch

    @staticmethod
    def _unwrap_ref(reference):
        return getattr(reference, "_raw", reference)

    def create(self, reference, *args, **kwargs):
        return self._raw.create(self._unwrap_ref(reference), *args, **kwargs)

    def set(self, reference, *args, **kwargs):
        return self._raw.set(self._unwrap_ref(reference), *args, **kwargs)

    def update(self, reference, *args, **kwargs):
        return self._raw.update(self._unwrap_ref(reference), *args, **kwargs)

    def delete(self, reference, *args, **kwargs):
        return self._raw.delete(self._unwrap_ref(reference), *args, **kwargs)

    def commit(self, *args, **kwargs):
        return _execute_resilient(self._raw.commit, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._raw, name)


class ResilientFirestoreClient:
    """Proxy para firestore.Client() que força timeout curto (4s), retry=None e circuit breaker 429."""

    def __init__(self, raw_client):
        self._raw = raw_client

    def collection(self, *args, **kwargs):
        return ResilientCollectionReference(self._raw.collection(*args, **kwargs))

    def collection_group(self, *args, **kwargs):
        return ResilientQuery(self._raw.collection_group(*args, **kwargs))

    def document(self, *args, **kwargs):
        return ResilientDocumentReference(self._raw.document(*args, **kwargs))

    def batch(self, *args, **kwargs):
        return ResilientWriteBatch(self._raw.batch(*args, **kwargs))

    def __getattr__(self, name):
        return getattr(self._raw, name)


def _resolve_credentials_path() -> str:
    """Resolve o caminho de credenciais do Firebase mesmo quando executado fora do diretório backend_ia."""
    configured = settings.FIREBASE_CREDENTIALS_PATH
    if os.path.exists(configured):
        return configured
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fallback = os.path.join(backend_dir, os.path.basename(configured))
    if os.path.exists(fallback):
        return fallback
    return configured


def init_firebase():
    global db
    creds_path = _resolve_credentials_path()
    if not firebase_admin._apps:
        if not os.path.exists(creds_path):
            logger.warning(f"Aviso: Arquivo de credenciais do Firebase não encontrado em {creds_path}")
            return

        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        db = ResilientFirestoreClient(firestore.client())
        logger.info("Firebase inicializado com sucesso!")
    elif db is None:
        db = ResilientFirestoreClient(firestore.client())
