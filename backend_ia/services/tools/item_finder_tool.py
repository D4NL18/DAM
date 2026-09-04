import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from config import firebase
from services.user_context import UserContext

logger = logging.getLogger(__name__)

# Fallback em memória para quando Firestore não estiver conectado
_in_memory_items: Dict[str, Dict[str, Any]] = {}

def _reset_memory():
    """Limpa o armazenamento em memória (útil para testes unitários)."""
    _in_memory_items.clear()

def _format_datetime(iso_str: Optional[str]) -> str:
    """Formata data ISO para formato amigável em pt-BR."""
    if not iso_str:
        return "data não informada"
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%d/%m/%Y às %H:%M")
    except Exception:
        return iso_str

def registrar_localizacao_objeto(
    objeto: str, 
    local: str, 
    categoria: str = "Geral", 
    detalhes: Optional[str] = None
) -> str:
    """
    Registra ou atualiza o local de um objeto na memória espacial do usuário.
    Se o objeto já existia, preserva o histórico de locais anteriores por onde ele passou.

    Args:
        objeto: Nome do objeto (ex: 'Passaporte', 'Chave reserva do carro', 'Óculos de sol').
        local: Onde o objeto foi guardado (ex: 'Segunda gaveta da cômoda do quarto', 'No chaveiro da entrada').
        categoria: Categoria do objeto (ex: 'Documentos', 'Veículos', 'Acessórios', 'Geral').
        detalhes: Informações adicionais contextuais (ex: 'Dentro de uma pasta azul').
    """
    if not objeto or not objeto.strip():
        return "Por favor, informe o nome do objeto que deseja registrar."
    if not local or not local.strip():
        return "Por favor, informe onde o objeto foi guardado."

    objeto_limpo = objeto.strip()

    local_limpo = local.strip()
    categoria_limpa = categoria.strip() if categoria else "Geral"
    detalhes_limpos = detalhes.strip() if detalhes else None
    objeto_key = objeto_limpo.lower()
    user_id = UserContext.get_user_id()
    doc_key = objeto_key if user_id == "daniel" else f"{user_id}__{objeto_key}"
    agora_iso = datetime.now(timezone.utc).isoformat()

    # Tentativa de uso do Firestore
    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("item_locations").document(doc_key)
            doc_snap = doc_ref.get()

            historico: List[Dict[str, Any]] = []
            if doc_snap.exists:
                dados_antigos = doc_snap.to_dict() or {}
                historico = dados_antigos.get("historico", [])
                # Se o local anterior for diferente ou foi atualizado, adiciona ao histórico
                if dados_antigos.get("local_atual"):
                    historico.append({
                        "local": dados_antigos.get("local_atual"),
                        "data": dados_antigos.get("atualizado_em"),
                        "detalhes": dados_antigos.get("detalhes")
                    })

            novo_registro = {
                "userId": user_id,
                "user_id": user_id,
                "objeto": objeto_limpo,
                "objeto_lower": objeto_key,
                "local_atual": local_limpo,
                "categoria": categoria_limpa,
                "detalhes": detalhes_limpos,
                "atualizado_em": agora_iso,
                "historico": historico
            }
            doc_ref.set(novo_registro)
            logger.info(f"Item '{objeto_limpo}' de [{user_id}] registrado no Firestore em '{local_limpo}'.")
            
            resp = f"📍 Localização de **{objeto_limpo}** registrada com sucesso!\n• Local: {local_limpo}\n• Categoria: {categoria_limpa}"
            if detalhes_limpos:
                resp += f"\n• Detalhes: {detalhes_limpos}"
            return resp

        except Exception as e:
            logger.warning(f"Erro ao salvar no Firestore, utilizando fallback em memória: {e}")

    # Fallback Gracioso em Memória
    historico_mem: List[Dict[str, Any]] = []
    if doc_key in _in_memory_items:
        dados_antigos = _in_memory_items[doc_key]
        historico_mem = list(dados_antigos.get("historico", []))
        if dados_antigos.get("local_atual"):
            historico_mem.append({
                "local": dados_antigos.get("local_atual"),
                "data": dados_antigos.get("atualizado_em"),
                "detalhes": dados_antigos.get("detalhes")
            })

    registro_mem = {
        "userId": user_id,
        "user_id": user_id,
        "objeto": objeto_limpo,
        "objeto_lower": objeto_key,
        "local_atual": local_limpo,
        "categoria": categoria_limpa,
        "detalhes": detalhes_limpos,
        "atualizado_em": agora_iso,
        "historico": historico_mem
    }
    _in_memory_items[doc_key] = registro_mem
    if user_id == "daniel":
        _in_memory_items[f"daniel__{objeto_key}"] = registro_mem
        _in_memory_items[objeto_key] = registro_mem

    logger.info(f"Item '{objeto_limpo}' de [{user_id}] salvo em memória em '{local_limpo}'.")

    resp = f"📍 Localização de **{objeto_limpo}** registrada com sucesso (memória)!\n• Local: {local_limpo}\n• Categoria: {categoria_limpa}"
    if detalhes_limpos:
        resp += f"\n• Detalhes: {detalhes_limpos}"
    return resp


def onde_guardei_objeto(objeto: str) -> str:
    """
    Pesquisa na memória espacial onde um determinado objeto foi guardado pelo usuário ativo.
    """
    if not objeto or not objeto.strip():
        return "Por favor, especifique o objeto que está procurando."

    user_id = UserContext.get_user_id()
    termo = objeto.strip().lower()
    doc_key = f"{user_id}__{termo}"

    # 1. Tenta Firestore
    if firebase.db is not None:
        try:
            # Busca exata particionada primeiro
            doc_ref = firebase.db.collection("item_locations").document(doc_key)
            doc_snap = doc_ref.get()
            if doc_snap.exists:
                dados = doc_snap.to_dict() or {}
                return _formatar_resposta_localizacao(dados)
            elif user_id == "daniel":
                # Fallback legado para Daniel
                doc_legacy = firebase.db.collection("item_locations").document(termo).get()
                if doc_legacy.exists:
                    return _formatar_resposta_localizacao(doc_legacy.to_dict() or {})

            # Busca por varredura filtrando estritamente pelo usuário ativo
            docs = firebase.db.collection("item_locations").stream()
            encontrados = []
            for d in docs:
                data = d.to_dict() or {}
                d_user = data.get("userId") or data.get("user_id") or "daniel"
                if d_user != user_id:
                    continue
                obj_name = data.get("objeto_lower", "")
                detalhes = (data.get("detalhes") or "").lower()
                categoria = (data.get("categoria") or "").lower()
                if termo in obj_name or obj_name in termo or termo in detalhes or termo in categoria:
                    encontrados.append(data)


            if encontrados:
                # Retorna o primeiro mais relevante ou lista todos se múltiplos
                if len(encontrados) == 1:
                    return _formatar_resposta_localizacao(encontrados[0])
                else:
                    linhas = ["Encontrei mais de um item correspondente:"]
                    for item in encontrados:
                        linhas.append(f"• **{item.get('objeto')}**: {item.get('local_atual')} (guardado em {_format_datetime(item.get('atualizado_em'))})")
                    return "\n".join(linhas)

            return f"Não encontrei nenhum registro sobre onde está guardado '{objeto}'. Deseja registrar a localização dele agora?"

        except Exception as e:
            logger.warning(f"Erro ao buscar no Firestore, tentando fallback em memória: {e}")

    # 2. Fallback em Memória
    if doc_key in _in_memory_items:
        return _formatar_resposta_localizacao(_in_memory_items[doc_key])
    elif user_id == "daniel" and termo in _in_memory_items:
        return _formatar_resposta_localizacao(_in_memory_items[termo])

    encontrados_mem = []
    for k, item in _in_memory_items.items():
        d_user = item.get("userId") or item.get("user_id") or "daniel"
        if d_user != user_id:
            continue
        obj_name = item.get("objeto_lower", "")
        detalhes = (item.get("detalhes") or "").lower()
        categoria = (item.get("categoria") or "").lower()
        if termo in obj_name or obj_name in termo or termo in detalhes or termo in categoria:
            encontrados_mem.append(item)


    if encontrados_mem:
        if len(encontrados_mem) == 1:
            return _formatar_resposta_localizacao(encontrados_mem[0])
        else:
            linhas = ["Encontrei mais de um item correspondente em memória:"]
            for item in encontrados_mem:
                linhas.append(f"• **{item.get('objeto')}**: {item.get('local_atual')} (guardado em {_format_datetime(item.get('atualizado_em'))})")
            return "\n".join(linhas)

    return f"Não encontrei nenhum registro sobre onde está guardado '{objeto}'. Deseja registrar a localização dele agora?"

def listar_historico_movimentacoes(objeto: str) -> str:
    """
    Exibe o histórico cronológico de todos os locais por onde o objeto já passou.

    Args:
        objeto: Nome do objeto cuja trajetória você deseja consultar.
    """
    if not objeto or not objeto.strip():
        return "Por favor, especifique o objeto para consultar o histórico."

    user_id = UserContext.get_user_id()
    termo = objeto.strip().lower()
    doc_key = f"{user_id}__{termo}"
    item_dados = None

    # 1. Firestore
    if firebase.db is not None:
        try:
            doc_ref = firebase.db.collection("item_locations").document(doc_key)
            doc_snap = doc_ref.get()
            if doc_snap.exists:
                item_dados = doc_snap.to_dict()
            elif user_id == "daniel":
                doc_legacy = firebase.db.collection("item_locations").document(termo).get()
                if doc_legacy.exists:
                    item_dados = doc_legacy.to_dict()

            if not item_dados:
                docs = firebase.db.collection("item_locations").stream()
                for d in docs:
                    data = d.to_dict() or {}
                    d_user = data.get("userId") or data.get("user_id") or "daniel"
                    if d_user == user_id and termo in data.get("objeto_lower", ""):
                        item_dados = data
                        break
        except Exception as e:
            logger.warning(f"Erro ao consultar histórico no Firestore: {e}")

    # 2. Fallback em Memória
    if not item_dados:
        if doc_key in _in_memory_items:
            item_dados = _in_memory_items[doc_key]
        elif user_id == "daniel" and termo in _in_memory_items:
            item_dados = _in_memory_items[termo]
        else:
            for k, it in _in_memory_items.items():
                d_user = it.get("userId") or it.get("user_id") or "daniel"
                if d_user == user_id and termo in it.get("objeto_lower", ""):
                    item_dados = it
                    break


    if not item_dados:
        return f"Não encontrei nenhum registro do objeto '{objeto}' para exibir histórico."

    historico = item_dados.get("historico", [])
    nome_obj = item_dados.get("objeto", objeto)
    local_atual = item_dados.get("local_atual")
    data_atual = _format_datetime(item_dados.get("atualizado_em"))

    if not historico:
        return (
            f"📍 **{nome_obj}**:\n"
            f"• Local Atual: {local_atual} (registrado em {data_atual})\n"
            f"• Não possui movimentações anteriores registradas."
        )

    linhas = [
        f"📍 **Histórico de Localizações - {nome_obj}**:",
        f"• **Local Atual**: {local_atual} (desde {data_atual})",
        "• **Movimentações Anteriores**:"
    ]
    for idx, h in enumerate(reversed(historico), 1):
        dt_hist = _format_datetime(h.get("data"))
        det = f" ({h.get('detalhes')})" if h.get("detalhes") else ""
        linhas.append(f"  {idx}. {h.get('local')} - guardado em {dt_hist}{det}")

    return "\n".join(linhas)

def _formatar_resposta_localizacao(dados: Dict[str, Any]) -> str:
    """Formata os dados do objeto em string amigável de resposta."""
    objeto = dados.get("objeto")
    local = dados.get("local_atual")
    categoria = dados.get("categoria", "Geral")
    detalhes = dados.get("detalhes")
    atualizado_em = _format_datetime(dados.get("atualizado_em"))

    resposta = (
        f"📍 **Onde Guardei Isso?**\n"
        f"• **Objeto**: {objeto}\n"
        f"• **Local Atual**: {local}\n"
        f"• **Categoria**: {categoria}\n"
        f"• **Guardado em**: {atualizado_em}"
    )
    if detalhes:
        resposta += f"\n• **Detalhes**: {detalhes}"
    return resposta
