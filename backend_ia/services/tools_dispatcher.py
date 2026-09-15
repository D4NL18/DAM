"""
ToolsDispatcher — Roteador e Despachante Dinâmico de Ferramentas (PC-11 / P-1101)
Responsável por selecionar estritamente o subconjunto de ferramentas necessário
para a intenção do usuário, reduzindo drasticamente o consumo de tokens.
"""
import re
import logging
from typing import List, Callable, Optional

# Ferramentas importadas individualmente por domínio
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

logger = logging.getLogger(__name__)


class ToolsDispatcher:
    """
    Roteador de ferramentas por intenção semântica com suporte a zero-overhead.
    """

    # Agrupamentos de ferramentas por domínio
    DOMAIN_TOOLS = {
        "finance": [registrar_gasto, consultar_resumo_gastos, dividir_conta_restaurante],
        "calendar_notes": [
            agendar_evento, consultar_agenda, editar_evento, excluir_evento,
            criar_anotacao, criar_lembrete, buscar_anotacoes,
            listar_lembretes_pendentes, concluir_lembrete
        ],
        "mobility": [
            consultar_rota, calcular_horario_saida, otimizar_rota_multiplos_pontos,
            planejar_roteiro_viagem, salvar_endereco, consultar_enderecos_salvos, remover_endereco
        ],
        "vehicle": [consultar_status_veiculo, acionar_travas_veiculo, cadastrar_ou_atualizar_veiculo],
        "esports_cs2": [consultar_jogos_cs2],
        "clash_of_clans": [consultar_clash_of_clans],
        "alexa": [acionar_rotina_alexa, falar_na_alexa],
        "nutrition": [consultar_lista_substituicao, avaliar_substituicao_alimento],
        "anime": [
            adicionar_anime_watchlist, consultar_proximo_episodio, listar_meus_animes,
            atualizar_progresso_anime, marcar_anime_concluido, grade_semanal_animes,
            sincronizar_perfil_anilist, consultar_novas_temporadas, explorar_temporada_animes
        ],
        "vault": [salvar_credencial, consultar_credencial, gerar_senha_forte, listar_servicos_cofre],
        "work_hours": [calcular_saldo_jornada, calcular_fechamento_semanal, registrar_ponto_dia],
        "media_files": [gerenciar_arquivos, traduzir_e_explicar_cardapio, traduzir_conteudo],
        "saved_videos": [salvar_video, consultar_videos_salvos, marcar_video_assistido, remover_video_salvo],
        "billing": [consultar_gcp_billing],
        "gift": [salvar_ideia_presente, consultar_ideias_presente, alertar_datas_proximas],
        "items": [registrar_localizacao_objeto, onde_guardei_objeto, listar_historico_movimentacoes],
        "utilities": [converter_unidade, interpretar_e_converter, onde_assistir, calcular_churrasco, consultar_saude],
        "trip": [criar_grupo_viagem, adicionar_despesa_viagem, calcular_fechamento_viagem],
        "briefing": [consultar_briefing_matinal, configurar_preferencias_briefing, consultar_preferencias_briefing],
        "translation": [traduzir_conteudo]
    }

    # Regex de detecção de intenções com normalização sem acentos
    INTENT_REGEXES = {
        "finance": re.compile(
            r"\b(gastei|comprei|paguei|compra|debito|credito|pix|despesa|despesas|fatura|saldo|resumo financeiro|resumo de despesas|quanto gastei)\b",
            re.IGNORECASE
        ),
        "calendar_notes": re.compile(
            r"\b(agenda|agendar|agendad[oa]|compromisso|compromissos|evento|eventos|lembrete|lembretes|anotacao|anotacoes|anotar|nota|notas|tarefa|tarefas|pendente|pendentes|minha agenda|reuniao|reunioes|programad[oa]|consulta|consultas|medico|dentista|treino|aniversario|festa|almoco|jantar|encontro|show)\b|"
            r"\b(marcar|marque|anota|anote|salva|salve|lembra|lembre|agende)\b|"
            r"\b(tenho|vou ter|vamos ter|vou)\b.*?\b(as\s+\d{1,2}|\d{1,2}h|\d{1,2}:\d{2}|horas?|hoje|amanha|segunda|terca|quarta|quinta|sexta|sabado|domingo)\b|"
            r"\b(hoje|amanha|segunda|terca|quarta|quinta|sexta|sabado|domingo)\b.*?\b(tenho|vou|as\s+\d{1,2}|\d{1,2}h|\d{1,2}:\d{2})\b",
            re.IGNORECASE
        ),
        "mobility": re.compile(
            r"\b(transito|rota|rotas|tempo de percurso|tempo de viagem|tempo ate|tempo para|horario de saida|horario para sair|sair para chegar|sair agora|trafego|waze|maps|endereco|enderecos)\b",
            re.IGNORECASE
        ),
        "vehicle": re.compile(
            r"\b(carro|veiculo|trancar|destrancar|travas|combustivel|odometro|status do carro)\b",
            re.IGNORECASE
        ),
        "esports_cs2": re.compile(
            r"\b(furia|cs2|counter strike|cs go|jogo de cs|jogos de cs|partida de cs|partidas de cs)\b",
            re.IGNORECASE
        ),
        "clash_of_clans": re.compile(
            r"\b(clash|clash of clans|guerra de cla|guerra no clash|raid weekend|capital do cla)\b",
            re.IGNORECASE
        ),
        "alexa": re.compile(
            r"\b(alexa|rotina alexa|falar na alexa|fala na alexa|echo dot|tocar musica na alexa)\b",
            re.IGNORECASE
        ),
        "nutrition": re.compile(
            r"\b(dietbox|dieta|substituicao|posso trocar|trocar alimento|calorias|nutricao|tabela nutricional)\b",
            re.IGNORECASE
        ),
        "anime": re.compile(
            r"\b(anime|animes|anilist|proximo episodio|manga|otaku|crunchyroll|temporada de anime)\b",
            re.IGNORECASE
        ),
        "vault": re.compile(
            r"\b(senha|senhas|cofre|credencial|credenciais|password|gerar senha)\b",
            re.IGNORECASE
        ),
        "work_hours": re.compile(
            r"\b(ponto|bater ponto|registrar ponto|saldo de horas|jornada de trabalho|horas extras|banco de horas)\b",
            re.IGNORECASE
        ),
        "media_files": re.compile(
            r"\b(converter arquivo|converter pdf|juntar pdf|dividir pdf|word para pdf|extrair texto|cardapio|menu|restaurante)\b",
            re.IGNORECASE
        ),
        "saved_videos": re.compile(
            r"\b(salvar video|guardar video|tiktok|reels|shorts|videos salvos)\b",
            re.IGNORECASE
        ),
        "billing": re.compile(
            r"\b(faturamento gcp|billing|custo cloud|gcp billing|orcamento gcp|finops|quanto gastei no gcp)\b",
            re.IGNORECASE
        ),
        "gift": re.compile(
            r"\b(presente|ideia de presente|presentes|comprar presente)\b",
            re.IGNORECASE
        ),
        "items": re.compile(
            r"\b(onde guardei|onde esta|localizacao de|guardar objeto|achar objeto)\b",
            re.IGNORECASE
        ),
        "utilities": re.compile(
            r"\b(converter unidade|gramas|quilometros|temperatura|churrasco|calcular churrasco|onde assistir|streaming|saude|medicamento)\b",
            re.IGNORECASE
        ),
        "trip": re.compile(
            r"\b(viagem|grupo de viagem|despesa de viagem|fechamento de viagem|splitwise)\b",
            re.IGNORECASE
        ),
        "briefing": re.compile(
            r"\b(briefing|resumo da manha|meu dia hoje|briefing matinal)\b",
            re.IGNORECASE
        ),
        "translation": re.compile(
            r"\b(traduzir|traduza|traducao|translate|translation|como se diz em)\b",
            re.IGNORECASE
        )
    }

    @staticmethod
    def _normalize(text: str) -> str:
        """Remove acentuações e normaliza para minúsculas."""
        import unicodedata
        if not text:
            return ""
        nfkd = unicodedata.normalize("NFKD", text)
        sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return sem_acento.lower()

    @classmethod
    def detect_domains(cls, text: str) -> List[str]:
        """Identifica quais domínios funcionais foram ativados pelo texto."""
        matched = []
        clean_text = cls._normalize(text)
        for domain, regex in cls.INTENT_REGEXES.items():
            if regex.search(clean_text):
                matched.append(domain)
        return matched

    @classmethod
    def resolve_tools(cls, text: str, has_media: bool = False) -> Optional[List[Callable]]:
        """
        P-1101: Retorna a lista restrita de ferramentas para a intenção.
        Retorna None se for conversa casual/geral para zero overhead de tokens.
        """
        domains = cls.detect_domains(text)

        # Se houver mídia (foto, áudio, doc), carrega ferramentas essenciais
        if has_media:
            tools_set = set()
            tools_set.update(cls.DOMAIN_TOOLS["media_files"])
            tools_set.update(cls.DOMAIN_TOOLS["finance"])  # Para comprovantes/recibos
            tools_set.update(cls.DOMAIN_TOOLS["translation"])
            for d in domains:
                tools_set.update(cls.DOMAIN_TOOLS.get(d, []))
            return list(tools_set)

        # Sem domínios identificados: conversa casual ➔ ZERO ferramentas
        if not domains:
            logger.info("[TOOLS DISPATCHER] Intenção casual detectada. Despachando ZERO ferramentas (tools=None).")
            return None

        # Coleta estritamente as ferramentas dos domínios identificados
        tools_list = []
        for d in domains:
            for tool_fn in cls.DOMAIN_TOOLS.get(d, []):
                if tool_fn not in tools_list:
                    tools_list.append(tool_fn)

        logger.info(f"[TOOLS DISPATCHER] Domínios {domains} ativados. {len(tools_list)} ferramentas carregadas.")
        return tools_list if tools_list else None

    @classmethod
    def get_all_tools(cls) -> List[Callable]:
        """Retorna todas as ferramentas disponíveis registradas para recuperação/fallback/auto-healing."""
        all_tools = []
        for tools in cls.DOMAIN_TOOLS.values():
            for t in tools:
                if t not in all_tools:
                    all_tools.append(t)
        return all_tools

