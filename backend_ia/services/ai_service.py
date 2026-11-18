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
    # P-1111: Modelo primário 'gemini-4-hydrogen' e cadeia determinística de fallback
    PRIMARY_MODEL = "gemini-4-hydrogen"
    GEMINI_MODEL_CHAIN = [
        "gemini-4-hydrogen",
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
                    "[AI SERVICE AUDIT P-0805] O LLM omitiu ou mascarou falha da tool "
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
                    "[AI SERVICE AUDIT P-0805] Alucinação de cadastro financeiro bloqueada! "
                    f"O modelo afirmou que cadastrou para '{user_text[:60]}', mas registrar_gasto/registrar_receita "
                    "NÃO foi executada com sucesso."
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

    @classmethod
    def _preprocess_media(
        cls,
        user_text: str,
        media_base64: Optional[str],
        media_mimetype: Optional[str],
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """Executa extração local de PDFs e compressão de imagens antes do envio ao Gemini."""
        if not (media_base64 and media_mimetype):
            return user_text, media_base64, media_mimetype

        mime_lower = media_mimetype.lower()
        if "pdf" in mime_lower:
            extracted_pdf_text = MediaOptimizer.extract_text_from_pdf(media_base64)
            if extracted_pdf_text:
                logger.info("[AI SERVICE] PDF convertido em texto digital local com sucesso. Dispensando envio multimodal.")
                return f"{user_text}\n\n[Documento PDF Extraído]:\n{extracted_pdf_text}", None, None
        elif "image" in mime_lower:
            opt_b64, opt_mime = MediaOptimizer.optimize_image(
                media_base64=media_base64,
                media_mimetype=media_mimetype,
                max_dimension=1024,
                quality=80,
            )
            return user_text, opt_b64, opt_mime

        return user_text, media_base64, media_mimetype

    @classmethod
    def _build_token_budget_history(cls, remote_jid: str) -> Tuple[list, str]:
        """Carrega histórico recente dentro do orçamento dinâmico de tokens (P-1201)."""
        history_docs = ChatRepository.get_recent_history(remote_jid, limit=8)
        max_history_tokens = 1500
        history = []
        token_budget_used = 0

        for msg in reversed(history_docs):
            text_content = msg.get("text") or ""
            estimated_tokens = len(text_content) // 4
            if token_budget_used + estimated_tokens > max_history_tokens:
                break
            token_budget_used += estimated_tokens
            role = "model" if msg.get("fromMe") else "user"
            history.insert(0, {"role": role, "parts": [text_content]})

        logger.info(f"[AI SERVICE] History: {len(history)}/{len(history_docs)} msgs loaded (~{token_budget_used} tokens)")
        recent_context = " ".join(
            [m["parts"][0] for m in history[-2:] if m.get("parts") and isinstance(m["parts"][0], str)]
        )
        return history, recent_context

    @classmethod
    def _build_media_part(cls, media_base64: Optional[str], media_mimetype: Optional[str]) -> Optional[dict]:
        """Sanitiza payload Base64 e monta estrutura multimodal aceita pelo Gemini."""
        if not (media_base64 and media_mimetype):
            return None

        clean_b64 = media_base64.split(",", 1)[1] if "," in media_base64 else media_base64
        clean_b64 = clean_b64.strip().replace("\n", "").replace("\r", "")
        media_bytes = base64.b64decode(clean_b64)
        clean_mimetype = media_mimetype.split(";")[0].strip()
        return {"mime_type": clean_mimetype, "data": media_bytes}

    @classmethod
    def _is_malformed_function_call(cls, response) -> bool:
        """Verifica se o candidato retornou finish_reason MALFORMED_FUNCTION_CALL (P-1108)."""
        if not (hasattr(response, "candidates") and response.candidates):
            return False
        finish_reason = getattr(response.candidates[0], "finish_reason", None)
        return finish_reason == 10 or str(finish_reason).upper().endswith("MALFORMED_FUNCTION_CALL")

    @classmethod
    def _extract_text_or_flag_malformed(cls, response, model_name: str) -> Tuple[Optional[str], bool]:
        """Extrai texto da resposta do modelo ou sinaliza necessidade de auto-healing."""
        if cls._is_malformed_function_call(response):
            return None, True
        try:
            return response.text, False
        except (ValueError, AttributeError) as ve:
            logger.warning(f"[AI SERVICE] response.text indisponível em '{model_name}' (possível chamada com tools ausentes): {ve}")
            return None, True

    @classmethod
    def _run_auto_healing_retry(
        cls,
        model_name: str,
        agora: str,
        history: list,
        part: Optional[dict],
        user_text: str,
        safe_prompt: str,
        selected_tools,
    ) -> str:
        """Reexecuta a chamada com catálogo completo de ferramentas em caso de MALFORMED_FUNCTION_CALL."""
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
            generation_config=cls.DEFAULT_GENERATION_CONFIG,
        )
        fallback_chat = fallback_model.start_chat(
            history=history,
            enable_automatic_function_calling=True,
        )
        retry_payload = [part, user_text] if part is not None else safe_prompt
        return fallback_chat.send_message(retry_payload).text

    @classmethod
    def _invoke_single_model(
        cls,
        model_name: str,
        selected_tools,
        system_instruction: str,
        history: list,
        part: Optional[dict],
        user_text: str,
        safe_prompt: str,
        agora: str,
    ) -> str:
        """Instancia um modelo específico da cadeia e realiza chamada com auto-healing."""
        model = genai.GenerativeModel(
            model_name=model_name,
            tools=selected_tools,
            system_instruction=system_instruction,
            generation_config=cls.DEFAULT_GENERATION_CONFIG,
        )
        chat = model.start_chat(
            history=history,
            enable_automatic_function_calling=bool(selected_tools),
        )
        payload = [part, user_text] if part is not None else safe_prompt
        response = chat.send_message(payload)

        final_text, is_malformed_call = cls._extract_text_or_flag_malformed(response, model_name)
        if is_malformed_call:
            return cls._run_auto_healing_retry(
                model_name=model_name,
                agora=agora,
                history=history,
                part=part,
                user_text=user_text,
                safe_prompt=safe_prompt,
                selected_tools=selected_tools,
            )
        return final_text

    @classmethod
    def _execute_model_chain(
        cls,
        selected_tools,
        system_instruction: str,
        history: list,
        part: Optional[dict],
        user_text: str,
        safe_prompt: str,
        agora: str,
    ) -> Optional[str]:
        """Percorre a cadeia de modelos configurada com fallback determinístico (P-1111)."""
        last_error = None
        for model_name in cls.GEMINI_MODEL_CHAIN:
            try:
                final_text = cls._invoke_single_model(
                    model_name=model_name,
                    selected_tools=selected_tools,
                    system_instruction=system_instruction,
                    history=history,
                    part=part,
                    user_text=user_text,
                    safe_prompt=safe_prompt,
                    agora=agora,
                )
                if model_name != cls.PRIMARY_MODEL:
                    logger.info(f"[AI SERVICE FALLBACK] Resposta gerada com sucesso pelo modelo de fallback '{model_name}'.")
                return final_text
            except Exception as model_err:
                last_error = model_err
                logger.warning(
                    f"[AI SERVICE FALLBACK] Falha ao utilizar modelo '{model_name}': {model_err}. "
                    "Tentando próximo modelo da cadeia de fallback..."
                )

        if last_error is not None:
            raise last_error
        return None

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
        user_text, media_base64, media_mimetype = AIService._preprocess_media(
            user_text=user_text,
            media_base64=media_base64,
            media_mimetype=media_mimetype,
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
        history, recent_context = AIService._build_token_budget_history(remote_jid)

        try:
            agora = get_brasilia_now_str("%Y-%m-%d %H:%M")

            # 6. Roteamento Dinâmico de Ferramentas & Prompts Modulares (P-1101 e P-1102)
            has_media = bool(media_base64 or orig_media_b64)
            selected_tools = ToolsDispatcher.resolve_tools(
                user_text,
                has_media=has_media,
                context_text=recent_context
            )
            detected_domains = ToolsDispatcher.detect_domains(user_text, context_text=recent_context)
            system_instruction = PromptComposer.compose_system_instruction(agora, domains=detected_domains)
            part = AIService._build_media_part(media_base64, media_mimetype)

            # 7. Cadeia de Modelos com Fallback Determinístico (P-1111) + Auto-Healing (P-1108)
            final_text = AIService._execute_model_chain(
                selected_tools=selected_tools,
                system_instruction=system_instruction,
                history=history,
                part=part,
                user_text=user_text,
                safe_prompt=safe_prompt,
                agora=agora,
            )

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
