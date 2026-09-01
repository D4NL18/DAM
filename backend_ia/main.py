from fastapi import FastAPI
from routers import webhook
from config.firebase import init_firebase
from services.ai_service import AIService
from contextlib import asynccontextmanager

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

@app.get("/")
def health_check():
    return {"status": "ok", "service": "DAM Motor IA"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
