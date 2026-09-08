import logging
import urllib.request
import urllib.parse
import json
import gzip
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
from config.timezone import TZ_BRASILIA

logger = logging.getLogger(__name__)

# Mapeamento de nomes populares para slugs exatos do Liquipedia
LIQUIPEDIA_ALIASES = {
    "furia": "FURIA",
    "mibr": "MIBR",
    "pain": "PaiN_Gaming",
    "imperial": "Imperial_Esports",
    "vitality": "Team_Vitality",
    "navi": "Natus_Vincere",
    "faze": "FaZe_Clan",
    "liquid": "Team_Liquid",
    "spirit": "Team_Spirit",
    "g2": "G2_Esports",
    "mouz": "MOUZ",
    "astralis": "Astralis",
    "complexity": "Complexity_Gaming",
    "virtus.pro": "Virtus.pro",
    "vp": "Virtus.pro",
    "heroic": "HEROIC",
    "eternal fire": "Eternal_Fire"
}

# Fallback estático caso a rede esteja indisponível
JOGOS_FALLBACK = [
    {"evento": "BLAST Open Fall 2026 - Playoffs (QF)", "horario": "04/09/2026 às 13:50", "time_a": "FURIA", "time_b": "Team Vitality", "formato": "MD3", "status": "Ao Vivo / Em Andamento"},
    {"evento": "FISSURE Playground #3 - Group B", "horario": "08/09/2026 às 02:30", "time_a": "FURIA", "time_b": "GamerLegion", "formato": "MD3", "status": "Agendado"},
    {"evento": "ESL Pro League Season 21", "horario": "Hoje às 17:30", "time_a": "MIBR", "time_b": "Complexity", "formato": "MD3", "status": "Agendado"},
    {"evento": "BLAST Premier Spring Final", "horario": "Amanhã às 11:00", "time_a": "paiN", "time_b": "Vitality", "formato": "MD3", "status": "Agendado"}
]

def obter_partidas_estruturadas_cs2(time: Optional[str] = "FURIA") -> list[dict]:
    """
    Retorna uma lista de partidas agendadas estruturadas para o time solicitado.
    Utiliza a agenda oficial do Liquipedia com fallback para radar em cache.
    """
    partidas_estruturadas = []
    time_query = time.strip() if time else "FURIA"
    time_upper = time_query.upper()

    # 1. Tentar via Liquipedia
    try:
        agenda = _buscar_agenda_liquipedia(time_query)
        for p in agenda:
            t1 = p.get("time1", "")
            t2 = p.get("time2", "")
            horario_completo = p.get("horario", "")
            torneio = p.get("torneio", "Torneio de CS2")

            hora_str = "12:00"
            data_str = ""
            hora_int = 12
            match_hora = re.search(r'(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}:\d{2})', horario_completo)
            if match_hora:
                data_str = match_hora.group(1)
                hora_str = match_hora.group(2)
                try:
                    hora_int = int(hora_str.split(":")[0])
                except Exception:
                    hora_int = 12

            partidas_estruturadas.append({
                "time_a": t1,
                "time_b": t2,
                "campeonato": torneio,
                "horario": hora_str,
                "horario_completo": horario_completo,
                "data_str": data_str,
                "hora_int": hora_int,
                "status": "AGENDADO",
                "placar": None,
                "vencedor": None
            })
    except Exception as e:
        logger.warning(f"Falha ao obter partidas estruturadas do Liquipedia: {e}")

    if partidas_estruturadas:
        return partidas_estruturadas

    # 2. Fallback de cache estruturado
    for j in JOGOS_FALLBACK:
        t_a = j.get("time_a", "")
        t_b = j.get("time_b", "")
        if time_upper in t_a.upper() or time_upper in t_b.upper():
            horario_raw = j.get("horario", "")
            hora_str = "12:00"
            data_str = ""
            hora_int = 12

            match_data_hora = re.search(r'(\d{2}/\d{2}/\d{4})\s+às\s+(\d{2}:\d{2})', horario_raw)
            match_hoje = re.search(r'(Hoje|Amanhã)\s+às\s+(\d{2}:\d{2})', horario_raw, re.IGNORECASE)

            if match_data_hora:
                data_str = match_data_hora.group(1)
                hora_str = match_data_hora.group(2)
            elif match_hoje:
                data_str = match_hoje.group(1)
                hora_str = match_hoje.group(2)

            try:
                hora_int = int(hora_str.split(":")[0])
            except Exception:
                hora_int = 12

            partidas_estruturadas.append({
                "time_a": t_a,
                "time_b": t_b,
                "campeonato": j.get("evento", "CS2"),
                "horario": hora_str,
                "horario_completo": horario_raw,
                "data_str": data_str,
                "hora_int": hora_int,
                "status": "AGENDADO",
                "placar": None,
                "vencedor": None
            })

    return partidas_estruturadas

_LIQUIPEDIA_CACHE: dict = {}

def _buscar_agenda_liquipedia(team_name: Optional[str] = None) -> list[dict]:
    """Consulta as próximas partidas agendadas através da API do Liquipedia CS2."""
    nome_limpo = team_name.lower().strip() if team_name else "furia"
    page_name = LIQUIPEDIA_ALIASES.get(nome_limpo, team_name.strip() if team_name else "FURIA")
    
    # Cache em memória de 60s para cumprir limites da API do Liquipedia (1 req / 30s)
    now_ts = datetime.now(timezone.utc).timestamp()
    if page_name in _LIQUIPEDIA_CACHE:
        cached_ts, cached_data = _LIQUIPEDIA_CACHE[page_name]
        if (now_ts - cached_ts) < 60:
            return cached_data

    url = f"https://liquipedia.net/counterstrike/api.php?action=parse&page={urllib.parse.quote(page_name)}&format=json"
    headers = {
        "User-Agent": "DAMBot/1.0 (https://github.com/D4NL18/DAM; danielmarinho@gmail.com)",
        "Accept-Encoding": "gzip"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = gzip.decompress(r.read()).decode("utf-8")
            data = json.loads(raw)
            html = data.get("parse", {}).get("text", {}).get("*", "")
    except Exception as e:
        logger.warning(f"Falha ao consultar agenda no Liquipedia ({page_name}): {e}")
        return []

    partidas = []
    matches_raw = html.split('data-timestamp="')

    for block in matches_raw[1:]:
        ts_str = block.split('"')[0]
        if not ts_str.isdigit():
            continue
        ts = int(ts_str)
        # Partidas a partir de agora (tolerância de até 3 horas atrás para partidas ao vivo)
        if ts < (now_ts - 10800):
            continue

        dt = datetime.fromtimestamp(ts, tz=TZ_BRASILIA)
        horario_br = dt.strftime("%d/%m/%Y às %H:%M")

        # Torneio e Etapa
        torneio_match = re.search(r'class="match-info-tournament-name"[^>]*>.*?<span>([^<]+)</span>', block, re.DOTALL)
        torneio = torneio_match.group(1).strip() if torneio_match else "Torneio de CS2"

        stage_match = re.search(r'class="match-info-stage">([^<]+)</span>', block)
        etapa = f" ({stage_match.group(1).strip()})" if stage_match else ""

        # Times
        teams = re.findall(r'<div class="match-info-opponent-identity">.*?title="([^"]+)"', block, re.DOTALL)
        t1 = teams[0] if len(teams) > 0 else (team_name or "Time A")
        t2 = teams[1] if len(teams) > 1 else "Adversário"

        partidas.append({
            "time1": t1,
            "time2": t2,
            "torneio": f"{torneio}{etapa}",
            "horario": horario_br
        })
        if len(partidas) >= 4:
            break

    _LIQUIPEDIA_CACHE[page_name] = (now_ts, partidas)
    return partidas

def _buscar_partidas_api(time: Optional[str] = None) -> Optional[str]:
    """Consulta histórico recente na API aberta de CS2."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DAM/1.0"}

    if time:
        time_clean = time.strip()
        url_team = f"https://api.csapi.de/teams/?name={urllib.parse.quote(time_clean)}"
        req = urllib.request.Request(url_team, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            teams = json.loads(resp.read().decode())

        if not teams:
            return None

        team = teams[0]
        team_id = team["id"]

        url_hist = f"https://api.csapi.de/teams/{team_id}/matchhistory"
        req_hist = urllib.request.Request(url_hist, headers=headers)
        with urllib.request.urlopen(req_hist, timeout=4) as resp_hist:
            matches = json.loads(resp_hist.read().decode())

        if not matches:
            return None

        resp_text = ""
        for m in matches[:3]:
            t1 = m.get("team1", {})
            t2 = m.get("team2", {})
            evento = m.get("event", "Torneio Profissional")
            best_of = m.get("best_of", 3)
            data_jogo = m.get("date", "Recente")
            winner = m.get("winner", {}).get("name") if m.get("winner") else None
            
            placar = f"{t1.get('score', 0)} x {t2.get('score', 0)}"
            status = f"Vitória: {winner} ({placar})" if winner else f"Placar: {placar}"
            resp_text += f"• [{evento}] {t1.get('name')} vs {t2.get('name')} (MD{best_of}) - {data_jogo} | {status}\n"
        return resp_text

    url_latest = "https://api.csapi.de/matches/latest"
    req_latest = urllib.request.Request(url_latest, headers=headers)
    with urllib.request.urlopen(req_latest, timeout=4) as resp_latest:
        latest = json.loads(resp_latest.read().decode())

    if not latest:
        return None

    resp_text = ""
    for m in latest[:3]:
        t1 = m.get("team1", {})
        t2 = m.get("team2", {})
        evento = m.get("event", "Torneio Profissional")
        best_of = m.get("best_of", 3)
        data_jogo = m.get("date", "Recente")
        winner = m.get("winner", {}).get("name") if m.get("winner") else None
        status = f"Vitória: {winner}" if winner else f"{t1.get('score', 0)} x {t2.get('score', 0)}"
        resp_text += f"• [{evento}] {t1.get('name')} vs {t2.get('name')} (MD{best_of}) - {data_jogo} | {status}\n"
    return resp_text

def consultar_jogos_cs2(time: Optional[str] = None) -> str:
    """
    Consulta os próximos jogos agendados em tempo real (Liquipedia) e os últimos resultados do cenário competitivo de Counter-Strike 2.

    Args:
        time (str, optional): Nome de qualquer time (ex: 'FURIA', 'FaZe', 'NAVI', 'Liquid', 'MIBR', 'paiN', 'Imperial', 'Spirit').
    """
    time_label = f"'{time}'" if time else "em Destaque"
    resp_blocos = []

    # 1. Buscar Próximas Partidas Agendadas (Liquipedia com fallback para radar estruturado)
    partidas_futuras = []
    try:
        agenda = _buscar_agenda_liquipedia(time)
        if agenda:
            partidas_futuras = agenda
    except Exception as e:
        logger.warning(f"Falha ao consultar agenda no Liquipedia: {e}")

    if not partidas_futuras:
        partidas_radar = obter_partidas_estruturadas_cs2(time)
        if partidas_radar:
            for p in partidas_radar:
                partidas_futuras.append({
                    "torneio": p.get("evento", "CS2"),
                    "time1": p.get("time_a", "Time A"),
                    "time2": p.get("time_b", "Time B"),
                    "horario": p.get("horario", ""),
                    "status": p.get("status", "Agendado")
                })

    if partidas_futuras:
        bloco_agenda = f"📅 **Próximas Partidas Agendadas / Ao Vivo:**\n"
        for p in partidas_futuras:
            status_txt = f" [{p.get('status')}]" if p.get('status') else ""
            bloco_agenda += f"• [{p['torneio']}] **{p['time1']}** vs **{p['time2']}** - ⏰ **{p['horario']}** (Horário de Brasília){status_txt}\n"
        resp_blocos.append(bloco_agenda)

    # 2. Buscar Histórico Recente de Resultados
    try:
        historico = _buscar_partidas_api(time)
        if historico:
            bloco_hist = f"🏁 **Últimos Resultados Registrados:**\n" + historico
            resp_blocos.append(bloco_hist)
    except Exception as e:
        logger.warning(f"Falha ao consultar histórico de partidas: {e}")

    if resp_blocos:
        cabecalho = f"🔫 **Counter-Strike 2 — Agenda & Resultados para {time_label}:**\n\n"
        return cabecalho + "\n".join(resp_blocos)

    # 3. Fallback de resiliência caso ambas as fontes estejam offline
    time_filtro = time.strip().upper() if time else None
    if time_filtro:
        filtrados = [j for j in JOGOS_FALLBACK if time_filtro in j["time_a"].upper() or time_filtro in j["time_b"].upper()]
        if not filtrados:
            return f"Não encontrei partidas agendadas ou recentes para o time '{time}' no momento."
        
        resp = f"🔫 **Partidas de Counter-Strike 2 para '{time}' (Radar Cache):**\n"
        for j in filtrados:
            resp += f"• [{j['evento']}] {j['time_a']} vs {j['time_b']} ({j['formato']}) - {j['horario']} (Horário de Brasília) | {j['status']}\n"
        return resp

    resp = "🔫 **Próximos Jogos em Destaque no Counter-Strike 2 (Radar Cache):**\n"
    for j in JOGOS_FALLBACK:
        resp += f"• [{j['evento']}] {j['time_a']} vs {j['time_b']} ({j['formato']}) - {j['horario']} (Horário de Brasília) | {j['status']}\n"
    return resp
