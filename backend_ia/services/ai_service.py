import logging
import google.generativeai as genai
from config.settings import settings
from repositories.chat_repository import ChatRepository
from services.tools.health_tool import consultar_saude
from services.tools.finance_tool import registrar_gasto, consultar_resumo_gastos
from services.tools.calendar_tool import agendar_evento, consultar_agenda, editar_evento, excluir_evento
from services.tools.vehicle_tool import consultar_status_veiculo, acionar_travas_veiculo, cadastrar_ou_atualizar_veiculo
from services.tools.esports_tool import consultar_jogos_cs2
from services.tools.alexa_tool import acionar_rotina_alexa, falar_na_alexa
from services.tools.maps_tool import (
    consultar_rota,
    calcular_horario_saida,
    otimizar_rota_multiplos_pontos,
    planejar_roteiro_viagem
)
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
from services.briefing_service import (
    consultar_briefing_matinal,
    configurar_preferencias_briefing,
    consultar_preferencias_briefing
)
from services.tools.clash_of_clans_tool import consultar_clash_of_clans
from services.tools.gcp_billing_tool import consultar_gcp_billing
from services.tools.nutrition_tool import (
    consultar_lista_substituicao,
    avaliar_substituicao_alimento
)
from services.tools.address_tool import (
    salvar_endereco,
    consultar_enderecos_salvos,
    remover_endereco
)
from services.tools.saved_videos_tool import (
    salvar_video,
    consultar_videos_salvos,
    marcar_video_assistido,
    remover_video_salvo
)
from services.tools.file_converter_tool import gerenciar_arquivos
from services.tools.translation_tool import traduzir_conteudo
from datetime import datetime
from config.timezone import get_brasilia_now_str


from services.guardrails_service import GuardrailsService
from services.prompts.prompt_composer import PromptComposer
from services.cache_service import ConversationCacheService
import base64
from typing import Optional

logger = logging.getLogger(__name__)

# Lista de ferramentas que a IA pode usar
AVAILABLE_TOOLS = [
    consultar_saude,
    registrar_gasto,
    consultar_resumo_gastos,
    agendar_evento,
    consultar_agenda,
    editar_evento,
    excluir_evento,
    consultar_status_veiculo,
    acionar_travas_veiculo,
    consultar_jogos_cs2,
    acionar_rotina_alexa,
    falar_na_alexa,
    consultar_rota,
    calcular_horario_saida,
    otimizar_rota_multiplos_pontos,
    planejar_roteiro_viagem,
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
    explorar_temporada_animes,
    consultar_briefing_matinal,
    configurar_preferencias_briefing,
    consultar_preferencias_briefing,
    cadastrar_ou_atualizar_veiculo,
    consultar_clash_of_clans,
    consultar_gcp_billing,
    consultar_lista_substituicao,
    avaliar_substituicao_alimento,
    salvar_endereco,
    consultar_enderecos_salvos,
    remover_endereco,
    salvar_video,
    consultar_videos_salvos,
    marcar_video_assistido,
    remover_video_salvo,
    gerenciar_arquivos,
    traduzir_conteudo
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
        # 1. Guardrail de Segurança: Checagem de Prompt Injection / Jailbreak
        is_injection, injection_reason = GuardrailsService.detect_prompt_injection(user_text)
        if is_injection:
            logger.warning(f"Mensagem bloqueada por Guardrail [{remote_jid}]: {injection_reason}")
            return GuardrailsService.get_defensive_response()

        # 2. Sanitização e Delimitação Semântica da Mensagem
        safe_prompt = GuardrailsService.wrap_user_message(user_text)

        # 3. Otimização de Tokens: Cache Semântico de Conversa (PC-08)
        if not media_base64 and not media_mimetype:
            cached_response = ConversationCacheService.get_cached_response(remote_jid, user_text)
            if cached_response:
                logger.info(f"[CACHE HIT] Resposta servida diretamente do cache para {remote_jid}")
                return cached_response

        # 4. Busca o histórico do usuário
        history_docs = ChatRepository.get_recent_history(remote_jid, limit=10)
        
        # Constrói o histórico no formato para start_chat
        history = []
        for msg in history_docs:
            role = "model" if msg.get("fromMe") else "user"
            history.append({"role": role, "parts": [msg.get("text")]})

        try:
            agora = get_brasilia_now_str("%Y-%m-%d %H:%M")
            system_instruction = PromptComposer.compose_system_instruction(agora)

            model = genai.GenerativeModel(
                model_name='gemini-3.6-flash',
                tools=AVAILABLE_TOOLS,
                system_instruction=system_instruction
            )
            
            chat = model.start_chat(
                history=history,
                enable_automatic_function_calling=True
            )
            
            if media_base64 and media_mimetype:
                # Sanitiza Base64 (remove prefixos data URI e quebras de linha/espaços)
                clean_b64 = media_base64
                if "," in clean_b64:
                    clean_b64 = clean_b64.split(",", 1)[1]
                clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
                media_bytes = base64.b64decode(clean_b64)

                # Normaliza MIME type para o padrão aceito pelo Gemini (sem parâmetros extras como codecs)
                clean_mimetype = media_mimetype.split(";")[0].strip()

                part = {
                    "mime_type": clean_mimetype,
                    "data": media_bytes
                }
                response = chat.send_message([part, user_text])
            else:
                response = chat.send_message(safe_prompt)

            final_text = response.text

            # 5. Salva no cache se elegível (PC-08)
            if not media_base64 and not media_mimetype and final_text:
                ConversationCacheService.save_response(remote_jid, user_text, final_text)

            return final_text
        except Exception as e:
            logger.error(f"Erro no Gemini: {e}")
            return "Desculpe, meus servidores estão indisponíveis no momento. Tente novamente mais tarde."
