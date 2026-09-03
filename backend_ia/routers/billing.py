import logging
import base64
import json
from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional
from config.settings import settings
from services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/api/billing-alert")
async def gcp_billing_alert(
    request: Request,
    authorization: Optional[str] = Header(None),
    apikey: Optional[str] = Header(None)
):
    """
    Webhook que recebe mensagens do Cloud Pub/Sub contendo notificações de orçamento do GCP Billing.
    Se o orçamento atingir os limites (50%, 80%, 100%), notifica o usuário no WhatsApp.
    """
    if settings.WEBHOOK_TOKEN:
        token = authorization or apikey
        if not token or (token != settings.WEBHOOK_TOKEN and token.replace("Bearer ", "") != settings.WEBHOOK_TOKEN):
            logger.warning("Tentativa de acesso não autorizado a /api/billing-alert")
            raise HTTPException(status_code=401, detail="Unauthorized")

    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Erro ao parsear JSON do Pub/Sub: {e}")
        return {"status": "error", "message": "Invalid JSON"}

    message = body.get("message", {})
    data_b64 = message.get("data")

    if not data_b64:
        return {"status": "ignored", "reason": "empty_pubsub_data"}

    try:
        decoded_str = base64.b64decode(data_b64).decode("utf-8")
        billing_info = json.loads(decoded_str)
    except Exception as e:
        logger.error(f"Erro ao decodificar payload Pub/Sub: {e}")
        return {"status": "error", "message": "Failed to decode PubSub data"}

    cost_amount = billing_info.get("costAmount", 0.0)
    budget_amount = billing_info.get("budgetAmount", 0.0)
    currency = billing_info.get("currencyCode", "BRL")
    budget_name = billing_info.get("budgetDisplayName", "GCP Cloud")

    percentual = (cost_amount / budget_amount * 100) if budget_amount > 0 else 0

    alerta_msg = (
        f"🚨 **Alerta de Orçamento GCP ({budget_name})!**\n"
        f"• Consumo atual: {currency} {cost_amount:.2f}\n"
        f"• Limite estipulado: {currency} {budget_amount:.2f}\n"
        f"• Percentual atingido: {percentual:.1f}%\n\n"
        f"Verifique o console do Google Cloud para detalhes de custos e FinOps."
    )

    if settings.ALLOWED_PHONE_NUMBER:
        dest_jid = f"{settings.ALLOWED_PHONE_NUMBER}@s.whatsapp.net"
        WhatsAppService.send_text(dest_jid, alerta_msg)

    return {"status": "alert_processed", "percentual": percentual}
