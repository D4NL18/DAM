import logging
import google.generativeai as genai
from config.settings import settings
from repositories.chat_repository import ChatRepository
from services.tools.health_tool import consultar_saude
from services.tools.finance_tool import registrar_gasto
from services.tools.calendar_tool import agendar_evento, consultar_agenda
from services.tools.vehicle_tool import consultar_status_veiculo, acionar_travas_veiculo
from services.tools.esports_tool import consultar_jogos_cs2
from services.tools.alexa_tool import acionar_rotina_alexa, falar_na_alexa
from datetime import datetime

import base64
from typing import Optional

logger = logging.getLogger(__name__)

# Lista de ferramentas que a IA pode usar
AVAILABLE_TOOLS = [
    consultar_saude,
    registrar_gasto,
    agendar_evento,
    consultar_agenda,
    consultar_status_veiculo,
    acionar_travas_veiculo,
    consultar_jogos_cs2,
    acionar_rotina_alexa,
    falar_na_alexa
]

class AIService:
    @staticmethod
    def setup():
        if not settings.GEMINI_API_KEY:
            logger.warning("Aviso: GEMINI_API_KEY não configurada.")
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)

    @staticmethod
    def process_message(
        remote_jid: str, 
        user_text: str, 
        media_base64: Optional[str] = None, 
        media_mimetype: Optional[str] = None
    ) -> str:
        # Busca o histórico do usuário
        history_docs = ChatRepository.get_recent_history(remote_jid, limit=10)
        
        # Constrói o histórico no formato para start_chat
        history = []
        for msg in history_docs:
            role = "model" if msg.get("fromMe") else "user"
            history.append({"role": role, "parts": [msg.get("text")]})

        try:
            agora = datetime.now().strftime("%Y-%m-%d %H:%M")
            model = genai.GenerativeModel(
                model_name='gemini-3.6-flash',
                tools=AVAILABLE_TOOLS,
                system_instruction=(
                    f"Você é o DAM, assistente pessoal inteligente. Hoje é {agora}. "
                    "Se receber fotos ou notas fiscais, analise os itens e valores. "
                    "Se receber áudios, responda diretamente ao conteúdo falado. "
                    "\n\n### REGRA FINANCEIRA MANDATÓRIA (MÉTODOS DE PAGAMENTO):\n"
                    "O usuário possui exatamente 3 formas/cartões de pagamento:\n"
                    "1. 'Cartão de Crédito Secundário' (cartão de crédito secundário ou compartilhado)\n"
                    "2. 'Cartão de Crédito Pessoal' (cartão de crédito titular pessoal)\n"
                    "3. 'Cartão de Débito' (conta corrente/débito. SE for Pix, cai SEMPRE aqui no débito)\n\n"
                    "REGRA DE CONDUTA:\n"
                    "- Se o usuário informar um gasto/compra e ESPECIFICAR a forma (ou se for Pix), chame a ferramenta 'registrar_gasto' imediatamente com o 'metodo_pagamento' correto.\n"
                    "- Se o usuário informar um gasto/compra e NÃO disser qual cartão/conta usou (e NÃO for Pix), NÃO chame a ferramenta ainda! Pergunte obrigatoriamente e educadamente ao usuário em qual cartão foi a cobrança ('Foi no seu cartão de crédito pessoal, no secundário ou no débito?'). Assim que ele responder, registre o gasto."
                )
            )
            
            chat = model.start_chat(
                history=history,
                enable_automatic_function_calling=True
            )
            
            if media_base64 and media_mimetype:
                media_bytes = base64.b64decode(media_base64)
                part = {
                    "mime_type": media_mimetype,
                    "data": media_bytes
                }
                response = chat.send_message([part, user_text])
            else:
                response = chat.send_message(user_text)

            return response.text
        except Exception as e:
            logger.error(f"Erro no Gemini: {e}")
            return "Desculpe, meus servidores estão indisponíveis no momento. Tente novamente mais tarde."
