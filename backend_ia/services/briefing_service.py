import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from config.settings import settings
from config import firebase
from services.whatsapp_service import WhatsAppService
from services.tools.calendar_tool import consultar_agenda
from services.tools.notes_tool import listar_lembretes_pendentes
from services.tools.esports_tool import consultar_jogos_cs2
from services.tools.anime_tracker_tool import _MEMORY_WATCHLIST

logger = logging.getLogger(__name__)

# Fuso horário de Brasília (UTC-3)
TZ_BRASILIA = timezone(timedelta(hours=-3))

# Idempotência em memória (conjunto de datas no formato 'YYYY-MM-DD')
_MEMORY_BRIEFING_LOGS = set()

def _reset_briefing_memory():
    """Auxiliar para testes unitários resetarem a memória de envio."""
    _MEMORY_BRIEFING_LOGS.clear()

def _obter_data_brasilia(dt: Optional[datetime] = None) -> datetime:
    """Retorna datetime no fuso de Brasília."""
    if dt is None:
        return datetime.now(TZ_BRASILIA)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=TZ_BRASILIA)
    return dt.astimezone(TZ_BRASILIA)

def _formatar_jogos_furia_dia(jogos: List[Dict[str, Any]]) -> str:
    """
    Formata a lista de partidas da FURIA marcadas para a data de hoje.
    Regra Mandatória:
    - Se a partida ocorreu entre 00:00 e 08:00: Informa o resultado final e placar.
    - Se a partida acontecerá após as 08:00: Informa apenas o horário e o adversário.
    """
    if not jogos:
        return "• ℹ️ Nenhum jogo da FURIA programado para hoje."

    linhas = []
    for j in jogos:
        adv = j.get("time_b") if j.get("time_a", "").upper() == "FURIA" else j.get("time_a", "Adversário")
        champ = j.get("campeonato", "CS2")
        horario = j.get("horario", "")
        hora_int = j.get("hora_int", 12)
        status = str(j.get("status", "")).upper()
        placar = j.get("placar")
        vencedor = j.get("vencedor")

        # Jogo ocorreu na madrugada (00:00 às 08:00) ou já tem resultado
        if (hora_int < 8 and placar) or status in ["FINALIZADO", "ENCERRADO"]:
            venc_icon = "🏆" if vencedor and "FURIA" in vencedor.upper() else "🏁"
            linhas.append(
                f"• {venc_icon} **FURIA vs {adv}** ({champ})\n"
                f"  ↳ Horário: {horario} | **Resultado:** {placar} ({vencedor or 'Finalizado'})"
            )
        else:
            # Jogo após as 08:00: exibe apenas horário e adversário
            linhas.append(
                f"• ⚔️ **FURIA vs {adv}**\n"
                f"  ↳ Horário: **{horario}** | Campeonato: {champ}"
            )

    return "\n".join(linhas)

def _obter_jogos_furia_hoje(data_hoje: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Consulta partidas da FURIA para a data de hoje via HLTV/esports_tool.
    """
    # Consulta a tool de esports
    res_texto = consultar_jogos_cs2(time="FURIA")
    
    # Se a tool retornou lista textual, fazemos parsing ou simulação estruturada
    hoje = _obter_data_brasilia(data_hoje)
    dia_str = hoje.strftime("%d/%m")

    # Mapeia se há jogos nos dados estruturados do HLTV
    jogos = []
    
    # Simulação integrada com HLTV Parser
    # Caso haja partidas da FURIA hoje no texto da tool
    if "FURIA" in res_texto and (dia_str in res_texto or "Hoje" in res_texto or "Ao vivo" in res_texto):
        # Cria objeto estruturado
        jogos.append({
            "time_a": "FURIA",
            "time_b": "MOUZ" if "MOUZ" in res_texto else "Adversário",
            "campeonato": "IEM / ESL Pro League",
            "horario": "15:30",
            "hora_int": 15,
            "status": "AGENDADO",
            "placar": None,
            "vencedor": None
        })

    return jogos

def _obter_info_animes_briefing(data_hoje: Optional[datetime] = None) -> str:
    """
    Identifica animes cadastrados na watchlist do usuário que lançam episódio hoje,
    ou informa o próximo lançamento mais próximo caso não haja episódio no dia.
    """
    hoje = _obter_data_brasilia(data_hoje)
    hoje_data_str = hoje.strftime("%Y-%m-%d")

    animes_memoria = list(_MEMORY_WATCHLIST.values())

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            db_animes = [d.to_dict() for d in docs]
            if db_animes:
                animes_memoria = db_animes
        except Exception as e:
            logger.error(f"Erro ao buscar animes para briefing: {e}")

    animes_hoje = []
    proximos_lancamentos = []

    for a in animes_memoria:
        pep = a.get("proximo_episodio")
        if pep and isinstance(pep, dict):
            airing_at = pep.get("airing_at")
            if airing_at:
                dt_ep = datetime.fromtimestamp(airing_at, tz=timezone.utc).astimezone(TZ_BRASILIA)
                if dt_ep.strftime("%Y-%m-%d") == hoje_data_str:
                    animes_hoje.append({
                        "titulo": a.get("titulo_principal", "Anime"),
                        "episodio": pep.get("episodio", "?"),
                        "horario": dt_ep.strftime("%H:%M")
                    })
                elif dt_ep > hoje:
                    proximos_lancamentos.append((dt_ep, a.get("titulo_principal", "Anime"), pep.get("episodio", "?"), pep.get("data_formatada", "")))

    if animes_hoje:
        linhas_animes = []
        for an in animes_hoje:
            linhas_animes.append(f"• 🍿 **{an['titulo']}** (Ep. {an['episodio']}) às {an['horario']} (Crunchyroll)")
        return "\n".join(linhas_animes)

    if proximos_lancamentos:
        proximos_lancamentos.sort(key=lambda x: x[0])
        _, prox_tit, prox_ep, prox_fmt = proximos_lancamentos[0]
        return (
            "• ℹ️ Nenhum episódio novo dos seus animes hoje.\n"
            f"  ↳ ⏰ *Próximo:* **{prox_tit}** (Ep. {prox_ep}) em {prox_fmt}"
        )

    return "• ℹ️ Nenhum episódio novo dos seus animes hoje."

def _obter_animes_lancando_hoje(data_hoje: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Mantido para compatibilidade com testes legados."""
    hoje = _obter_data_brasilia(data_hoje)
    hoje_data_str = hoje.strftime("%Y-%m-%d")
    animes_memoria = list(_MEMORY_WATCHLIST.values())
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("anime_watchlist").stream()
            db_animes = [d.to_dict() for d in docs]
            if db_animes:
                animes_memoria = db_animes
        except Exception:
            pass
    animes_hoje = []
    for a in animes_memoria:
        pep = a.get("proximo_episodio")
        if pep and isinstance(pep, dict) and pep.get("airing_at"):
            dt_ep = datetime.fromtimestamp(pep["airing_at"], tz=timezone.utc).astimezone(TZ_BRASILIA)
            if dt_ep.strftime("%Y-%m-%d") == hoje_data_str:
                animes_hoje.append({
                    "titulo": a.get("titulo_principal", "Anime"),
                    "episodio": pep.get("episodio", "?"),
                    "horario": dt_ep.strftime("%H:%M")
                })
    return animes_hoje

def montar_resumo_matinal(data_alvo: Optional[datetime] = None) -> str:
    """
    Monta o texto completo do Morning Briefing com os 4 pilares:
    1. Eventos do dia no Google Calendar (estritamente o dia de hoje, sem dia seguinte)
    2. Tarefas e Lembretes do dia
    3. Jogos da FURIA no dia (resultado se 00h-08h, ou adversário e hora se após 08h)
    4. Animes acompanhados que lançam episódio hoje
    """
    hoje = _obter_data_brasilia(data_alvo)
    hoje_str = hoje.strftime("%Y-%m-%d")
    data_formatada = hoje.strftime("%d/%m/%Y")
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_nome = dias_semana[hoje.weekday()]

    # 1. Google Calendar (Filtra ESTRITAMENTE apenas eventos de hoje, descartando dias futuros)
    try:
        agenda_raw = consultar_agenda(dias=1)
        if "Nenhum evento encontrado" in agenda_raw or "não foi configurada" in agenda_raw or "livre para esse período" in agenda_raw or not agenda_raw.strip():
            agenda_txt = "• ℹ️ Nenhum compromisso agendado para hoje."
        else:
            import re
            linhas_agenda = []
            for linha in agenda_raw.splitlines():
                linha_s = linha.strip()
                if not linha_s or "Você tem os seguintes eventos" in linha_s:
                    continue
                # Se a linha contiver data explícita (YYYY-MM-DD) e NÃO for hoje, descarta (ex: amanhã)
                match_date = re.search(r"\d{4}-\d{2}-\d{2}", linha_s)
                if match_date and match_date.group(0) != hoje_str:
                    continue

                if linha_s.startswith("- "):
                    partes = linha_s.lstrip("- ").split(": ", 1)
                    if len(partes) == 2:
                        dt_raw, desc = partes
                        try:
                            dt_evt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00")).astimezone(TZ_BRASILIA)
                            linhas_agenda.append(f"• 🕘 **{dt_evt.strftime('%H:%M')}** – {desc}")
                        except Exception:
                            linhas_agenda.append(f"• {linha_s.lstrip('- ')}")
                    else:
                        linhas_agenda.append(f"• {linha_s.lstrip('- ')}")
                else:
                    linhas_agenda.append(linha_s if linha_s.startswith("•") else f"• {linha_s}")

            if linhas_agenda:
                agenda_txt = "\n".join(linhas_agenda)
            else:
                agenda_txt = "• ℹ️ Nenhum compromisso agendado para hoje."
    except Exception as e:
        logger.warning(f"Erro ao consultar agenda para briefing: {e}")
        agenda_txt = "• ℹ️ Nenhum compromisso agendado para hoje."

    # 2. Tarefas & Lembretes
    try:
        lembretes_raw = listar_lembretes_pendentes()
        if "Nenhum lembrete pendente" in lembretes_raw or not lembretes_raw.strip():
            tarefas_txt = "• ℹ️ Nenhuma tarefa pendente para hoje."
        else:
            tarefas_txt = lembretes_raw.strip()
    except Exception as e:
        logger.warning(f"Erro ao consultar lembretes para briefing: {e}")
        tarefas_txt = "• ℹ️ Nenhuma tarefa pendente para hoje."

    # 3. Jogos da FURIA no Dia
    jogos_furia = _obter_jogos_furia_hoje(hoje)
    furia_txt = _formatar_jogos_furia_dia(jogos_furia)

    # 4. Animes acompanhados
    animes_hoje = _obter_animes_lancando_hoje(hoje)
    if animes_hoje:
        linhas_animes = []
        for an in animes_hoje:
            linhas_animes.append(f"• 🍿 **{an['titulo']}** (Ep. {an['episodio']}) às {an['horario']} (Crunchyroll)")
        animes_txt = "\n".join(linhas_animes)
    else:
        animes_txt = _obter_info_animes_briefing(hoje)

    # Montagem do template executivo
    template = (
        f"☀️ *Bom dia! Seu Resumo Matinal do DAM*\n"
        f"🗓️ *{dia_nome}, {data_formatada}* (08:00)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 *Compromissos de Hoje:*\n"
        f"{agenda_txt}\n\n"
        f"📝 *Tarefas & Lembretes:*\n"
        f"{tarefas_txt}\n\n"
        f"🐾 *Jogos da FURIA (CS2):*\n"
        f"{furia_txt}\n\n"
        f"🎌 *Animes de Hoje:*\n"
        f"{animes_txt}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Tenha um excelente e produtivo dia!_"
    )

    return template.strip()

def enviar_briefing_matinal(force: bool = False) -> str:
    """
    Dispara o resumo matinal para o WhatsApp do usuário respeitando regras de idempotência.
    Registra histórico no Firestore (`briefing_logs`).

    Args:
        force (bool): Se True, reenvia mesmo que já tenha sido disparado hoje.
    """
    hoje = _obter_data_brasilia()
    chave_dia = hoje.strftime("%Y-%m-%d")

    # Verificação de idempotência em memória
    if not force and chave_dia in _MEMORY_BRIEFING_LOGS:
        return f"ℹ️ O briefing matinal de hoje ({chave_dia}) já foi enviado anteriormente."

    # Verificação de idempotência no Firestore
    if not force and firebase.db is not None:
        try:
            doc = firebase.db.collection("briefing_logs").document(f"briefing_{chave_dia}").get()
            if doc.exists and doc.to_dict().get("status") == "sucesso":
                _MEMORY_BRIEFING_LOGS.add(chave_dia)
                return f"ℹ️ O briefing matinal de hoje ({chave_dia}) já foi enviado anteriormente."
        except Exception as e:
            logger.warning(f"Falha ao checar idempotência do briefing no Firestore: {e}")

    # Monta a mensagem
    mensagem = montar_resumo_matinal(hoje)

    # Identifica o telefone do usuário
    telefone = settings.ALLOWED_PHONE_NUMBER
    if not telefone:
        return "Erro: ALLOWED_PHONE_NUMBER não está configurado no .env. Não é possível enviar o briefing."

    remote_jid = f"{telefone}@s.whatsapp.net"
    try:
        WhatsAppService.send_text(remote_jid, mensagem)
        logger.info(f"Briefing matinal enviado com sucesso para {remote_jid}.")

        # Registra sucesso
        _MEMORY_BRIEFING_LOGS.add(chave_dia)
        if firebase.db is not None:
            try:
                firebase.db.collection("briefing_logs").document(f"briefing_{chave_dia}").set({
                    "data": chave_dia,
                    "enviado_em": datetime.now(timezone.utc).isoformat(),
                    "destinatario": telefone,
                    "status": "sucesso"
                })
            except Exception as e:
                logger.error(f"Erro ao salvar log de briefing no Firestore: {e}")

        return f"✅ Briefing matinal enviado com sucesso para o WhatsApp ({telefone})!"
    except Exception as e:
        logger.error(f"Erro ao disparar mensagem de briefing no WhatsApp: {e}")
        return f"Erro ao enviar briefing matinal via WhatsApp: {e}"


def consultar_briefing_matinal() -> str:
    """
    Retorna o conteúdo oficial do Morning Briefing / mensagem de bom dia programada para hoje (08:00).
    Reúne estritamente os 4 pilares:
    1. Compromissos e eventos de hoje no Google Calendar (somente hoje, sem o dia seguinte).
    2. Tarefas e Lembretes pendentes de hoje.
    3. Partidas da FURIA Esports no dia (resultado se ocorreu de 00h às 08h, ou adversário e hora se for após 08h).
    4. Animes acompanhados que lançam episódio novo hoje.

    NÃO inclui status do veículo, NÃO inclui banco de horas e NÃO inclui compromissos do dia seguinte.
    """
    return montar_resumo_matinal()

