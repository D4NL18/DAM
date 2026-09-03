import logging
import re
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Header
from typing import Optional
from services.ai_service import AIService
from services.whatsapp_service import WhatsAppService
from repositories.chat_repository import ChatRepository
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

def normalize_digits(value: str) -> str:
    """Extrai apenas dígitos de uma string."""
    return re.sub(r"\D", "", value or "")

def extrair_ddd_e_numero(digits: str) -> tuple[str, str]:
    """Extrai DDD (2 dígitos) e os últimos 8 dígitos do telefone brasileiro tolerando o 9º dígito."""
    if len(digits) < 10:
        return "", digits[-8:] if len(digits) >= 8 else digits
    num8 = digits[-8:]
    if len(digits) >= 11 and digits[-9] == "9":
        ddd = digits[-11:-9]
    else:
        ddd = digits[-10:-8]
    return ddd, num8

def is_allowed_user(remote_jid: str, allowed_phone: str) -> bool:
    """
    Valida estritamente se o JID remoto pertence ao usuário autorizado.
    Fail-safe: se allowed_phone estiver vazio, rejeita sumariamente.
    Tolera a oscilação do 9º dígito no Brasil.
    """
    if not allowed_phone or not remote_jid:
        return False
    
    # Ignora grupos e canais
    if "@g.us" in remote_jid or "@newsletter" in remote_jid:
        return False

    allowed_digits = normalize_digits(allowed_phone)
    jid_user = remote_jid.split("@")[0]
    jid_digits = normalize_digits(jid_user)

    if not allowed_digits or not jid_digits:
        return False

    # Valida DDD e os 8 dígitos finais
    ddd_allowed, num_allowed = extrair_ddd_e_numero(allowed_digits)
    ddd_jid, num_jid = extrair_ddd_e_numero(jid_digits)

    if num_allowed != num_jid:
        return False

    if ddd_allowed and ddd_jid and ddd_allowed != ddd_jid:
        return False

    return True

def process_and_reply(
    remote_jid: str, 
    text: str, 
    media_base64: Optional[str] = None, 
    media_mimetype: Optional[str] = None
):
    print(f"--> [BACKGROUND] Iniciando IA para {remote_jid}: '{text}'", flush=True)
    try:
        ai_response = AIService.process_message(remote_jid, text, media_base64, media_mimetype)
        print(f"--> [BACKGROUND] IA respondeu ({len(ai_response)} chars). Enviando WhatsApp...", flush=True)
        resp = WhatsAppService.send_text(remote_jid, ai_response)
        print(f"--> [BACKGROUND] Envio WhatsApp resultado: {resp}", flush=True)
        ChatRepository.save_log(remote_jid=remote_jid, from_me=True, text=ai_response)
    except Exception as e:
        print(f"--> [BACKGROUND ERROR] Falha no processamento da mensagem: {e}", flush=True)

@router.post("/api/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    # Security Audit: Validação de Token de Webhook
    if settings.WEBHOOK_TOKEN:
        token = authorization or apikey
        if not token or (token != settings.WEBHOOK_TOKEN and token.replace("Bearer ", "") != settings.WEBHOOK_TOKEN):
            logger.warning("Tentativa de acesso ao webhook com token inválido ou ausente.")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Erro ao parsear JSON do webhook: {e}")
        return {"status": "error", "message": "Invalid JSON"}

    event = str(payload.get("event", "")).lower()
    print(f"--> [WEBHOOK] Evento recebido: '{event}' | Sender: {payload.get('sender')}", flush=True)

    # Guard clause: processa unicamente messages.upsert
    if event not in ["messages.upsert", "messages_upsert"]:
        print(f"--> [WEBHOOK] Ignorando evento não-upsert: '{event}'", flush=True)
        return {"status": "ignored", "reason": "not_messages_upsert"}

    data = payload.get("data")
    if not isinstance(data, dict):
        print("--> [WEBHOOK] Data inválido (não é dict)", flush=True)
        return {"status": "ignored", "reason": "invalid_data_format"}

    key = data.get("key")
    if not isinstance(key, dict):
        print("--> [WEBHOOK] Key inválido (não é dict)", flush=True)
        return {"status": "ignored", "reason": "invalid_key_format"}

    remote_jid = key.get("remoteJid", "")
    message_id = key.get("id")
    print(f"--> [WEBHOOK] Mensagem de remoteJid: {remote_jid} | id: {message_id}", flush=True)

    # Guard clause: ignora grupos e canais
    if "@g.us" in remote_jid or "@newsletter" in remote_jid:
        print(f"--> [WEBHOOK] Ignorando grupo/newsletter: {remote_jid}", flush=True)
        return {"status": "ignored", "reason": "group_or_newsletter"}

    # Guard clause: isolamento inviolável para o número pessoal permitido
    if not is_allowed_user(remote_jid, settings.ALLOWED_PHONE_NUMBER):
        print(f"--> [WEBHOOK] Bloqueado! Número não autorizado: {remote_jid} (Esperado: {settings.ALLOWED_PHONE_NUMBER})", flush=True)
        return {"status": "ignored", "reason": "unauthorized_user"}

    print(f"--> [WEBHOOK] APROVADO! Processando mensagem de {remote_jid}", flush=True)

    message = data.get("message")
    if not isinstance(message, dict):
        return {"status": "ignored", "reason": "empty_message"}

    message_type = data.get("messageType", "")
    media_base64 = None
    media_mimetype = None

    # Extração de texto padrão
    text = (
        message.get("conversation") 
        or message.get("extendedTextMessage", {}).get("text", "")
    )

    # Suporte Multimodal a Imagem (US-3.6)
    if "imageMessage" in message or message_type == "imageMessage":
        img_info = message.get("imageMessage", {})
        caption = img_info.get("caption") if isinstance(img_info, dict) else None
        text = caption or text or "Analise esta imagem enviada pelo usuário."
        b64 = message.get("base64") or data.get("base64")
        if b64:
            media_base64 = b64
            media_mimetype = img_info.get("mimetype", "image/jpeg") if isinstance(img_info, dict) else "image/jpeg"

    # Suporte Multimodal a Áudio (US-3.6)
    elif "audioMessage" in message or message_type == "audioMessage":
        audio_info = message.get("audioMessage", {})
        text = text or "Transcreva e responda ao que o usuário solicitou neste áudio."
        b64 = message.get("base64") or data.get("base64")
        if b64:
            media_base64 = b64
            media_mimetype = audio_info.get("mimetype", "audio/ogg") if isinstance(audio_info, dict) else "audio/ogg"

    if not text:
        return {"status": "ignored", "reason": "empty_text"}

    # Anti-loop: se terminar com caractere invisível, foi enviado pelo próprio bot
    if text.endswith("\u200b"):
        return {"status": "ignored", "reason": "bot_echo_anti_loop"}

    # Salva log da mensagem do usuário no banco
    ChatRepository.save_log(remote_jid=remote_jid, from_me=False, text=text, message_id=message_id)

    # Processamento assíncrono em background
    background_tasks.add_task(process_and_reply, remote_jid, text, media_base64, media_mimetype)
    return {"status": "processing"}
