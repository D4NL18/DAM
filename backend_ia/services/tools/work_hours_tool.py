import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union
from config import firebase

logger = logging.getLogger(__name__)

# Fallback em memória caso Firestore não esteja inicializado
_MEMORY_WORK_HOURS: List[Dict[str, Any]] = []

def _limpar_dados_memoria():
    """Auxiliar para testes unitários resetarem a memória."""
    _MEMORY_WORK_HOURS.clear()

def _parse_time_to_minutes(time_str: str) -> int:
    """Converte 'HH:MM' em minutos do dia."""
    parts = time_str.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

def formatar_horas_minutos(horas_float: float, incluir_sinal: bool = False) -> str:
    """Formata valor em float (ex: 8.5) para string legível (ex: '8h30min')."""
    total_minutos = int(round(abs(horas_float) * 60))
    h = total_minutos // 60
    m = total_minutos % 60

    prefixo = ""
    if incluir_sinal:
        if horas_float > 0.001:
            prefixo = "+"
        elif horas_float < -0.001:
            prefixo = "-"

    if m == 0:
        return f"{prefixo}{h}h00"
    return f"{prefixo}{h}h{m:02d}min"

def interpretar_horas(horas_input: Union[str, List[str], float, int]) -> float:
    """
    Interpreta deterministicamente valores de horas flexíveis em formatos variados:
    - Decimais: '8.5h', '8,5', 8.5 -> 8.5
    - Horas e minutos: '8h', '7h30', '9h15', '7h30min', '7:30' -> 8.0, 7.5, 9.25, 7.5, 7.5
    - Batidas de ponto: ['09:00', '12:00', '13:00', '18:00'] ou '09:00, 12:00, 13:00, 18:00' -> 8.0
    """
    if isinstance(horas_input, (int, float)):
        return float(horas_input)

    # Se for lista de batidas
    if isinstance(horas_input, list):
        # Filtra horários no formato HH:MM
        timestamps = [t.strip() for t in horas_input if isinstance(t, str) and re.match(r'^\d{1,2}:\d{2}$', t.strip())]
        if len(timestamps) >= 2:
            total_min = 0
            for i in range(0, len(timestamps) - 1, 2):
                t1 = _parse_time_to_minutes(timestamps[i])
                t2 = _parse_time_to_minutes(timestamps[i + 1])
                if t2 >= t1:
                    total_min += (t2 - t1)
                else:
                    total_min += (t2 + 1440 - t1)
            return round(total_min / 60.0, 2)
        elif len(timestamps) == 1:
            return round(_parse_time_to_minutes(timestamps[0]) / 60.0, 2)
        else:
            raise ValueError(f"Lista de batidas inválida ou vazia: {horas_input}")

    texto = str(horas_input).strip()

    # Se a string contém uma lista formatada ex: "['09:00', '12:00', ...]"
    # ou múltiplas ocorrências de HH:MM separadas por vírgula, traço, etc.
    hh_mm_matches = re.findall(r'\b\d{1,2}:\d{2}\b', texto)
    if len(hh_mm_matches) >= 2:
        total_min = 0
        for i in range(0, len(hh_mm_matches) - 1, 2):
            t1 = _parse_time_to_minutes(hh_mm_matches[i])
            t2 = _parse_time_to_minutes(hh_mm_matches[i + 1])
            if t2 >= t1:
                total_min += (t2 - t1)
            else:
                total_min += (t2 + 1440 - t1)
        return round(total_min / 60.0, 2)
    elif len(hh_mm_matches) == 1 and (":" in texto and not any(k in texto.lower() for k in ["h", "min"])):
        # Único horário no formato HH:MM (ex: "7:30" ou "8:00") representando duração
        parts = hh_mm_matches[0].split(":")
        return round(int(parts[0]) + int(parts[1]) / 60.0, 2)

    # Formato horas e minutos (ex: "7h30", "7h30min", "9h15", "8h 45m")
    hm_match = re.match(r'^(\d+)\s*h\s*(\d{1,2})(?:\s*(?:m|min|mins))?$', texto, re.IGNORECASE)
    if hm_match:
        h = int(hm_match.group(1))
        m = int(hm_match.group(2))
        return round(h + (m / 60.0), 2)

    # Formato apenas minutos (ex: "45m", "45min")
    m_only_match = re.match(r'^(\d+)\s*(?:m|min|mins|minutos?)$', texto, re.IGNORECASE)
    if m_only_match:
        m = int(m_only_match.group(1))
        return round(m / 60.0, 2)

    # Formato apenas horas ou decimal com h (ex: "8h", "8.5h", "8,5h", "8 hrs")
    h_match = re.match(r'^(\d+(?:[.,]\d+)?)\s*(?:h|hrs|horas?)?$', texto, re.IGNORECASE)
    if h_match:
        val_str = h_match.group(1).replace(',', '.')
        return round(float(val_str), 2)

    raise ValueError(f"Não foi possível interpretar o formato de horas: '{texto}'")

def calcular_saldo_jornada(horas_trabalhadas_texto: str, meta_diaria_horas: float = 8.0) -> str:
    """
    Calcula o saldo de jornada diária comparando as horas trabalhadas com a meta diária.

    Args:
        horas_trabalhadas_texto (str): String com as horas trabalhadas (ex: '8h', '7h30', '9h15', '8.5h', ou '09:00, 18:00').
        meta_diaria_horas (float): Meta diária de horas a cumprir (padrão: 8.0).
    """
    try:
        horas_trabalhadas = interpretar_horas(horas_trabalhadas_texto)
    except Exception as e:
        return f"Erro ao interpretar horas: {e}"

    saldo = round(horas_trabalhadas - meta_diaria_horas, 2)
    horas_str = formatar_horas_minutos(horas_trabalhadas)
    meta_str = formatar_horas_minutos(meta_diaria_horas)
    saldo_str = formatar_horas_minutos(saldo, incluir_sinal=True)

    if saldo > 0.001:
        status = "Crédito (Horas extras a receber/armazenar)"
    elif saldo < -0.001:
        status = "Débito (Saldo devedor a compensar)"
    else:
        status = "Meta cumprida exatamente"

    return (
        f"⏱️ **Saldo de Jornada Diária:**\n"
        f"• Horas Trabalhadas: **{horas_str}**\n"
        f"• Meta Diária: **{meta_str}**\n"
        f"• Balanço Líquido: **{saldo_str}** ({status})"
    )

def calcular_fechamento_semanal(registros_dias: Any, meta_semanal_horas: float = 40.0) -> str:
    """
    Calcula o fechamento semanal do banco de horas acumulando os registros diários.

    Args:
        registros_dias: Lista de dicionários ou JSON string representando cada dia trabalhado (ex: [{'dia': 'Segunda', 'horas': '8h30'}]).
        meta_semanal_horas (float): Meta total semanal contratual (padrão: 40.0).
    """
    if isinstance(registros_dias, str):
        try:
            import json
            registros_dias = json.loads(registros_dias)
        except Exception:
            pass

    if not registros_dias or not isinstance(registros_dias, list):
        return "Erro: Nenhum registro diário válido fornecido para o fechamento semanal."

    total_trabalhado = 0.0
    linhas_dias = []

    for idx, reg in enumerate(registros_dias, 1):
        nome_dia = reg.get("dia") or reg.get("data") or f"Dia {idx}"
        horas_raw = reg.get("horas") if "horas" in reg else reg.get("horas_trabalhadas_texto") or reg.get("horas_trabalhadas", 0)
        meta_dia = float(reg.get("meta_diaria_horas") or reg.get("meta_diaria") or 8.0)

        try:
            horas_dia = interpretar_horas(horas_raw)
        except Exception as e:
            return f"Erro ao processar o dia '{nome_dia}': {e}"

        total_trabalhado += horas_dia
        saldo_dia = round(horas_dia - meta_dia, 2)
        saldo_dia_str = formatar_horas_minutos(saldo_dia, incluir_sinal=True)
        duracao_dia_str = formatar_horas_minutos(horas_dia)

        linhas_dias.append(f"• **{nome_dia}**: {duracao_dia_str} (Saldo: {saldo_dia_str})")

    saldo_semanal = round(total_trabalhado - meta_semanal_horas, 2)
    total_str = formatar_horas_minutos(total_trabalhado)
    meta_str = formatar_horas_minutos(meta_semanal_horas)
    saldo_str = formatar_horas_minutos(saldo_semanal, incluir_sinal=True)

    if saldo_semanal > 0.001:
        resumo_status = "Crédito positivo a receber / armazenar no banco de horas 🟢"
    elif saldo_semanal < -0.001:
        resumo_status = "Saldo devedor negativo a compensar 🔴"
    else:
        resumo_status = "Meta cumprida perfeitamente (saldo zerado) ⚪"

    return (
        f"📅 **Fechamento Semanal de Banco de Horas**\n\n"
        f"📊 **Detalhamento Diário:**\n" + "\n".join(linhas_dias) + "\n\n"
        f"• **Total Acumulado:** **{total_str}**\n"
        f"• **Meta Semanal:** **{meta_str}**\n"
        f"• **Balanço Líquido Final:** **{saldo_str}**\n"
        f"• **Situação:** {resumo_status}"
    )

def registrar_ponto_dia(
    data: str, 
    horas_trabalhadas_texto: str, 
    meta_diaria_horas: float = 8.0, 
    descricao: Optional[str] = None
) -> str:
    """
    Registra o ponto diário de horas trabalhadas no sistema (Firestore e memória).

    Args:
        data (str): Data do registro (ex: '2026-09-03', 'Hoje', '03/09/2026').
        horas_trabalhadas_texto (str): Horas trabalhadas ('8h', '7h30', '09:00, 18:00', etc.).
        meta_diaria_horas (float): Meta de horas para o dia (padrão: 8.0).
        descricao (str, opcional): Observações sobre o dia (ex: 'Plantão', 'Home office', 'Compensação').
    """
    try:
        horas_trabalhadas = interpretar_horas(horas_trabalhadas_texto)
    except Exception as e:
        return f"Erro ao interpretar horas: {e}"

    saldo = round(horas_trabalhadas - meta_diaria_horas, 2)
    
    registro_id = str(uuid.uuid4())
    data_limpa = data.strip()
    
    ponto_data = {
        "id": registro_id,
        "data": data_limpa,
        "horas_texto": str(horas_trabalhadas_texto),
        "horas_trabalhadas": horas_trabalhadas,
        "meta_diaria": meta_diaria_horas,
        "saldo_horas": saldo,
        "descricao": descricao.strip() if descricao else None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    _MEMORY_WORK_HOURS.append(ponto_data)

    if firebase.db is not None:
        try:
            firebase.db.collection("work_hours").add(ponto_data)
            logger.info(f"Ponto do dia {data_limpa} salvo no Firestore.")
        except Exception as e:
            logger.error(f"Erro ao salvar ponto no Firestore: {e}")

    horas_str = formatar_horas_minutos(horas_trabalhadas)
    meta_str = formatar_horas_minutos(meta_diaria_horas)
    saldo_str = formatar_horas_minutos(saldo, incluir_sinal=True)

    obs_str = f"\n• Observação: {descricao.strip()}" if descricao else ""
    return (
        f"🕒 **Ponto Registrado com Sucesso!**\n"
        f"• Data: **{data_limpa}**\n"
        f"• Horas Trabalhadas: **{horas_str}**\n"
        f"• Meta Diária: **{meta_str}**\n"
        f"• Saldo do Dia: **{saldo_str}**"
        f"{obs_str}"
    )
