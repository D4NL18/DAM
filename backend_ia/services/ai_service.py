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
from services.tools.maps_tool import consultar_rota, calcular_horario_saida
from services.tools.notes_tool import (
    criar_anotacao,
    criar_lembrete,
    buscar_anotacoes,
    listar_lembretes_pendentes,
    concluir_lembrete
)
from services.tools.gift_curator_tool import (
    salvar_ideia_presente,
    consultar_ideias_presente,
    alertar_datas_proximas
)
from services.tools.restaurant_split_tool import dividir_conta_restaurante
from services.tools.item_finder_tool import (
    registrar_localizacao_objeto,
    onde_guardei_objeto,
    listar_historico_movimentacoes
)
from services.tools.password_vault_tool import (
    salvar_credencial,
    consultar_credencial,
    gerar_senha_forte,
    listar_servicos_cofre
)
from services.tools.menu_translator_tool import traduzir_e_explicar_cardapio
from services.tools.unit_converter_tool import converter_unidade, interpretar_e_converter
from services.tools.streaming_tool import onde_assistir
from services.tools.bbq_planner_tool import calcular_churrasco
from services.tools.trip_ledger_tool import (
    criar_grupo_viagem,
    adicionar_despesa_viagem,
    calcular_fechamento_viagem
)
from services.tools.work_hours_tool import (
    calcular_saldo_jornada,
    calcular_fechamento_semanal,
    registrar_ponto_dia
)
from services.tools.anime_tracker_tool import (
    adicionar_anime_watchlist,
    consultar_proximo_episodio,
    listar_meus_animes,
    atualizar_progresso_anime,
    marcar_anime_concluido,
    grade_semanal_animes,
    sincronizar_perfil_anilist,
    consultar_novas_temporadas,
    explorar_temporada_animes
)
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
    falar_na_alexa,
    consultar_rota,
    calcular_horario_saida,
    criar_anotacao,
    criar_lembrete,
    buscar_anotacoes,
    listar_lembretes_pendentes,
    concluir_lembrete,
    salvar_ideia_presente,
    consultar_ideias_presente,
    alertar_datas_proximas,
    dividir_conta_restaurante,
    registrar_localizacao_objeto,
    onde_guardei_objeto,
    listar_historico_movimentacoes,
    salvar_credencial,
    consultar_credencial,
    gerar_senha_forte,
    listar_servicos_cofre,
    traduzir_e_explicar_cardapio,
    converter_unidade,
    interpretar_e_converter,
    onde_assistir,
    calcular_churrasco,
    criar_grupo_viagem,
    adicionar_despesa_viagem,
    calcular_fechamento_viagem,
    calcular_saldo_jornada,
    calcular_fechamento_semanal,
    registrar_ponto_dia,
    adicionar_anime_watchlist,
    consultar_proximo_episodio,
    listar_meus_animes,
    atualizar_progresso_anime,
    marcar_anime_concluido,
    grade_semanal_animes,
    sincronizar_perfil_anilist,
    consultar_novas_temporadas,
    explorar_temporada_animes
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
                    "- Se o usuário informar um gasto/compra e NÃO disser qual cartão/conta usou (e NÃO for Pix), NÃO chame a ferramenta ainda! Pergunte obrigatoriamente e educadamente ao usuário em qual cartão foi a cobrança ('Foi no seu cartão de crédito pessoal, no secundário ou no débito?'). Assim que ele responder, registre o gasto.\n\n"
                    "### REGRA MANDATÓRIA DE DIVISÃO DE CONTAS E VIAGENS (FASES 11 E 18):\n"
                    "- Ao dividir contas de restaurantes ou despesas de grupos/viagens, a divisão e o demonstrativo DEVEM ser organizados e agrupados estritamente pelo NOME DAS PESSOAS (ex: 'Você', 'João', 'Maria', 'Pedro'), discriminando o que cada um consumiu e o valor final individual. NUNCA separe contas por chave Pix.\n\n"
                    "### REGRA DE ROTAS E TRÂNSITO (FASE 8):\n"
                    "- Quando o usuário disser 'casa', utilize a residência configurada. Para qualquer outro destino que o usuário escrever (ex: 'Shopping da Bahia', 'Farol da Barra', 'Aeroporto', ou qualquer endereço/ponto turístico), consulte a rota e o trânsito buscando diretamente pelo nome do destino informado.\n\n"
                    "### REGRA DE ANIMES E ANILIST:\n"
                    "- Para interação com animes e com a conta do AniList:\n"
                    "  1. 'adicionar_anime_watchlist': Quando o usuário disser para adicionar anime à lista ('adiciona Dandadan na minha lista', 'coloque Solo Leveling nos meus animes').\n"
                    "  2. 'atualizar_progresso_anime': Quando o usuário disser que assistiu um episódio para subir o contador ('assisti o ep 8 de Frieren', 'vi mais um ep de One Piece' -> se for 'mais um ep', passe incrementar=True).\n"
                    "  3. 'listar_meus_animes': Quando o usuário perguntar o que está assistindo ('o que eu to vendo?', 'o que estou assistindo?', 'meus animes em andamento'), chame listar_meus_animes(status='assistindo').\n"
                    "  4. 'marcar_anime_concluido': Quando o usuário disser que terminou ou finalizou um anime ('terminei Frieren', 'acabei Solo Leveling, nota 9'). Se ele der uma nota, passe no argumento nota.\n"
                    "  5. 'consultar_proximo_episodio': Quando perguntar datas de lançamento de novos episódios ('quando sai ep de X?').\n"
                    "  6. 'consultar_novas_temporadas': Quando perguntar sobre continuações ('vai ter 2 temporada de X?').\n"
                    "  7. 'grade_semanal_animes': Para a grade de lançamentos da semana dos animes acompanhados.\n"
                    "  8. 'explorar_temporada_animes': Para saber lançamentos e novidades da temporada atual/futura."
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
