import json
import logging
import math
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
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


# ═══════════════════════════════════════════════════════════════════════
# GERENCIADOR DE ROTAS AVANCADO
# ═══════════════════════════════════════════════════════════════════════

# Mapeamento de tipos de lugar (Google Places) para tempo de permanencia
_TEMPO_POR_TIPO: Dict[str, int] = {
    "museum": 120,            # Museus: 2h
    "art_gallery": 90,        # Galerias: 1.5h
    "park": 90,               # Parques: 1.5h
    "natural_feature": 90,    # Natureza: 1.5h
    "amusement_park": 180,    # Parques tematicos: 3h
    "zoo": 150,               # Zoos: 2.5h
    "aquarium": 90,           # Aquarios: 1.5h
    "church": 30,             # Igrejas: 30min
    "place_of_worship": 30,
    "restaurant": 60,         # Restaurantes: 1h
    "cafe": 45,               # Cafes: 45min
    "bar": 60,
    "shopping_mall": 120,     # Shopping: 2h
    "store": 45,
    "stadium": 120,
    "beach": 120,             # Praias: 2h
    "campground": 180,
    "tourist_attraction": 90, # Atracoes genericas: 1.5h
    "point_of_interest": 60,  # Default
}


def _fazer_requisicao_maps(url: str) -> dict:
    """Helper HTTP centralizado para todas as chamadas a APIs do Google Maps."""
    req = urllib.request.Request(url, headers={"User-Agent": "DAM-Assistant/1.0"})
    with urllib.request.urlopen(req, timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _obter_matrix_distancias(enderecos: List[str], modo: str = "driving") -> List[List[int]]:
    """
    P-001: Consulta a Distance Matrix API para todos os pares de enderecos.
    Retorna matriz [i][j] com duracao em segundos de i para j.
    Em caso de erro, retorna matriz com distancias euclidianas simuladas.
    """
    n = len(enderecos)
    # Matriz de fallback (distancias baseadas em ordem de insercao)
    fallback = [[abs(i - j) * 900 for j in range(n)] for i in range(n)]

    if not settings.GOOGLE_MAPS_API_KEY:
        return fallback

    try:
        enderecos_encoded = "|".join(urllib.parse.quote(e) for e in enderecos)
        url = (
            "https://maps.googleapis.com/maps/api/distancematrix/json?"
            f"origins={enderecos_encoded}&"
            f"destinations={enderecos_encoded}&"
            f"mode={modo}&"
            "departure_time=now&"
            f"key={settings.GOOGLE_MAPS_API_KEY}"
        )
        data = _fazer_requisicao_maps(url)

        if data.get("status") != "OK":
            logger.warning(f"Distance Matrix API status: {data.get('status')}")
            return fallback

        matrix = []
        for row in data.get("rows", []):
            linha = []
            for elem in row.get("elements", []):
                if elem.get("status") == "OK":
                    dur = elem.get("duration_in_traffic") or elem.get("duration", {})
                    linha.append(dur.get("value", 900))
                else:
                    linha.append(99999)
            matrix.append(linha)

        return matrix if matrix else fallback

    except Exception as e:
        logger.error(f"Erro na Distance Matrix API: {e}")
        return fallback


def _nearest_neighbor_tsp(duracao_matrix: List[List[int]], start: int, end: Optional[int]) -> List[int]:
    """
    P-002: Algoritmo Nearest Neighbor (heuristica gulosa para TSP).
    Retorna a ordem dos indices de visita (incluindo start e end se fornecido).
    """
    n = len(duracao_matrix)
    visitados = {start}
    rota = [start]
    atual = start

    nos_intermediarios = [i for i in range(n) if i != start and i != end]

    while nos_intermediarios:
        proximo = min(nos_intermediarios, key=lambda j: duracao_matrix[atual][j])
        rota.append(proximo)
        visitados.add(proximo)
        nos_intermediarios.remove(proximo)
        atual = proximo

    if end is not None and end != start:
        rota.append(end)

    return rota


def _estimar_tempo_no_local(nome_local: str) -> int:
    """
    P-004: Estima o tempo de permanencia em minutos usando a Places API.
    Fallback por categoria caso a API nao esteja disponivel.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return 60  # default 1h

    try:
        url = (
            "https://maps.googleapis.com/maps/api/place/textsearch/json?"
            f"query={urllib.parse.quote(nome_local)}&"
            f"key={settings.GOOGLE_MAPS_API_KEY}"
        )
        data = _fazer_requisicao_maps(url)

        if data.get("status") == "OK" and data.get("results"):
            tipos = data["results"][0].get("types", [])
            for tipo in tipos:
                if tipo in _TEMPO_POR_TIPO:
                    return _TEMPO_POR_TIPO[tipo]
    except Exception as e:
        logger.warning(f"Erro ao estimar tempo no local '{nome_local}': {e}")

    return 60  # default 1h


def _formatar_duracao(minutos_total: int) -> str:
    """Formata duracao em texto legivel (ex: 1h 30min ou 45min)."""
    if minutos_total >= 60:
        h = minutos_total // 60
        m = minutos_total % 60
        return f"{h}h {m:02d}min" if m > 0 else f"{h}h"
    return f"{minutos_total}min"


def otimizar_rota_multiplos_pontos(
    origem: str,
    paradas: str,
    destino: str,
    modo: str = "driving"
) -> str:
    """
    Calcula a ordem otimizada para visitar multiplas paradas entre uma origem e um destino,
    minimizando o tempo total de deslocamento. Usa a Google Maps Distance Matrix API.
    Ideal para roteiros de compras, entregas, passeios com varias paradas no dia.

    Args:
        origem (str): Ponto de partida (ex: 'casa', 'Av. Paulista, 1000'). Suporta apelidos.
        paradas (str): Paradas intermediarias separadas por '|' (ex: 'Mercado|Farmacia|Padaria').
        destino (str): Ponto de chegada final (ex: 'casa', 'Shopping Ibirapuera').
        modo (str): Modo de transporte: 'driving' (padrao), 'walking', 'transit', 'bicycling'.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return (
            "⚠️ A Google Maps API Key nao esta configurada.\n"
            "Para usar o otimizador de rotas, adicione GOOGLE_MAPS_API_KEY no .env."
        )

    # Resolve apelidos (P-008)
    origem_r = resolver_apelido_endereco(origem)
    destino_r = resolver_apelido_endereco(destino)
    paradas_lista = [p.strip() for p in paradas.split("|") if p.strip()]

    if not paradas_lista:
        return "Informe ao menos uma parada para otimizar a rota."

    # Monta lista completa: [origem, ...paradas, destino]
    todos = [origem_r] + paradas_lista + ([destino_r] if destino_r != origem_r else [])
    destino_idx = len(todos) - 1 if destino_r != origem_r else None

    try:
        matrix = _obter_matrix_distancias(todos, modo)

        # Otimiza a ordem das paradas (P-002): indices 1..N-1 sao as paradas
        rota_idx = _nearest_neighbor_tsp(matrix, start=0, end=destino_idx)

        # Calcula tempo de cada trecho e acumula
        linhas = [f"📍 *Rota Otimizada — {len(paradas_lista)} parada(s):*", ""]
        tempo_total_seg = 0
        passo = 1

        for i in range(len(rota_idx) - 1):
            de_idx = rota_idx[i]
            para_idx = rota_idx[i + 1]
            seg = matrix[de_idx][para_idx]
            tempo_total_seg += seg
            minutos = round(seg / 60)

            de_nome = todos[de_idx]
            para_nome = todos[para_idx]

            if i == 0:
                icone = "🚀"
            elif i == len(rota_idx) - 2:
                icone = "🏁"
            else:
                icone = f"{passo}️⃣"
                passo += 1

            linhas.append(
                f"{icone} *{de_nome}* → *{para_nome}*\n"
                f"   ↳ ⏱️ {_formatar_duracao(minutos)}"
            )

        tempo_total_min = round(tempo_total_seg / 60)
        linhas.append("")
        linhas.append(f"⏳ *Tempo total de deslocamento: {_formatar_duracao(tempo_total_min)}*")
        linhas.append(f"🚗 Modo: {modo}")

        return "\n".join(linhas)

    except Exception as e:
        logger.error(f"Erro ao otimizar rota: {e}")
        return "Erro ao calcular a rota otimizada. Verifique os enderecos e tente novamente."


def planejar_roteiro_viagem(
    pontos: str,
    dias: int,
    horas_por_dia: int = 8,
    cidade_base: str = ""
) -> str:
    """
    Distribui pontos turisticos em dias de viagem de forma inteligente, agrupando
    pontos proximos geograficamente e respeitando o budget de horas diarias.
    Estima o tempo de permanencia em cada atracaoo usando a Google Places API.
    Ideal para planejar roteiros com multiplos dias em uma cidade ou regiao.

    Args:
        pontos (str): Atracoes separadas por '|' (ex: 'Museu do Ipiranga|Parque Ibirapuera|Pinacoteca').
        dias (int): Quantidade de dias disponiveis para o roteiro.
        horas_por_dia (int): Budget de horas uteis por dia de turismo (padrao: 8h).
        cidade_base (str): Cidade ou regiao para contexto de busca (ex: 'Sao Paulo'). Opcional.
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return (
            "⚠️ A Google Maps API Key nao esta configurada.\n"
            "Para usar o planejador de roteiro, adicione GOOGLE_MAPS_API_KEY no .env."
        )

    pontos_lista = [p.strip() for p in pontos.split("|") if p.strip()]

    if not pontos_lista:
        return "Informe ao menos um ponto para planejar o roteiro."

    if dias < 1:
        return "O numero de dias deve ser ao menos 1."

    budget_minutos = horas_por_dia * 60

    # 1. Estima tempo de permanencia em cada ponto (P-004)
    try:
        contexto = f" {cidade_base}" if cidade_base else ""
        tempos = {p: _estimar_tempo_no_local(p + contexto) for p in pontos_lista}
    except Exception as e:
        logger.error(f"Erro ao estimar tempos: {e}")
        tempos = {p: 60 for p in pontos_lista}

    # 2. Obtem matriz de distancias entre todos os pontos (P-006)
    try:
        matrix = _obter_matrix_distancias(pontos_lista)
    except Exception as e:
        logger.error(f"Erro na matrix de distancias para roteiro: {e}")
        n = len(pontos_lista)
        matrix = [[abs(i - j) * 900 for j in range(n)] for i in range(n)]

    # 3. Ordena os pontos geograficamente via Nearest Neighbor (P-006)
    ordem_idx = _nearest_neighbor_tsp(matrix, start=0, end=None)
    pontos_ordenados = [pontos_lista[i] for i in ordem_idx]

    # 4. Distribui os pontos pelos dias (P-005): greedy por budget
    dias_roteiro: List[List[dict]] = [[] for _ in range(dias)]
    dia_atual = 0
    minutos_usados = 0

    for ponto in pontos_ordenados:
        tempo_ponto = tempos[ponto]
        # Estima deslocamento ate o proximo ponto no mesmo dia
        if dias_roteiro[dia_atual]:
            ultimo_idx = pontos_lista.index(dias_roteiro[dia_atual][-1]["nome"])
            ponto_idx = pontos_lista.index(ponto)
            deslocamento = round(matrix[ultimo_idx][ponto_idx] / 60)
        else:
            deslocamento = 0

        tempo_necessario = tempo_ponto + deslocamento

        # Se nao couber no dia atual, avanca para o proximo
        if minutos_usados + tempo_necessario > budget_minutos and dias_roteiro[dia_atual]:
            dia_atual = min(dia_atual + 1, dias - 1)
            minutos_usados = 0
            deslocamento = 0  # Primeiro ponto do dia nao tem deslocamento

        dias_roteiro[dia_atual].append({
            "nome": ponto,
            "tempo_local": tempo_ponto,
            "deslocamento": deslocamento
        })
        minutos_usados += tempo_ponto + deslocamento

    # 5. Monta o texto do roteiro
    linhas = [
        f"🗺️ *Roteiro de {dias} dia(s) — {len(pontos_lista)} atracoes*",
        f"⏰ Budget diario: {horas_por_dia}h por dia",
        ""
    ]

    for d_idx, pontos_do_dia in enumerate(dias_roteiro):
        if not pontos_do_dia:
            continue

        total_dia = sum(p["tempo_local"] + p["deslocamento"] for p in pontos_do_dia)
        linhas.append(f"📅 *Dia {d_idx + 1}* _(~{_formatar_duracao(total_dia)} no total)_")

        for i, p in enumerate(pontos_do_dia):
            icone = "📍" if i == 0 else "➡️"
            deslocamento_txt = f" _(+{_formatar_duracao(p['deslocamento'])} de deslocamento)_" if p["deslocamento"] > 0 else ""
            linhas.append(
                f"  {icone} *{p['nome']}*{deslocamento_txt}\n"
                f"     ↳ 🕐 Tempo estimado no local: {_formatar_duracao(p['tempo_local'])}"
            )

        linhas.append("")

    linhas.append("💡 _Ordem otimizada por proximidade geografica._")
    return "\n".join(linhas)
