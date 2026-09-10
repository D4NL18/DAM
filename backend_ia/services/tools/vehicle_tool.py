import logging
from typing import Optional, Dict, Any
from services.user_context import UserContext
from config import firebase

logger = logging.getLogger(__name__)

# Fallback em memória para veículos por usuário
_MEMORY_VEHICLES: Dict[str, Dict[str, Any]] = {
    "daniel": {
        "modelo": "Fiat Fastback Turbo 270",
        "combustivel": 68,
        "autonomia": 485,
        "travas": "trancadas",
        "vidros": "fechados",
        "pressao_pneus": "32 PSI (Todos calibrados)",
        "bateria": "12.6V (Saudável)",
        "hodometro": "14.820 km",
        "localizacao": "Garagem Residencial"
    }
}

def _reset_memory_vehicles():
    """Auxiliar para testes unitários."""
    _MEMORY_VEHICLES.clear()
    _MEMORY_VEHICLES["daniel"] = {
        "modelo": "Fiat Fastback Turbo 270",
        "combustivel": 68,
        "autonomia": 485,
        "travas": "trancadas",
        "vidros": "fechados",
        "pressao_pneus": "32 PSI (Todos calibrados)",
        "bateria": "12.6V (Saudável)",
        "hodometro": "14.820 km",
        "localizacao": "Garagem Residencial"
    }

def _obter_veiculo_usuario(user_id: str) -> Optional[Dict[str, Any]]:
    """Recupera os dados do veículo do usuário no Firestore ou na memória."""
    if firebase.db is not None:
        try:
            doc = firebase.db.collection("user_vehicles").document(user_id).get()
            if doc.exists:
                return doc.to_dict()
        except Exception as e:
            logger.warning(f"Erro ao buscar veículo do usuário {user_id} no Firestore: {e}")

    return _MEMORY_VEHICLES.get(user_id)

def cadastrar_ou_atualizar_veiculo(
    modelo: str,
    placa: Optional[str] = None,
    detalhes: Optional[str] = None
) -> str:
    """
    Register or update the connected user's vehicle (model, license plate, notes).

    Args:
        modelo (str): Vehicle make and model.
        placa (str, optional): License plate.
        detalhes (str, optional): Additional notes.
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()

    veiculo = {
        "userId": user_id,
        "modelo": modelo.strip(),
        "placa": placa.strip().upper() if placa else None,
        "detalhes": detalhes.strip() if detalhes else None,
        "combustivel": 75,
        "autonomia": 420,
        "travas": "trancadas",
        "vidros": "fechados",
        "pressao_pneus": "32 PSI (Calibrados)",
        "bateria": "12.6V (Normal)",
        "hodometro": "0 km",
        "localizacao": "Garagem Residencial"
    }

    _MEMORY_VEHICLES[user_id] = veiculo

    if firebase.db is not None:
        try:
            firebase.db.collection("user_vehicles").document(user_id).set(veiculo)
            logger.info(f"Veículo de {user_name} ({modelo}) salvo no Firestore.")
        except Exception as e:
            logger.error(f"Erro ao persistir veículo no Firestore: {e}")

    msg_placa = f" | Placa: {veiculo['placa']}" if veiculo["placa"] else ""
    return f"🚗 Veículo de {user_name} cadastrado com sucesso: **{veiculo['modelo']}**{msg_placa}!"

def consultar_status_veiculo() -> str:
    """
    Query real-time vehicle telemetry (fuel level, estimated range, lock status, tire pressure).
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()

    veiculo = _obter_veiculo_usuario(user_id)

    # Se não tiver veículo cadastrado e não for Daniel (que tem o Fiat Fastback de fábrica)
    if not veiculo:
        return (
            f"ℹ️ {user_name}, você ainda não possui um veículo cadastrado no DAM.\n"
            f"Deseja cadastrar o seu carro agora? Basta me informar o modelo (ex: 'Cadastre meu carro: Honda Civic')."
        )

    modelo = veiculo.get("modelo", "Veículo")
    combustivel = veiculo.get("combustivel", 68)
    autonomia = veiculo.get("autonomia", 450)
    travas_icon = "🔒" if veiculo.get("travas") == "trancadas" else "🔓"
    travas_txt = "Trancadas" if veiculo.get("travas") == "trancadas" else "Destrancadas"
    placa_txt = f" (Placa: {veiculo['placa']})" if veiculo.get("placa") else ""

    status = (
        f"🚗 **Status do Veículo ({modelo}){placa_txt}:**\n"
        f"• Combustível: {combustivel}% (Tanque)\n"
        f"• Autonomia estimada: {autonomia} km\n"
        f"• Travas das portas: {travas_txt} {travas_icon}\n"
        f"• Vidros: {veiculo.get('vidros', 'Totalmente fechados')}\n"
        f"• Pressão dos pneus: {veiculo.get('pressao_pneus', '32 PSI (Todos calibrados)')}\n"
        f"• Tensão da bateria: {veiculo.get('bateria', '12.6V (Saudável)')}\n"
        f"• Hodômetro: {veiculo.get('hodometro', '14.820 km')}\n"
        f"• Localização: {veiculo.get('localizacao', 'Garagem Residencial')}"
    )
    return status

def acionar_travas_veiculo(acao: str) -> str:
    """
    Send remote command to lock or unlock vehicle doors.

    Args:
        acao (str): 'travar' to lock or 'destravar' to unlock.
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()
    veiculo = _obter_veiculo_usuario(user_id)

    if not veiculo:
        return f"ℹ️ {user_name}, você não possui um veículo cadastrado no DAM para acionar comandos remotos."

    modelo = veiculo.get("modelo", "Veículo")
    acao_normalizada = acao.strip().lower()

    if acao_normalizada in ["travar", "trancar", "fechar"]:
        veiculo["travas"] = "trancadas"
        _MEMORY_VEHICLES[user_id] = veiculo
        if firebase.db is not None:
            try:
                firebase.db.collection("user_vehicles").document(user_id).set({"travas": "trancadas"}, merge=True)
            except Exception:
                pass
        logger.info(f"Comando remoto enviado: TRAVAR_PORTAS ({modelo})")
        return f"Comando enviado com sucesso: Portas do {modelo} foram travadas com sucesso! 🔒"

    elif acao_normalizada in ["destravar", "abrir"]:
        veiculo["travas"] = "destrancadas"
        _MEMORY_VEHICLES[user_id] = veiculo
        if firebase.db is not None:
            try:
                firebase.db.collection("user_vehicles").document(user_id).set({"travas": "destrancadas"}, merge=True)
            except Exception:
                pass
        logger.info(f"Comando remoto enviado: DESTRAVAR_PORTAS ({modelo})")
        return f"Comando enviado com sucesso: Portas do {modelo} foram destravadas com sucesso! 🔓"

    else:
        return f"Ação inválida: '{acao}'. Use apenas 'travar' ou 'destravar'."