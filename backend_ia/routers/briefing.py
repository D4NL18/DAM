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

def _obter_usuarios_alvo() -> list[str]:
    """Recupera a lista de IDs de usuários ativos no Firestore ou fallback."""
    usuarios = ["daniel", "lari"]
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("briefing_preferences").stream()
            for doc in docs:
                uid = doc.id.lower().strip()
                if uid not in usuarios:
                    usuarios.append(uid)
        except Exception:
            logger.exception("Erro ao listar usuários em briefing_preferences no Firestore")
    return usuarios


def _executar_disparo_multi_usuario(usuarios: list[str], force: bool) -> list[dict]:
    """Executa o envio do briefing matinal para uma lista de usuários."""
    detalhes = []
    for uid in usuarios:
        try:
            prefs = obter_preferencias_briefing(uid)
            if prefs.get("ativo", True):
                res = enviar_briefing_matinal(force=force, user_id=uid)
                detalhes.append({"userId": uid, "resultado": res})
        except Exception:
            logger.exception("Erro ao enviar briefing matinal para usuário %s", uid)
            detalhes.append({"userId": uid, "erro": "Falha no envio do briefing"})
    return detalhes


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

    # Prevenção contra Log Injection (pythonsecurity:S5145): não loga dados arbitrários do usuário
    is_individual = bool(user_id)
    logger.info("Disparo do briefing matinal solicitado (force=%s, individual=%s)", force, is_individual)

    if user_id:
        safe_uid = user_id.strip().lower()
        resultado = enviar_briefing_matinal(force=force, user_id=safe_uid)
        return {"status": "ok", "mensagem": resultado, "userId": safe_uid}

    usuarios = _obter_usuarios_alvo()
    detalhes = _executar_disparo_multi_usuario(usuarios, force)

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

    safe_uid = user_id.strip().lower() if user_id else None
    texto = montar_resumo_matinal(user_id=safe_uid)
    return {"status": "ok", "userId": safe_uid or "daniel", "preview": texto}
