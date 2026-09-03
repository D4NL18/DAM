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

    # TMDB API (Guia de Streaming Onde Assistir)
    TMDB_API_KEY: str = ""
    TMDB_ACCESS_TOKEN: str = ""

    # Google Maps API & Endereços Favoritos (Fase 8)
    GOOGLE_MAPS_API_KEY: str = ""
    USER_HOME_ADDRESS: str = "Avenida Paulista, 1000 - Bela Vista, São Paulo - SP"
    USER_WORK_ADDRESS: str = "Avenida Brigadeiro Faria Lima, 3500 - Itaim Bibi, São Paulo - SP"

    # Cofre Seguro de Senhas e Credenciais (Fase 13)
    VAULT_SECRET_KEY: str = "DAM_VAULT_MASTER_SECRET_2026"
    VAULT_ENCRYPTION_KEY: str = ""

    # Chave Pix do Usuário (Divisor de Contas / Splitwise - Fases 11 e 18)
    USER_PIX_KEY: str = ""

    # Perfil AniList (Anime Tracker)
    ANILIST_USERNAME: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
