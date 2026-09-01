import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "DAM_Instance"
    GEMINI_API_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-adminsdk.json"
    WEBHOOK_TOKEN: str = "DamBot2026SecureKey!"

    # Número pessoal permitido para interagir (Security & Privacy)
    ALLOWED_PHONE_NUMBER: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
