import logging
import re
import unicodedata
import uuid
from typing import Any, Dict, List, Optional
from config import firebase
from config.timezone import get_brasilia_now_str
from services.user_context import UserContext

logger = logging.getLogger(__name__)

# Armazenamento em memória para testes unitários ou fallback quando Firestore offline
_mock_storage: List[Dict[str, Any]] = []

# Sinônimos semânticos para buscas de hardware / peças de computador
_PC_SYNONYM_TRIGGERS = {
    "pc", "computador", "peca", "pecas", "hardware", "componente", "componentes",
    "setup", "upgrade", "maquina", "desktop", "gamer"
}
_PC_ITEM_KEYWORDS = {
    "pc", "computador", "peca", "pecas", "hardware", "processador", "cpu", "gpu",
    "placa de video", "placa-mae", "placa mae", "motherboard", "rtx", "gtx", "radeon",
    "geforce", "intel", "core i", "i5", "i7", "i9", "ryzen", "amd", "zotac", "asus",
    "msi", "gigabyte", "corsair", "kingston", "samsung", "nvme", "ssd", "hd", "ram",
    "ddr4", "ddr5", "memoria", "fonte", "psu", "750w", "850w", "80plus", "80 plus",
    "cooler", "water cooler", "gabinete", "lga", "am4", "am5", "microatx", "atx"
}


def _reset_mock_storage() -> None:
    """Limpa o armazenamento mock em memória (para testes unitários)."""
    global _mock_storage
    _mock_storage.clear()


def _normalize_text(text: str) -> str:
    """Remove acentos e normaliza para minúsculas."""
    if not text:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(text))
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return no_accent.lower().strip()


def _matches_search(item: Dict[str, Any], busca_raw: str) -> bool:
    """
    Verifica se o item da wishlist corresponde ao termo de busca,
    suportando normalização sem acentos, tokens parciais e sinônimos de hardware/PC.
    """
    busca_norm = _normalize_text(busca_raw)
    if not busca_norm:
        return True

    haystack = " ".join([
        str(item.get("nome_produto", "")),
        str(item.get("descricao", "")),
        str(item.get("categoria", "")),
        str(item.get("link", ""))
    ])
    haystack_norm = _normalize_text(haystack)

    # 1. Substring direta normalizada
    if busca_norm in haystack_norm:
        return True

    # 2. Expansão semântica para peças de computador / hardware
    tokens_busca = [
        t for t in re.findall(r"[a-z0-9]+", busca_norm)
        if (len(t) >= 2 or t.isdigit()) and t not in {"de", "do", "da", "dos", "das", "no", "na", "em", "para", "pro", "pra", "meu", "minha"}
    ]
    if any(t in _PC_SYNONYM_TRIGGERS for t in tokens_busca) or busca_norm in _PC_SYNONYM_TRIGGERS:
        if any(re.search(rf"\b{re.escape(kw)}\b", haystack_norm) for kw in _PC_ITEM_KEYWORDS):
            return True

    # 3. Match por tokens significativos
    haystack_tokens = set(re.findall(r"[a-z0-9]+", haystack_norm))
    if tokens_busca and all((t in haystack_tokens if t.isdigit() else t in haystack_norm) for t in tokens_busca):
        return True

    return False


class WishlistRepository:
    """Repositório de dados para a coleção 'wishlist' do Firestore com fallback in-memory."""

    COLLECTION = "wishlist"

    @staticmethod
    def salvar(item: Dict[str, Any]) -> Dict[str, Any]:
        """Persiste um item na wishlist no Firestore vinculado ao usuário ativo."""
        user_id = UserContext.get_user_id()
        if not item.get("id"):
            item["id"] = f"wsh_{uuid.uuid4().hex[:8]}"

        item["userId"] = user_id
        item["user_id"] = user_id
        agora = get_brasilia_now_str()
        item.setdefault("criadoEm", agora)
        item["atualizadoEm"] = agora

        # Atualiza ou insere no mock em memória
        existing_idx = next((idx for idx, x in enumerate(_mock_storage) if x.get("id") == item["id"]), None)
        if existing_idx is not None:
            _mock_storage[existing_idx] = dict(item)
        else:
            _mock_storage.append(dict(item))

        if firebase.db is not None:
            try:
                firebase.db.collection(WishlistRepository.COLLECTION).document(item["id"]).set(item)
                logger.info(f"[WISHLIST] Item '{item.get('nome_produto')}' ({item['id']}) salvo no Firestore para {user_id}.")
            except Exception as e:
                logger.error(f"Erro ao salvar item no Firestore (wishlist): {e}. Mantido em memória.")

        return item

    @staticmethod
    def listar(user_id: Optional[str] = None, status: str = "todos", busca: str = "") -> List[Dict[str, Any]]:
        """Recupera itens da wishlist filtrando por usuário, status e termo de busca."""
        alvo_user = user_id or UserContext.get_user_id()
        todos_map: Dict[str, Dict[str, Any]] = {}

        if firebase.db is not None:
            try:
                docs = firebase.db.collection(WishlistRepository.COLLECTION).stream()
                for doc in docs:
                    data = doc.to_dict()
                    if data:
                        doc_id = data.get("id") or doc.id
                        data["id"] = doc_id
                        todos_map[doc_id] = data
            except Exception as e:
                logger.error(f"Erro ao consultar Firestore (wishlist): {e}. Usando mock.")
                for m in _mock_storage:
                    todos_map[m.get("id", str(uuid.uuid4()))] = m
        else:
            for m in _mock_storage:
                todos_map[m.get("id", str(uuid.uuid4()))] = m

        todos = list(todos_map.values())

        itens_usuario = [
            i for i in todos
            if (i.get("userId") or i.get("user_id") or "daniel") == alvo_user
        ]

        status_clean = (status or "todos").strip().lower()
        if status_clean in ["desejado", "comprado"]:
            itens_usuario = [i for i in itens_usuario if i.get("status", "desejado") == status_clean]

        if busca and busca.strip():
            itens_usuario = [i for i in itens_usuario if _matches_search(i, busca)]

        itens_usuario.sort(key=lambda x: str(x.get("criadoEm", "")), reverse=True)
        return itens_usuario

    @staticmethod
    def obter_por_id(item_id: str, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Busca um item específico pelo ID garantindo que pertença ao usuário ativo."""
        alvo_user = user_id or UserContext.get_user_id()

        if firebase.db is not None:
            try:
                doc = firebase.db.collection(WishlistRepository.COLLECTION).document(item_id).get()
                if doc.exists:
                    d = doc.to_dict()
                    if d and (d.get("userId") or d.get("user_id") or "daniel") == alvo_user:
                        return d
            except Exception as e:
                logger.error(f"Erro ao obter doc Firestore {item_id}: {e}")

        for item in _mock_storage:
            if item.get("id") == item_id and (item.get("userId") or item.get("user_id") or "daniel") == alvo_user:
                return item

        return None

    @staticmethod
    def atualizar(item_id: str, updates: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Atualiza campos de um item existente respeitando o isolamento multiusuário."""
        alvo_user = user_id or UserContext.get_user_id()
        atualizado = False

        updates["atualizadoEm"] = get_brasilia_now_str()

        for item in _mock_storage:
            if item.get("id") == item_id and (item.get("userId") or item.get("user_id") or "daniel") == alvo_user:
                item.update(updates)
                atualizado = True
                break

        if firebase.db is not None:
            try:
                doc_ref = firebase.db.collection(WishlistRepository.COLLECTION).document(item_id)
                doc = doc_ref.get()
                if doc.exists:
                    d = doc.to_dict() or {}
                    if (d.get("userId") or d.get("user_id") or "daniel") == alvo_user:
                        doc_ref.update(updates)
                        atualizado = True
                    else:
                        logger.warning(f"Tentativa de atualização de wishlist de outro usuário: {item_id}")
            except Exception as e:
                logger.error(f"Erro ao atualizar doc Firestore {item_id}: {e}")

        return atualizado

    @staticmethod
    def remover(item_id: str, user_id: Optional[str] = None) -> bool:
        """Remove definitivamente um item da wishlist do usuário ativo."""
        global _mock_storage
        alvo_user = user_id or UserContext.get_user_id()
        removido = False

        inicial_len = len(_mock_storage)
        _mock_storage = [
            i for i in _mock_storage
            if not (i.get("id") == item_id and (i.get("userId") or i.get("user_id") or "daniel") == alvo_user)
        ]
        if len(_mock_storage) < inicial_len:
            removido = True

        if firebase.db is not None:
            try:
                doc_ref = firebase.db.collection(WishlistRepository.COLLECTION).document(item_id)
                doc = doc_ref.get()
                if doc.exists:
                    d = doc.to_dict() or {}
                    if (d.get("userId") or d.get("user_id") or "daniel") == alvo_user:
                        doc_ref.delete()
                        removido = True
                    else:
                        logger.warning(f"Tentativa de remoção de wishlist de outro usuário: {item_id}")
            except Exception as e:
                logger.error(f"Erro ao remover doc Firestore {item_id}: {e}")

        return removido
