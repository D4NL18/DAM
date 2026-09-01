import logging
from fastapi import APIRouter, BackgroundTasks, Request, HTTPException, Header
from typing import Optional
from services.ai_service import AIService
from services.whatsapp_service import WhatsAppService
from repositories.chat_repository import ChatRepository
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

def process_and_reply(remote_jid: str, text: str):
    # 1. Obter resposta do Gemini (inclui recuperar histórico e enviar a nova msg)
    ai_response = AIService.process_message(remote_jid, text)
    
    # 2. Enviar resposta para o WhatsApp
    WhatsAppService.send_text(remote_jid, ai_response)
    
    # 3. Salvar no Firestore a resposta do DAM
    ChatRepository.save_log(remote_jid=remote_jid, from_me=True, text=ai_response)

@router.post("/api/whatsapp/webhook")
async def whatsapp_webhook(
    request: Request, 
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    logger.warning(f"HEADERS CHEGANDO: {request.headers}")
    # Security Audit: Validação de Token de Webhook (se configurado)
    if settings.WEBHOOK_TOKEN:
        token = authorization or apikey
        logger.warning(f"TOKEN PARSED: {token} | ESPERADO: {settings.WEBHOOK_TOKEN}")
        # Suporta tanto formato 'Bearer token' quanto enviar apenas o token diretamente
        if not token or (token != settings.WEBHOOK_TOKEN and token.replace("Bearer ", "") != settings.WEBHOOK_TOKEN):
            logger.warning("Tentativa de acesso ao webhook com token inválido ou ausente.")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
        
        # Filtro básico para Evolution API v2 (messages.upsert)
        if payload.get("event") == "messages.upsert":
            data = payload.get("data", {})
            key = data.get("key", {})
            
            # Ignora mensagens enviadas pelo próprio bot e mensagens de grupo (simples verificação de formato JID)
            remote_jid = key.get("remoteJid", "")
            from_me = key.get("fromMe", False)
            message_id = key.get("id")
            
            # evolution api groups end with @g.us
            is_group = "@g.us" in remote_jid
            
            # Só responde no "Chat Comigo Mesmo"
            # O WhatsApp pode ocultar o 9º dígito no Brasil, então pegamos os últimos 8 dígitos.
            phone_filter = settings.ALLOWED_PHONE_NUMBER[-8:] if settings.ALLOWED_PHONE_NUMBER else ""
            is_me = (phone_filter in remote_jid) if phone_filter else True
            
            if is_me and not is_group:
                # Extração do texto baseada na estrutura da Evolution API
                message = data.get("message", {})
                # O texto pode vir em diferentes campos
                text = message.get("conversation") or message.get("extendedTextMessage", {}).get("text", "")
                
                # Anti-Loop: Se terminar com o caractere invisível, foi o bot que enviou, então ignora.
                if text and not text.endswith("\u200b"):
                    # Salva log da mensagem do usuário no banco
                    ChatRepository.save_log(remote_jid=remote_jid, from_me=False, text=text, message_id=message_id)
                    
                    # Coloca em background o processamento
                    background_tasks.add_task(process_and_reply, remote_jid, text)
                    
    except Exception as e:
        logger.error(f"Erro ao processar webhook: {e}")

    # Sempre retorne 200 rápido para a Evolution API não dar timeout
    return {"status": "processing"}
