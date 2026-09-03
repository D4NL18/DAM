"""
Clash of Clans Tool — Modulo de Integracao com a API Supercell
Domain: Entretenimento & Lazer
Regras de Negocio: P-001 ao P-010

Fornece:
  - _encode_tag: P-002, encoding de tags com '#'
  - _fetch_coc_data: P-001, autenticacao Bearer e chamada HTTP
  - _verificar_raid_season: P-003 ao P-005, logica de alerta de Raid Weekend
  - _verificar_clan_war: P-006 ao P-007, logica de alerta de Guerra de Clas
  - consultar_clash_of_clans: Tool registravel na IA para queries manuais
  - alerta_raid_capital: Job agendado — Domingo 12h
  - alerta_clan_war: Job agendado — Diario 06h
"""
import logging
import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.clashofclans.com/v1"


# ─────────────────────────────────────────────────────────────
# Helpers internos
# ─────────────────────────────────────────────────────────────

def _encode_tag(tag: str) -> str:
    """P-002: Substitui '#' por '%23' para uso seguro em URLs."""
    return tag.strip().upper().replace("#", "%23")


def _fetch_coc_data(endpoint: str) -> dict:
    """
    P-001: Realiza chamada GET autenticada na Supercell API.
    Lanca excecao em caso de erro HTTP ou timeout (P-009: capturado pelo caller).
    """
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {settings.COC_API_TOKEN}",
        "Accept": "application/json"
    }
    with httpx.Client(timeout=8.0) as client:
        response = client.get(url, headers=headers)
        response.raise_for_status()
        return response.json()


# ─────────────────────────────────────────────────────────────
# Logica de Negocio: Raid Weekend (Capital do Cla)
# ─────────────────────────────────────────────────────────────

def _verificar_raid_season(data: dict, player_tag: str) -> str | None:
    """
    P-003: Verifica se o estado da season e 'ongoing'.
    P-004: Localiza o jogador pelo player_tag na lista de membros.
    P-005: Retorna mensagem de alerta se houver ataques restantes; None caso contrario.
    """
    if data.get("state") != "ongoing":
        return None

    tag_normalizada = player_tag.strip().upper()
    membro = next(
        (m for m in data.get("members", []) if m.get("tag", "").upper() == tag_normalizada),
        None
    )

    if membro is None:
        return None

    feitos = membro.get("attacks", 0)
    limite = membro.get("attackLimit", 6) + membro.get("bonusAttackLimit", 0)
    restantes = limite - feitos

    if restantes <= 0:
        return None

    return (
        f"⚔️ *Alerta de Capital do Clã — Raid Weekend!*\n\n"
        f"Você ainda tem *{restantes} ataque(s) disponível(is)* de {limite} "
        f"no Raid Weekend atual.\n"
        f"Já realizados: {feitos}. Não perca os recursos da Capital! 💰"
    )


# ─────────────────────────────────────────────────────────────
# Logica de Negocio: Guerra de Clas
# ─────────────────────────────────────────────────────────────

def _verificar_clan_war(data: dict, player_tag: str) -> str | None:
    """
    P-006: Verifica se o estado e 'inWar'. Preparation e notInWar sao ignorados.
    P-007: Alerta se o jogador tem menos ataques que o attacksPerMember.
    """
    if data.get("state") != "inWar":
        return None

    ataques_por_membro = data.get("attacksPerMember", 2)
    tag_normalizada = player_tag.strip().upper()

    membro = next(
        (m for m in data.get("clan", {}).get("members", [])
         if m.get("tag", "").upper() == tag_normalizada),
        None
    )

    if membro is None:
        return None

    ataques_feitos = len(membro.get("attacks", []))
    restantes = ataques_por_membro - ataques_feitos

    if restantes <= 0:
        return None

    return (
        f"🏹 *Alerta de Guerra de Clãs!*\n\n"
        f"Seu clã está em guerra e você ainda tem *{restantes} ataque(s) pendente(s)* "
        f"de {ataques_por_membro} disponíveis.\n"
        f"Já realizados: {ataques_feitos}. Ataque antes do prazo! ⏰"
    )


# ─────────────────────────────────────────────────────────────
# Tool registravel na IA — Consulta interativa via chat
# ─────────────────────────────────────────────────────────────

def consultar_clash_of_clans(tipo: str) -> str:
    """
    Consulta o status atual do Clash of Clans para o jogador e cla configurados.
    Use para responder perguntas sobre raids da Capital do Cla ou guerras de clas.

    Args:
        tipo (str): Tipo de consulta — 'raid' para Capital do Cla, 'guerra' para Guerra de Clas.
    """
    tipo_norm = tipo.lower().strip()

    try:
        player_tag = settings.COC_PLAYER_TAG
        clan_tag_encoded = _encode_tag(settings.COC_CLAN_TAG)

        if tipo_norm == "raid":
            # Pega a temporada mais recente de raids
            endpoint = f"clans/{clan_tag_encoded}/capitalraidseasons?limit=1"
            data = _fetch_coc_data(endpoint)
            items = data.get("items", [])

            if not items:
                return "Não há temporadas de Raid Weekend disponíveis no momento para o seu clã."

            season = items[0]
            alerta = _verificar_raid_season(season, player_tag)

            if alerta:
                return alerta

            estado = season.get("state", "desconhecido")
            if estado == "ongoing":
                return (
                    f"✅ *Capital do Clã — Raid Weekend ativo.*\n"
                    f"Você já utilizou todos os seus ataques nesta temporada. Bom trabalho! 🎉"
                )
            return (
                f"ℹ️ *Capital do Clã — Raid Weekend encerrado.*\n"
                f"A temporada atual está no estado: `{estado}`. "
                f"O próximo Raid Weekend começa na sexta-feira."
            )

        elif tipo_norm in ("guerra", "war"):
            endpoint = f"clans/{clan_tag_encoded}/currentwar"
            data = _fetch_coc_data(endpoint)
            alerta = _verificar_clan_war(data, player_tag)

            if alerta:
                return alerta

            estado = data.get("state", "desconhecido")
            if estado == "inWar":
                return "✅ *Guerra de Clãs ativa.* Você já utilizou todos os seus ataques! Bom trabalho! ⚔️"
            if estado == "preparation":
                return "⏳ *Guerra de Clãs em preparação.* Os ataques ainda não estão disponíveis."
            return "ℹ️ *Seu clã não está em guerra no momento.*"

        else:
            return (
                "Por favor, especifique o tipo de consulta:\n"
                "• `raid` — Status do Raid Weekend da Capital do Clã\n"
                "• `guerra` — Status da Guerra de Clãs atual"
            )

    except Exception as e:
        logger.error(f"Erro ao consultar Clash of Clans [{tipo}]: {e}")
        return (
            "⚠️ Não foi possível consultar o Clash of Clans agora. "
            "A API da Supercell pode estar indisponível. Tente novamente em alguns minutos."
        )


# ─────────────────────────────────────────────────────────────
# Jobs Agendados (chamados pelo scheduler em main.py)
# ─────────────────────────────────────────────────────────────

def alerta_raid_capital() -> None:
    """
    Job agendado: Domingo 12h (Brasilia).
    Verifica ataques pendentes no Raid Weekend e envia alerta via WhatsApp (P-010).
    P-009: Falhas de API sao capturadas silenciosamente.
    """
    import asyncio
    asyncio.run(_alerta_raid_capital_async())


async def _alerta_raid_capital_async() -> None:
    from services.whatsapp_service import WhatsAppService
    try:
        player_tag = settings.COC_PLAYER_TAG
        clan_tag_encoded = _encode_tag(settings.COC_CLAN_TAG)
        endpoint = f"clans/{clan_tag_encoded}/capitalraidseasons?limit=1"

        data = _fetch_coc_data(endpoint)
        items = data.get("items", [])

        if not items:
            logger.info("[CoC Raid] Nenhuma season de raid disponivel.")
            return

        mensagem = _verificar_raid_season(items[0], player_tag)
        if mensagem:
            WhatsAppService.send_message(settings.ALLOWED_PHONE_NUMBER, mensagem)
            logger.info("[CoC Raid] Alerta de Raid Weekend enviado com sucesso.")
        else:
            logger.info("[CoC Raid] Nenhum alerta necessario — ataques ja completos ou season encerrada.")

    except Exception as e:
        logger.error(f"[CoC Raid] Erro no job de alerta de Raid Weekend: {e}")


def alerta_clan_war() -> None:
    """
    Job agendado: Diario 06h (Brasilia).
    Verifica ataques de guerra pendentes e envia alerta via WhatsApp (P-010).
    P-009: Falhas de API sao capturadas silenciosamente.
    """
    import asyncio
    asyncio.run(_alerta_clan_war_async())


async def _alerta_clan_war_async() -> None:
    from services.whatsapp_service import WhatsAppService
    try:
        player_tag = settings.COC_PLAYER_TAG
        clan_tag_encoded = _encode_tag(settings.COC_CLAN_TAG)
        endpoint = f"clans/{clan_tag_encoded}/currentwar"

        data = _fetch_coc_data(endpoint)
        mensagem = _verificar_clan_war(data, player_tag)

        if mensagem:
            WhatsAppService.send_message(settings.ALLOWED_PHONE_NUMBER, mensagem)
            logger.info("[CoC War] Alerta de Guerra de Clas enviado com sucesso.")
        else:
            logger.info("[CoC War] Nenhum alerta necessario — sem guerra ativa ou ataques completos.")

    except Exception as e:
        logger.error(f"[CoC War] Erro no job de alerta de Guerra de Clas: {e}")
