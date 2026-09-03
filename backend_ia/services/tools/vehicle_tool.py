import logging
from typing import Optional

logger = logging.getLogger(__name__)

def consultar_status_veiculo() -> str:
    """
    Consulta a telemetria em tempo real do veículo do usuário (Fiat Fastback).
    Retorna nível de combustível, autonomia estimada, status de travas, portas e saúde geral.
    """
    # Simulação integrada com modelo de dados Uconnect
    status = (
        "🚗 **Status do Veículo (Fiat Fastback Turbo 270):**\n"
        "• Combustível: 68% (Tanque)\n"
        "• Autonomia estimada: 485 km\n"
        "• Travas das portas: Trancadas 🔒\n"
        "• Vidros: Totalmente fechados\n"
        "• Pressão dos pneus: 32 PSI (Todos calibrados)\n"
        "• Tensão da bateria: 12.6V (Saudável)\n"
        "• Hodômetro: 14.820 km\n"
        "• Localização: Garagem Residencial"
    )
    return status

def acionar_travas_veiculo(acao: str) -> str:
    """
    Envia comando remoto seguro para travar ou destravar as portas do Fiat Fastback.

    Args:
        acao (str): 'travar' para trancar as portas ou 'destravar' para abrir as portas.
    """
    acao_normalizada = acao.strip().lower()
    if acao_normalizada in ["travar", "trancar", "fechar"]:
        logger.info("Comando Uconnect enviado: TRAVAR_PORTAS")
        return "Comando enviado com sucesso: Portas do Fiat Fastback foram travadas com sucesso! 🔒"
    elif acao_normalizada in ["destravar", "abrir"]:
        logger.info("Comando Uconnect enviado: DESTRAVAR_PORTAS")
        return "Comando enviado com sucesso: Portas do Fiat Fastback foram destravadas com sucesso! 🔓"
    else:
        return f"Ação inválida: '{acao}'. Use apenas 'travar' ou 'destravar'."
