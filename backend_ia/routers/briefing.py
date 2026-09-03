import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from config.settings import settings
from services.security_service import SecurityService
from services.briefing_service import montar_resumo_matinal, enviar_briefing_matinal

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["Morning Briefing"])

@router.post("/morning")
def trigger_morning_briefing(
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None),
    force: bool = Query(False, description="Forçar envio mesmo que já tenha sido enviado hoje")
):
    """
    Dispara o Morning Briefing matinal das 08:00 para o WhatsApp do usuário.
    Protegido via token Bearer ou apikey.
    Pode ser invocado manualmente ou via Cloud Scheduler / Cron Job.
    """
    token = apikey or authorization
    if not token or not SecurityService.validate_webhook_token(token, settings.WEBHOOK_TOKEN):
        logger.warning("Tentativa não autorizada de disparar briefing matinal.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado. Forneça o token correto no header 'apikey' ou 'Authorization'."
        )

    logger.info(f"Disparo do briefing matinal solicitado (force={force}).")
    resultado = enviar_briefing_matinal(force=force)
    return {"status": "ok", "mensagem": resultado}

@router.get("/preview")
def preview_morning_briefing(
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    """
    Retorna a pré-visualização do texto do briefing de hoje sem disparar para o WhatsApp.
    """
    token = apikey or authorization
    if not token or not SecurityService.validate_webhook_token(token, settings.WEBHOOK_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autorizado."
        )

    texto = montar_resumo_matinal()
    return {"status": "ok", "preview": texto}
