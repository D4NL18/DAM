import contextvars
import re
from typing import Optional, Dict, Any

# Variáveis de contexto para rastrear o usuário ativo no ciclo de vida da requisição
_current_user_id: contextvars.ContextVar[str] = contextvars.ContextVar("current_user_id", default="daniel")
_current_user_name: contextvars.ContextVar[str] = contextvars.ContextVar("current_user_name", default="Admin")
_current_user_phone: contextvars.ContextVar[str] = contextvars.ContextVar("current_user_phone", default="5511999999999")


class UserContext:
    """Gerencia o contexto do usuário autenticado de forma assíncrona e thread-safe."""

    # Mapeamento oficial dos usuários do sistema
    USERS = {
        "daniel": {
            "id": "daniel",
            "name": "Admin",
            "phone": "5511999999999",
            "calendar_env_key": "CALENDAR_ID_DANIEL",
            "can_access_other_calendars": True,
        },
        "lari": {
            "id": "lari",
            "name": "User",
            "phone": "5511888888888",
            "calendar_env_key": "CALENDAR_ID_LARI",
            "can_access_other_calendars": False,
        }
    }

    @classmethod
    def get_user_phone_by_id(cls, user_id: str) -> str:
        """Recupera o telefone configurado do usuário dinamicamente das configurações ou fallback dos USERS."""
        u_id = user_id.lower().strip()
        if u_id == "admin":
            u_id = "daniel"
        elif u_id == "user":
            u_id = "lari"

        try:
            from config.settings import settings
            nums = settings.allowed_numbers_list
            if u_id == "daniel":
                if nums:
                    return nums[0]
                return settings.ALLOWED_PHONE_NUMBER or cls.USERS.get("daniel", {}).get("phone", "5511999999999")
            elif u_id == "lari":
                if len(nums) > 1:
                    return nums[1]
                return cls.USERS.get("lari", {}).get("phone", "5511888888888")
        except Exception:
            pass

        return cls.USERS.get(u_id, {}).get("phone", "")

    @classmethod
    def set_user(cls, user_id: str, phone: str = "") -> None:
        u_id = user_id.lower().strip()
        if u_id == "admin":
            u_id = "daniel"
        elif u_id == "user":
            u_id = "lari"
        user_info = cls.get_user_info(u_id)
        _current_user_id.set(user_info["id"])
        _current_user_name.set(user_info["name"])
        _current_user_phone.set(phone or user_info["phone"])

    @classmethod
    def get_user_id(cls) -> str:
        return _current_user_id.get()

    @classmethod
    def get_user_name(cls) -> str:
        return _current_user_name.get()

    @classmethod
    def get_user_phone(cls) -> str:
        return _current_user_phone.get()

    @classmethod
    def get_user_info(cls, user_id: Optional[str] = None) -> Dict[str, Any]:
        target_id = (user_id or cls.get_user_id()).lower().strip()
        if target_id == "admin":
            target_id = "daniel"
        elif target_id == "user":
            target_id = "lari"
        info = dict(cls.USERS.get(target_id, cls.USERS["daniel"]))
        dynamic_phone = cls.get_user_phone_by_id(target_id)
        if dynamic_phone:
            info["phone"] = dynamic_phone
        return info

    @classmethod
    def resolve_user_from_phone(cls, phone_or_jid: str) -> Optional[Dict[str, Any]]:
        """Resolve o usuário correspondente a partir do número ou JID recebido no WhatsApp."""
        if not phone_or_jid:
            return None

        digits = re.sub(r"\D", "", phone_or_jid.split("@")[0])
        if len(digits) < 8:
            return None

        num8 = digits[-8:]
        for user_id, info in cls.USERS.items():
            user_phone = cls.get_user_phone_by_id(user_id) or info.get("phone", "")
            u_digits = re.sub(r"\D", "", user_phone)
            if u_digits[-8:] == num8:
                resolved = dict(info)
                resolved["phone"] = user_phone
                return resolved
            # Fallback para o phone estático no USERS
            static_digits = re.sub(r"\D", "", info.get("phone", ""))
            if static_digits[-8:] == num8:
                return dict(info)
        return None

def resolve_user_from_phone(phone_or_jid: str) -> Optional[Dict[str, Any]]:
    """Função utilitária no nível do módulo para resolução rápida."""
    return UserContext.resolve_user_from_phone(phone_or_jid)