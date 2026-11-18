import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timezone, timedelta
from routers import webhook, health, billing, dashboard, briefing, files, finance, translation
from config.firebase import init_firebase
from services.ai_service import AIService
from typing import Optional
from services.briefing_service import (
    enviar_briefing_matinal,
    verificar_e_disparar_briefings_agendados,
    _obter_todos_usuarios_briefing,
    obter_preferencias_briefing,
    _normalizar_horario,
)
from services.tools.clash_of_clans_tool import alerta_raid_capital, alerta_clan_war
from services.whatsapp_service import WhatsAppService
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

_briefing_schedule_changed = asyncio.Event()
_main_loop: Optional[asyncio.AbstractEventLoop] = None


def notificar_mudanca_briefing() -> None:
    """Acorda o scheduler de briefing de forma thread-safe quando preferências mudam."""
    try:
        if _main_loop is not None and _main_loop.is_running():
            _main_loop.call_soon_threadsafe(_briefing_schedule_changed.set)
        else:
            _briefing_schedule_changed.set()
    except Exception:
        pass


def _coletar_horarios_alvo() -> list[str]:
    """Lê preferências dos usuários configurados e retorna horários únicos ordenados."""
    horarios = set()
    try:
        for uid in _obter_todos_usuarios_briefing():
            prefs = obter_preferencias_briefing(uid)
            if prefs.get("ativo", True):
                horarios.add(_normalizar_horario(prefs.get("horario", "08:00")))
    except Exception as e:
        logger.error(f"Erro ao coletar horários de briefing: {e}")
    if not horarios:
        horarios.add("08:00")
    return sorted(horarios)


def _calcular_segundos_ate(hora_alvo: str, tz) -> float:
    """Calcula segundos até o próximo HH:MM alvo (+1s de margem contra wake-up precoce)."""
    agora = datetime.now(tz)
    partes = hora_alvo.split(":")
    alvo_hoje = agora.replace(hour=int(partes[0]), minute=int(partes[1]), second=0, microsecond=0)
    if alvo_hoje <= agora:
        alvo_hoje += timedelta(days=1)
    return max(1.0, (alvo_hoje - agora).total_seconds() + 1.0)


async def _rotina_briefing_diario():
    """Scheduler event-driven: dorme até o próximo horário agendado sem polling no Firestore."""
    global _main_loop
    _main_loop = asyncio.get_running_loop()
    tz_br = timezone(timedelta(hours=-3))
    startup_catchup_done = False

    while True:
        try:
            agora = datetime.now(tz_br)
            hora_atual = agora.strftime("%H:%M")

            # Catch-up único na inicialização caso o servidor suba durante a janela matinal
            if not startup_catchup_done:
                startup_catchup_done = True
                if "06:00" <= hora_atual < "12:00":
                    if not await asyncio.to_thread(WhatsAppService.is_connected, True):
                        logger.warning("[Briefing Scheduler] WhatsApp desconectado. Catch-up de inicialização ignorado.")
                    else:
                        logger.info(f"[Briefing Scheduler] Executando catch-up único de inicialização às {hora_atual}...")
                        disparados_init = await asyncio.to_thread(
                            verificar_e_disparar_briefings_agendados, hora_atual, False, True
                        )
                        if disparados_init:
                            logger.info(f"[Briefing Scheduler] Catch-up enviado para: {', '.join(disparados_init)}")

            _briefing_schedule_changed.clear()
            horarios = await asyncio.to_thread(_coletar_horarios_alvo)
            logger.info(f"[Briefing Scheduler] Horários agendados: {horarios}")

            agora = datetime.now(tz_br)
            hora_atual = agora.strftime("%H:%M")
            proximos_hoje = [h for h in horarios if h > hora_atual]
            proximo = proximos_hoje[0] if proximos_hoje else horarios[0]
            segundos = _calcular_segundos_ate(proximo, tz_br)

            logger.info(f"[Briefing Scheduler] Próximo disparo: {proximo} (em {int(segundos)}s)")

            try:
                await asyncio.wait_for(_briefing_schedule_changed.wait(), timeout=segundos)
                logger.info("[Briefing Scheduler] Preferências alteradas, recalculando horários...")
                continue
            except asyncio.TimeoutError:
                pass

            if not await asyncio.to_thread(WhatsAppService.is_connected, True):
                logger.warning("[Briefing Scheduler] WhatsApp desconectado. Disparo agendado ignorado sem retries.")
                continue

            hora_disparo = datetime.now(tz_br).strftime("%H:%M")
            logger.info(f"[Briefing Scheduler] Disparando briefings para {hora_disparo}...")
            disparados = await asyncio.to_thread(
                verificar_e_disparar_briefings_agendados, hora_disparo, False, True
            )
            if disparados:
                logger.info(f"[Briefing Scheduler] Briefing enviado para: {', '.join(disparados)}")
        except Exception as e:
            logger.error(f"[Briefing Scheduler] Erro: {e}")
            await asyncio.sleep(300)

async def _rotina_raid_capital():
    """Job: Todo domingo as 12:00 (Brasilia) — Alerta de Raid Weekend da Capital do Cla."""
    tz_br = timezone(timedelta(hours=-3))
    while True:
        try:
            agora = datetime.now(tz_br)
            if agora.weekday() == 6 and agora.hour == 12 and agora.minute == 0:
                if not await asyncio.to_thread(WhatsAppService.is_connected, True):
                    logger.warning("[CoC Scheduler] WhatsApp desconectado. Alerta de Raid Weekend ignorado.")
                else:
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
                if not await asyncio.to_thread(WhatsAppService.is_connected, True):
                    logger.warning("[CoC Scheduler] WhatsApp desconectado. Alerta de Guerra de Clas ignorado.")
                else:
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
