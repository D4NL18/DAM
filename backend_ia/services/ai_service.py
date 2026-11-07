import logging
import re
import unicodedata
import google.generativeai as genai
from config.settings import settings
from repositories.chat_repository import ChatRepository
from services.tools.health_tool import consultar_saude
from services.tools.finance_tool import registrar_gasto, registrar_receita, consultar_resumo_gastos
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
    atualizar_anotacao,
    excluir_anotacao,
    listar_lembretes_pendentes,
    concluir_lembrete
)
from services.tools.wishlist_tool import (
    adicionar_item_wishlist,
    consultar_wishlist,
    atualizar_item_wishlist,
    marcar_item_wishlist_comprado,
    remover_item_wishlist
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
    consultar_meu_episodio_anime,
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
from services.tools_dispatcher import ToolsDispatcher
from services.media_optimizer import MediaOptimizer
from services.execution_audit import ExecutionAuditContext
import base64
from typing import Optional, Set, Tuple

logger = logging.getLogger(__name__)


class AIService:
    # P-1111: Modelo primário 'gemini-flash-latest' e cadeia determinística de fallback
    PRIMARY_MODEL = "gemini-flash-latest"
    GEMINI_MODEL_CHAIN = [
        "gemini-flash-latest",
        "gemini-3.8-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
    ]

    # P-0804: Calibração determinística de temperatura para eliminar alucinações e manter foco estrito
    DEFAULT_GENERATION_CONFIG = {
        "temperature": 0.0,
        "top_p": 0.1,
        "top_k": 1,
    }

    _FINANCE_WRITE_INTENT_RE = re.compile(
        r"\b("
        r"cadastr(a|e|ar|ei)|lanc(a|e|ar|ei)|registr(a|e|ar|ei)|adicion(a|e|ar|ei)|"
        r"gast(ei|o)|compr(ei|a)|paguei|recebi|reembolso"
        r")\b.*\b("
        r"reais|r\$|\d+|financeiro|gasto|despesa|receita|mercado|ifood|uber|farmacia|"
        r"cartao|pix|debito|credito|conta|luz|agua|internet|aluguel"
        r")\b",
        re.IGNORECASE,
    )

    _FAKE_FINANCE_CONFIRMATION_RE = re.compile(
        r"\b("
        r"cadastrei|registrei|lancei|cadastrad[oa] com sucesso|registrad[oa] com sucesso|"
        r"lancad[oa] com sucesso|lancamento realizado|gasto registrado|despesa cadastrada|"
        r"receita registrada|adicionei o gasto|adicionei a despesa"
        r")\b",
        re.IGNORECASE,
    )

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

    @classmethod
    def _verify_and_enforce_honest_feedback(
        cls,
        user_text: str,
        recent_context: str,
        detected_domains: Optional[Set[str]],
        final_text: Optional[str],
    ) -> Tuple[Optional[str], bool]:
        """
        P-0805: Auditoria pós-geração para impedir confirmações falsas (alucinação de sucesso)
        e garantir que erros reais de ferramentas sejam exibidos de forma transparente.
        Retorna (texto_final_auditado, houve_substituicao_por_erro).
        """
        if not final_text:
            return final_text, False

        norm_final = cls._normalize_text(final_text)

        # 1. Se alguma tool falhou explicitamente no turno, verifica se o LLM ocultou o erro
        failures = ExecutionAuditContext.get_failures()
        if failures:
            last_failure_msg = failures[-1]["message"]
            claims_fake_success = bool(cls._FAKE_FINANCE_CONFIRMATION_RE.search(norm_final))
            mentions_error_honestly = any(
                marker in norm_final
                for marker in (
                    "nao foi cadastrad",
                    "nao esta disponivel",
                    "metodo de pagamento nao identificado",
                    "erro ao salvar",
                    "erro:",
                    "falha",
                    "invalido",
                )
            )
            if claims_fake_success or not mentions_error_honestly:
                logger.warning(
                    f"[AI SERVICE AUDIT P-0805] O LLM omitiu ou mascarou falha da tool "
                    f"'{failures[-1]['tool']}'. Substituindo resposta pelo feedback de erro real."
                )
                return last_failure_msg, True

        # 2. Se o usuário pediu para cadastrar algo no financeiro e o LLM afirmou que cadastrou,
        # mas nenhuma tool financeira (registrar_gasto / registrar_receita) teve sucesso no turno:
        combined_user_context = cls._normalize_text(f"{recent_context} {user_text}".strip())
        norm_user = cls._normalize_text(user_text)

        is_finance_write_request = bool(
            cls._FINANCE_WRITE_INTENT_RE.search(norm_user)
            or (
                detected_domains
                and "finance" in detected_domains
                and cls._FINANCE_WRITE_INTENT_RE.search(combined_user_context)
            )
        )
        claims_finance_registered = bool(cls._FAKE_FINANCE_CONFIRMATION_RE.search(norm_final))

        if is_finance_write_request and claims_finance_registered:
            if not ExecutionAuditContext.has_successful_execution({"registrar_gasto", "registrar_receita"}):
                logger.error(
                    f"[AI SERVICE AUDIT P-0805] Alucinação de cadastro financeiro bloqueada! "
                    f"O modelo afirmou que cadastrou para '{user_text[:60]}', mas registrar_gasto/registrar_receita "
                    f"NÃO foi executada com sucesso."
                )
                honest_error = (
                    "❌ **Erro — O lançamento NÃO foi cadastrado:** A gravação no módulo financeiro **não foi gravada** "
                    "(nenhuma confirmação de escrita foi registrada no banco de dados). "
                    "Verifique se informou a descrição, o valor em reais e o método de pagamento "
                    "(*Cartão de Crédito Pessoal*, *Cartão de Crédito Secundário* ou *Cartão de Débito/Pix*) "
                    "e tente novamente."
                )
                return honest_error, True

        return final_text, False

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
        # 0. Reseta o contexto de auditoria de execução de ferramentas do turno (P-0805)
        ExecutionAuditContext.reset()

        # 1. Guardrail de Segurança: Checagem de Prompt Injection / Jailbreak
        is_injection, injection_reason = GuardrailsService.detect_prompt_injection(user_text)
        if is_injection:
            logger.warning(f"Mensagem bloqueada por Guardrail [{remote_jid}]: {injection_reason}")
            return GuardrailsService.get_defensive_response()

        # 2. Otimização Multimodal de Mídias (P-1103 e P-1104)
        orig_media_b64 = media_base64
        if media_base64 and media_mimetype:
            # 2.1. Extração Local Prioritária para Documentos PDF (PyMuPDF)
            if "pdf" in media_mimetype.lower():
                extracted_pdf_text = MediaOptimizer.extract_text_from_pdf(media_base64)
                if extracted_pdf_text:
                    logger.info(f"[AI SERVICE] PDF convertido em texto digital local com sucesso. Dispensando envio multimodal.")
                    user_text = f"{user_text}\n\n[Documento PDF Extraído]:\n{extracted_pdf_text}"
                    media_base64 = None
                    media_mimetype = None

            # 2.2. Downsampling Adaptativo e Compressão de Imagens (Pillow)
            elif "image" in media_mimetype.lower():
                media_base64, media_mimetype = MediaOptimizer.optimize_image(
                    media_base64=media_base64,
                    media_mimetype=media_mimetype,
                    max_dimension=1024,
                    quality=80
                )

        # 3. Sanitização e Delimitação Semântica da Mensagem
        safe_prompt = GuardrailsService.wrap_user_message(user_text)

        # 4. Otimização de Tokens: Cache Semântico e Multimodal (PC-08 / P-1106)
        cached_response = ConversationCacheService.get_cached_response(
            remote_jid=remote_jid, 
            query=user_text,
            media_base64=media_base64 or orig_media_b64
        )
        if cached_response:
            logger.info(f"[CACHE HIT] Resposta servida diretamente do cache para {remote_jid}")
            return cached_response

        # 5. Busca o histórico do usuário (Janela Dinâmica por Token Budget)
        history_docs = ChatRepository.get_recent_history(remote_jid, limit=8)
        
        # Constrói o histórico com token-budget dinâmico (P-1201)
        MAX_HISTORY_TOKENS = 1500
        history = []
        token_budget_used = 0
        for msg in reversed(history_docs):  # Mais recente primeiro
            text_content = msg.get("text") or ""
            estimated_tokens = len(text_content) // 4  # Heurística: ~4 chars/token
            if token_budget_used + estimated_tokens > MAX_HISTORY_TOKENS:
                break
            token_budget_used += estimated_tokens
            role = "model" if msg.get("fromMe") else "user"
            history.insert(0, {"role": role, "parts": [text_content]})
        
        logger.info(f"[AI SERVICE] History: {len(history)}/{len(history_docs)} msgs loaded (~{token_budget_used} tokens)")

        try:
            agora = get_brasilia_now_str("%Y-%m-%d %H:%M")

            # 6. Roteamento Dinâmico de Ferramentas & Prompts Modulares (P-1101 e P-1102)
            has_media = bool(media_base64 or orig_media_b64)
            recent_context = " ".join(
                [m["parts"][0] for m in history[-2:] if m.get("parts") and isinstance(m["parts"][0], str)]
            )
            selected_tools = ToolsDispatcher.resolve_tools(
                user_text,
                has_media=has_media,
                context_text=recent_context
            )
            detected_domains = ToolsDispatcher.detect_domains(user_text, context_text=recent_context)
            system_instruction = PromptComposer.compose_system_instruction(agora, domains=detected_domains)

            part = None
            if media_base64 and media_mimetype:
                # Sanitiza Base64 (remove prefixos data URI e quebras de linha/espaços)
                clean_b64 = media_base64
                if "," in clean_b64:
                    clean_b64 = clean_b64.split(",", 1)[1]
                clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
                media_bytes = base64.b64decode(clean_b64)

                # Normaliza MIME type para o padrão aceito pelo Gemini
                clean_mimetype = media_mimetype.split(";")[0].strip()

                part = {
                    "mime_type": clean_mimetype,
                    "data": media_bytes
                }

            # 7. Cadeia de Modelos com Fallback Determinístico (P-1111) + Auto-Healing (P-1108) + Temperatura Calibrada (P-0804)
            final_text = None
            last_error = None

            for model_name in AIService.GEMINI_MODEL_CHAIN:
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        tools=selected_tools,
                        system_instruction=system_instruction,
                        generation_config=AIService.DEFAULT_GENERATION_CONFIG
                    )

                    chat = model.start_chat(
                        history=history,
                        enable_automatic_function_calling=True if selected_tools else False
                    )

                    if part is not None:
                        response = chat.send_message([part, user_text])
                    else:
                        response = chat.send_message(safe_prompt)

                    is_malformed_call = False
                    if hasattr(response, "candidates") and response.candidates:
                        candidate = response.candidates[0]
                        finish_reason = getattr(candidate, "finish_reason", None)
                        if finish_reason == 10 or str(finish_reason).upper().endswith("MALFORMED_FUNCTION_CALL"):
                            is_malformed_call = True

                    if not is_malformed_call:
                        try:
                            final_text = response.text
                        except (ValueError, AttributeError) as ve:
                            logger.warning(f"[AI SERVICE] response.text indisponível em '{model_name}' (possível chamada com tools ausentes): {ve}")
                            is_malformed_call = True

                    if is_malformed_call:
                        logger.warning(
                            f"[AI SERVICE AUTO-HEALING] Chamada em '{model_name}' com tools={len(selected_tools) if selected_tools else 0} falhou para '{user_text[:50]}...'. "
                            "Retentando automaticamente com catálogo completo de ferramentas e prompt irrestrito..."
                        )
                        fallback_tools = ToolsDispatcher.get_all_tools()
                        fallback_instruction = PromptComposer.compose_system_instruction(agora, domains=None)
                        fallback_model = genai.GenerativeModel(
                            model_name=model_name,
                            tools=fallback_tools,
                            system_instruction=fallback_instruction,
                            generation_config=AIService.DEFAULT_GENERATION_CONFIG
                        )
                        fallback_chat = fallback_model.start_chat(
                            history=history,
                            enable_automatic_function_calling=True
                        )
                        if part is not None:
                            retry_resp = fallback_chat.send_message([part, user_text])
                        else:
                            retry_resp = fallback_chat.send_message(safe_prompt)
                        final_text = retry_resp.text

                    if model_name != AIService.PRIMARY_MODEL:
                        logger.info(f"[AI SERVICE FALLBACK] Resposta gerada com sucesso pelo modelo de fallback '{model_name}'.")
                    break
                except Exception as model_err:
                    last_error = model_err
                    logger.warning(
                        f"[AI SERVICE FALLBACK] Falha ao utilizar modelo '{model_name}': {model_err}. "
                        "Tentando próximo modelo da cadeia de fallback..."
                    )
                    continue

            if final_text is None and last_error is not None:
                raise last_error

            # 8. Auditoria Anti-Alucinação de Escrita e Feedback de Erro Honesto (P-0805)
            final_text, was_error_override = AIService._verify_and_enforce_honest_feedback(
                user_text=user_text,
                recent_context=recent_context,
                detected_domains=detected_domains,
                final_text=final_text,
            )

            # 9. Salva no cache apenas se elegível e não for um erro interceptado (PC-08 / P-1106)
            if final_text and not was_error_override:
                ConversationCacheService.save_response(
                    remote_jid=remote_jid, 
                    query=user_text, 
                    response_text=final_text,
                    media_base64=media_base64 or orig_media_b64
                )

            return final_text
        except Exception:
            logger.exception("Erro no Gemini")
            return "Desculpe, meus servidores estão indisponíveis no momento. Tente novamente mais tarde."
