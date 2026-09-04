import base64
import logging
import requests
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    def send_text(remote_jid: str, text: str) -> Optional[Dict[str, Any]]:
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
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem via WhatsApp: {e}")
            return None

    @staticmethod
    def send_voice_note(remote_jid: str, audio_bytes: bytes, mime_type: str = "audio/mp3") -> Optional[Dict[str, Any]]:
        """
        Envia uma nota de voz gravada (PTT - Push-To-Talk) para o WhatsApp via Evolution API.
        """
        url = f"{settings.EVOLUTION_API_URL}/message/sendWhatsAppAudio/{settings.EVOLUTION_INSTANCE_NAME}"
        
        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }

        b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
        payload = {
            "number": remote_jid,
            "audio": b64_audio,
            "encoding": True
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar nota de voz via WhatsApp: {e}")
            return None

    @staticmethod
    def send_document(
        remote_jid: str,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "application/pdf",
        caption: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Envia um documento/arquivo (PDF, Word, Imagem, etc.) para o WhatsApp via Evolution API.
        """
        url = f"{settings.EVOLUTION_API_URL}/message/sendMedia/{settings.EVOLUTION_INSTANCE_NAME}"

        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }

        b64_file = base64.b64encode(file_bytes).decode("utf-8")
        payload = {
            "number": remote_jid,
            "media": b64_file,
            "mediatype": "document",
            "mimetype": mime_type,
            "fileName": filename,
            "caption": (caption + "\u200b") if caption else "\u200b"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar documento via WhatsApp: {e}")
            return None


