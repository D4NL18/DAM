from typing import Optional
import uuid
import logging
from datetime import datetime, timezone
from config import firebase

logger = logging.getLogger(__name__)

def normalizar_metodo_pagamento(metodo: Optional[str]) -> Optional[str]:
    """
    Normaliza o método de pagamento para uma das 3 modalidades estritas:
    1. 'Cartão de Crédito Secundário'
    2. 'Cartão de Crédito Pessoal'
    3. 'Cartão de Débito' (inclui Pix)
    """
    if not metodo:
        return None

    m = metodo.strip().lower()

    # 1. Cartão Secundário / Compartilhado / Familiar
    if any(k in m for k in ["one", "pai", "secundar", "secundár", "compartilh", "familiar"]):
        return "Cartão de Crédito Secundário"

    # 3. Débito e Pix (se for pix, sempre cai no de débito)
    if "pix" in m or "debito" in m or "débito" in m:
        return "Cartão de Débito"

    # 2. Cartão de crédito pessoal
    if "credito" in m or "crédito" in m or "pessoal" in m:
        return "Cartão de Crédito Pessoal"

    return None

def registrar_gasto(descricao: str, valor: float, categoria: str, metodo_pagamento: str) -> str:
    """
    Registra um novo gasto financeiro do usuário.
    Todo gasto deve obrigatoriamente estar associado a uma das 3 modalidades:
    - 'Cartão de Crédito Secundário'
    - 'Cartão de Crédito Pessoal'
    - 'Cartão de Débito' (Pix conta como débito)

    Args:
        descricao (str): O que foi comprado ou pago (ex: 'Almoço Ifood', 'Uber').
        valor (float): O valor gasto.
        categoria (str): A categoria do gasto (ex: 'Alimentação', 'Transporte', 'Lazer', 'Moradia').
        metodo_pagamento (str): 'Cartão de Crédito Secundário', 'Cartão de Crédito Pessoal' ou 'Cartão de Débito' (se for Pix, use 'Cartão de Débito').
    """
    metodo_normalizado = normalizar_metodo_pagamento(metodo_pagamento)
    if not metodo_normalizado:
        return (
            "Método de pagamento não identificado. Em qual das suas contas/cartões foi a cobrança?\n"
            "• Cartão de crédito secundário\n"
            "• Cartão de crédito pessoal\n"
            "• Cartão de débito (ou Pix)"
        )

    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."
    
    try:
        data_to_save = {
            "id": str(uuid.uuid4()),
            "description": descricao,
            "amount": valor,
            "category": categoria,
            "payment_method": metodo_normalizado,
            "date": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc)
        }
        
        firebase.db.collection("finances").add(data_to_save)
        logger.info(f"Gasto registrado: {descricao} - R$ {valor:.2f} [{metodo_normalizado}]")
        return (
            f"Sucesso! Registrei o gasto de R$ {valor:.2f} com '{descricao}' "
            f"na categoria {categoria} no cartão **{metodo_normalizado}**."
        )
    
    except Exception as e:
        logger.error(f"Erro ao registrar finanças: {e}")
        return "Desculpe, ocorreu um erro ao salvar seu gasto. Tente novamente mais tarde."
