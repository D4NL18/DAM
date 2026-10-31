"""
Serviço de Migração e Saneamento de Dados Financeiros Legados (FG-09 / P-0903)
Corrige anomalias contábeis de forma segura e idempotente.
"""
import logging
from typing import Optional, Dict, Any
from config import firebase
from services.user_context import UserContext
from services.tools.finance_tool import _normalize_str

logger = logging.getLogger(__name__)


def sanear_transacoes_legadas(user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Saneia documentos da coleção 'finances' para o usuário especificado:
    - Converte categoria 'Reembolso' para 'Receitas'
    - Converte valores negativos para positivos
    - Converte descrições com termos de reembolso/estorno para type='income' e category='Receitas'
    """
    effective_user = user_id or UserContext.get_user_id() or "daniel"
    total_scanned = 0
    remediated = 0
    already_clean = 0

    if firebase.db is None:
        return {
            "userId": effective_user,
            "totalScanned": 0,
            "remediated": 0,
            "alreadyClean": 0,
            "status": "COMPLETED"
        }

    try:
        col = firebase.db.collection("finances")
        docs = col.stream()
        for doc in docs:
            if not hasattr(doc, "to_dict"):
                continue
            data = doc.to_dict() or {}
            doc_user = data.get("userId") or data.get("user_id") or "daniel"
            if doc_user != effective_user:
                continue

            total_scanned += 1

            cat_raw = str(data.get("category") or "")
            cat_norm = _normalize_str(cat_raw)
            desc_raw = str(data.get("description") or "")
            desc_norm = _normalize_str(desc_raw)
            tx_type = data.get("type")

            try:
                amount = float(data.get("amount") or 0.0)
            except (ValueError, TypeError):
                amount = 0.0

            reembolso_terms = ["reembolso", "estorno", "devolucao"]
            has_reembolso_desc = any(t in desc_norm for t in reembolso_terms)

            is_anomalous = False
            if cat_norm == "reembolso":
                is_anomalous = True
            elif amount < 0:
                is_anomalous = True
            elif has_reembolso_desc and tx_type != "income":
                is_anomalous = True

            if is_anomalous:
                clean_amount = abs(amount)
                update_payload = {
                    "type": "income",
                    "category": "Receitas",
                    "amount": clean_amount
                }
                if hasattr(doc, "reference") and hasattr(doc.reference, "update"):
                    doc.reference.update(update_payload)
                remediated += 1
            else:
                already_clean += 1

        logger.info(
            f"Saneamento de transações para [{effective_user}]: "
            f"total={total_scanned}, remediated={remediated}, alreadyClean={already_clean}"
        )

        return {
            "userId": effective_user,
            "totalScanned": total_scanned,
            "remediated": remediated,
            "alreadyClean": already_clean,
            "status": "COMPLETED"
        }

    except Exception as e:
        logger.error(f"Erro ao sanear transações legadas para [{effective_user}]: {e}")
        return {
            "userId": effective_user,
            "totalScanned": total_scanned,
            "remediated": remediated,
            "alreadyClean": already_clean,
            "status": "ERROR",
            "error": str(e)
        }
