"""
ExecutionAuditContext — Rastreador Determinístico de Execução e Erros de Ferramentas (P-0805)
Impede que o modelo de IA afirme ter cadastrado/registrado algo quando a ferramenta
não foi executada ou quando a ferramenta retornou erro/pendência.
"""
import contextvars
import functools
from typing import Dict, List, Any, Optional, Set, Callable


_AUDIT_EVENTS: contextvars.ContextVar[Optional[List[Dict[str, Any]]]] = contextvars.ContextVar(
    "dam_execution_audit_events", default=None
)


class ExecutionAuditContext:
    """Contexto isolado por requisição/turno para auditar execuções reais de ferramentas."""

    @classmethod
    def reset(cls) -> None:
        """Limpa os eventos do turno atual."""
        _AUDIT_EVENTS.set([])

    @classmethod
    def _get_list(cls) -> List[Dict[str, Any]]:
        events = _AUDIT_EVENTS.get()
        if events is None:
            events = []
            _AUDIT_EVENTS.set(events)
        return events

    @classmethod
    def record_success(cls, tool_name: str, message: str) -> None:
        """Registra que uma ferramenta de mutação concluiu a gravação com sucesso."""
        cls._get_list().append({
            "tool": tool_name,
            "success": True,
            "reason": "ok",
            "message": message,
        })

    @classmethod
    def record_failure(cls, tool_name: str, message: str, reason: str = "error") -> None:
        """Registra que uma ferramenta falhou ou não pôde concluir o cadastro."""
        cls._get_list().append({
            "tool": tool_name,
            "success": False,
            "reason": reason,
            "message": message,
        })

    @classmethod
    def get_events(cls) -> List[Dict[str, Any]]:
        return list(cls._get_list())

    @classmethod
    def has_successful_execution(cls, tool_names: Optional[Set[str]] = None) -> bool:
        for ev in cls._get_list():
            if ev.get("success") is True:
                if tool_names is None or ev.get("tool") in tool_names:
                    return True
        return False

    @classmethod
    def get_failures(cls, tool_names: Optional[Set[str]] = None) -> List[Dict[str, Any]]:
        failures = []
        for ev in cls._get_list():
            if ev.get("success") is False:
                if tool_names is None or ev.get("tool") in tool_names:
                    failures.append(ev)
        return failures


def audit_tool_execution(tool_name: Optional[str] = None) -> Callable:
    """
    Decorator universal para ferramentas de mutação.
    Intercepta strings com marcadores de falha (❌, ⚠️, 'erro:', 'não foi cadastrad', 'não foi gravad')
    ou exceções e registra automaticamente no ExecutionAuditContext.
    """
    def decorator(func: Callable) -> Callable:
        name = tool_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
                if isinstance(res, str):
                    res_lower = res.lower()
                    if (
                        res.startswith("❌") 
                        or res.startswith("⚠️") 
                        or "erro:" in res_lower
                        or "não foi cadastrad" in res_lower
                        or "não foi gravad" in res_lower
                        or "não foi possível" in res_lower
                        or "não está disponível" in res_lower
                    ):
                        ExecutionAuditContext.record_failure(name, res, reason="tool_reported_failure")
                        return res
                ExecutionAuditContext.record_success(name, str(res) if res is not None else "ok")
                return res
            except Exception as e:
                err_msg = f"❌ Erro ao executar ferramenta '{name}': {e}"
                ExecutionAuditContext.record_failure(name, err_msg, reason="exception")
                raise

        return wrapper
    return decorator
