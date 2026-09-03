import re
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

class GuardrailsService:
    """
    Serviço de segurança contra Prompt Injection, Jailbreak e vazamento de instruções do sistema.
    Aplica técnicas defensivas em profundidade antes que o texto do usuário atinja o modelo LLM.
    """

    # Padrões suspeitos de injeção de prompt e jailbreak (case-insensitive)
    _INJECTION_PATTERNS = [
        # Tentativas diretas de ignorar instruções anteriores
        re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts|rules|commands)", re.IGNORECASE),
        re.compile(r"(ignore|esque[cç]a)\s+(todas\s+as\s+|qualquer\s+|as\s+|os\s+)?(instru[cç][oõ]es|diretrizes|regras|comandos)\s*(anteriores|acima)?", re.IGNORECASE),
        
        # Tentativas de extrair/vazar o prompt do sistema ou regras
        re.compile(r"(repeat|show|reveal|display|output|print|give)(\s+me)?\s+(all\s+)?(your\s+)?(system\s+prompt|initial\s+instructions|system\s+instructions|developer\s+instructions)", re.IGNORECASE),
        re.compile(r"(mostre|revele|imprima|repita|diga|quais\s+s[aã]o)(\s+me)?\s+(o\s+|as\s+)?(seu\s+|suas\s+)?(system\s+prompt|prompt\s+de\s+sistema|instru[cç][oõ]es\s+iniciais|regras\s+de\s+sistema)", re.IGNORECASE),
        
        # Personas antagônicas / Jailbreaks conhecidos
        re.compile(r"\b(DAN|jailbreak|developer\s+mode|unrestricted\s+mode|god\s+mode)\b", re.IGNORECASE),
        re.compile(r"voc[eê]\s+agora\s+[eé]\s+(um\s+ia\s+sem\s+regras|dan|modo\s+desenvolvedor)", re.IGNORECASE),
        
        # Delimitadores e tags falsas para tentar enganar o parser
        re.compile(r"<\s*/?\s*(system|system_instruction|assistant|developer|admin)\s*>", re.IGNORECASE),
    ]

    # Caracteres invisíveis, zero-width e caracteres de controle anômalos
    _CONTROL_CHARS_PATTERN = re.compile(r"[\u200B-\u200D\uFEFF\u0000-\u0008\u000E-\u001F\u007F-\u009F]")

    @classmethod
    def sanitize_user_input(cls, user_text: str) -> str:
        """
        Remove caracteres de controle invisíveis e normaliza espaços sem alterar o sentido legítimo.
        """
        if not user_text:
            return ""
        # Remove caracteres invisíveis e de controle
        cleaned = cls._CONTROL_CHARS_PATTERN.sub("", user_text)
        # Limita espaços consecutivos excessivos
        cleaned = re.sub(r"[ \t]{3,}", "  ", cleaned)
        return cleaned.strip()

    @classmethod
    def detect_prompt_injection(cls, user_text: str) -> Tuple[bool, Optional[str]]:
        """
        Avalia se a entrada do usuário contém padrões conhecidos de Prompt Injection ou Jailbreak.
        Retorna uma tupla: (is_injection: bool, motivo: Optional[str]).
        """
        if not user_text:
            return False, None

        sanitized = cls.sanitize_user_input(user_text)

        for pattern in cls._INJECTION_PATTERNS:
            match = pattern.search(sanitized)
            if match:
                matched_snippet = match.group(0)
                logger.warning(f"Tentativa de Prompt Injection interceptada: '{matched_snippet}'")
                return True, f"Padrão suspeito de injeção detectado: {matched_snippet}"

        return False, None

    @classmethod
    def wrap_user_message(cls, user_text: str) -> str:
        """
        Envolve a mensagem do usuário em delimitadores semânticos estritos (<user_message>),
        impedindo que o modelo interprete texto do usuário como comando de sistema.
        """
        sanitized = cls.sanitize_user_input(user_text)
        # Escapa tags de fechamento acidentais ou maliciosas
        safe_text = sanitized.replace("</user_message>", "&lt;/user_message&gt;")
        return (
            "<user_message>\n"
            f"{safe_text}\n"
            "</user_message>"
        )

    @classmethod
    def get_defensive_response(cls) -> str:
        """
        Resposta padronizada e segura quando uma tentativa de injeção for bloqueada preventivamente.
        """
        return (
            "⚠️ Não posso processar esta solicitação pois ela contém padrões que violam as políticas "
            "de integridade e segurança do sistema. Se você precisa de ajuda com suas finanças, "
            "agenda, animes, mobilidade ou tarefas, por favor reformule sua pergunta."
        )
