import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from google.oauth2 import service_account
from googleapiclient.discovery import build
from services.user_context import UserContext
from config.settings import settings
from config.timezone import TZ_BRASILIA

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def _get_calendar_service():
    creds_path = os.environ.get('GOOGLE_CALENDAR_CREDENTIALS')
    if not creds_path or not os.path.exists(creds_path):
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path, scopes=SCOPES)
        service = build('calendar', 'v3', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Erro ao autenticar Calendar: {e}")
        return None

def _resolve_calendar_target(target_user: str = "auto") -> Tuple[Optional[str], str, Optional[str]]:
    """
    Resolve o calendarId e o nome do titular da agenda, aplicando a matriz de permissões.
    Retorna (calendar_id, nome_titular, erro_permissao).
    """
    caller_id = UserContext.get_user_id()
    t_clean = (target_user or "auto").strip().lower()

    if t_clean in ["auto", "", "me", "minha", "meu", "proprio", "próprio"]:
        target = caller_id
    elif "lari" in t_clean:
        target = "lari"
    elif "dan" in t_clean:
        target = "daniel"
    else:
        target = caller_id

    target_info = UserContext.get_user_info(target)
    target_name = target_info.get("name", target.capitalize())

    # Permissão: Usuário secundário não pode acessar a agenda do admin
    if caller_id == "lari" and target == "daniel":
        return None, target_name, "Acesso restrito: Você só possui permissão para consultar sua própria agenda."

    # Resolução dos IDs
    if target == "daniel":
        cal_id = getattr(settings, "CALENDAR_ID_DANIEL", None) or settings.CALENDAR_ID or "primary"
        return cal_id, target_name, None
    elif target == "lari":
        cal_id = getattr(settings, "CALENDAR_ID_LARI", None)
        if not cal_id:
            return None, target_name, (
                "A agenda Google secundária ainda não foi vinculada. "
                "Para ativar, compartilhe o Google Calendar com a Service Account do DAM "
                "e preencha a variável CALENDAR_ID_LARI nas configurações."
            )
        return cal_id, target_name, None

    cal_fallback = settings.CALENDAR_ID or "primary"
    return cal_fallback, UserContext.get_user_name(), None

def agendar_evento(
    titulo: str, 
    inicio_iso: str, 
    duracao_minutos: int = 60,
    descricao: str = None,
    localizacao: str = None,
    usuario: str = "auto"
) -> str:
    """
    Schedule an event or meeting on Google Calendar.
    
    Args:
        titulo (str): Event title.
        inicio_iso (str): Start datetime in ISO format.
        duracao_minutos (int): Duration in minutes. Default 60.
        descricao (str, optional): Event description or notes.
        localizacao (str, optional): Location or video call link.
        usuario (str, optional): 'auto' for current user, or 'daniel'/'lari'.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada pelo administrador."

    calendar_id, titular, erro = _resolve_calendar_target(usuario)
    if erro:
        return erro

    try:
        inicio_dt = datetime.fromisoformat(inicio_iso.replace('Z', '+00:00'))
        fim_dt = inicio_dt + timedelta(minutes=duracao_minutos)

        event = {
            'summary': titulo,
            'start': {
                'dateTime': inicio_dt.isoformat(),
            },
            'end': {
                'dateTime': fim_dt.isoformat(),
            },
        }

        if descricao:
            event['description'] = descricao
        if localizacao:
            event['location'] = localizacao

        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        info_extra = []
        if localizacao:
            info_extra.append(f"Local: {localizacao}")
        if descricao:
            info_extra.append(f"Descrição: {descricao}")
        extra_str = f" ({', '.join(info_extra)})" if info_extra else ""

        agenda_indicador = f" na agenda de {titular}" if titular != UserContext.get_user_name() else ""
        return f"Evento '{titulo}' agendado com sucesso{agenda_indicador}!{extra_str} (Link: {created_event.get('htmlLink')})"
    
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        return f"Não consegui agendar o evento devido a um erro: {e}"

def consultar_agenda(dias: int = 1, dias_a_frente: int = None, usuario: str = "auto") -> str:
    """
    Query upcoming Google Calendar events.
    
    Args:
        dias (int): Days ahead to search (default: 1).
        dias_a_frente (int, optional): Alias for days ahead.
        usuario (str, optional): 'auto' for current user, or 'daniel'/'lari'.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada."

    limite_dias = dias_a_frente if dias_a_frente is not None else dias
    calendar_id, titular, erro = _resolve_calendar_target(usuario)
    if erro:
        return erro

    try:
        now = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=limite_dias)).isoformat()

        events_result = service.events().list(
            calendarId=calendar_id, timeMin=now, timeMax=time_max,
            maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        caller_name = UserContext.get_user_name()
        is_own = (titular == caller_name)

        if not events:
            if is_own:
                return "Sua agenda está livre para esse período!"
            return f"A agenda de {titular} está livre para esse período!"
        
        if is_own:
            resp = "Você tem os seguintes eventos:\n"
        else:
            resp = f"Eventos na agenda de {titular}:\n"

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Sem título')
            loc = f" | Local: {event['location']}" if event.get('location') else ""
            desc = f" | Descrição: {event['description']}" if event.get('description') else ""
            resp += f"- {start}: {summary}{loc}{desc}\n"
        return resp
    
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return f"Erro ao acessar a agenda de {titular}."


def _formatar_horario_evento(event: dict) -> str:
    start = event.get('start', {})
    dt_str = start.get('dateTime') or start.get('date') or ""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt_br = dt.astimezone(TZ_BRASILIA)
        else:
            dt_br = dt
        return dt_br.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return dt_str


def _localizar_eventos_por_termo(
    service,
    calendar_id: str,
    termo: str,
    data_referencia: Optional[str] = None,
    dias_busca: int = 30
) -> list[dict]:
    """
    Localiza eventos no Google Calendar que contenham o termo no título ou descrição.
    """
    termo_clean = (termo or "").strip().lower()
    
    if data_referencia:
        dt_ref = None
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]:
            try:
                dt_ref = datetime.strptime(data_referencia.split("T")[0] if "T" in data_referencia else data_referencia, fmt)
                break
            except Exception:
                pass

        if dt_ref:
            time_min = dt_ref.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=TZ_BRASILIA).isoformat()
            time_max = dt_ref.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=TZ_BRASILIA).isoformat()
        else:
            now_br = datetime.now(TZ_BRASILIA)
            time_min = now_br.isoformat()
            time_max = (now_br + timedelta(days=dias_busca)).isoformat()
    else:
        now_br = datetime.now(TZ_BRASILIA)
        time_min = now_br.isoformat()
        time_max = (now_br + timedelta(days=dias_busca)).isoformat()

    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        items = events_result.get('items', [])
    except Exception as e:
        logger.error(f"Erro ao consultar eventos no Google Calendar: {e}")
        return []

    correspondentes = []
    for item in items:
        summary = (item.get('summary') or "").lower()
        description = (item.get('description') or "").lower()
        item_id = item.get('id', "")
        if termo_clean in summary or termo_clean in description or item_id == termo:
            correspondentes.append(item)

    return correspondentes


def excluir_evento(
    termo_busca: str,
    data_referencia: Optional[str] = None,
    usuario: str = "auto"
) -> str:
    """
    Delete or cancel a Google Calendar event by name or search term.
    
    Args:
        termo_busca (str): Event title or search keyword.
        data_referencia (str, optional): Approximate date of the event (e.g. 'YYYY-MM-DD').
        usuario (str, optional): 'auto' for current user, or 'daniel'/'lari'.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada pelo administrador."

    calendar_id, titular, erro = _resolve_calendar_target(usuario)
    if erro:
        return erro

    eventos = _localizar_eventos_por_termo(service, calendar_id, termo_busca, data_referencia)
    if not eventos:
        data_str = f" na data {data_referencia}" if data_referencia else ""
        return f"Não encontrei nenhum evento com o termo '{termo_busca}'{data_str} na agenda de {titular}."

    if len(eventos) > 1:
        linhas = [f"Encontrei mais de um evento com o termo '{termo_busca}' na agenda de {titular}. Por favor, especifique qual deseja cancelar:"]
        for ev in eventos:
            hora = _formatar_horario_evento(ev)
            summary = ev.get('summary', 'Sem título')
            linhas.append(f"• **{summary}** – {hora}")
        return "\n".join(linhas)

    alvo = eventos[0]
    event_id = alvo.get("id")
    titulo = alvo.get("summary", "Evento")
    horario_str = _formatar_horario_evento(alvo)

    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        agenda_indicador = f" na agenda de {titular}" if titular != UserContext.get_user_name() else " da sua agenda"
        return f"O evento '{titulo}' ({horario_str}) foi cancelado e excluído com sucesso{agenda_indicador}!"
    except Exception as e:
        logger.error(f"Erro ao excluir evento {event_id}: {e}")
        return f"Ocorreu um erro ao tentar excluir o evento '{titulo}': {e}"


def editar_evento(
    termo_busca: str,
    novo_titulo: Optional[str] = None,
    novo_inicio_iso: Optional[str] = None,
    nova_duracao_minutos: Optional[int] = None,
    nova_descricao: Optional[str] = None,
    nova_localizacao: Optional[str] = None,
    data_referencia: Optional[str] = None,
    usuario: str = "auto"
) -> str:
    """
    Edit or reschedule an existing Google Calendar event.
    
    Args:
        termo_busca (str): Current title or keyword of the event.
        novo_titulo (str, optional): New title.
        novo_inicio_iso (str, optional): New start datetime in ISO format.
        nova_duracao_minutos (int, optional): New duration in minutes.
        nova_descricao (str, optional): New description.
        nova_localizacao (str, optional): New location.
        data_referencia (str, optional): Approximate date for search.
        usuario (str, optional): 'auto' for current user, or 'daniel'/'lari'.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada pelo administrador."

    calendar_id, titular, erro = _resolve_calendar_target(usuario)
    if erro:
        return erro

    eventos = _localizar_eventos_por_termo(service, calendar_id, termo_busca, data_referencia)
    if not eventos:
        data_str = f" na data {data_referencia}" if data_referencia else ""
        return f"Não encontrei nenhum evento com o termo '{termo_busca}'{data_str} na agenda de {titular}."

    if len(eventos) > 1:
        linhas = [f"Encontrei mais de um evento com o termo '{termo_busca}' na agenda de {titular}. Por favor, especifique qual deseja editar:"]
        for ev in eventos:
            hora = _formatar_horario_evento(ev)
            summary = ev.get('summary', 'Sem título')
            linhas.append(f"• **{summary}** – {hora}")
        return "\n".join(linhas)

    alvo = eventos[0]
    event_id = alvo.get("id")
    titulo_antigo = alvo.get("summary", "Evento")

    patch_body = {}
    alteracoes = []

    if novo_titulo:
        patch_body['summary'] = novo_titulo
        alteracoes.append(f"título para '{novo_titulo}'")

    if nova_descricao is not None:
        patch_body['description'] = nova_descricao
        alteracoes.append("descrição atualizada")

    if nova_localizacao is not None:
        patch_body['location'] = nova_localizacao
        alteracoes.append(f"local para '{nova_localizacao}'")

    if novo_inicio_iso:
        try:
            inicio_dt = datetime.fromisoformat(novo_inicio_iso.replace('Z', '+00:00'))
            if nova_duracao_minutos:
                duracao = nova_duracao_minutos
            else:
                try:
                    orig_start_str = alvo.get('start', {}).get('dateTime')
                    orig_end_str = alvo.get('end', {}).get('dateTime')
                    if orig_start_str and orig_end_str:
                        orig_start = datetime.fromisoformat(orig_start_str.replace('Z', '+00:00'))
                        orig_end = datetime.fromisoformat(orig_end_str.replace('Z', '+00:00'))
                        duracao = max(15, int((orig_end - orig_start).total_seconds() / 60))
                    else:
                        duracao = 60
                except Exception:
                    duracao = 60

            fim_dt = inicio_dt + timedelta(minutes=duracao)
            patch_body['start'] = {'dateTime': inicio_dt.isoformat()}
            patch_body['end'] = {'dateTime': fim_dt.isoformat()}
            alteracoes.append(f"horário para {inicio_dt.strftime('%d/%m/%Y às %H:%M')}")
        except Exception as e:
            logger.error(f"Erro ao parsear novo horário: {e}")
            return f"Formato de horário inválido: '{novo_inicio_iso}'."

    if not patch_body:
        return f"Nenhuma alteração foi solicitada para o evento '{titulo_antigo}'."

    try:
        updated_event = service.events().patch(calendarId=calendar_id, eventId=event_id, body=patch_body).execute()
        agenda_indicador = f" na agenda de {titular}" if titular != UserContext.get_user_name() else " na sua agenda"
        titulo_final = updated_event.get('summary', titulo_antigo)
        return f"Evento '{titulo_final}' atualizado com sucesso{agenda_indicador}! Alterações realizadas: {', '.join(alteracoes)}."
    except Exception as e:
        logger.error(f"Erro ao editar evento {event_id}: {e}")
        return f"Ocorreu um erro ao tentar editar o evento '{titulo_antigo}': {e}"

