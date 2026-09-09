import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timezone, timedelta
from routers import webhook, health, billing, dashboard, briefing, files, finance
from config.firebase import init_firebase
from services.ai_service import AIService
from services.briefing_service import enviar_briefing_matinal, verificar_e_disparar_briefings_agendados
from services.tools.clash_of_clans_tool import alerta_raid_capital, alerta_clan_war
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def _rotina_briefing_diario():
    """Tarefa em background que verifica minuto a minuto os horários de briefing dos usuários ativos."""
    tz_br = timezone(timedelta(hours=-3))
    ultimo_minuto_disparado = None
    while True:
        try:
            agora = datetime.now(tz_br)
            minuto_atual = agora.strftime("%Y-%m-%d %H:%M")
            hora_minuto = agora.strftime("%H:%M")

            if minuto_atual != ultimo_minuto_disparado:
                ultimo_minuto_disparado = minuto_atual
                disparados = await asyncio.to_thread(verificar_e_disparar_briefings_agendados, hora_minuto, False, True)
                if disparados:
                    logger.info(f"Morning Briefing disparado às {hora_minuto} para: {', '.join(disparados)}")
        except Exception as e:
            logger.error(f"Erro no scheduler do briefing matinal: {e}")
        
        await asyncio.sleep(30)

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

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DAM Motor IA"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
