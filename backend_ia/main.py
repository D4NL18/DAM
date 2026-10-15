import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timezone, timedelta
from routers import webhook, health, billing, dashboard, briefing, files, finance, translation
from config.firebase import init_firebase
from services.ai_service import AIService
from services.briefing_service import (
    enviar_briefing_matinal,
    verificar_e_disparar_briefings_agendados,
    _obter_todos_usuarios_briefing,
    obter_preferencias_briefing,
    _normalizar_horario,
)
from services.tools.clash_of_clans_tool import alerta_raid_capital, alerta_clan_war
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Evento para forçar o scheduler a recarregar os horários quando preferências mudam
_briefing_schedule_changed = asyncio.Event()

def notificar_mudanca_briefing():
    """Chamado quando preferências de briefing são alteradas para o scheduler recalcular."""
    try:
        _briefing_schedule_changed.set()
    except Exception:
        pass


def _coletar_horarios_alvo() -> list[str]:
    """Lê preferências de todos os usuários UMA VEZ e retorna lista de horários únicos ordenados."""
    horarios = set()
    try:
        usuarios = _obter_todos_usuarios_briefing()
        for uid in usuarios:
            prefs = obter_preferencias_briefing(uid)
            if prefs.get("ativo", True):
                h = _normalizar_horario(prefs.get("horario", "08:00"))
                horarios.add(h)
    except Exception as e:
        logger.error(f"Erro ao coletar horários de briefing: {e}")
    if not horarios:
        horarios.add("08:00")
    return sorted(horarios)


def _calcular_segundos_ate(hora_alvo: str, tz) -> float:
    """Calcula quantos segundos faltam até o horário HH:MM de hoje (ou amanhã se já passou)."""
    agora = datetime.now(tz)
    partes = hora_alvo.split(":")
    alvo_hoje = agora.replace(hour=int(partes[0]), minute=int(partes[1]), second=0, microsecond=0)
    if alvo_hoje <= agora:
        alvo_hoje += timedelta(days=1)
    return (alvo_hoje - agora).total_seconds()


async def _rotina_briefing_diario():
    """Scheduler event-driven: dorme até o próximo horário de briefing ao invés de poll a cada 30s."""
    tz_br = timezone(timedelta(hours=-3))

    while True:
        try:
            # 1. Coleta horários configurados (leitura única no Firestore)
            horarios = await asyncio.to_thread(_coletar_horarios_alvo)
            logger.info(f"[Briefing Scheduler] Horários agendados: {horarios}")

            # 2. Encontra o próximo horário mais perto
            agora = datetime.now(tz_br)
            hora_atual = agora.strftime("%H:%M")
            proximos_hoje = [h for h in horarios if h > hora_atual]

            if proximos_hoje:
                proximo = proximos_hoje[0]
                segundos = _calcular_segundos_ate(proximo, tz_br)
            else:
                # Todos os horários de hoje já passaram, dorme até o primeiro de amanhã
                proximo = horarios[0]
                segundos = _calcular_segundos_ate(proximo, tz_br)

            logger.info(f"[Briefing Scheduler] Próximo disparo: {proximo} (em {int(segundos)}s)")

            # 3. Dorme até o horário alvo OU até ser acordado por mudança de preferências
            _briefing_schedule_changed.clear()
            try:
                await asyncio.wait_for(_briefing_schedule_changed.wait(), timeout=segundos)
                # Se chegou aqui, foi acordado por mudança de preferências — recalcula
                logger.info("[Briefing Scheduler] Preferências alteradas, recalculando horários...")
                continue
            except asyncio.TimeoutError:
                pass  # Timeout normal = chegou a hora do disparo

            # 4. Dispara os briefings para o horário atual
            hora_disparo = datetime.now(tz_br).strftime("%H:%M")
            logger.info(f"[Briefing Scheduler] Disparando briefings para {hora_disparo}...")
            disparados = await asyncio.to_thread(
                verificar_e_disparar_briefings_agendados, hora_disparo, False, True
            )
            if disparados:
                logger.info(f"[Briefing Scheduler] Briefing enviado para: {', '.join(disparados)}")

        except Exception as e:
            logger.error(f"[Briefing Scheduler] Erro: {e}")
            # Backoff de 5 minutos em caso de erro para não martelar Firestore
            await asyncio.sleep(300)

async def _rotina_raid_capital():
    """Job: Todo domingo as 12:00 (Brasilia) — Alerta de Raid Weekend da Capital do Cla."""
    tz_br = timezone(timedelta(hours=-3))
    while True:
        try:
            agora = datetime.now(tz_br)
            if agora.weekday() == 6 and agora.hour == 12 and agora.minute == 0:
                logger.info("[CoC Scheduler] Disparando alerta de Raid Weekend (Domingo 12:00 Brasilia).")
                await asyncio.to_thread(alerta_raid_capital)
                await asyncio.sleep(65)
        except Exception as e:
            logger.error(f"[CoC Scheduler] Erro no scheduler de Raid Weekend: {e}")
        await asyncio.sleep(30)

async def _rotina_guerra_clas():
    """Job: Diariamente as 06:00 (Brasilia) — Alerta de Guerra de Clas ativa."""
    tz_br = timezone(timedelta(hours=-3))
    while True:
        try:
            agora = datetime.now(tz_br)
            if agora.hour == 6 and agora.minute == 0:
                logger.info("[CoC Scheduler] Disparando alerta de Guerra de Clas (06:00 Brasilia).")
                await asyncio.to_thread(alerta_clan_war)
                await asyncio.sleep(65)
        except Exception as e:
            logger.error(f"[CoC Scheduler] Erro no scheduler de Guerra de Clas: {e}")
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializações na subida do app
    init_firebase()
    AIService.setup()
    
    # Inicia schedulers em background
    scheduler_task = asyncio.create_task(_rotina_briefing_diario())
    raid_task = asyncio.create_task(_rotina_raid_capital())
    war_task = asyncio.create_task(_rotina_guerra_clas())
    yield
    scheduler_task.cancel()
    raid_task.cancel()
    war_task.cancel()

from middleware.rate_limiter import RateLimiterMiddleware
from middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(title="DAM IA Assistant", lifespan=lifespan)

# Middlewares de Defesa e Segurança
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    RateLimiterMiddleware,
    max_requests_per_minute=100,
    webhook_max_requests_per_minute=200
)

# Configuração de CORS Restritivo (apenas domínios autorizados do Dashboard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://bot-dam-72ef2.web.app",
        "https://bot-dam-72ef2.firebaseapp.com",
        "http://localhost:4200"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Registrando rotas
app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(finance.router)
app.include_router(briefing.router)
app.include_router(files.router)
app.include_router(translation.router)

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DAM Motor IA"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
