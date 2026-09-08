import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config import firebase

logger = logging.getLogger(__name__)


class FileConversionRepository:
    """
    Repositório thread-safe para auditoria e histórico de conversões de arquivos (US-09).
    Persiste na coleção 'file_conversions' do Firestore com fallback local em memória.
    Garante isolamento estrito de dados por usuário (P-0905).
    """

    COLLECTION_NAME = "file_conversions"
    _storage: List[Dict[str, Any]] = []
    _lock = threading.RLock()

    @classmethod
    def clear_in_memory(cls) -> None:
        """Limpa armazenamento de fallback em memória (utilizado em testes)."""
        with cls._lock:
            cls._storage.clear()

    @classmethod
    def save_conversion(
        cls,
        user_id: str,
        conversion_type: str,
        source_format: str,
        target_format: str,
        file_size_bytes: int,
        output_size_bytes: Optional[int] = None,
        status: str = "success",
        execution_time_ms: int = 0,
        error_message: Optional[str] = None
    ) -> str:
        """
        Registra uma operação de conversão no Firestore e no fallback em memória.
        """
        record_id = str(uuid.uuid4())
        record = {
            "id": record_id,
            "user_id": user_id,
            "userId": user_id,
            "conversion_type": conversion_type,
            "source_format": source_format.lower(),
            "target_format": target_format.lower(),
            "file_size_bytes": file_size_bytes,
            "output_size_bytes": output_size_bytes or 0,
            "status": status,
            "error_message": error_message,
            "execution_time_ms": execution_time_ms,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        with cls._lock:
            cls._storage.append(dict(record))

        # Tenta persistir no Firestore se disponível
        try:
            db = getattr(firebase, "db", None)
            if db:
                db.collection(cls.COLLECTION_NAME).document(record_id).set(record)
                logger.info(f"Conversao {record_id} registrada no Firestore com sucesso.")
        except Exception as e:
            logger.warning(f"Fallback para memoria ao registrar conversao: {e}")

        return record_id

    @classmethod
    def get_user_conversions(cls, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna as conversões mais recentes do usuário informado, com isolamento estrito.
        """
        # Tenta buscar do Firestore
        try:
            db = getattr(firebase, "db", None)
            if db:
                docs = (
                    db.collection(cls.COLLECTION_NAME)
                    .where("user_id", "==", user_id)
                    .order_by("created_at", direction="DESCENDING")
                    .limit(limit)
                    .stream()
                )
                results = [doc.to_dict() for doc in docs]
                if results:
                    return results
        except Exception as e:
            logger.debug(f"Firestore query fallback para memoria: {e}")

        # Fallback para memória
        with cls._lock:
            user_records = [
                r for r in cls._storage
                if r.get("user_id") == user_id or r.get("userId") == user_id
            ]
            user_records.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return user_records[:limit]
