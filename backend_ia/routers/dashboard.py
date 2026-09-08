import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Query
from config import firebase
from services.tools.calendar_tool import _get_calendar_service
from services.tools.notes_tool import _obter_todos_itens
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Dashboard"])

@router.get("/finance/monthly-summary")
def get_finance_monthly_summary(
    year: int = Query(default=datetime.now().year),
    month: int = Query(default=datetime.now().month)
) -> Dict[str, Any]:
    """
    Retorna o resumo financeiro mensal consultando diretamente a coleção 'finances' no Firestore.
    Se a coleção estiver vazia, retorna listas zeradas sem mocks artificiais.
    """
    total_spent = 0.0
    category_map: Dict[str, float] = {}
    recent_txs: List[Dict[str, Any]] = []

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("finances").stream()
            for doc in docs:
                data = doc.to_dict() or {}
                # Filtragem de ano e mês (campo 'date' ou 'created_at')
                date_str = data.get("date") or data.get("created_at") or ""
                valido = True
                if date_str:
                    try:
                        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        if dt.year != year or dt.month != month:
                            valido = False
                    except Exception:
                        pass

                if valido:
                    amount = float(data.get("amount") or 0.0)
                    category = data.get("category") or "Outros"
                    total_spent += amount
                    category_map[category] = category_map.get(category, 0.0) + amount

                    recent_txs.append({
                        "id": doc.id,
                        "date": date_str or datetime.now().isoformat(),
                        "description": data.get("description") or "Transação sem descrição",
                        "amount": amount,
                        "category": category
                    })
        except Exception as e:
            logger.error(f"Erro ao consultar finances no Firestore: {e}")

    # Ordena as transações mais recentes
    recent_txs.sort(key=lambda x: x.get("date", ""), reverse=True)

    expenses_by_category = [
        {"category": cat, "amount": round(val, 2)}
        for cat, val in sorted(category_map.items(), key=lambda x: x[1], reverse=True)
    ]

    return {
        "totalSpent": round(total_spent, 2),
        "currency": "BRL",
        "expensesByCategory": expenses_by_category,
        "recentTransactions": recent_txs[:10]
    }

@router.get("/health/summary")
def get_health_summary(
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Retorna o resumo de métricas de saúde consultando a coleção 'health_metrics' no Firestore.
    Se não houver métricas, retorna valores zerados sem dados mockados.
    """
    step_count = 0
    active_energy = 0
    heart_rate_avg = 0
    sleep_hours = 0.0
    metrics_list: List[Dict[str, Any]] = []

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("health_metrics").stream()
            for doc in docs:
                payload = doc.to_dict() or {}
                raw_data = payload.get("data") or {}
                metrics = raw_data.get("metrics") or []

                for m in metrics:
                    name = m.get("name")
                    m_data = m.get("data") or []
                    if not m_data:
                        continue

                    if name == "step_count" and step_count == 0:
                        step_count = int(m_data[0].get("qty") or 0)
                    elif name == "active_energy" and active_energy == 0:
                        active_energy = int(m_data[0].get("qty") or 0)
                    elif name == "heart_rate" and heart_rate_avg == 0:
                        heart_rate_avg = int(m_data[0].get("Avg") or m_data[0].get("qty") or 0)
                    elif name == "sleep_analysis" and sleep_hours == 0.0:
                        sleep_hours = float(m_data[0].get("total_sleep") or m_data[0].get("qty") or 0.0)

                metrics_list.append({"id": doc.id, "created_at": payload.get("created_at")})
        except Exception as e:
            logger.error(f"Erro ao consultar health_metrics no Firestore: {e}")

    return {
        "stepCount": step_count,
        "totalSteps": step_count,
        "activeEnergyBurned": active_energy,
        "totalActiveEnergyBurned": active_energy,
        "heartRateAvg": heart_rate_avg,
        "avgHeartRate": heart_rate_avg,
        "sleepHours": round(sleep_hours, 1),
        "metrics": metrics_list,
        "dailyRecords": []
    }

@router.get("/agenda")
@router.get("/agenda/summary")
def get_agenda_summary(period: str = Query(default="hoje")) -> Dict[str, Any]:
    """
    Retorna a agenda (hoje, semana ou mês) e lembretes consultando diretamente o Google Calendar e 'notes_reminders'.
    Se não houver compromissos, retorna lista vazia.
    """
    upcoming_events: List[Dict[str, Any]] = []
    meeting_hours = 0.0

    service = _get_calendar_service()
    if service:
        try:
            now = datetime.now(timezone.utc)
            hoje_inicio = now.replace(hour=0, minute=0, second=0, microsecond=0)

            if period == "semana":
                dias_desde_domingo = (now.weekday() + 1) % 7
                start_day_dt = hoje_inicio - timedelta(days=dias_desde_domingo)
                end_day_dt = start_day_dt + timedelta(days=7)
            elif period == "mes":
                start_day_dt = hoje_inicio.replace(day=1)
                if start_day_dt.month == 12:
                    end_day_dt = start_day_dt.replace(year=start_day_dt.year + 1, month=1)
                else:
                    end_day_dt = start_day_dt.replace(month=start_day_dt.month + 1)
            else:  # "hoje"
                start_day_dt = hoje_inicio
                end_day_dt = hoje_inicio + timedelta(days=1)

            start_day = start_day_dt.isoformat()
            end_day = end_day_dt.isoformat()
            calendar_id = settings.CALENDAR_ID if settings.CALENDAR_ID else 'primary'

            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=start_day,
                timeMax=end_day,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            items = events_result.get('items', [])
            for item in items:
                start = item.get('start', {}).get('dateTime') or item.get('start', {}).get('date', '')
                end = item.get('end', {}).get('dateTime') or item.get('end', {}).get('date', '')

                # Cálculo de duração
                try:
                    s_dt = datetime.fromisoformat(start)
                    e_dt = datetime.fromisoformat(end)
                    duracao = (e_dt - s_dt).total_seconds() / 3600.0
                    meeting_hours += duracao
                    if period in ["semana", "mes"]:
                        hora_inicio = s_dt.strftime("%d/%m %H:%M")
                        hora_fim = e_dt.strftime("%H:%M")
                    else:
                        hora_inicio = s_dt.strftime("%H:%M")
                        hora_fim = e_dt.strftime("%H:%M")
                except Exception:
                    hora_inicio = start[:10] if len(start) >= 10 else start
                    hora_fim = end[:10] if len(end) >= 10 else end

                summary_lower = (item.get('summary') or '').lower()
                cat = "reuniao" if any(w in summary_lower for w in ["reunião", "sync", "call", "meet", "alinhamento"]) else (
                    "saude" if any(w in summary_lower for w in ["médic", "dentist", "exame", "treino", "academia"]) else (
                        "pessoal" if any(w in summary_lower for w in ["almoço", "jantar", "aniversário", "cinema", "viagem"]) else "trabalho"
                    )
                )

                upcoming_events.append({
                    "id": item.get('id', ''),
                    "title": item.get('summary', 'Sem Título'),
                    "description": item.get('description', ''),
                    "startTime": hora_inicio,
                    "endTime": hora_fim,
                    "location": item.get('location', ''),
                    "meetUrl": item.get('hangoutLink', ''),
                    "category": cat,
                    "status": "confirmed"
                })
        except Exception as e:
            logger.error(f"Erro ao buscar Google Calendar no endpoint da agenda: {e}")

    # Lembretes reais da coleção 'notes_reminders'
    lembretes_reais = []
    try:
        todos_itens = _obter_todos_itens()
        for item in todos_itens:
            lembretes_reais.append({
                "id": item.get("id", ""),
                "text": item.get("title", ""),
                "dueTime": item.get("due_date", ""),
                "completed": item.get("status") == "completed"
            })
    except Exception as e:
        logger.warning(f"Erro ao ler lembretes para a agenda: {e}")

    next_event = upcoming_events[0] if upcoming_events else None

    return {
        "todayTotalEvents": len(upcoming_events),
        "totalMeetingHours": round(meeting_hours, 1),
        "nextEvent": next_event,
        "upcomingEvents": upcoming_events,
        "insights": [],
        "reminders": lembretes_reais[:5]
    }
