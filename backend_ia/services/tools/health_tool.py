from services.user_context import UserContext
from config import firebase
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

def consultar_saude(dias_retroativos: int = 7) -> str:
    """
    Queries the user's health data saved in the database.

    Args:
        dias_retroativos (int): The number of days to search in the past.
    """
    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."
    
    try:
        agora = datetime.now(timezone.utc)
        limite_data = agora - timedelta(days=dias_retroativos)
        
        docs = firebase.db.collection("health_metrics") \
                 .where("timestamp", ">=", limite_data) \
                 .order_by("timestamp", direction="DESCENDING") \
                 .limit(10) \
                 .stream()

        user_id = UserContext.get_user_id()

        records = []
        for doc in docs:
            data = doc.to_dict()
            doc_user = data.get("userId") or data.get("user_id") or "daniel"
            if doc_user != user_id:
                continue

            # Estrutura baseada no que recebemos do webhook
            payload = data.get("payload", {})
            metrics = payload.get("metrics", {})
            data_registro = data.get("timestamp").strftime("%d/%m/%Y %H:%M")
            records.append(f"Em {data_registro}: Passos: {metrics.get('steps', 'N/A')}, Calorias: {metrics.get('activeEnergy', 'N/A')}, Batimentos médios: {metrics.get('heartRate', 'N/A')} bpm")


        if not records:
            return f"Não encontrei registros de saúde nos últimos {dias_retroativos} dias."
        
        return "Aqui estão os dados recentes:\n" + "\n".join(records)

    except Exception as e:
        logger.error(f"Erro ao consultar saúde: {e}")
        return "Ocorreu um erro ao buscar os dados de saúde."
