import logging
from fastapi import FastAPI
from routers import webhook, health, billing
from config.firebase import init_firebase
from services.ai_service import AIService
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializações na subida do app
    init_firebase()
    AIService.setup()
    yield
    # Limpezas no encerramento (se necessário)

app = FastAPI(title="DAM IA Assistant", lifespan=lifespan)

# Registrando rotas
app.include_router(webhook.router)
app.include_router(health.router)
app.include_router(billing.router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "DAM Motor IA"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
