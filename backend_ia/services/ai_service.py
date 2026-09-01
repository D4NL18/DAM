import logging
import google.generativeai as genai
from config.settings import settings
from repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def setup():
        if not settings.GEMINI_API_KEY:
            logger.warning("Aviso: GEMINI_API_KEY não configurada.")
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def process_message(remote_jid: str, user_text: str) -> str:
        # Busca o histórico do usuário
        history = ChatRepository.get_recent_history(remote_jid, limit=10)
        
        # Constrói o histórico no formato esperado pelo genai (opcionalmente)
        messages = []
        for msg in history:
            role = "model" if msg.get("fromMe") else "user"
            messages.append({"role": role, "parts": [msg.get("text")]})
            
        # Adiciona a mensagem atual se ela já não for a última no histórico (evita duplicação)
        if not messages or messages[-1].get("role") != "user" or messages[-1].get("parts")[0] != user_text:
            messages.append({"role": "user", "parts": [user_text]})

        try:
            model = genai.GenerativeModel('gemini-flash-latest')
            # system instruction pode ser adicionada ao modelo aqui se necessário.
            
            response = model.generate_content(messages)
            return response.text
        except Exception as e:
            logger.error(f"Erro no Gemini: {e}")
            return "Desculpe, meus servidores estão indisponíveis no momento. Tente novamente mais tarde."
