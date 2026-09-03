import logging
from config import firebase
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ChatRepository:
    COLLECTION = "chat_logs"

    @staticmethod
    def save_log(remote_jid: str, from_me: bool, text: str, message_id: str = None):
        if firebase.db is None:
            logger.warning("Firebase não inicializado, pulando salvamento de log.")
            return

        doc_data = {
            "remoteJid": remote_jid,
            "fromMe": from_me,
            "text": text,
            "timestamp": datetime.now(timezone.utc)
        }
        if message_id:
            doc_data["messageId"] = message_id

        firebase.db.collection(ChatRepository.COLLECTION).add(doc_data)

    @staticmethod
    def get_recent_history(remote_jid: str, limit: int = 10):
        if firebase.db is None:
            return []

        docs = firebase.db.collection(ChatRepository.COLLECTION) \
                 .where("remoteJid", "==", remote_jid) \
                 .order_by("timestamp", direction="DESCENDING") \
                 .limit(limit) \
                 .stream()

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # O Firestore retorna descending, precisamos inverter para a ordem cronológica
        history = []
        for doc in docs:
            data = doc.to_dict()
            if data.get("timestamp") and data["timestamp"] >= today_start:
                history.append(data)
        
        history.reverse()
        return history
