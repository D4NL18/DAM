import re
import secrets
import logging
from typing import Any, Optional, Dict, List, Union

logger = logging.getLogger(__name__)

class SecurityService:
    """
    Serviço de Segurança e Auditoria (Fase 6).
    Responsável por sanitizar logs confidenciais (LGPD/SecOps),
    mascarar senhas, tokens, CPFs e chaves de API, além de
    prover validação criptograficamente segura contra timing attacks.
    """

    # Regex para CPF: com máscara (000.000.000-00) ou 11 dígitos contíguos
    _CPF_PATTERN = re.compile(
        r"\b(\d{3})\.?(\d{3})\.?(\d{3})[-.]?(\d{2})\b"
    )

    # Regex para tokens no formato Bearer
    _BEARER_PATTERN = re.compile(
        r"(Bearer\s+)([A-Za-z0-9_\-\.]{6,})",
        re.IGNORECASE
    )

    # Regex para chaves conhecidas de API (OpenAI sk-..., Google AIza...)
    _API_KEY_PATTERNS = [
        re.compile(r"\b(sk-[a-zA-Z0-9_\-]{20,})\b"),
        re.compile(r"\b(AIza[0-9A-Za-z\-_]{30,45})\b"),
    ]

    # Regex para campos chave-valor de senhas e tokens em texto/json
    _KEY_VALUE_SECRET_PATTERN = re.compile(
        r"""(["']?(?:password|passwd|senha|secret|token|apikey|api_key|access_token|refresh_token|private_key|auth)["']?\s*[:=]\s*["']?)([^"'}\s,;]+)(["']?)""",
        re.IGNORECASE
    )

    # Chaves de dicionário consideradas sensíveis
    SENSITIVE_KEYS = {
        "password", "passwd", "senha",
        "token", "access_token", "refresh_token", "auth_token", "webhook_token",
        "secret", "client_secret", "secret_key", "private_key",
        "apikey", "api_key", "key",
        "authorization", "proxy-authorization",
        "cpf", "credit_card", "card_number", "cvv"
    }

    @classmethod
    def mask_cpf(cls, text: str) -> str:
        """
        Substitui CPFs no texto mantendo apenas os 3 primeiros e os 2 últimos dígitos.
        Ex: 123.456.789-01 -> 123.***.***-01
        """
        if not text:
            return text

        def _replace_cpf(match: re.Match) -> str:
            d1, _, _, d4 = match.groups()
            return f"{d1}.***.***-{d4}"

        return cls._CPF_PATTERN.sub(_replace_cpf, text)

    @classmethod
    def mask_phone(cls, phone_or_jid: str) -> str:
        """
        Mascara números de telefone e JIDs para auditoria segura sem vazamento de dados pessoais (LGPD).
        Ex: 5571991269995@s.whatsapp.net -> 5571****9995@s.whatsapp.net
        """
        if not phone_or_jid:
            return ""
        
        parts = phone_or_jid.split("@")
        num = parts[0]
        suffix = f"@{parts[1]}" if len(parts) > 1 else ""
        
        if len(num) <= 6:
            masked = "***"
        else:
            masked = f"{num[:4]}****{num[-4:]}"
        return f"{masked}{suffix}"

    @classmethod
    def mask_tokens_and_secrets(cls, text: str) -> str:
        """
        Mascara tokens Bearer, chaves de API e pares chave-valor contendo senhas/tokens.
        """
        if not text:
            return text

        # Mascara Bearer <token>
        text = cls._BEARER_PATTERN.sub(r"\1[REDACTED_TOKEN]", text)

        # Mascara chaves de API específicas
        for pattern in cls._API_KEY_PATTERNS:
            text = pattern.sub("[REDACTED_API_KEY]", text)

        # Mascara campos de chave-valor sensíveis
        def _replace_kv(match: re.Match) -> str:
            prefix = match.group(1)
            suffix = match.group(3) or ""
            return f"{prefix}[REDACTED_SECRET]{suffix}"

        text = cls._KEY_VALUE_SECRET_PATTERN.sub(_replace_kv, text)
        return text

    @classmethod
    def sanitize_log(cls, message: str) -> str:
        """
        Sanitização completa de strings para logs seguros.
        Remove/mascara CPFs, senhas, chaves de API e tokens de autenticação.
        """
        if not isinstance(message, str):
            message = str(message)

        sanitized = cls.mask_cpf(message)
        sanitized = cls.mask_tokens_and_secrets(sanitized)
        return sanitized

    @classmethod
    def sanitize_dict(cls, data: Union[Dict, List, Any]) -> Union[Dict, List, Any]:
        """
        Percorre recursivamente estruturas de dados (dicionários/listas)
        e mascara chaves confidenciais e strings sensíveis.
        """
        if isinstance(data, dict):
            sanitized_dict = {}
            for key, val in data.items():
                key_lower = str(key).lower().replace("-", "_")
                if key_lower in cls.SENSITIVE_KEYS:
                    sanitized_dict[key] = "[REDACTED_SENSITIVE]"
                else:
                    sanitized_dict[key] = cls.sanitize_dict(val)
            return sanitized_dict
        elif isinstance(data, list):
            return [cls.sanitize_dict(item) for item in data]
        elif isinstance(data, str):
            return cls.sanitize_log(data)
        return data

    @staticmethod
    def validate_webhook_token(
        received_token: Optional[str], 
        expected_token: Optional[str]
    ) -> bool:
        """
        Valida o token recebido contra o token esperado utilizando
        secrets.compare_digest para prevenir ataques de temporização (Timing Attacks).
        Suporta tanto tokens diretos quanto prefixados com 'Bearer '.
        """
        if not expected_token:
            return True

        if not received_token:
            return False

        clean_received = received_token.strip()
        if clean_received.lower().startswith("bearer "):
            clean_received = clean_received[7:].strip()

        clean_expected = expected_token.strip()
        if clean_expected.lower().startswith("bearer "):
            clean_expected = clean_expected[7:].strip()

        return secrets.compare_digest(clean_received, clean_expected)


class SensitiveDataFilter(logging.Filter):
    """
    Filtro para logging padrão do Python que sanitiza automaticamente
    qualquer mensagem de log antes de ser emitida para stdout/arquivos.
    """
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = SecurityService.sanitize_log(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    SecurityService.sanitize_log(str(a)) if isinstance(a, str) else a 
                    for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = SecurityService.sanitize_dict(record.args)
        return True
