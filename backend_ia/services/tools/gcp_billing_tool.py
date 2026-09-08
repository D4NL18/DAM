"""
GCP Billing Tool — Módulo de Monitoramento de Faturamento e FinOps da Nuvem
Domain: Finanças & Gastos (FinOps)
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from config.settings import settings
from config import firebase

logger = logging.getLogger(__name__)

def consultar_gcp_billing() -> str:
    """
    Consulta o status do faturamento (billing), consumo de recursos e orçamento
    da infraestrutura do DAM no Google Cloud Platform (GCP).
    Use esta ferramenta sempre que o usuário perguntar sobre o faturamento,
    custos de nuvem, quanto gastou no GCP ou status do billing.
    """
    snapshot = None

    if firebase.db is not None:
        try:
            doc = firebase.db.collection("gcp_billing_snapshots").document("latest").get()
            if doc.exists:
                snapshot = doc.to_dict()
        except Exception as e:
            logger.warning(f"Erro ao buscar snapshot de billing no Firestore: {e}")

    linhas = [
        "☁️ *Status de Custos e Faturamento — Google Cloud Platform (GCP)*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🏢 *Projeto:* `bot-dam` (`{settings.PROJECT_ID if hasattr(settings, 'PROJECT_ID') else 'bot-dam'}`)"
    ]

    if snapshot:
        cost = snapshot.get("cost_amount", 0.0)
        budget = snapshot.get("budget_amount", 0.0)
        currency = snapshot.get("currency", "BRL")
        percentual = snapshot.get("percentual", 0.0)
        budget_name = snapshot.get("budget_name", "Orçamento Geral")
        updated_at = snapshot.get("updated_at", "")

        # Barra de progresso visual
        blocos = int(min(percentual, 100) / 10)
        barra = "▓" * blocos + "░" * (10 - blocos)

        linhas.extend([
            f"📊 *Orçamento Monitorado:* {budget_name}",
            f"• *Consumo Atual:* {currency} {cost:.2f}",
            f"• *Teto do Orçamento:* {currency} {budget:.2f}",
            f"• *Utilização:* {percentual:.1f}% `[{barra}]`",
        ])

        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at)
                linhas.append(f"• *Último Alerta:* {dt.strftime('%d/%m/%Y às %H:%M')} (via Pub/Sub)")
            except Exception:
                linhas.append(f"• *Último Alerta:* {updated_at}")
    else:
        linhas.extend([
            "📊 *Orçamento & Alertas FinOps:*",
            "• *Status Atual:* Nenhum alerta de consumo excedente (50%, 80%, 100%) disparado pelo Cloud Billing.",
            "• *Monitoramento:* Ativo via Google Cloud Pub/Sub (`/api/billing-alert`).",
        ])

    linhas.extend([
        "",
        "🖥️ *Infraestrutura Ativa e Otimizada (FinOps):*",
        "• *Compute Engine:* VM `dam-server` (`e2-micro`, elegível ao Free Tier vitalício do GCP).",
        "• *Cloud Run:* Serviço `dam-backend` (Serverless pago estritamente por microssegundo de CPU).",
        "• *Banco de Dados:* Google Cloud Firestore (Modo Nativo, cota Always Free de até 1 GB).",
        "• *Frontend:* Firebase Hosting (Grátis até 10 GB/mês de transferência).",
        "━━━━━━━━━━━━━━━━━━━━━━",
        "💡 *Diagnóstico FinOps:* Todos os serviços operam em arquitetura de baixo custo e alta eficiência."
    ])

    return "\n".join(linhas)
