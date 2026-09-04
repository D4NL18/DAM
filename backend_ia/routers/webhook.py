import logging
import re
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Header
from typing import Optional
from services.ai_service import AIService
from services.whatsapp_service import WhatsAppService
from services.security_service import SecurityService
from services.tts_service import TTSService
from repositories.chat_repository import ChatRepository
from services.user_context import UserContext
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

def is_allowed_user(remote_jid: str, allowed_phone: str = "") -> bool:
    """
    Valida estritamente se o JID remoto pertence a um dos usuários autorizados (Daniel ou Lari).
    Tolera a oscilação do 9º dígito no Brasil.
    """
    if not remote_jid:
        return False
    
    # Ignora grupos e canais
    if "@g.us" in remote_jid or "@newsletter" in remote_jid:
        return False

    jid_user = remote_jid.split("@")[0]
    jid_digits = normalize_digits(jid_user)

    if not jid_digits:
        return False

    ddd_jid, num_jid = extrair_ddd_e_numero(jid_digits)

    # Coleta todos os números autorizados
    telefones_autorizados = []
    if allowed_phone:
        telefones_autorizados.append(allowed_phone)
    if hasattr(settings, "ALLOWED_PHONE_NUMBERS") and settings.ALLOWED_PHONE_NUMBERS:
        if isinstance(settings.ALLOWED_PHONE_NUMBERS, list):
            telefones_autorizados.extend(settings.ALLOWED_PHONE_NUMBERS)
        elif isinstance(settings.ALLOWED_PHONE_NUMBERS, str):
            telefones_autorizados.extend([p.strip() for p in settings.ALLOWED_PHONE_NUMBERS.split(",") if p.strip()])

    if not telefones_autorizados:
        return False

    for allowed in telefones_autorizados:
        allowed_digits = normalize_digits(allowed)
        if not allowed_digits:
            continue
        ddd_allowed, num_allowed = extrair_ddd_e_numero(allowed_digits)
        if num_allowed == num_jid and (not ddd_allowed or not ddd_jid or ddd_allowed == ddd_jid):
            return True

    return False

async def process_and_reply(
    remote_jid: str, 
    text: str, 
    media_base64: Optional[str] = None, 
    media_mimetype: Optional[str] = None
):
    # Ativa o contexto do usuário da mensagem atual
    user_info = UserContext.resolve_user_from_phone(remote_jid)
    if user_info:
        UserContext.set_user(user_info["id"], user_info["phone"])
    else:
        UserContext.set_user("daniel", remote_jid)

    masked_jid = SecurityService.mask_phone(remote_jid)
    safe_text = SecurityService.sanitize_log(text)
    user_name = UserContext.get_user_name()
    logger.info(f"--> [BACKGROUND] Processando mensagem de {user_name} ({masked_jid}): '{safe_text}'")

    try:
        ai_response = AIService.process_message(remote_jid, text, media_base64, media_mimetype)
        logger.info(f"--> [BACKGROUND] IA respondeu ({len(ai_response)} chars).")

        # Verifica se deve responder em áudio
        deve_enviar_audio = False
        if media_mimetype and "audio" in media_mimetype:
            deve_enviar_audio = True
        elif TTSService.should_reply_with_audio(text):
            deve_enviar_audio = True

        enviado_com_sucesso = False
        if deve_enviar_audio:
            logger.info(f"--> [BACKGROUND] Sintetizando voz via TTSService para {masked_jid}...")
            audio_bytes = TTSService.synthesize_speech(ai_response)
            if audio_bytes:
                resp = WhatsAppService.send_voice_note(remote_jid, audio_bytes)
                if resp is not None:
                    logger.info(f"--> [BACKGROUND] Áudio entregue via WhatsApp para {masked_jid}")
                    enviado_com_sucesso = True
            else:
                logger.warning("--> [BACKGROUND] Falha na síntese de áudio. Acionando fallback para texto.")

        # Fallback para envio de texto caso áudio não tenha sido acionado ou tenha falhado
        if not enviado_com_sucesso:
            resp = WhatsAppService.send_text(remote_jid, ai_response)
            logger.info(f"--> [BACKGROUND] Mensagem de texto entregue via WhatsApp para {masked_jid}")

        ChatRepository.save_log(remote_jid=remote_jid, from_me=True, text=ai_response)
    except Exception as e:
        logger.error(f"--> [BACKGROUND ERROR] Falha no processamento da mensagem: {e}")


@router.post("/api/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    # Validação de Token de Webhook (Segurança)
    if settings.WEBHOOK_TOKEN:
        token = authorization or apikey
        if not SecurityService.validate_webhook_token(token, settings.WEBHOOK_TOKEN):
            logger.warning("Tentativa de acesso ao webhook com token inválido ou ausente.")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
    except Exception as e:
        logger.error(f"Erro ao parsear JSON do webhook: {e}")
        return {"status": "error", "message": "Invalid JSON"}

    event = str(payload.get("event", "")).lower()

    # Guard clause: processa unicamente messages.upsert
    if event not in ["messages.upsert", "messages_upsert"]:
        return {"status": "ignored", "reason": "not_messages_upsert"}

    data = payload.get("data")
    if not isinstance(data, dict):
        return {"status": "ignored", "reason": "invalid_data_format"}

    key = data.get("key")
    if not isinstance(key, dict):
        return {"status": "ignored", "reason": "invalid_key_format"}

    remote_jid = key.get("remoteJid", "")
    message_id = key.get("id")
    masked_jid = SecurityService.mask_phone(remote_jid)

    # Guard clause: ignora mensagens enviadas pelo próprio bot (anti-loop)
    if key.get("fromMe", False):
        return {"status": "ignored", "reason": "from_me"}

    # Guard clause: ignora grupos e canais
    if "@g.us" in remote_jid or "@newsletter" in remote_jid:
        return {"status": "ignored", "reason": "group_or_newsletter"}

    # Guard clause: isolamento inviolável para o número pessoal permitido
    if not is_allowed_user(remote_jid, settings.ALLOWED_PHONE_NUMBER):
        logger.warning(f"--> [WEBHOOK] Bloqueado! Número não autorizado: {masked_jid}")
        return {"status": "ignored", "reason": "unauthorized_user"}

    logger.info(f"--> [WEBHOOK] Mensagem autorizada recebida de {masked_jid}")

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

    # Suporte a Documentos e Arquivos (US-09)
    elif "documentMessage" in message or message_type == "documentMessage":
        doc_info = message.get("documentMessage", {})
        doc_filename = doc_info.get("fileName", "documento") if isinstance(doc_info, dict) else "documento"
        caption = doc_info.get("caption") if isinstance(doc_info, dict) else None
        text = caption or text or f"Recebi o documento '{doc_filename}'. Analise ou processe a conversão solicitada."
        b64 = message.get("base64") or data.get("base64")
        if b64:
            media_base64 = b64
            media_mimetype = doc_info.get("mimetype", "application/pdf") if isinstance(doc_info, dict) else "application/pdf"


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
