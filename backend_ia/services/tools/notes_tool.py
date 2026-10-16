import logging
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from config import firebase

logger = logging.getLogger(__name__)

# Padrão regex reutilizado para higienização e extração de tags (evita literais duplicados - python:S1192)
TAG_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-]+")

# Armazenamento em memória para fallback/mock (quando Firebase não inicializado ou em testes)
_mock_storage: List[Dict[str, Any]] = []

def _reset_mock_storage() -> None:
    """Limpa o armazenamento em memória (útil para testes unitários)."""
    global _mock_storage
    _mock_storage.clear()

from services.user_context import UserContext

def _obter_todos_itens(colecao: Optional[str] = None) -> List[Dict[str, Any]]:
    """Recupera todos os itens da coleção indicada ou de ambas se None, ou do mock, filtrados pelo usuário ativo."""
    user_id = UserContext.get_user_id()
    todos = []
    if firebase.db is not None:
        try:
            if colecao:
                docs = firebase.db.collection(colecao).stream()
                todos = [doc.to_dict() for doc in docs]
            else:
                docs_rem = firebase.db.collection("notes_reminders").stream()
                todos = [doc.to_dict() for doc in docs_rem]
                docs_notes = firebase.db.collection("information_notes").stream()
                todos.extend([doc.to_dict() for doc in docs_notes])
        except Exception as e:
            logger.error(f"Erro ao ler Firestore: {e}. Usando mock.")
            if colecao:
                todos = [i for i in _mock_storage if i.get("_colecao") == colecao]
            else:
                todos = list(_mock_storage)
    else:
        if colecao:
            todos = [i for i in _mock_storage if i.get("_colecao") == colecao]
        else:
            todos = list(_mock_storage)

    # Filtra estritamente pelo usuário ativo (retrocompatibilidade: se sem user_id, pertence ao daniel)
    return [i for i in todos if (i.get("userId") or i.get("user_id") or "daniel") == user_id]

def _salvar_item(item: Dict[str, Any], colecao: str = "notes_reminders") -> None:
    """Salva um item no Firestore na coleção indicada ou no armazenamento em memória vinculado ao usuário ativo."""
    user_id = UserContext.get_user_id()
    item["userId"] = user_id
    item["user_id"] = user_id
    item["_colecao"] = colecao
    _mock_storage.append(item)
    if firebase.db is not None:
        try:
            firebase.db.collection(colecao).document(item["id"]).set(item)
        except Exception as e:
            logger.error(f"Erro ao salvar no Firestore ({colecao}): {e}. Mantido em mock.")

def _atualizar_item(item_id: str, updates: Dict[str, Any], colecao: str = "notes_reminders") -> bool:
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
            doc_ref = firebase.db.collection(colecao).document(item_id)
            doc = doc_ref.get()
            if doc.exists:
                doc_data = doc.to_dict()
                if (doc_data.get("userId") or doc_data.get("user_id") or "daniel") == user_id:
                    doc_ref.update(updates)
                    atualizado = True
                else:
                    logger.warning(f"Tentativa de atualização de item de outro usuário: {item_id}")
        except Exception as e:
            logger.error(f"Erro ao atualizar Firestore doc {item_id} em {colecao}: {e}")

    return atualizado


def calcular_proxima_ocorrencia(data_hora_str: str, recorrencia: Optional[str], data_base: Optional[datetime] = None) -> str:
    """Calcula a próxima data/hora válida se a data informada já tiver expirado e houver recorrência."""
    if not recorrencia or not data_hora_str:
        return data_hora_str

    rec = str(recorrencia).lower().strip()
    if rec not in ["diaria", "diario", "semanal", "mensal", "anual"]:
        return data_hora_str

    tz_br = timezone(timedelta(hours=-3))
    base = data_base or datetime.now(tz_br)

    dt = None
    try:
        if "T" in data_hora_str:
            dt = datetime.fromisoformat(data_hora_str.replace("Z", "+00:00"))
        else:
            dt = datetime.strptime(data_hora_str[:16], "%Y-%m-%d %H:%M")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tz_br)
    except Exception:
        return data_hora_str

    import calendar
    while dt < base:
        if rec in ["diaria", "diario"]:
            dt += timedelta(days=1)
        elif rec == "semanal":
            dt += timedelta(weeks=1)
        elif rec == "mensal":
            ano = dt.year + (1 if dt.month == 12 else 0)
            mes = 1 if dt.month == 12 else dt.month + 1
            max_dias = calendar.monthrange(ano, mes)[1]
            dia = min(dt.day, max_dias)
            dt = dt.replace(year=ano, month=mes, day=dia)
        elif rec == "anual":
            dt = dt.replace(year=dt.year + 1)

    return dt.strftime("%Y-%m-%d %H:%M")



def _extrair_tokens_tags(dado: Any) -> List[str]:
    """Extrai recursivamente tokens válidos de tags de strings ou listas aninhadas."""
    if isinstance(dado, str):
        return [t.lower() for t in TAG_TOKEN_PATTERN.findall(dado)]
    if isinstance(dado, (list, tuple, set)):
        tokens: List[str] = []
        for item in dado:
            tokens.extend(_extrair_tokens_tags(item))
        return tokens
    return []


def _formatar_tags_exibicao(tags_raw: Any) -> str:
    """Higieniza e formata tags para exibição limpa sem aninhamentos de arrays ou strings."""
    if not tags_raw:
        return ""
    tokens = _extrair_tokens_tags(tags_raw)
    tags_unicas = list(dict.fromkeys(tokens))
    return f" [#{' #'.join(tags_unicas)}]" if tags_unicas else ""


def criar_anotacao(titulo: str, conteudo: str, tags: Optional[Any] = None) -> str:
    """
    Save personal note, quote, or information in the dedicated information database.
    Does NOT create a reminder.

    Args:
        titulo (str): Note or topic title (e.g. 'Orçamento PC EUA', 'Anotação de reunião').
        conteudo (str): Detailed text, numbers, or information to remember.
        tags (list[str] or str, optional): Tags for categorization.
    """
    tags_limpas = list(dict.fromkeys(_extrair_tokens_tags(tags))) if tags else []

    item = {
        "id": str(uuid.uuid4()),
        "tipo": "nota",
        "titulo": titulo.strip(),
        "conteudo": conteudo.strip(),
        "tags": tags_limpas,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _salvar_item(item, colecao="information_notes")
    tags_str = _formatar_tags_exibicao(tags_limpas)
    return f"📝 Anotação '{item['titulo']}' salva com sucesso no banco de informações!{tags_str} (ID: {item['id'][:8]})"


def criar_lembrete(
    titulo: str, 
    data_hora_lembrete: str, 
    tags: Optional[Any] = None,
    recorrencia: Optional[str] = None
) -> str:
    """
    Create a reminder with date/time notification, pending status and optional recurrence.

    Args:
        titulo (str): Reminder subject (e.g. 'Aniversário de namoro', 'Pagar pré-pago Claro'). Never include '(Recorrente:...)' in the title.
        data_hora_lembrete (str): Scheduled datetime (e.g. 'YYYY-MM-DD HH:MM'). For recurring reminders, specify the first occurrence.
        tags (list[str] or str, optional): Categories/tags.
        recorrencia (str, optional): Recurrence frequency if recurring: 'diaria', 'semanal', 'mensal', 'anual'. Leave None for one-time reminders.
    """
    tags_limpas = list(dict.fromkeys(_extrair_tokens_tags(tags))) if tags else []

    rec_detectada = recorrencia
    tit_limpo = titulo.strip()

    padroes_rec = [
        (r"\(Recorrente:\s*todo\s+dia\s+(\d+)[^)]*\)", "mensal"),
        (r"\(Recorrente:\s*di[aá]ri[^)]*\)", "diaria"),
        (r"\(Recorrente:\s*semanal[^)]*\)", "semanal"),
        (r"\(Recorrente:\s*mensal[^)]*\)", "mensal"),
        (r"\(Recorrente:\s*anual[^)]*\)", "anual"),
        (r"\btodo\s+dia\s+\d+\b", "mensal"),
        (r"\bdiari[ao]mente\b|\btodo\s+dia\b", "diaria"),
        (r"\bsemanalmente\b|\btod[ao]s?\s+(segunda|terça|quarta|quinta|sexta|s[aá]bado|domingo)\b", "semanal"),
        (r"\bmensalmente\b|\btodo\s+m[eê]s\b", "mensal"),
        (r"\banualmente\b|\btodo\s+ano\b", "anual")
    ]
    if not rec_detectada:
        tit_lower = tit_limpo.lower()
        for padrao, tipo_rec in padroes_rec:
            if re.search(padrao, tit_lower, re.IGNORECASE):
                rec_detectada = tipo_rec
                break

    # Remove qualquer marcador artificial "(Recorrente:...)" do título
    tit_limpo = re.sub(r"\s*\(Recorrente:[^)]*\)", "", tit_limpo).strip()

    # Se for recorrente e a data informada já tiver passado, calcula a próxima ocorrência válida
    data_agendada = data_hora_lembrete.strip()
    if rec_detectada:
        data_agendada = calcular_proxima_ocorrencia(data_agendada, rec_detectada)

    item = {
        "id": str(uuid.uuid4()),
        "tipo": "lembrete",
        "titulo": tit_limpo,
        "data_hora_lembrete": data_agendada,
        "recorrencia": rec_detectada,
        "status": "pendente",
        "tags": tags_limpas,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    _salvar_item(item, colecao="notes_reminders")
    tags_str = _formatar_tags_exibicao(tags_limpas)
    rec_str = f" | 🔄 Recorrência: {rec_detectada.capitalize()}" if rec_detectada else ""
    return (
        f"⏰ Lembrete agendado com sucesso!\n"
        f"• **Assunto:** {item['titulo']}{tags_str}\n"
        f"• **Quando:** {item['data_hora_lembrete']}{rec_str}\n"
        f"• **Status:** Pendente ⏳ (ID: {item['id'][:8]})"
    )


def buscar_anotacoes(termo: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    Search saved notes by keyword or category tag in the information notes database.

    Args:
        termo (str, optional): Search keyword in title or content.
        tag (str, optional): Tag name to filter.
    """
    notas = _obter_todos_itens(colecao="information_notes")
    if not notas:
        todos = _obter_todos_itens(colecao="notes_reminders")
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


def _obter_data_filtro_lembrete(data_referencia: Optional[str]) -> str:
    """Retorna a string YYYY-MM-DD da data de referência informada ou de hoje em Brasília."""
    if data_referencia:
        return str(data_referencia)[:10]
    tz_br = timezone(timedelta(hours=-3))
    return datetime.now(tz_br).strftime("%Y-%m-%d")


def _filtrar_lembretes_por_data(lembretes: List[Dict[str, Any]], data_alvo: str) -> List[Dict[str, Any]]:
    """
    Filtra lembretes cuja data/hora coincida estritamente com a data alvo informada (YYYY-MM-DD).
    Regra mandatória: SE NÃO FOR PRA HOJE / DATA ALVO, NÃO É PRA MOSTRAR!
    Suporta tanto formato ISO (YYYY-MM-DD) quanto formato brasileiro (DD/MM/YYYY).
    """
    if not data_alvo:
        return []
    data_iso = str(data_alvo)[:10]
    data_br = ""
    try:
        dt = datetime.strptime(data_iso, "%Y-%m-%d")
        data_br = dt.strftime("%d/%m/%Y")
    except Exception:
        pass

    filtrados = []
    for item in lembretes:
        d_str = str(item.get("data_hora_lembrete", "")).strip()
        if not d_str:
            continue
        if data_iso in d_str or (data_br and data_br in d_str):
            filtrados.append(item)
    return filtrados


def listar_lembretes_pendentes(apenas_hoje: bool = True, data_referencia: Optional[str] = None) -> str:
    """
    List pending reminders. Defaults to strictly TODAY's reminders in Brasilia time.

    Args:
        apenas_hoje (bool, optional): If True (default), filter for today only. If False, list all.
        data_referencia (str, optional): Target date 'YYYY-MM-DD' filter.
    """
    todos = _obter_todos_itens()
    lembretes = [
        item for item in todos 
        if item.get("tipo") == "lembrete" and item.get("status") == "pendente"
    ]

    filtrar_data = apenas_hoje or bool(data_referencia)
    if filtrar_data:
        data_alvo_str = _obter_data_filtro_lembrete(data_referencia)
        lembretes = _filtrar_lembretes_por_data(lembretes, data_alvo_str)

    if not lembretes:
        msg_sufixo = " para hoje" if filtrar_data else " no momento"
        return f"🎉 Nenhum lembrete pendente{msg_sufixo}! Você está em dia."

    # Ordena por data_hora_lembrete
    lembretes_ordenados = sorted(lembretes, key=lambda x: str(x.get("data_hora_lembrete", "")))

    linhas = [f"⏰ **Lembretes Pendentes ({len(lembretes_ordenados)}):**"]
    for idx, lemb in enumerate(lembretes_ordenados, start=1):
        tags_fmt = _formatar_tags_exibicao(lemb.get("tags"))
        linhas.append(
            f"{idx}. **{lemb['titulo']}**{tags_fmt}\n"
            f"   📅 Horário: {lemb.get('data_hora_lembrete')} | 🆔 `{lemb['id'][:8]}`"
        )

    return "\n".join(linhas)


def concluir_lembrete(lembrete_id_ou_titulo: str) -> str:
    """
    Mark a reminder as completed by its ID or title.
    For recurring reminders, advances to the next period.

    Args:
        lembrete_id_ou_titulo (str): Reminder ID or title substring.
    """
    termo = lembrete_id_ou_titulo.strip().lower()
    todos = _obter_todos_itens(colecao="notes_reminders")

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
    recorrencia = candidato.get("recorrencia")

    if recorrencia:
        tz_br = timezone(timedelta(hours=-3))
        prox_data = calcular_proxima_ocorrencia(
            candidato.get("data_hora_lembrete", ""),
            recorrencia,
            datetime.now(tz_br) + timedelta(minutes=1)
        )
        _atualizar_item(item_id, {
            "data_hora_lembrete": prox_data,
            "ultima_conclusao": concluido_em,
            "updated_at": concluido_em
        }, colecao="notes_reminders")
        return f"✅ Lembrete recorrente **'{candidato['titulo']}'** concluído! Próxima ocorrência agendada para: **{prox_data}**."
    else:
        _atualizar_item(item_id, {"status": "concluido", "concluido_em": concluido_em}, colecao="notes_reminders")
        return f"✅ Lembrete **'{candidato['titulo']}'** marcado como concluído com sucesso!"
