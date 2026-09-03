import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "DAM_Instance"
    GEMINI_API_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-adminsdk.json"
    WEBHOOK_TOKEN: str = ""
    CALENDAR_ID: str = ""

    # Número pessoal permitido para interagir (Security & Privacy)
    ALLOWED_PHONE_NUMBER: str = ""

    # Automação Residencial (Alexa / Voice Monkey)
    VOICE_MONKEY_API_TOKEN: str = ""

    # Catálogo e Streaming de Filmes/Séries (TMDB API)
    TMDB_API_KEY: str = ""
    TMDB_ACCESS_TOKEN: str = ""

    # Mobilidade Urbana e Rotas (Google Maps)
    GOOGLE_MAPS_API_KEY: str = ""
    USER_HOME_ADDRESS: str = ""
    USER_WORK_ADDRESS: str = ""

    # Cofre Criptografado de Credenciais (AES-256)
    VAULT_SECRET_KEY: str = ""
    VAULT_ENCRYPTION_KEY: str = ""

    # Pagamentos e Rateios (Chave Pix)
    USER_PIX_KEY: str = ""

    # Rastreamento de Animes (AniList API)
    ANILIST_USERNAME: str = ""
    ANILIST_ACCESS_TOKEN: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
