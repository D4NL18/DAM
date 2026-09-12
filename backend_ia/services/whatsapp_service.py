import base64
import logging
import re
import requests
from typing import Optional, Dict, Any
from config.settings import settings

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    def _format_destination_number(remote_jid: str) -> str:
        """
        Normaliza o número/JID de destino para a Evolution API.
        - Se for grupo (@g.us), mantém intacto o JID do grupo.
        - Se for número de usuário individual (@s.whatsapp.net ou dígitos), extrai apenas os dígitos numéricos.
          Isso permite que a Evolution API consulte e resolva nativamente a variação do 9º dígito no WhatsApp,
          evitando erros 400 (Bad Request / exists: false) em contas registradas sem o 9 (ex: DDD 71 da Lari).
        """
        if not remote_jid:
            return ""
        dest = str(remote_jid).strip()
        if dest.endswith("@g.us"):
            return dest
        if "@s.whatsapp.net" in dest:
            return re.sub(r"\D", "", dest.split("@")[0])
        return dest

    @staticmethod
    def send_text(remote_jid: str, text: str) -> Optional[Dict[str, Any]]:
        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{settings.EVOLUTION_INSTANCE_NAME}"
        
        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        
        target_number = WhatsAppService._format_destination_number(remote_jid)
        payload = {
            "number": target_number,
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

    @staticmethod
    def get_base64_from_media_message(
        message_id: str, 
        message_data: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, str]]:
        """
        Recupera o Base64 e metadados de uma mídia recebida via Evolution API.
        Usa o endpoint /chat/getBase64FromMediaMessage/{instance}.
        """
        url = f"{settings.EVOLUTION_API_URL}/chat/getBase64FromMediaMessage/{settings.EVOLUTION_INSTANCE_NAME}"
        
        headers = {
            "apikey": settings.EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }

        # Payload aceito pela Evolution API:
        msg_payload: Dict[str, Any] = {"key": {"id": message_id}}
        if message_data and isinstance(message_data, dict):
            if "key" in message_data and isinstance(message_data["key"], dict):
                msg_payload["key"] = message_data["key"]
            if "message" in message_data:
                msg_payload["message"] = message_data["message"]

        payload = {
            "message": msg_payload,
            "convertToMp4": False
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                return None
            
            b64 = data.get("base64")
            mimetype = data.get("mimetype")
            if not b64 and isinstance(data.get("data"), dict):
                b64 = data["data"].get("base64")
                mimetype = mimetype or data["data"].get("mimetype")

            if b64:
                return {
                    "base64": b64,
                    "mimetype": mimetype or "application/octet-stream"
                }
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Não foi possível obter mídia da Evolution API (ID {message_id}): {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar mídia da Evolution API (ID {message_id}): {e}")
            return None



