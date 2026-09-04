import logging
import threading
import uuid
import unicodedata
import re
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config import firebase

logger = logging.getLogger(__name__)


def remover_acentos(texto: str) -> str:
    """Normaliza texto para minúsculas e sem acentos para busca flexível."""
    if not texto:
        return ""
    norm = unicodedata.normalize("NFKD", texto.strip().lower()).encode("ascii", "ignore").decode("utf-8")
    return re.sub(r"\s+", " ", norm).strip()


class SavedVideosRepository:
    """
    Repositório thread-safe para gerenciamento de vídeos salvos das redes sociais.
    Persiste no Firebase Firestore com fallback em memória (_storage) para desenvolvimento e testes.
    """

    COLLECTION_NAME = "saved_videos"
    _instance: Optional["SavedVideosRepository"] = None
    _lock = threading.RLock()

    def __init__(self) -> None:
        self._storage: List[Dict[str, Any]] = []

    @classmethod
    def get_instance(cls) -> "SavedVideosRepository":
        """Retorna a instância singleton do repositório."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def clear_for_tests(self) -> None:
        """Limpa o armazenamento em memória para testes unitários isolados."""
        with self._lock:
            self._storage.clear()

    def salvar(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Salva um novo vídeo no Firestore ou no armazenamento em memória."""
        with self._lock:
            agora_iso = datetime.now(timezone.utc).isoformat()
            if "id" not in item or not item["id"]:
                item["id"] = str(uuid.uuid4())
            if "created_at" not in item:
                item["created_at"] = agora_iso
            item["updated_at"] = agora_iso

            # Armazena na memória local
            self._storage.append(dict(item))

            # Persiste no Firestore se disponível
            if firebase.db is not None:
                try:
                    firebase.db.collection(self.COLLECTION_NAME).document(item["id"]).set(item)
                except Exception as e:
                    logger.error(f"Erro ao salvar vídeo no Firestore: {e}. Mantido em fallback local.")

            return item

    def listar_por_usuario(
        self,
        user_id: str,
        plataforma: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna todos os vídeos salvos pertencentes ao usuário ativo,
        com filtros opcionais de plataforma e status, ordenados por data decrescente.
        """
        with self._lock:
            todos: List[Dict[str, Any]] = []

            # Tenta ler do Firestore primeiro
            if firebase.db is not None:
                try:
                    query = firebase.db.collection(self.COLLECTION_NAME).where("userId", "==", user_id)
                    if plataforma and plataforma.lower() != "todos":
                        query = query.where("plataforma", "==", plataforma)
                    if status and status.lower() != "todos":
                        query = query.where("status", "==", status)
                    docs = query.stream()
                    todos = [doc.to_dict() for doc in docs]
                except Exception as e:
                    logger.error(f"Erro ao consultar vídeos no Firestore: {e}. Usando cache local.")
                    todos = list(self._storage)
            else:
                todos = list(self._storage)

            # Filtro estrito de isolamento por usuário
            resultado = [
                i for i in todos
                if (i.get("userId") or i.get("user_id") or "daniel") == user_id
            ]

            # Aplicação de filtros em memória
            if plataforma and plataforma.lower() != "todos":
                plat_norm = plataforma.strip().lower()
                resultado = [i for i in resultado if i.get("plataforma", "").lower() == plat_norm]

            if status and status.lower() != "todos":
                status_norm = status.strip().lower()
                resultado = [i for i in resultado if i.get("status", "").lower() == status_norm]

            # Ordenação decrescente por created_at
            resultado.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return resultado

    def buscar_por_termo(
        self,
        user_id: str,
        termo: str,
        plataforma: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Realiza busca semântica e por palavras-chave nos campos titulo, descricao,
        tags, categoria e plataforma para o usuário autenticado.
        Prioriza correspondências que contenham todos os tokens da busca.
        """
        videos = self.listar_por_usuario(user_id=user_id, plataforma=plataforma, status=status)
        if not termo or not termo.strip():
            return videos

        termo_norm = remover_acentos(termo)
        tokens_busca = [t for t in termo_norm.split(" ") if t]

        matches_exatos: List[Dict[str, Any]] = []
        matches_parciais: List[Dict[str, Any]] = []

        for v in videos:
            campos_para_busca = [
                v.get("titulo", ""),
                v.get("descricao", ""),
                v.get("categoria", ""),
                v.get("plataforma", ""),
                " ".join(v.get("tags", [])) if isinstance(v.get("tags"), list) else str(v.get("tags", ""))
            ]
            conteudo_completo = remover_acentos(" ".join(campos_para_busca))

            # Prioriza itens que contêm todos os tokens da busca
            if all(token in conteudo_completo for token in tokens_busca):
                matches_exatos.append(v)
            elif any(token in conteudo_completo for token in tokens_busca):
                matches_parciais.append(v)

        return matches_exatos if matches_exatos else matches_parciais

    def obter_por_id(self, user_id: str, video_id: str) -> Optional[Dict[str, Any]]:
        """Recupera um vídeo pelo ID garantindo que pertença ao usuário ativo."""
        with self._lock:
            for item in self._storage:
                if item.get("id") == video_id and (item.get("userId") or item.get("user_id") or "daniel") == user_id:
                    return item

            if firebase.db is not None:
                try:
                    doc = firebase.db.collection(self.COLLECTION_NAME).document(video_id).get()
                    if doc.exists:
                        data = doc.to_dict()
                        if (data.get("userId") or data.get("user_id") or "daniel") == user_id:
                            return data
                except Exception as e:
                    logger.error(f"Erro ao buscar vídeo {video_id} no Firestore: {e}")

            return None

    def atualizar_status(self, user_id: str, video_id: str, novo_status: str) -> bool:
        """Atualiza o status de um vídeo (ex: 'assistido') pertencente ao usuário."""
        with self._lock:
            agora_iso = datetime.now(timezone.utc).isoformat()
            atualizado = False

            for item in self._storage:
                if item.get("id") == video_id and (item.get("userId") or item.get("user_id") or "daniel") == user_id:
                    item["status"] = novo_status
                    item["updated_at"] = agora_iso
                    if novo_status == "assistido":
                        item["assistido_em"] = agora_iso
                    atualizado = True
                    break

            if firebase.db is not None:
                try:
                    doc_ref = firebase.db.collection(self.COLLECTION_NAME).document(video_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        data = doc.to_dict()
                        if (data.get("userId") or data.get("user_id") or "daniel") == user_id:
                            updates = {"status": novo_status, "updated_at": agora_iso}
                            if novo_status == "assistido":
                                updates["assistido_em"] = agora_iso
                            doc_ref.update(updates)
                            atualizado = True
                except Exception as e:
                    logger.error(f"Erro ao atualizar status de vídeo {video_id} no Firestore: {e}")

            return atualizado

    def excluir(self, user_id: str, video_id: str) -> bool:
        """Exclui permanentemente um vídeo garantindo isolamento por usuário."""
        with self._lock:
            encontrado = False
            for i, item in enumerate(self._storage):
                if item.get("id") == video_id and (item.get("userId") or item.get("user_id") or "daniel") == user_id:
                    self._storage.pop(i)
                    encontrado = True
                    break

            if firebase.db is not None:
                try:
                    doc_ref = firebase.db.collection(self.COLLECTION_NAME).document(video_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        data = doc.to_dict()
                        if (data.get("userId") or data.get("user_id") or "daniel") == user_id:
                            doc_ref.delete()
                            encontrado = True
                except Exception as e:
                    logger.error(f"Erro ao excluir vídeo {video_id} no Firestore: {e}")

            return encontrado
