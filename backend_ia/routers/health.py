import logging
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from config import firebase
from config.settings import settings
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/health-webhook")
async def health_webhook(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    # Validar token estático simples
    expected_token = settings.WEBHOOK_TOKEN
    if expected_token:
        if authorization != f"Bearer {expected_token}" and authorization != expected_token:
            logger.warning("Tentativa de acesso não autorizado ao webhook de saúde.")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        payload = await request.json()
        
        # Estrutura genérica baseada no Health Auto Export
        # Assumindo que o payload traga data do tipo:
        # { "date": "2024-03-01", "metrics": { "steps": 10000, "activeEnergy": 500, "heartRate": 72 } }
        
        data_to_save = {
            "timestamp": datetime.now(timezone.utc),
            "payload": payload,
            # Se for um formato conhecido do Auto Export:
            # "date": payload.get("data", {}).get("date")
        }

        if firebase.db:
            firebase.db.collection("health_metrics").add(data_to_save)
            logger.info("Métricas de saúde salvas com sucesso.")
        else:
            logger.error("Firebase não inicializado.")
            raise HTTPException(status_code=500, detail="Database not configured")

        return {"status": "success", "message": "Health data received"}
    except Exception as e:
        logger.error(f"Erro ao processar webhook de saúde: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")
