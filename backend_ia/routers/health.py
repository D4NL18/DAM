import logging
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from config import firebase
from config.settings import settings
from services.security_service import SecurityService
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/health-webhook")
async def health_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    # Validar token de webhook de forma segura (Fase 6)
    if settings.WEBHOOK_TOKEN:
        token = authorization or apikey
        if not SecurityService.validate_webhook_token(token, settings.WEBHOOK_TOKEN):
            logger.warning("Tentativa de acesso não autorizado ao webhook de saúde.")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
        
        # Estrutura genérica baseada no Health Auto Export
        # Assumindo que o payload traga data do tipo:
        # { "date": "2024-03-01", "metrics": { "steps": 10000, "activeEnergy": 500, "heartRate": 72 } }
        
        user_id = (
            request.headers.get("x-user-id")
            or request.query_params.get("user")
            or request.query_params.get("userId")
            or request.query_params.get("user_id")
            or "daniel"
        ).lower().strip()
        data_to_save = {
            "userId": user_id,
            "user_id": user_id,
            "timestamp": datetime.now(timezone.utc),
            "payload": payload,
        }

        if firebase.db:
            firebase.db.collection("health_metrics").add(data_to_save)
            logger.info(f"Métricas de saúde para [{user_id}] salvas com sucesso.")

        else:
            logger.error("Firebase não inicializado.")
            raise HTTPException(status_code=500, detail="Database not configured")

        return {"status": "success", "message": "Health data received"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook de saúde: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
