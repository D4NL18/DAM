import logging
import re
import unicodedata
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from config import firebase
from services.user_context import UserContext

logger = logging.getLogger(__name__)

# Padrão regex reutilizado para higienização e extração de tags (evita literais duplicados - python:S1192)
TAG_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-]+")

# Armazenamento em memória para fallback/mock (quando Firebase não inicializado ou em testes)
_mock_storage: List[Dict[str, Any]] = []

# Sinônimos semânticos para buscas de hardware / peças de computador nas anotações
_PC_SYNONYM_TRIGGERS = {
    "pc", "computador", "peca", "pecas", "hardware", "componente", "componentes",
    "setup", "upgrade", "maquina", "desktop", "gamer", "miami", "micro center", "microcenter"
}
_PC_NOTE_KEYWORDS = {
    "pc", "computador", "peca", "pecas", "hardware", "processador", "cpu", "gpu",
    "placa de video", "placa-mae", "placa mae", "motherboard", "rtx", "gtx", "radeon",
    "geforce", "intel", "core i", "i5", "i7", "i9", "ryzen", "amd", "zotac", "asus",
    "msi", "gigabyte", "corsair", "ssd", "nvme", "ram", "ddr4", "ddr5", "fonte",
    "micro center", "microcenter", "combo"
}


def _reset_mock_storage() -> None:
    """Limpa o armazenamento em memória (útil para testes unitários)."""
    global _mock_storage
    _mock_storage.clear()


def _normalizar_texto(texto: str) -> str:
    """Remove acentos e normaliza para minúsculas."""
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    sem_acento = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return sem_acento.lower().strip()


def _obter_todos_itens(colecao: Optional[str] = None) -> List[Dict[str, Any]]:
    """Recupera todos os itens da coleção indicada ou de ambas se None, ou do mock, filtrados pelo usuário ativo."""
    user_id = UserContext.get_user_id()
    todos = []
    if firebase.db is not None:
        try:
            if colecao:
                docs = firebase.db.collection(colecao).stream()
                for doc in docs:
                    d = doc.to_dict()
                    if d:
                        d.setdefault("id", doc.id)
                        d.setdefault("_colecao", colecao)
                        todos.append(d)
            else:
                docs_rem = firebase.db.collection("notes_reminders").stream()
                for doc in docs_rem:
                    d = doc.to_dict()
                    if d:
                        d.setdefault("id", doc.id)
                        d.setdefault("_colecao", "notes_reminders")
                        todos.append(d)
                docs_notes = firebase.db.collection("information_notes").stream()
                for doc in docs_notes:
                    d = doc.to_dict()
                    if d:
                        d.setdefault("id", doc.id)
                        d.setdefault("_colecao", "information_notes")
                        todos.append(d)
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


def _obter_todas_anotacoes() -> List[Dict[str, Any]]:
    """
    Recupera e unifica todas as anotações do usuário ativo tanto da coleção dedicada
    'information_notes' quanto de registros legados ('tipo' == 'nota') em 'notes_reminders'.
    """
    notas_map: Dict[str, Dict[str, Any]] = {}
    for item in _obter_todos_itens(colecao="information_notes"):
        item_id = str(item.get("id") or uuid.uuid4())
        notas_map[item_id] = item

    for item in _obter_todos_itens(colecao="notes_reminders"):
        if item.get("tipo") == "nota":
            item_id = str(item.get("id") or uuid.uuid4())
            if item_id not in notas_map:
                notas_map[item_id] = item

    notas = list(notas_map.values())
    notas.sort(key=lambda x: str(x.get("updated_at") or x.get("created_at") or ""), reverse=True)
    return notas


def _salvar_item(item: Dict[str, Any], colecao: str = "notes_reminders") -> None:
    """Salva um item no Firestore na coleção indicada ou no armazenamento em memória vinculado ao usuário ativo."""
    user_id = UserContext.get_user_id()
    item["userId"] = user_id
    item["user_id"] = user_id
    item["_colecao"] = colecao

    existing_idx = next((idx for idx, x in enumerate(_mock_storage) if x.get("id") == item.get("id")), None)
    if existing_idx is not None:
        _mock_storage[existing_idx] = dict(item)
    else:
        _mock_storage.append(item)

    if firebase.db is not None:
        try:
            firebase.db.collection(colecao).document(item["id"]).set(item)
            logger.info(f"[NOTES] Item '{item.get('titulo')}' ({item['id']}) salvo em '{colecao}' para {user_id}.")
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
                doc_data = doc.to_dict() or {}
                if (doc_data.get("userId") or doc_data.get("user_id") or "daniel") == user_id:
                    doc_ref.update(updates)
                    atualizado = True
                else:
                    logger.warning(f"Tentativa de atualização de item de outro usuário: {item_id}")
        except Exception as e:
            logger.error(f"Erro ao atualizar Firestore doc {item_id} em {colecao}: {e}")

    return atualizado


def _remover_item(item_id: str, colecao: str = "information_notes") -> bool:
    """Remove um item do Firestore e do mock garantindo isolamento por usuário."""
    global _mock_storage
    user_id = UserContext.get_user_id()
    removido = False

    tam_antes = len(_mock_storage)
    _mock_storage = [
        i for i in _mock_storage
        if not (i.get("id") == item_id and (i.get("userId") or i.get("user_id") or "daniel") == user_id)
    ]
    if len(_mock_storage) < tam_antes:
        removido = True

    if firebase.db is not None:
        for col in {colecao, "information_notes", "notes_reminders"}:
            try:
                doc_ref = firebase.db.collection(col).document(item_id)
                doc = doc_ref.get()
                if doc.exists:
                    doc_data = doc.to_dict() or {}
                    if (doc_data.get("userId") or doc_data.get("user_id") or "daniel") == user_id:
                        doc_ref.delete()
                        removido = True
            except Exception as e:
                logger.error(f"Erro ao excluir Firestore doc {item_id} em {col}: {e}")

    return removido


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
    Save personal note, quote, list, or information in the dedicated Firestore 'information_notes' database.
    Does NOT create a reminder.

    Args:
        titulo (str): Note or topic title (e.g. 'Orçamento PC EUA', 'Peças de Computador', 'Anotação de reunião').
        conteudo (str): Detailed text, numbers, components, or information to remember.
        tags (list[str] or str, optional): Tags for categorization.
    """
    tags_limpas = list(dict.fromkeys(_extrair_tokens_tags(tags))) if tags else []
    agora_iso = datetime.now(timezone.utc).isoformat()

    item = {
        "id": str(uuid.uuid4()),
        "tipo": "nota",
        "titulo": (titulo or "Anotação").strip(),
        "conteudo": (conteudo or "").strip(),
        "tags": tags_limpas,
        "created_at": agora_iso,
        "updated_at": agora_iso,
    }

    _salvar_item(item, colecao="information_notes")
    tags_str = _formatar_tags_exibicao(tags_limpas)
    return f"📝 Anotação '{item['titulo']}' salva com sucesso no banco de informações!{tags_str} (ID: {item['id'][:8]})"


def _corresponde_termo_nota(nota: Dict[str, Any], termo_busca: str) -> bool:
    """Verifica correspondência semântica e sem acentos de uma anotação com o termo buscado."""
    termo_norm = _normalizar_texto(termo_busca)
    if not termo_norm:
        return True

    texto_nota = _normalizar_texto(
        f"{nota.get('titulo', '')} {nota.get('conteudo', '')} {' '.join(nota.get('tags', []))}"
    )

    if termo_norm in texto_nota:
        return True

    tokens = [
        t for t in re.findall(r"[a-z0-9]+", termo_norm)
        if len(t) >= 2 and t not in {"de", "do", "da", "dos", "das", "no", "na", "em", "para", "pro", "pra", "meu", "minha"}
    ]
    if any(t in _PC_SYNONYM_TRIGGERS for t in tokens) or termo_norm in _PC_SYNONYM_TRIGGERS:
        if any(kw in texto_nota for kw in _PC_NOTE_KEYWORDS):
            return True

    if tokens and all(t in texto_nota for t in tokens):
        return True

    return False


def _formatar_lista_anotacoes(notas: List[Dict[str, Any]], cabecalho: str) -> str:
    linhas = [cabecalho]
    for idx, item in enumerate(notas, start=1):
        tags_fmt = f" `#{' #'.join(item.get('tags', []))}`" if item.get("tags") else ""
        linhas.append(
            f"{idx}. **{item.get('titulo', 'Sem título')}**{tags_fmt} *(ID: {str(item.get('id', ''))[:8]})*\n"
            f"   {item.get('conteudo', '')}"
        )
    return "\n\n".join(linhas)


def buscar_anotacoes(termo: Optional[str] = None, tag: Optional[str] = None) -> str:
    """
    Search saved notes by keyword or category tag in the Firestore information notes database.
    Leave termo and tag empty (None) to list ALL saved notes.

    Args:
        termo (str, optional): Search keyword in title or content.
        tag (str, optional): Tag name to filter.
    """
    notas = _obter_todas_anotacoes()

    if not notas:
        return "Nenhuma anotação encontrada no seu histórico."

    filtradas = []
    termo_busca = termo.strip() if termo else None
    tag_busca = _normalizar_texto(tag) if tag else None

    for n in notas:
        corresponde_termo = _corresponde_termo_nota(n, termo_busca) if termo_busca else True
        corresponde_tag = True

        if tag_busca:
            tags_item = [_normalizar_texto(t) for t in n.get("tags", [])]
            corresponde_tag = any(tag_busca in t for t in tags_item) or (tag_busca in _normalizar_texto(n.get("titulo", "")))

        if corresponde_termo and corresponde_tag:
            filtradas.append(n)

    if not filtradas:
        criterios = []
        if termo:
            criterios.append(f"termo '{termo}'")
        if tag:
            criterios.append(f"tag '{tag}'")
        msg_nao_encontrada = f"Nenhuma anotação encontrada para os critérios informados ({', '.join(criterios)})."
        # Retorna também todas as anotações existentes como contexto de fallback para evitar falso negativo na IA
        fallback_lista = _formatar_lista_anotacoes(
            notas,
            f"📋 **Suas Anotações Salvas no Banco ({len(notas)}):**"
        )
        return f"{msg_nao_encontrada}\n\n{fallback_lista}"

    return _formatar_lista_anotacoes(filtradas, f"📋 **Anotações Encontradas ({len(filtradas)}):**")


def atualizar_anotacao(
    id_ou_titulo: str,
    novo_titulo: Optional[str] = None,
    novo_conteudo: Optional[str] = None,
    tags: Optional[Any] = None
) -> str:
    """
    Update an existing note in the Firestore database by its ID prefix or title.

    Args:
        id_ou_titulo (str): Note ID (or prefix) or title substring to locate.
        novo_titulo (str, optional): New title if changing.
        novo_conteudo (str, optional): Updated content text.
        tags (list[str] or str, optional): Updated tags list.
    """
    termo = _normalizar_texto(id_ou_titulo)
    if not termo:
        return "Por favor, informe o ID ou título da anotação que deseja atualizar."

    notas = _obter_todas_anotacoes()
    candidato = None
    for n in notas:
        nid = str(n.get("id", "")).lower()
        ntit = _normalizar_texto(n.get("titulo", ""))
        if nid == termo or nid.startswith(termo) or termo in ntit:
            candidato = n
            break

    if not candidato:
        return f"Não encontrei nenhuma anotação com o termo ou ID '{id_ou_titulo}'."

    updates: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if novo_titulo and novo_titulo.strip():
        updates["titulo"] = novo_titulo.strip()
    if novo_conteudo and novo_conteudo.strip():
        updates["conteudo"] = novo_conteudo.strip()
    if tags is not None:
        updates["tags"] = list(dict.fromkeys(_extrair_tokens_tags(tags)))

    colecao_alvo = candidato.get("_colecao") or "information_notes"
    _atualizar_item(candidato["id"], updates, colecao=colecao_alvo)
    tit_final = updates.get("titulo") or candidato.get("titulo")
    return f"✅ Anotação **'{tit_final}'** (ID: `{candidato['id'][:8]}`) atualizada com sucesso no banco de dados!"


def excluir_anotacao(id_ou_titulo: str) -> str:
    """
    Delete a saved note from the Firestore database by its ID prefix or title.

    Args:
        id_ou_titulo (str): Note ID (or prefix) or title substring to delete.
    """
    termo = _normalizar_texto(id_ou_titulo)
    if not termo:
        return "Por favor, informe o ID ou título da anotação que deseja excluir."

    notas = _obter_todas_anotacoes()
    candidato = None
    for n in notas:
        nid = str(n.get("id", "")).lower()
        ntit = _normalizar_texto(n.get("titulo", ""))
        if nid == termo or nid.startswith(termo) or termo in ntit:
            candidato = n
            break

    if not candidato:
        return f"Não encontrei nenhuma anotação com o termo ou ID '{id_ou_titulo}'."

    colecao_alvo = candidato.get("_colecao") or "information_notes"
    _remover_item(candidato["id"], colecao=colecao_alvo)
    return f"🗑️ Anotação **'{candidato.get('titulo')}'** removida com sucesso do banco de dados!"


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
    todos = _obter_todos_itens(colecao="notes_reminders")
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
