import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from config import firebase

logger = logging.getLogger(__name__)

# Armazenamento em memória para fallback/mock (quando Firebase não inicializado ou em testes)
_mock_storage: List[Dict[str, Any]] = []

def _reset_mock_storage() -> None:
    """Limpa o armazenamento em memória (útil para testes unitários)."""
    global _mock_storage
    _mock_storage.clear()

from services.user_context import UserContext

def _obter_todos_itens() -> List[Dict[str, Any]]:
    """Recupera todos os itens da coleção 'notes_reminders' ou do mock filtrados pelo usuário ativo."""
    user_id = UserContext.get_user_id()
    todos = []
    if firebase.db is not None:
        try:
            docs = firebase.db.collection("notes_reminders").stream()
            todos = [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Erro ao ler Firestore notes_reminders: {e}. Usando mock.")
            todos = list(_mock_storage)
    else:
        todos = list(_mock_storage)

    # Filtra estritamente pelo usuário ativo (retrocompatibilidade: se sem user_id, pertence ao daniel)
    return [i for i in todos if (i.get("userId") or i.get("user_id") or "daniel") == user_id]

def _salvar_item(item: Dict[str, Any]) -> None:
    """Salva um item no Firestore ou no armazenamento em memória vinculado ao usuário ativo."""
    user_id = UserContext.get_user_id()
    item["userId"] = user_id
    item["user_id"] = user_id
    _mock_storage.append(item)
    if firebase.db is not None:
        try:
            firebase.db.collection("notes_reminders").document(item["id"]).set(item)
        except Exception as e:
            logger.error(f"Erro ao salvar no Firestore: {e}. Mantido em mock.")

def _atualizar_item(item_id: str, updates: Dict[str, Any]) -> bool:
    """Atualiza um item no Firestore e no mock, garantindo que pertença ao usuário ativo."""
    user_id = UserContext.get_user_id()
    atualizado = False
    for item in _mock_storage:
        if item.get("id") == item_id and (item.get("userId") or item.get("user_id") or "daniel") == user_id:
            item.update(updates)
            atualizado = True
            break
            
    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("notes_reminders").document(item_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_data = doc.to_dict()
                if (doc_data.get("userId") or doc_data.get("user_id") or "daniel") == user_id:
                    doc_ref.update(updates)
                    atualizado = True
                else:
                    logger.warning(f"Tentativa de atualização de item de outro usuário: {item_id}")
        except Exception as e:
            logger.error(f"Erro ao atualizar Firestore doc {item_id}: {e}")

    return atualizado



def criar_anotacao(titulo: str, conteudo: str, tags: Optional[List[str]] = None) -> str:
    """
    Cria e salva uma anotação de conhecimento pessoal na coleção 'notes_reminders'.

    Args:
        titulo (str): Título conciso da anotação.
        conteudo (str): Conteúdo descritivo ou corpo da anotação.
        tags (list[str], opcional): Lista de etiquetas para categorização (ex: ['trabalho', 'ideias']).
    """
    if tags is None:
        tags_limpas = []
    elif isinstance(tags, list):
        tags_limpas = [str(t).strip().lower() for t in tags if str(t).strip()]
    else:
        tags_limpas = [t.strip().lower() for t in str(tags).split(",") if t.strip()]

    item = {
        "id": str(uuid.uuid4()),
        "tipo": "nota",
        "titulo": titulo.strip(),
        "conteudo": conteudo.strip(),
        "tags": tags_limpas,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _salvar_item(item)
    tags_str = f" [#{' #'.join(tags_limpas)}]" if tags_limpas else ""
    return f"📝 Anotação '{item['titulo']}' salva com sucesso!{tags_str} (ID: {item['id'][:8]})"


def criar_lembrete(titulo: str, data_hora_lembrete: str, tags: Optional[List[str]] = None) -> str:
    """
    Cria um lembrete com data/hora para notificação e salva na coleção 'notes_reminders' com status 'pendente'.

    Args:
        titulo (str): Descrição ou assunto do lembrete.
        data_hora_lembrete (str): Data e horário do lembrete (ex: '2026-09-04 15:00' ou 'Amanhã às 10h').
        tags (list[str], opcional): Lista de categorias/etiquetas do lembrete.
    """
    if tags is None:
        tags_limpas = []
    elif isinstance(tags, list):
        tags_limpas = [str(t).strip().lower() for t in tags if str(t).strip()]
    else:
        tags_limpas = [t.strip().lower() for t in str(tags).split(",") if t.strip()]

    item = {
        "id": str(uuid.uuid4()),
        "tipo": "lembrete",
        "titulo": titulo.strip(),
        "data_hora_lembrete": data_hora_lembrete.strip(),
        "status": "pendente",
        "tags": tags_limpas,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _salvar_item(item)
    tags_str = f" [#{' #'.join(tags_limpas)}]" if tags_limpas else ""
    return (
        f"⏰ Lembrete agendado com sucesso!\n"
        f"• **Assunto:** {item['titulo']}{tags_str}\n"
        f"• **Quando:** {item['data_hora_lembrete']}\n"
        f"• **Status:** Pendente ⏳ (ID: {item['id'][:8]})"
    )


def buscar_anotacoes(termo: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    Busca anotações salvas por palavra-chave ou por tag de categoria.

    Args:
        termo (str, opcional): Texto ou termo para buscar no título e no conteúdo das anotações.
        tag (str, opcional): Nome da tag para filtrar (ex: 'saude', 'financas', 'ideias').
    """
    todos = _obter_todos_itens()
    notas = [item for item in todos if item.get("tipo") == "nota"]

    if not notas:
        return "Nenhuma anotação encontrada no seu histórico."

    filtradas = []
    termo_busca = termo.strip().lower() if termo else None
    tag_busca = tag.strip().lower() if tag else None

    for n in notas:
        corresponde_termo = True
        corresponde_tag = True

        if termo_busca:
            tit = n.get("titulo", "").lower()
            cont = n.get("conteudo", "").lower()
            corresponde_termo = (termo_busca in tit) or (termo_busca in cont)

        if tag_busca:
            tags_item = [t.lower() for t in n.get("tags", [])]
            corresponde_tag = any(tag_busca in t for t in tags_item)

        if corresponde_termo and corresponde_tag:
            filtradas.append(n)

    if not filtradas:
        criterios = []
        if termo:
            criterios.append(f"termo '{termo}'")
        if tag:
            criterios.append(f"tag '{tag}'")
        return f"Nenhuma anotação encontrada para os critérios informados ({', '.join(criterios)})."

    linhas = [f"📋 **Anotações Encontradas ({len(filtradas)}):**"]
    for idx, item in enumerate(filtradas, start=1):
        tags_fmt = f" `#{' #'.join(item.get('tags', []))}`" if item.get("tags") else ""
        linhas.append(
            f"{idx}. **{item['titulo']}**{tags_fmt} *(ID: {item['id'][:8]})*\n"
            f"   {item['conteudo']}"
        )

    return "\n\n".join(linhas)


def listar_lembretes_pendentes() -> str:
    """
    Lista todos os lembretes que ainda estão com status 'pendente', ordenados pela data/horário.
    """
    todos = _obter_todos_itens()
    lembretes = [
        item for item in todos 
        if item.get("tipo") == "lembrete" and item.get("status") == "pendente"
    ]

    if not lembretes:
        return "🎉 Nenhum lembrete pendente no momento! Você está em dia."

    # Ordena por data_hora_lembrete
    lembretes_ordenados = sorted(lembretes, key=lambda x: str(x.get("data_hora_lembrete", "")))

    linhas = [f"⏰ **Lembretes Pendentes ({len(lembretes_ordenados)}):**"]
    for idx, lemb in enumerate(lembretes_ordenados, start=1):
        tags_fmt = f" [#{' #'.join(lemb.get('tags', []))}]" if lemb.get("tags") else ""
        linhas.append(
            f"{idx}. **{lemb['titulo']}**{tags_fmt}\n"
            f"   📅 Horário: {lemb.get('data_hora_lembrete')} | 🆔 `{lemb['id'][:8]}`"
        )

    return "\n\n".join(linhas)


def concluir_lembrete(lembrete_id_ou_titulo: str) -> str:
    """
    Marca um lembrete como 'concluido' utilizando seu ID (completo ou prefixo) ou o título.

    Args:
        lembrete_id_ou_titulo (str): ID do lembrete ou parte do título para busca.
    """
    termo = lembrete_id_ou_titulo.strip().lower()
    todos = _obter_todos_itens()

    candidato = None
    for item in todos:
        if item.get("tipo") == "lembrete" and item.get("status") == "pendente":
            item_id = str(item.get("id", "")).lower()
            item_titulo = str(item.get("titulo", "")).lower()

            if item_id == termo or item_id.startswith(termo) or termo in item_titulo:
                candidato = item
                break

    if not candidato:
        return f"Não encontrei nenhum lembrete pendente com o termo ou ID '{lembrete_id_ou_titulo}'."

    item_id = candidato["id"]
    concluido_em = datetime.now(timezone.utc).isoformat()
    _atualizar_item(item_id, {"status": "concluido", "concluido_em": concluido_em})

    return f"✅ Lembrete **'{candidato['titulo']}'** marcado como concluído com sucesso!"
