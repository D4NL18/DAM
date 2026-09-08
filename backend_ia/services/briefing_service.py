import logging
import re
from datetime import datetime, timezone, timedelta, date
from typing import Optional, List, Dict, Any

from config.settings import settings
from config import firebase
from services.whatsapp_service import WhatsAppService
from services.user_context import UserContext, resolve_user_from_phone
from services.tools.calendar_tool import consultar_agenda
from services.tools.notes_tool import listar_lembretes_pendentes
from services.tools.esports_tool import consultar_jogos_cs2, obter_partidas_estruturadas_cs2
from services.tools.anime_tracker_tool import _MEMORY_WATCHLIST
from services.tools.clash_of_clans_tool import _fetch_coc_data, _encode_tag, _verificar_raid_season, _verificar_clan_war

logger = logging.getLogger(__name__)

# Fuso horário de Brasília (UTC-3)
TZ_BRASILIA = timezone(timedelta(hours=-3))

# Idempotência em memória (conjunto de strings de datas/usuários)
_MEMORY_BRIEFING_LOGS = set()

# Configurações padrão de preferências por usuário
_DEFAULT_PREFERENCES: Dict[str, Dict[str, Any]] = {
    "daniel": {
        "userId": "daniel",
        "userName": "Daniel",
        "horario": "08:00",
        "topicos": ["agenda", "lembretes", "furia", "animes", "clash"],
        "ativo": True
    },
    "lari": {
        "userId": "lari",
        "userName": "Lari",
        "horario": "08:00",
        "topicos": ["agenda", "lembretes", "saude"],
        "ativo": True
    }
}

_MEMORY_BRIEFING_PREFERENCES: Dict[str, Dict[str, Any]] = {}

def _reset_briefing_memory():
    """Auxiliar para testes unitários resetarem a memória de envio."""
    _MEMORY_BRIEFING_LOGS.clear()

def _reset_briefing_preferences():
    """Auxiliar para testes unitários resetarem as preferências."""
    _MEMORY_BRIEFING_PREFERENCES.clear()

def obter_preferencias_briefing(user_id: Optional[str] = None) -> Dict[str, Any]:
    """Obtém as preferências de briefing para o usuário informado (ou ativo)."""
    uid = (user_id or UserContext.get_user_id() or "daniel").lower().strip()
    if uid in _MEMORY_BRIEFING_PREFERENCES:
        return dict(_MEMORY_BRIEFING_PREFERENCES[uid])

    if firebase.db is not None:
        try:
            doc = firebase.db.collection("briefing_preferences").document(uid).get()
            if doc.exists:
                prefs = doc.to_dict()
                _MEMORY_BRIEFING_PREFERENCES[uid] = prefs
                return dict(prefs)
        except Exception as e:
            logger.warning(f"Erro ao buscar preferências de briefing no Firestore para {uid}: {e}")

    default_prefs = _DEFAULT_PREFERENCES.get(uid, {
        "userId": uid,
        "userName": UserContext.get_user_name(),
        "horario": "08:00",
        "topicos": ["agenda", "lembretes"],
        "ativo": True
    })
    _MEMORY_BRIEFING_PREFERENCES[uid] = dict(default_prefs)
    return dict(default_prefs)

def salvar_preferencias_briefing(user_id: str, prefs: Dict[str, Any]) -> None:
    """Persiste as preferências de briefing na memória e no Firestore."""
    uid = user_id.lower().strip()
    _MEMORY_BRIEFING_PREFERENCES[uid] = prefs
    if firebase.db is not None:
        try:
            firebase.db.collection("briefing_preferences").document(uid).set(prefs)
        except Exception as e:
            logger.error(f"Erro ao salvar preferências de briefing no Firestore: {e}")

def configurar_preferencias_briefing(
    horario: Optional[str] = None,
    topicos: Optional[List[str]] = None,
    adicionar_topicos: Optional[List[str]] = None,
    remover_topicos: Optional[List[str]] = None,
    ativo: Optional[bool] = None
) -> str:
    """
    Configura as preferências da mensagem de bom dia (Morning Briefing) para o usuário ativo.
    Permite definir horário de envio (ex: '07:30'), selecionar os tópicos desejados e ativar/pausar.

    Args:
        horario (str, optional): Novo horário no formato 'HH:MM' (ex: '07:30', '08:00').
        topicos (list[str], optional): Lista completa de tópicos desejados.
        adicionar_topicos (list[str], optional): Tópicos a incluir (ex: ['saude', 'veiculo']).
        remover_topicos (list[str], optional): Tópicos a retirar (ex: ['animes', 'furia']).
        ativo (bool, optional): Ativar (True) ou pausar (False) o envio automático diário.
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()
    prefs = obter_preferencias_briefing(user_id)

    alteracoes = []
    if horario and horario.strip():
        h_limpo = horario.strip()
        prefs["horario"] = h_limpo
        alteracoes.append(f"• Horário de envio: **{h_limpo}**")

    topicos_atuais = list(prefs.get("topicos", ["agenda", "lembretes"]))

    if topicos is not None:
        topicos_atuais = [t.strip().lower() for t in topicos if t and t.strip()]
        alteracoes.append(f"• Lista de tópicos redefinida para: {', '.join(topicos_atuais)}")

    if adicionar_topicos:
        for t in adicionar_topicos:
            tn = t.strip().lower()
            if tn and tn not in topicos_atuais:
                topicos_atuais.append(tn)
                alteracoes.append(f"• Tópico adicionado: **{tn}**")

    if remover_topicos:
        for t in remover_topicos:
            tn = t.strip().lower()
            if tn in topicos_atuais:
                topicos_atuais.remove(tn)
                alteracoes.append(f"• Tópico removido: **{tn}**")

    prefs["topicos"] = topicos_atuais

    if ativo is not None:
        prefs["ativo"] = bool(ativo)
        status_txt = "Ativado ✅" if prefs["ativo"] else "Pausado ⏸️"
        alteracoes.append(f"• Envio diário automático: **{status_txt}**")

    salvar_preferencias_briefing(user_id, prefs)

    if not alteracoes:
        return f"ℹ️ Nenhuma alteração solicitada para o briefing de {user_name}."

    topicos_str = ", ".join(topicos_atuais) if topicos_atuais else "Nenhum tópico selecionado"
    return (
        f"⚙️ **Preferências de Bom Dia Atualizadas ({user_name}):**\n"
        + "\n".join(alteracoes)
        + f"\n\n📋 **Configuração Vigente:**\n"
        f"• Horário de Envio: **{prefs.get('horario', '08:00')}**\n"
        f"• Tópicos Ativos: **{topicos_str}**\n"
        f"• Status: **{'Ativo ✅' if prefs.get('ativo', True) else 'Pausado ⏸️'}**"
    )

def consultar_preferencias_briefing() -> str:
    """
    Consulta as configurações atuais da mensagem de bom dia do usuário ativo (horário, tópicos e status).
    """
    user_id = UserContext.get_user_id()
    user_name = UserContext.get_user_name()
    prefs = obter_preferencias_briefing(user_id)
    topicos_str = ", ".join(prefs.get("topicos", [])) if prefs.get("topicos") else "Nenhum"
    status_str = "Ativo ✅" if prefs.get("ativo", True) else "Pausado ⏸️"

    return (
        f"⚙️ **Suas Configurações do Bom Dia ({user_name}):**\n"
        f"• Horário de Envio: **{prefs.get('horario', '08:00')}**\n"
        f"• Tópicos Selecionados: **{topicos_str}**\n"
        f"• Envio Automático: **{status_str}**\n\n"
        f"💡 _Para alterar, diga por exemplo: 'Mude meu bom dia para 07:30 e adicione saúde'_"
    )

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

        if (hora_int < 8 and placar) or status in ["FINALIZADO", "ENCERRADO"]:
            venc_icon = "🏆" if vencedor and "FURIA" in vencedor.upper() else "🏁"
            linhas.append(
                f"• {venc_icon} **FURIA vs {adv}** ({champ})\n"
                f"  ↳ Horário: {horario} | **Resultado:** {placar} ({vencedor or 'Finalizado'})"
            )
        else:
            linhas.append(
                f"• ⚔️ **FURIA vs {adv}**\n"
                f"  ↳ Horário: **{horario}** | Campeonato: {champ}"
            )

    return "\n".join(linhas)

def _obter_jogos_furia_hoje(data_hoje: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """Consulta partidas da FURIA para a data de hoje via Liquipedia/esports_tool."""
    hoje = _obter_data_brasilia(data_hoje)
    dia_mes = hoje.strftime("%d/%m")
    data_completa = hoje.strftime("%d/%m/%Y")

    partidas = obter_partidas_estruturadas_cs2(time="FURIA")
    jogos_hoje = []

    for p in partidas:
        p_data = p.get("data_str", "")
        p_horario = p.get("horario_completo", "") or p.get("horario", "")
        if dia_mes in p_data or data_completa in p_horario or dia_mes in p_horario or "hoje" in p_data.lower() or "hoje" in p_horario.lower():
            jogos_hoje.append(p)

    return jogos_hoje

def _obter_info_animes_briefing(data_hoje: Optional[datetime] = None) -> str:
    """Identifica animes cadastrados na watchlist do usuário que lançam episódio hoje."""
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
        # P-0412: apenas animes em andamento (assistindo)
        if a.get("status_usuario", "").lower() != "assistindo":
            continue

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
        if a.get("status_usuario", "").lower() != "assistindo":
            continue
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

def _obter_alertas_coc() -> str:
    """Consulta a API do Clash of Clans e retorna alertas/status de guerras e raids."""
    if not settings.COC_API_TOKEN or not settings.COC_CLAN_TAG or not settings.COC_PLAYER_TAG:
        return ""

    alertas = []
    clan_tag_encoded = _encode_tag(settings.COC_CLAN_TAG)
    player_tag = settings.COC_PLAYER_TAG

    # 1. Raid Weekend
    try:
        data = _fetch_coc_data(f"clans/{clan_tag_encoded}/capitalraidseasons?limit=1")
        items = data.get("items", [])
        if items:
            msg = _verificar_raid_season(items[0], player_tag)
            if msg:
                alertas.append("• ⚔️ *Raid Weekend:* Você ainda tem ataques disponíveis na Capital do Clã!")
    except Exception as e:
        logger.warning(f"[CoC Briefing] Erro ao consultar Raid Weekend: {e}")

    # 2. Guerra de Clãs
    try:
        data = _fetch_coc_data(f"clans/{clan_tag_encoded}/currentwar")
        war_state = data.get("state")
        if war_state == "inWar":
            adv_name = data.get("opponent", {}).get("name", "Adversário")
            ataques_por_membro = data.get("attacksPerMember", 2)
            tag_norm = player_tag.strip().upper()
            membro = next(
                (m for m in data.get("clan", {}).get("members", []) if m.get("tag", "").upper() == tag_norm),
                None
            )
            if membro is not None:
                ataques_feitos = len(membro.get("attacks", []))
                restantes = ataques_por_membro - ataques_feitos
                if restantes > 0:
                    alertas.append(f"• 🏹 *Guerra de Clãs:* Ativa contra **{adv_name}** — Você tem *{restantes} ataque(s) pendente(s)*!")
                else:
                    alertas.append(f"• 🏹 *Guerra de Clãs:* Ativa contra **{adv_name}** (Seus ataques: Concluídos ✅)")
            else:
                alertas.append(f"• 🏹 *Guerra de Clãs:* Ativa contra **{adv_name}** (Você não está escalado)")
        elif war_state == "preparation":
            adv_name = data.get("opponent", {}).get("name", "Adversário")
            alertas.append(f"• 🏹 *Guerra de Clãs:* Em preparação contra **{adv_name}** (Dia de batalha começa em breve)")
    except Exception as e:
        logger.warning(f"[CoC Briefing] Erro ao consultar Guerra de Clãs: {e}")

    # 3. Liga de Guerras (CWL)
    try:
        data = _fetch_coc_data(f"clans/{clan_tag_encoded}/currentwar/leaguegroup")
        rounds = data.get("rounds", [])
        cwl_encontrada = False
        for round_data in reversed(rounds):
            if cwl_encontrada:
                break
            for war_tag in round_data.get("warTags", []):
                if war_tag == "#0":
                    continue
                try:
                    war_tag_encoded = _encode_tag(war_tag)
                    war_data = _fetch_coc_data(f"clanwarleagues/wars/{war_tag_encoded}")
                    if war_data.get("state") == "inWar":
                        clan_tags_guerra = [
                            war_data.get("clan", {}).get("tag", "").upper(),
                            war_data.get("opponent", {}).get("tag", "").upper()
                        ]
                        meu_clan_tag = settings.COC_CLAN_TAG.strip().upper()
                        if meu_clan_tag in clan_tags_guerra:
                            if war_data.get("clan", {}).get("tag", "").upper() == meu_clan_tag:
                                side_data = war_data["clan"]
                                adv_name = war_data.get("opponent", {}).get("name", "Adversário")
                            else:
                                side_data = war_data["opponent"]
                                adv_name = war_data.get("clan", {}).get("name", "Adversário")

                            ataques_por_membro = war_data.get("attacksPerMember", 1)
                            tag_norm = player_tag.strip().upper()
                            membro = next(
                                (m for m in side_data.get("members", []) if m.get("tag", "").upper() == tag_norm),
                                None
                            )
                            if membro is not None:
                                feitos = len(membro.get("attacks", []))
                                restantes = ataques_por_membro - feitos
                                if restantes > 0:
                                    alertas.append(f"• 🏆 *Liga de Guerras (CWL):* Rodada ativa contra **{adv_name}** — Você tem *{restantes} ataque pendente*! ⚔️")
                                else:
                                    alertas.append(f"• 🏆 *Liga de Guerras (CWL):* Rodada ativa contra **{adv_name}** (Seu ataque: Concluído ✅)")
                            else:
                                alertas.append(f"• 🏆 *Liga de Guerras (CWL):* Rodada ativa contra **{adv_name}** (Você não foi escalado hoje)")
                            cwl_encontrada = True
                            break
                except Exception:
                    continue
    except Exception as e:
        logger.warning(f"[CoC Briefing] Erro ao consultar Liga de Guerras: {e}")

    return "\n".join(alertas)

def _obter_resumo_saude_briefing(user_id: str) -> str:
    """Busca métricas recentes de saúde do usuário para inclusão no briefing."""
    try:
        from services.tools.health_tool import consultar_saude
        dados = consultar_saude(dias_retroativos=2)
        if "Não encontrei registros" in dados or "Erro" in dados:
            return "• ℹ️ Nenhuma métrica de saúde registrada recentemente."
        linhas = [f"• {l.strip()}" for l in dados.splitlines() if "Passos:" in l]
        return "\n".join(linhas[:2]) if linhas else "• ℹ️ Registros sincronizados pelo Apple Health."
    except Exception as e:
        logger.warning(f"Erro ao buscar saúde para briefing: {e}")
        return "• ℹ️ Informações de saúde indisponíveis no momento."

def _obter_resumo_veiculo_briefing(user_id: str) -> str:
    """Busca o status do veículo do usuário para o briefing."""
    try:
        from services.tools.vehicle_tool import _obter_veiculo_usuario
        v = _obter_veiculo_usuario(user_id)
        if not v:
            return ""
        mod = v.get("modelo", "Veículo")
        comb = v.get("combustivel", 68)
        aut = v.get("autonomia", 450)
        travas = "🔒 Trancado" if v.get("travas") == "trancadas" else "🔓 Destrancado"
        return f"• 🚗 **{mod}:** {comb}% tanque (~{aut} km) | {travas}"
    except Exception as e:
        logger.warning(f"Erro ao buscar veículo para briefing: {e}")
        return ""

def montar_resumo_matinal(data_alvo: Optional[datetime] = None, user_id: Optional[str] = None) -> str:
    """
    Monta o texto completo do Morning Briefing respeitando as preferências de tópicos do usuário.
    """
    if isinstance(data_alvo, str):
        user_id = data_alvo
        data_alvo = None

    target_user_id = (user_id or UserContext.get_user_id() or "daniel").lower().strip()
    target_user_name = "Daniel" if target_user_id == "daniel" else ("Lari" if target_user_id == "lari" else target_user_id.capitalize())

    antigo_user_id = UserContext.get_user_id()
    antigo_user_phone = UserContext.get_user_phone()
    UserContext.set_user(target_user_id)
    try:
        prefs = obter_preferencias_briefing(target_user_id)
        topicos = set(prefs.get("topicos", ["agenda", "lembretes"]))
        horario_config = prefs.get("horario", "08:00")

        hoje = _obter_data_brasilia(data_alvo)
        hoje_str = hoje.strftime("%Y-%m-%d")
        data_formatada = hoje.strftime("%d/%m/%Y")
        dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        dia_nome = dias_semana[hoje.weekday()]

        blocos = []

        # 1. Google Calendar
        if "agenda" in topicos:
            try:
                agenda_raw = consultar_agenda(dias=1, usuario=target_user_id)
                if "Nenhum evento encontrado" in agenda_raw or "não foi configurada" in agenda_raw or "livre para esse período" in agenda_raw or not agenda_raw.strip():
                    agenda_txt = "• ℹ️ Nenhum compromisso agendado para hoje."
                else:
                    linhas_agenda = []
                    for linha in agenda_raw.splitlines():
                        linha_s = linha.strip()
                        if not linha_s or "Você tem os seguintes eventos" in linha_s:
                            continue
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

                    agenda_txt = "\n".join(linhas_agenda) if linhas_agenda else "• ℹ️ Nenhum compromisso agendado para hoje."
            except Exception as e:
                logger.warning(f"Erro ao consultar agenda para briefing: {e}")
                agenda_txt = "• ℹ️ Nenhum compromisso agendado para hoje."

            blocos.append(f"📅 *Compromissos de Hoje:*\n{agenda_txt}")

        # 2. Tarefas & Lembretes (P-0410: Restrito exclusivamente ao dia de hoje)
        if "lembretes" in topicos:
            try:
                lembretes_raw = listar_lembretes_pendentes(apenas_hoje=True, data_referencia=hoje_str)
                if "Nenhum lembrete pendente" in lembretes_raw or not lembretes_raw.strip():
                    tarefas_txt = "• ℹ️ Nenhuma tarefa pendente para hoje."
                else:
                    tarefas_txt = lembretes_raw.strip()
            except Exception as e:
                logger.warning(f"Erro ao consultar lembretes para briefing: {e}")
                tarefas_txt = "• ℹ️ Nenhuma tarefa pendente para hoje."

            blocos.append(f"📝 *Tarefas & Lembretes:*\n{tarefas_txt}")

        # 3. Saúde (Métricas de sono/passos)
        if "saude" in topicos:
            saude_txt = _obter_resumo_saude_briefing(target_user_id)
            blocos.append(f"🏃 *Saúde & Bem-Estar:*\n{saude_txt}")

        # 4. Veículo
        if "veiculo" in topicos:
            veic_txt = _obter_resumo_veiculo_briefing(target_user_id)
            if veic_txt:
                blocos.append(f"🚗 *Status do Veículo:*\n{veic_txt}")

        # 5. Jogos da FURIA (CS2)
        if "furia" in topicos or "esports" in topicos:
            jogos_furia = _obter_jogos_furia_hoje(hoje)
            furia_txt = _formatar_jogos_furia_dia(jogos_furia)
            blocos.append(f"🐾 *Jogos da FURIA (CS2):*\n{furia_txt}")

        # 6. Animes (apenas se configurado e Daniel tiver animes)
        if "animes" in topicos and target_user_id == "daniel":
            animes_hoje = _obter_animes_lancando_hoje(hoje)
            if animes_hoje:
                linhas_animes = [f"• 🍿 **{an['titulo']}** (Ep. {an['episodio']}) às {an['horario']} (Crunchyroll)" for an in animes_hoje]
                animes_txt = "\n".join(linhas_animes)
            else:
                animes_txt = _obter_info_animes_briefing(hoje)
            blocos.append(f"🎌 *Animes de Hoje:*\n{animes_txt}")

        # 7. Clash of Clans (apenas se configurado e Daniel)
        if "clash" in topicos and target_user_id == "daniel":
            coc_alertas = _obter_alertas_coc()
            if coc_alertas:
                blocos.append(f"⚔️ *Clash of Clans — Ataques Pendentes:*\n{coc_alertas}")

        corpo = "\n\n".join(blocos)

        template = (
            f"☀️ *Bom dia! Seu Resumo Matinal do DAM*\n"
            f"🗓️ *{dia_nome}, {data_formatada}* ({horario_config})\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{corpo}\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 _Tenha um excelente e produtivo dia!_"
        )

        return template.strip()
    finally:
        UserContext.set_user(antigo_user_id, antigo_user_phone)

def _obter_telefone_usuario(user_id: str) -> str:
    """Resolve o número de telefone do usuário para envio de WhatsApp."""
    uid = user_id.lower().strip()
    if uid == "daniel":
        return "5571991269995"
    elif uid == "lari":
        return "5571983278254"

    for phone in settings.allowed_numbers_list:
        info = resolve_user_from_phone(phone)
        if info and info.get("id") == uid:
            return phone

    return settings.ALLOWED_PHONE_NUMBER

def _obter_todos_usuarios_briefing() -> List[str]:
    """Retorna lista consolidada de usuários cadastrados para o briefing."""
    usuarios = ["daniel", "lari"]
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("briefing_preferences").stream()
            for doc in docs:
                uid = doc.id.lower().strip()
                if uid not in usuarios:
                    usuarios.append(uid)
        except Exception:
            logger.exception("Erro ao buscar preferências de briefing no Firestore")
    return usuarios


def _disparar_briefing_se_horario_correto(uid: str, hora_minuto: str, force: bool) -> bool:
    """Verifica preferências e dispara o briefing caso o horário coincida."""
    try:
        prefs = obter_preferencias_briefing(uid)
        if not prefs.get("ativo", True):
            return False

        horario_user = str(prefs.get("horario", "08:00")).strip()
        if horario_user == hora_minuto:
            logger.info("Disparando briefing matinal para %s no horário configurado (%s).", uid, horario_user)
            enviar_briefing_matinal(force=force, user_id=uid)
            return True
    except Exception:
        logger.exception("Erro ao disparar briefing agendado para %s", uid)
    return False


def verificar_e_disparar_briefings_agendados(hora_minuto: Optional[str] = None, force: bool = False) -> List[str]:
    """
    P-0417: Avalia usuários cadastrados e dispara o briefing para aqueles cujo horário
    configurado coincidir com hora_minuto.
    Retorna a lista de user_ids para os quais o disparo foi efetuado.
    """
    if not hora_minuto:
        hoje = _obter_data_brasilia()
        hora_minuto = hoje.strftime("%H:%M")

    hora_alvo = hora_minuto.strip()
    usuarios_alvo = _obter_todos_usuarios_briefing()

    disparados = []
    for uid in usuarios_alvo:
        if _disparar_briefing_se_horario_correto(uid, hora_alvo, force):
            disparados.append(uid)

    return disparados

def enviar_briefing_matinal(force: bool = False, user_id: Optional[str] = None) -> str:
    """
    Dispara o resumo matinal personalizado para o WhatsApp do usuário respeitando regras de idempotência.

    Args:
        force (bool): Se True, reenvia mesmo que já tenha sido disparado hoje.
        user_id (str, opcional): Usuário alvo ('daniel' ou 'lari'). Se omitido, usa UserContext.
    """
    target_user_id = (user_id or UserContext.get_user_id() or "daniel").lower().strip()
    target_user_name = "Daniel" if target_user_id == "daniel" else ("Lari" if target_user_id == "lari" else target_user_id.capitalize())

    hoje = _obter_data_brasilia()
    chave_dia_user = f"{hoje.strftime('%Y-%m-%d')}_{target_user_id}"
    chave_dia_legada = hoje.strftime("%Y-%m-%d")

    # Idempotência em memória
    if not force:
        if chave_dia_user in _MEMORY_BRIEFING_LOGS or (target_user_id == "daniel" and chave_dia_legada in _MEMORY_BRIEFING_LOGS):
            return f"ℹ️ O briefing matinal de hoje ({chave_dia_legada}) já foi enviado para {target_user_name}."

    # Idempotência no Firestore
    if not force and firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("briefing_logs").document(f"briefing_{chave_dia_user}").get()
            if doc_ref.exists and doc_ref.to_dict().get("status") == "sucesso":
                _MEMORY_BRIEFING_LOGS.add(chave_dia_user)
                return f"ℹ️ O briefing matinal de hoje ({chave_dia_legada}) já foi enviado para {target_user_name}."
            if target_user_id == "daniel":
                doc_leg = firebase.db.collection("briefing_logs").document(f"briefing_{chave_dia_legada}").get()
                if doc_leg.exists and doc_leg.to_dict().get("status") == "sucesso":
                    _MEMORY_BRIEFING_LOGS.add(chave_dia_legada)
                    return f"ℹ️ O briefing matinal de hoje ({chave_dia_legada}) já foi enviado para {target_user_name}."
        except Exception as e:
            logger.warning(f"Falha ao checar idempotência do briefing no Firestore: {e}")

    # Monta a mensagem personalizada
    mensagem = montar_resumo_matinal(data_alvo=hoje, user_id=target_user_id)

    telefone = _obter_telefone_usuario(target_user_id)
    if not telefone:
        return f"Erro: Telefone para usuário '{target_user_id}' não configurado."

    remote_jid = f"{telefone}@s.whatsapp.net"
    try:
        WhatsAppService.send_text(remote_jid, mensagem)
        logger.info(f"Briefing matinal enviado com sucesso para {remote_jid} ({target_user_name}).")

        # Registra sucesso
        _MEMORY_BRIEFING_LOGS.add(chave_dia_user)
        _MEMORY_BRIEFING_LOGS.add(chave_dia_legada)

        if firebase.db is not None:
            try:
                firebase.db.collection("briefing_logs").document(f"briefing_{chave_dia_user}").set({
                    "data": chave_dia_legada,
                    "userId": target_user_id,
                    "enviado_em": datetime.now(timezone.utc).isoformat(),
                    "destinatario": telefone,
                    "status": "sucesso"
                })
            except Exception as e:
                logger.error(f"Erro ao salvar log de briefing no Firestore: {e}")

        return f"✅ Briefing matinal enviado com sucesso para o WhatsApp de {target_user_name} ({telefone})!"
    except Exception as e:
        logger.error(f"Erro ao disparar mensagem de briefing no WhatsApp: {e}")
        return f"Erro ao enviar briefing matinal via WhatsApp: {e}"

def consultar_briefing_matinal() -> str:
    """
    Retorna o conteúdo oficial do Morning Briefing / mensagem de bom dia programada para o usuário ativo.
    """
    return montar_resumo_matinal()