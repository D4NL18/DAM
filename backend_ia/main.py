import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from datetime import datetime, timezone, timedelta
from routers import webhook, health, billing, dashboard, briefing
from config.firebase import init_firebase
from services.ai_service import AIService
from services.briefing_service import enviar_briefing_matinal
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

async def _rotina_briefing_diario():
    """Tarefa em background que verifica se são 08:00 (Brasília) para disparar o briefing matinal."""
    tz_br = timezone(timedelta(hours=-3))
    while True:
        try:
            agora = datetime.now(tz_br)
            # Se for 08:00 da manhã
            if agora.hour == 8 and agora.minute == 0:
                logger.info("Horário de Morning Briefing atingido (08:00 Brasília). Disparando...")
                enviar_briefing_matinal(force=False)
                # Dorme 65 segundos para não disparar mais de uma vez dentro do mesmo minuto
                await asyncio.sleep(65)
        except Exception as e:
            logger.error(f"Erro no scheduler do briefing matinal: {e}")
        
        await asyncio.sleep(30)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializações na subida do app
    init_firebase()
    AIService.setup()
    
    # Inicia scheduler matinal em background
    scheduler_task = asyncio.create_task(_rotina_briefing_diario())
    yield
    scheduler_task.cancel()

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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Registrando rotas
app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(billing.router)
app.include_router(dashboard.router)
app.include_router(briefing.router)

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "DAM Motor IA"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
