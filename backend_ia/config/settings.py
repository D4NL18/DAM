import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "DAM_Instance"
    GEMINI_API_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-adminsdk.json"
    WEBHOOK_TOKEN: str = "DamBot2026SecureKey!"
    CALENDAR_ID: str = ""

    # Número pessoal permitido para interagir (Security & Privacy)
    ALLOWED_PHONE_NUMBER: str = ""

    # Voice Monkey API (Automação Residencial Alexa)
    VOICE_MONKEY_API_TOKEN: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
