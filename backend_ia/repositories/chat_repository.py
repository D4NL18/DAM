import logging
from config import firebase
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Cache em memória como fallback quando Firestore está indisponível (ex: quota 429)
_MEMORY_CHAT_CACHE: dict[str, list] = {}
_MEMORY_CACHE_MAX = 20  # máximo de mensagens por usuário em memória


class ChatRepository:
    COLLECTION = "chat_logs"

    @staticmethod
    def save_log(remote_jid: str, from_me: bool, text: str, message_id: str = None):
        # Salva sempre no cache em memória como fallback
        entry = {
            "remoteJid": remote_jid,
            "fromMe": from_me,
            "text": text,
            "timestamp": datetime.now(timezone.utc),
        }
        if message_id:
            entry["messageId"] = message_id

        cache = _MEMORY_CHAT_CACHE.setdefault(remote_jid, [])
        cache.append(entry)
        if len(cache) > _MEMORY_CACHE_MAX:
            cache.pop(0)

        if firebase.db is None:
            logger.warning("Firebase não inicializado, log salvo apenas em memória.")
            return

        try:
            firebase.db.collection(ChatRepository.COLLECTION).add(entry)
        except Exception as e:
            logger.warning(f"Firestore indisponível ao salvar log ({e}). Usando cache em memória.")

    @staticmethod
    def get_recent_history(remote_jid: str, limit: int = 10):
        if firebase.db is not None:
            try:
                docs = firebase.db.collection(ChatRepository.COLLECTION) \
                         .where("remoteJid", "==", remote_jid) \
                         .order_by("timestamp", direction="DESCENDING") \
                         .limit(limit) \
                         .stream()

                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                history = []
                for doc in docs:
                    data = doc.to_dict()
                    if data.get("timestamp") and data["timestamp"] >= today_start:
                        history.append(data)
                history.reverse()
                return history
            except Exception as e:
                logger.warning(f"Firestore indisponível ao buscar histórico ({e}). Usando cache em memória.")

        # Fallback: retorna histórico do cache em memória
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        cache = _MEMORY_CHAT_CACHE.get(remote_jid, [])
        history = [m for m in cache if m.get("timestamp") and m["timestamp"] >= today_start]
        return history[-limit:]
