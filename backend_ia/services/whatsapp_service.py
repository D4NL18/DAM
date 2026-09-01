import logging
import requests
from config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    def send_text(remote_jid: str, text: str):
        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"
        
        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        # O Evolution espera apenas o número ou JID (ex: 5511999999999@s.whatsapp.net)
        payload = {
            "number": remote_jid,
            "text": text + "\u200b"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem via WhatsApp: {e}")
            return None
