import logging
from typing import Optional
from fastapi import APIRouter, Header, HTTPException, Query, status
from config.settings import settings
from services.security_service import SecurityService
from config import firebase
from services.briefing_service import (
    montar_resumo_matinal,
    enviar_briefing_matinal,
    obter_preferencias_briefing
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["Morning Briefing"])

@router.post("/morning")
def trigger_morning_briefing(
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None),
    force: bool = Query(False, description="Forçar envio mesmo que já tenha sido enviado hoje"),
    user_id: Optional[str] = Query(None, description="Usuário alvo ('daniel', 'lari' ou todos se omitido)")
):
    """
    Dispara o Morning Briefing matinal para o WhatsApp dos usuários.
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

    logger.info(f"Disparo do briefing matinal solicitado (force={force}, user_id={user_id}).")
    if user_id:
        resultado = enviar_briefing_matinal(force=force, user_id=user_id)
        return {"status": "ok", "mensagem": resultado, "userId": user_id}

    # Dispara para todos os usuários ativos
    usuarios_alvo = ["daniel", "lari"]
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("briefing_preferences").stream()
            for d in docs:
                uid = d.id.lower().strip()
                if uid not in usuarios_alvo:
                    usuarios_alvo.append(uid)
        except Exception as e:
            logger.warning(f"Erro ao listar usuários em briefing_preferences: {e}")

    detalhes = []
    for uid in usuarios_alvo:
        try:
            prefs = obter_preferencias_briefing(uid)
            if prefs.get("ativo", True):
                res = enviar_briefing_matinal(force=force, user_id=uid)
                detalhes.append({"userId": uid, "resultado": res})
        except Exception as e:
            logger.error(f"Erro ao enviar briefing para {uid}: {e}")
            detalhes.append({"userId": uid, "erro": str(e)})

    return {
        "status": "ok",
        "mensagem": f"Briefings processados para {len(detalhes)} usuário(s).",
        "detalhes": detalhes
    }

@router.get("/preview")
def preview_morning_briefing(
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None),
    user_id: Optional[str] = Query(None, description="Usuário alvo para pré-visualização")
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

    texto = montar_resumo_matinal(user_id=user_id)
    return {"status": "ok", "userId": user_id or "daniel", "preview": texto}
