import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    EVOLUTION_API_URL: str = "http://localhost:8080"
    EVOLUTION_API_KEY: str = ""
    EVOLUTION_INSTANCE_NAME: str = "DAM_Instance"
    GEMINI_API_KEY: str = ""
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-adminsdk.json"
    WEBHOOK_TOKEN: str = ""
    # Google Calendar IDs por usuário
    CALENDAR_ID: str = ""
    CALENDAR_ID_DANIEL: str = ""
    CALENDAR_ID_LARI: str = ""

    # Números permitidos para interagir (Security & Privacy)
    ALLOWED_PHONE_NUMBER: str = "5511999999999"
    ALLOWED_PHONE_NUMBERS: str = "5511999999999,5511888888888"

    @property
    def allowed_numbers_list(self) -> list[str]:
        nums = [n.strip() for n in self.ALLOWED_PHONE_NUMBERS.split(",") if n.strip()]
        if self.ALLOWED_PHONE_NUMBER and self.ALLOWED_PHONE_NUMBER not in nums:
            nums.append(self.ALLOWED_PHONE_NUMBER)
        return nums


    # Número do WhatsApp Business do Bot (DAM)
    BOT_PHONE_NUMBER: str = "5511777777777"

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

    # Clash of Clans (Supercell API)
    COC_API_TOKEN: str = ""
    COC_CLAN_TAG: str = ""
    COC_PLAYER_TAG: str = ""

    # Google Cloud Translation API (US-10)
    GOOGLE_TRANSLATE_API_KEY: str = ""
    TRANSLATION_FREE_TIER_MONTHLY_LIMIT: int = 500000

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
