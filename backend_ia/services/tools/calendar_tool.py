import os
import logging
from datetime import datetime, timedelta, timezone
from google.oauth2 import service_account
from googleapiclient.discovery import build
from config.settings import settings

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

def agendar_evento(
    titulo: str, 
    inicio_iso: str, 
    duracao_minutos: int = 60,
    descricao: str = None,
    localizacao: str = None
) -> str:
    """
    Agenda um evento ou reunião no Google Calendar do usuário.
    Use esta ferramenta quando o usuário pedir para marcar algo na agenda.

    Args:
        titulo (str): O nome do evento.
        inicio_iso (str): Data e hora de início no formato ISO (ex: '2026-03-10T15:00:00-03:00').
        duracao_minutos (int): Duração do evento em minutos.
        descricao (str, optional): Descrição, notas ou pauta detalhada do evento.
        localizacao (str, optional): Localização física, sala ou link de videoconferência.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada pelo administrador."

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

        calendar_id = settings.CALENDAR_ID if settings.CALENDAR_ID else 'primary'
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        info_extra = []
        if localizacao:
            info_extra.append(f"Local: {localizacao}")
        if descricao:
            info_extra.append(f"Descrição: {descricao}")
        extra_str = f" ({', '.join(info_extra)})" if info_extra else ""

        return f"Evento '{titulo}' agendado com sucesso!{extra_str} (Link: {created_event.get('htmlLink')})"
    
    except Exception as e:
        logger.error(f"Erro ao criar evento: {e}")
        return f"Não consegui agendar o evento devido a um erro: {e}"

def consultar_agenda(dias: int = 1, dias_a_frente: int = None) -> str:
    """
    Consulta os próximos eventos no Google Calendar do usuário.
    Use esta ferramenta para saber o que o usuário tem marcado.

    Args:
        dias (int): Número de dias no futuro para buscar eventos (default: 1).
        dias_a_frente (int, optional): Alias para número de dias no futuro.
    """
    service = _get_calendar_service()
    if not service:
        return "A integração com o Google Calendar ainda não foi configurada."

    limite_dias = dias_a_frente if dias_a_frente is not None else dias

    try:
        now = datetime.now(timezone.utc).isoformat()
        time_max = (datetime.now(timezone.utc) + timedelta(days=limite_dias)).isoformat()

        calendar_id = settings.CALENDAR_ID if settings.CALENDAR_ID else 'primary'
        events_result = service.events().list(
            calendarId=calendar_id, timeMin=now, timeMax=time_max,
            maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = events_result.get('items', [])

        if not events:
            return "Sua agenda está livre para esse período!"
        
        resp = "Você tem os seguintes eventos:\n"
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'Sem título')
            loc = f" | Local: {event['location']}" if event.get('location') else ""
            desc = f" | Descrição: {event['description']}" if event.get('description') else ""
            resp += f"- {start}: {summary}{loc}{desc}\n"
        return resp
    
    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        return "Erro ao acessar a agenda."
