import logging
import threading
import re
import unicodedata
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from config.firebase import db
from config.settings import settings

logger = logging.getLogger(__name__)


def normalize_alias(alias: str) -> str:
    """Normaliza apelidos para chaves consistentes."""
    if not alias:
        return ""
    
    # Remove acentos para comparação semântica
    norm = unicodedata.normalize("NFKD", alias.strip().lower()).encode("ascii", "ignore").decode("utf-8")
    norm = re.sub(r"\s+", " ", norm).strip()
    
    # Mapeamentos diretos
    if norm in ["casa", "minha casa", "home", "residencia"]:
        return "casa"
    if norm in ["trabalho", "meu trabalho", "escritorio", "meu escritorio", "firma", "work", "office"]:
        return "trabalho"
    
    # Remove múltiplos espaços preservando o texto original em minúsculas
    return re.sub(r"\s+", " ", alias.strip().lower())



class AddressRepository:
    """Repositório de locais e endereços do usuário com persistência no Firestore e cache L1."""
    
    COLLECTION_NAME = "user_addresses"
    _cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    _lock = threading.RLock()

    @classmethod
    def _doc_id(cls, user_jid: str, alias: str) -> str:
        safe_jid = re.sub(r"[^a-zA-Z0-9]", "_", user_jid or "default_user")
        safe_alias = re.sub(r"[^a-zA-Z0-9]", "_", alias)
        return f"{safe_jid}__{safe_alias}"

    @classmethod
    def save_address(
        cls,
        user_jid: str,
        alias: str,
        address: str,
        formatted_address: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        details: str = ""
    ) -> Dict[str, Any]:
        """Salva ou atualiza um endereço no Firestore e no cache L1."""
        clean_alias = normalize_alias(alias)
        jid = user_jid or settings.ALLOWED_PHONE_NUMBER or "default_user"
        
        now_iso = datetime.now(timezone.utc).isoformat()
        data = {
            "user_jid": jid,
            "alias": clean_alias,
            "address": address.strip(),
            "formatted_address": (formatted_address or address).strip(),
            "latitude": latitude,
            "longitude": longitude,
            "details": details.strip() if details else "",
            "updated_at": now_iso
        }

        with cls._lock:
            cls._cache[(jid, clean_alias)] = data

        if db:
            try:
                doc_id = cls._doc_id(jid, clean_alias)
                db.collection(cls.COLLECTION_NAME).document(doc_id).set(data)
                logger.info(f"[AddressRepository] Endereço '{clean_alias}' persistido no Firestore para {jid}")
            except Exception as e:
                logger.error(f"[AddressRepository] Erro ao gravar endereço no Firestore: {e}")

        return data

    @classmethod
    def get_address(cls, user_jid: str, alias: str) -> Optional[Dict[str, Any]]:
        """Busca um endereço pelo apelido no cache L1 ou no Firestore."""
        clean_alias = normalize_alias(alias)
        jid = user_jid or settings.ALLOWED_PHONE_NUMBER or "default_user"

        with cls._lock:
            if (jid, clean_alias) in cls._cache:
                return cls._cache[(jid, clean_alias)]

        if db:
            try:
                doc_id = cls._doc_id(jid, clean_alias)
                doc = db.collection(cls.COLLECTION_NAME).document(doc_id).get()
                if doc.exists:
                    data = doc.to_dict()
                    with cls._lock:
                        cls._cache[(jid, clean_alias)] = data
                    return data
            except Exception as e:
                logger.error(f"[AddressRepository] Erro ao consultar endereço no Firestore: {e}")

        return None

    @classmethod
    def list_addresses(cls, user_jid: str = "") -> List[Dict[str, Any]]:
        """Lista todos os endereços cadastrados para o usuário."""
        jid = user_jid or settings.ALLOWED_PHONE_NUMBER or "default_user"
        enderecos: Dict[str, Dict[str, Any]] = {}

        # Pega do cache L1
        with cls._lock:
            for (cj, ca), val in cls._cache.items():
                if cj == jid:
                    enderecos[ca] = val

        if db:
            try:
                docs = db.collection(cls.COLLECTION_NAME).where("user_jid", "==", jid).stream()
                for doc in docs:
                    data = doc.to_dict()
                    alias = data.get("alias", "")
                    if alias:
                        enderecos[alias] = data
                        with cls._lock:
                            cls._cache[(jid, alias)] = data
            except Exception as e:
                logger.error(f"[AddressRepository] Erro ao listar endereços no Firestore: {e}")

        return list(enderecos.values())

    @classmethod
    def delete_address(cls, user_jid: str, alias: str) -> bool:
        """Remove um endereço do banco e do cache."""
        clean_alias = normalize_alias(alias)
        jid = user_jid or settings.ALLOWED_PHONE_NUMBER or "default_user"

        with cls._lock:
            cls._cache.pop((jid, clean_alias), None)

        if db:
            try:
                doc_id = cls._doc_id(jid, clean_alias)
                db.collection(cls.COLLECTION_NAME).document(doc_id).delete()
                logger.info(f"[AddressRepository] Endereço '{clean_alias}' removido do Firestore.")
                return True
            except Exception as e:
                logger.error(f"[AddressRepository] Erro ao deletar endereço no Firestore: {e}")
                return False
        return True
