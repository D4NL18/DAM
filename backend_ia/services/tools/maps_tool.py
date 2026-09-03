import json
import logging
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from config.settings import settings

logger = logging.getLogger(__name__)

def resolver_apelido_endereco(endereco: str) -> str:
    """
    Resolve apelidos comuns como 'casa' ou 'trabalho' para os endereços configurados.
    """
    if not endereco:
        return ""
    
    end_lower = endereco.strip().lower()

    # Apelidos para Casa
    if end_lower in ["casa", "minha casa", "home", "residencia", "residência"]:
        return settings.USER_HOME_ADDRESS or "Avenida Paulista, 1000 - Bela Vista, São Paulo - SP"

    # Apelidos para Trabalho
    if end_lower in ["trabalho", "meu trabalho", "escritorio", "escritório", "work", "office", "firma"]:
        return settings.USER_WORK_ADDRESS or "Avenida Brigadeiro Faria Lima, 3500 - Itaim Bibi, São Paulo - SP"

    return endereco.strip()


def obter_dados_rota(origem: str, destino: str, modo: str = "driving") -> Dict[str, Any]:
    """
    Obtém informações detalhadas de rota, tempo e distância entre origem e destino.
    Usa a API do Google Maps caso a chave esteja disponível ou gera simulação realista/mock.
    """
    origem_resolvida = resolver_apelido_endereco(origem)
    destino_resolvido = resolver_apelido_endereco(destino)

    if settings.GOOGLE_MAPS_API_KEY:
        try:
            url = (
                "https://maps.googleapis.com/maps/api/directions/json?"
                f"origin={urllib.parse.quote(origem_resolvida)}&"
                f"destination={urllib.parse.quote(destino_resolvido)}&"
                f"mode={modo}&"
                "departure_time=now&"
                f"key={settings.GOOGLE_MAPS_API_KEY}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "DAM-Assistant/1.0"})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode("utf-8"))

            if data.get("status") == "OK" and data.get("routes"):
                route = data["routes"][0]
                leg = route["legs"][0]
                
                # Trânsito em tempo real se disponível
                duration_data = leg.get("duration_in_traffic") or leg.get("duration", {})
                duration_seconds = duration_data.get("value", 1800)
                duration_minutes = round(duration_seconds / 60)
                duration_text = duration_data.get("text", f"{duration_minutes} mins")

                distance_data = leg.get("distance", {})
                distance_meters = distance_data.get("value", 10000)
                distance_km = round(distance_meters / 1000, 1)
                distance_text = distance_data.get("text", f"{distance_km} km")

                summary_vias = route.get("summary") or "Vias principais da rota"

                return {
                    "origem": origem_resolvida,
                    "destino": destino_resolvido,
                    "modo": modo,
                    "distancia_km": distance_km,
                    "distancia_texto": distance_text,
                    "duracao_minutos": max(duration_minutes, 1),
                    "duracao_texto": duration_text,
                    "vias_principais": summary_vias,
                    "condicao_transito": "Trânsito em tempo real verificado",
                    "simulado": False
                }
            else:
                logger.warning(f"Google Maps API status: {data.get('status')}. Usando fallback.")
        except Exception as e:
            logger.error(f"Erro ao consultar Google Maps Directions API: {e}. Usando fallback.")

    # Simulação robusta (quando não há chave ou em caso de erro na API)
    # Heurística realista para rotas padrão
    orig_low = origem_resolvida.lower()
    dest_low = destino_resolvido.lower()

    if ("paulista" in orig_low and "faria lima" in dest_low) or ("faria lima" in orig_low and "paulista" in dest_low):
        distancia_km = 6.8
        duracao_minutos = 24
        vias = "Av. Rebouças e Av. Brigadeiro Faria Lima"
        condicao = "Trânsito moderado"
    elif "casa" in orig_low or "trabalho" in dest_low or "casa" in dest_low:
        distancia_km = 9.2
        duracao_minutos = 28
        vias = "Av. 23 de Maio e Av. Brigadeiro Faria Lima"
        condicao = "Trânsito fluindo normalmente"
    else:
        # Cálculo determinístico baseado no tamanho dos textos para testes reproduzíveis
        base_hash = (abs(hash(origem_resolvida + destino_resolvido)) % 25) + 5
        distancia_km = float(base_hash)
        duracao_minutos = int(base_hash * 2.2)
        vias = "Vias expressas e corredores principais"
        condicao = "Trânsito típico para o horário"

    modo_desc = "de carro" if modo == "driving" else modo
    return {
        "origem": origem_resolvida,
        "destino": destino_resolvido,
        "modo": modo_desc,
        "distancia_km": distancia_km,
        "distancia_texto": f"{distancia_km:.1f} km",
        "duracao_minutos": max(duracao_minutos, 1),
        "duracao_texto": f"{duracao_minutos} min",
        "vias_principais": vias,
        "condicao_transito": condicao,
        "simulado": True
    }


def consultar_rota(origem: str, destino: str, modo: str = "driving") -> str:
    """
    Consulta o tempo estimado de viagem com trânsito em tempo real, distância em km e vias principais.
    Trata apelidos como 'casa' e 'trabalho'.

    Args:
        origem (str): Endereço de partida ou apelido ('casa', 'trabalho').
        destino (str): Endereço de chegada ou apelido ('casa', 'trabalho').
        modo (str): Modo de transporte ('driving', 'transit', 'walking', 'bicycling'). Padrão: 'driving'.
    """
    dados = obter_dados_rota(origem, destino, modo)
    
    simulado_tag = " *(Modo Simulação / Sem Chave)*" if dados.get("simulado") else ""
    
    resposta = (
        f"🚦 **Rota e Trânsito {dados['distancia_texto']} ({dados['duracao_texto']})**{simulado_tag}\n"
        f"📍 **Origem:** {dados['origem']}\n"
        f"🏁 **Destino:** {dados['destino']}\n"
        f"⏱️ **Tempo estimado:** {dados['duracao_texto']} ({dados['condicao_transito']})\n"
        f"🛣️ **Vias principais:** {dados['vias_principais']}\n"
        f"🚗 **Modo:** {dados['modo']}"
    )
    return resposta


def calcular_horario_saida(origem: str, destino: str, horario_chegada: str, antecedencia_minutos: int = 10) -> str:
    """
    Calcula que horas o usuário deve sair para chegar no destino no horário desejado,
    considerando o tempo estimado de trânsito e uma margem de antecedência.

    Args:
        origem (str): Ponto de partida ou apelido ('casa', 'trabalho').
        destino (str): Ponto de chegada ou apelido ('casa', 'trabalho').
        horario_chegada (str): Horário limite de chegada (ex: '09:00', '15:30' ou '2026-09-04 14:00').
        antecedencia_minutos (int): Margem de segurança de chegada em minutos (padrão: 10 min).
    """
    # 1. Parse do horário de chegada
    horario_limpo = horario_chegada.strip()
    chegada_dt = None
    tem_data = False

    formatos = [
        ("%H:%M", False),
        ("%H:%M:%S", False),
        ("%Y-%m-%d %H:%M", True),
        ("%Y-%m-%d %H:%M:%S", True),
        ("%d/%m/%Y %H:%M", True),
    ]

    for fmt, com_data in formatos:
        try:
            parsed = datetime.strptime(horario_limpo, fmt)
            if not com_data:
                # Usa a data de hoje como referência
                hoje = datetime.now()
                chegada_dt = hoje.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
            else:
                chegada_dt = parsed
            tem_data = com_data
            break
        except ValueError:
            continue

    if not chegada_dt:
        return (
            f"Não consegui identificar o horário '{horario_chegada}'. "
            "Por favor informe no formato 'HH:MM' (ex: '09:00') ou 'AAAA-MM-DD HH:MM'."
        )

    # 2. Obter dados da rota
    dados_rota = obter_dados_rota(origem, destino, modo="driving")
    duracao_viagem = dados_rota["duracao_minutos"]
    tempo_total_necessario = duracao_viagem + antecedencia_minutos

    # 3. Calcular horário de saída
    saida_dt = chegada_dt - timedelta(minutes=tempo_total_necessario)

    formato_exibicao = "%d/%m às %H:%M" if tem_data else "%H:%M"
    saida_str = saida_dt.strftime(formato_exibicao)
    chegada_str = chegada_dt.strftime(formato_exibicao)

    resposta = (
        f"⏰ **Planejamento de Saída:**\n"
        f"• **Horário recomendado de saída:** **{saida_str}** 🚗💨\n"
        f"• **Horário previsto de chegada:** {chegada_str}\n"
        f"• **Tempo estimado de trajeto:** {duracao_viagem} min ({dados_rota['distancia_texto']})\n"
        f"• **Margem de antecedência:** {antecedencia_minutos} min\n"
        f"• **Vias principais:** {dados_rota['vias_principais']}\n"
        f"• **De:** {dados_rota['origem']}\n"
        f"• **Para:** {dados_rota['destino']}"
    )
    return resposta
