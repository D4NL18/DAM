from typing import Optional, List, Dict, Any
import uuid
import logging
import re
import time
import unicodedata
from datetime import datetime, timezone, timedelta
from config import firebase
from services.user_context import UserContext
from routers.finance import DEFAULT_CATEGORIES

logger = logging.getLogger(__name__)

# Cache L1 em memória para categorias do usuário: (user_id, db_instance_id) -> (timestamp, list_categories)
_USER_CATEGORIES_CACHE: Dict[tuple, tuple[float, List[Dict[str, Any]]]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutos


def normalizar_metodo_pagamento(metodo: Optional[str]) -> Optional[str]:
    """
    Normaliza o método de pagamento para uma das 3 modalidades estritas:
    1. 'Cartão de Crédito Secundário'
    2. 'Cartão de Crédito Pessoal'
    3. 'Cartão de Débito' (inclui Pix)
    """
    if not metodo:
        return None

    m = metodo.strip().lower()

    # 1. Cartão Secundário / Compartilhado / Familiar
    if any(k in m for k in ["one", "pai", "secundar", "secundár", "compartilh", "familiar"]):
        return "Cartão de Crédito Secundário"

    # 3. Débito e Pix (se for pix, sempre cai no de débito)
    if "pix" in m or "debito" in m or "débito" in m:
        return "Cartão de Débito"

    # 2. Cartão de crédito pessoal
    if "credito" in m or "crédito" in m or "pessoal" in m:
        return "Cartão de Crédito Pessoal"

    return None


def _normalize_str(s: str) -> str:
    """Normaliza string para comparação sem acentos e em minúsculas."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()


def obter_categorias_usuario(user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retorna as categorias ativas do usuário com cache L1 em memória (5 min).
    Se o banco estiver vazio ou indisponível, retorna DEFAULT_CATEGORIES.
    """
    effective_user = user_id or UserContext.get_user_id() or "daniel"
    now_ts = time.time()
    cache_key = (effective_user, id(firebase.db))

    if cache_key in _USER_CATEGORIES_CACHE:
        cached_time, cached_data = _USER_CATEGORIES_CACHE[cache_key]
        if now_ts - cached_time < CACHE_TTL_SECONDS:
            return cached_data

    defaults = [c for c in DEFAULT_CATEGORIES if c.get("name", "").lower() not in ["christian", "reembolso"]]

    if firebase.db is None:
        return defaults

    categories = []
    try:
        col = firebase.db.collection("finance_categories")
        docs = []
        if hasattr(col, "where"):
            stream_obj = col.where("userId", "==", effective_user).stream()
            docs = list(stream_obj)
        if not docs and hasattr(col, "stream"):
            all_docs = list(col.stream())
            docs = [d for d in all_docs if hasattr(d, "to_dict") and (d.to_dict() or {}).get("userId") == effective_user]

        for d in docs:
            if not hasattr(d, "to_dict"):
                continue
            data = d.to_dict() or {}
            name = data.get("name")
            if name and str(name).strip().lower() not in ["christian", "reembolso"]:
                categories.append({
                    "id": getattr(d, "id", str(uuid.uuid4())),
                    "name": str(name).strip(),
                    "color": data.get("color", "#64748b")
                })
    except Exception as e:
        logger.warning(f"Erro ao buscar categorias customizadas para [{effective_user}]: {e}")

    if categories:
        _USER_CATEGORIES_CACHE[cache_key] = (now_ts, categories)
        return categories

    _USER_CATEGORIES_CACHE[cache_key] = (now_ts, defaults)
    return defaults


def normalizar_categoria(cat: Optional[str], user_id: Optional[str] = None) -> str:
    """
    Normaliza a categoria para um nome oficial autorizado (P-0901).
    - Suporta aliases e sinônimos conhecidos.
    - Proíbe categoricamente a atribuição de 'Reembolso' (converte para 'Receitas' ou 'Outros').
    - Verifica as categorias ativas do usuário.
    - Fallback determinístico para 'Outros'.
    """
    if not cat:
        return "Outros"

    c_norm = _normalize_str(cat)
    if not c_norm:
        return "Outros"

    # Proibição estrita de "Reembolso" (P-0901 / P-0902)
    if "reembolso" in c_norm:
        return "Receitas"

    # Mapeamento de sinônimos conhecidos
    synonym_rules = [
        ("iFood", [r"\bifood\b", r"\bdelivery\b"]),
        ("Mercado", [r"\bsupermercado\b", r"\balmoco\b", r"\bcomida\b", r"\bacougue\b", r"\bpadaria\b", r"\balimentacao\b"]),
        ("Carro", [r"\bgasolina\b", r"\bcombustivel\b", r"\buber\b", r"\bestacionamento\b", r"\bmecanico\b", r"\bveiculo\b"]),
        ("Farmácia", [r"\bfarmacia\b", r"\bremedio\b", r"\bdrogaria\b", r"\bmedico\b", r"\bmedica\b", r"\bconsulta\b", r"\bexame\b"]),
        ("Casa", [r"\baluguel\b", r"\bcondominio\b", r"\bluz\b", r"\benergia\b", r"\bagua\b", r"\binternet\b", r"\bmoradia\b"]),
        ("Lazer", [r"\bcinema\b", r"\bjogos?\b", r"\bgames?\b", r"\bchurrasco\b", r"\bbar\b", r"\bpasseio\b", r"\bviagem\b"]),
    ]

    for target_cat, patterns in synonym_rules:
        for pat in patterns:
            if re.search(pat, c_norm):
                return target_cat

    # Comparação com categorias ativas do usuário
    user_cats = obter_categorias_usuario(user_id)
    for c in user_cats:
        c_name = c.get("name", "")
        if _normalize_str(c_name) == c_norm:
            return c_name

    return "Outros"


def registrar_gasto(descricao: str, valor: float, categoria: str, metodo_pagamento: str) -> str:
    """
    Record a new expense for the user.

    Args:
        descricao (str): Expense description.
        valor (float): Amount spent.
        categoria (str): Expense category (e.g. Food, Transport, Leisure).
        metodo_pagamento (str): 'Cartão de Crédito Secundário', 'Cartão de Crédito Pessoal' or 'Cartão de Débito'.
    """
    metodo_normalizado = normalizar_metodo_pagamento(metodo_pagamento)
    if not metodo_normalizado:
        return (
            "Método de pagamento não identificado. Em qual das suas contas/cartões foi a cobrança?\n"
            "• Cartão de crédito secundário\n"
            "• Cartão de crédito pessoal\n"
            "• Cartão de débito (ou Pix)"
        )

    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."

    try:
        user_id = UserContext.get_user_id() or "daniel"
        cat_normalizada = normalizar_categoria(categoria, user_id)
        amount = abs(float(valor))

        data_to_save = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "user_id": user_id,
            "description": descricao,
            "amount": amount,
            "category": cat_normalizada,
            "type": "expense_variable",
            "payment_method": metodo_normalizado,
            "date": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        firebase.db.collection("finances").add(data_to_save)
        desc_log = (descricao[:30] + "...") if len(descricao) > 30 else descricao
        logger.info(f"Gasto registrado para [{user_id}]: {desc_log} - R$ {amount:.2f} [{metodo_normalizado}]")
        return (
            f"Sucesso! Registrei o gasto de R$ {amount:.2f} com '{descricao}' "
            f"na categoria {cat_normalizada} no cartão **{metodo_normalizado}**."
        )

    except Exception as e:
        logger.error(f"Erro ao registrar finanças: {e}")
        return "Desculpe, ocorreu um erro ao salvar seu gasto. Tente novamente mais tarde."


def registrar_receita(descricao: str, valor: float, metodo_recebimento: Optional[str] = None) -> str:
    """
    Record a new income/reimbursement for the user (P-0902).

    Args:
        descricao (str): Income/reimbursement description.
        valor (float): Amount received.
        metodo_recebimento (str, optional): Payment method received into (Pix, Cartão de Débito, etc.).
    """
    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."

    try:
        user_id = UserContext.get_user_id() or "daniel"
        amount = abs(float(valor))
        metodo_norm = normalizar_metodo_pagamento(metodo_recebimento) or "Cartão de Débito"

        data_to_save = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "user_id": user_id,
            "description": descricao,
            "amount": amount,
            "category": "Receitas",
            "type": "income",
            "payment_method": metodo_norm,
            "date": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc),
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        firebase.db.collection("finances").add(data_to_save)
        desc_log = (descricao[:30] + "...") if len(descricao) > 30 else descricao
        logger.info(f"Receita registrada para [{user_id}]: {desc_log} - R$ {amount:.2f} [{metodo_norm}]")

        valor_fmt = f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return (
            f"Sucesso! Registrei a receita de {valor_fmt} referente a '{descricao}' "
            f"na categoria Receitas ({metodo_norm})."
        )
    except Exception as e:
        logger.error(f"Erro ao registrar receita: {e}")
        return "Desculpe, ocorreu um erro ao salvar a receita. Tente novamente mais tarde."


def _match_category(item_cat: str, target_cat: str) -> bool:
    """Compara categorias tratando variações de escrita e sinônimos comuns."""
    i_norm = _normalize_str(item_cat)
    t_norm = _normalize_str(target_cat)
    if not i_norm or not t_norm:
        return False
    if t_norm in i_norm or i_norm in t_norm:
        return True

    aliases = {
        "moradia": ["casa", "habitacao", "aluguel", "condominio", "contas fixas"],
        "casa": ["moradia", "habitacao", "contas fixas"],
        "alimentacao": ["mercado", "supermercado", "mercadinho", "restaurante", "ifood", "comida", "padaria"],
        "mercado": ["alimentacao", "supermercado", "mercadinho", "comida"],
        "transporte": ["carro", "combustivel", "uber", "veiculo", "gasolina"],
        "saude": ["farmacia", "medico", "consulta", "exame", "hospital"]
    }
    for alias in aliases.get(t_norm, []):
        if alias in i_norm:
            return True
    return False


def _calcular_intervalo_busca(
    agora: datetime,
    mes: Optional[int],
    ano: Optional[int],
    dias_retroativos: Optional[int]
) -> tuple[datetime, datetime, str, int, int]:
    """Calcula as datas de início e fim e o título do período."""
    if dias_retroativos and dias_retroativos > 0:
        inicio = agora - timedelta(days=dias_retroativos)
        return inicio, agora, f"últimos {dias_retroativos} dias", agora.year, agora.month

    ano_alvo = ano if ano else agora.year
    mes_alvo = mes if mes else agora.month
    inicio = datetime(ano_alvo, mes_alvo, 1, 0, 0, 0, tzinfo=timezone.utc)
    if mes_alvo == 12:
        fim = datetime(ano_alvo + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    else:
        fim = datetime(ano_alvo, mes_alvo + 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    meses_nomes = [
        "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    nome_mes = meses_nomes[mes_alvo] if 1 <= mes_alvo <= 12 else f"Mês {mes_alvo}"
    return inicio, fim, f"{nome_mes}/{ano_alvo}", ano_alvo, mes_alvo


def _obter_documentos_financas(col, inicio: datetime, fim: datetime, dias_retroativos: Optional[int]) -> list:
    """Busca documentos da coleção com fallback para stream direto."""
    docs = []
    if hasattr(col, "where"):
        try:
            if dias_retroativos and dias_retroativos > 0:
                stream_obj = col.where("timestamp", ">=", inicio).stream()
            else:
                stream_obj = col.where("timestamp", ">=", inicio).where("timestamp", "<", fim).stream()
            candidate_where = list(stream_obj)
            if candidate_where and any(hasattr(d, "to_dict") and isinstance(d.to_dict(), dict) and "amount" in d.to_dict() for d in candidate_where):
                docs = candidate_where
        except Exception:
            pass

    if not docs and hasattr(col, "stream"):
        try:
            candidate_stream = list(col.stream())
            if candidate_stream and any(hasattr(d, "to_dict") and isinstance(d.to_dict(), dict) and "amount" in d.to_dict() for d in candidate_stream):
                docs = candidate_stream
        except Exception:
            pass

    return docs


def _parse_data_transacao(data: dict) -> Optional[datetime]:
    """Extrai e normaliza o datetime do registro financeiro."""
    dt_raw = data.get("date") or data.get("created_at") or data.get("timestamp")
    if isinstance(dt_raw, datetime):
        return dt_raw if dt_raw.tzinfo else dt_raw.replace(tzinfo=timezone.utc)
    if isinstance(dt_raw, str) and dt_raw:
        try:
            dt = datetime.fromisoformat(dt_raw.replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except Exception:
            return None
    return None


def _transacao_no_periodo(dt: Optional[datetime], inicio: datetime, ano_alvo: int, mes_alvo: int, dias_retroativos: Optional[int]) -> bool:
    """Valida se o datetime da transação está contido no período filtrado."""
    if not dt:
        return True
    if dias_retroativos and dias_retroativos > 0:
        return dt >= inicio
    return dt.year == ano_alvo and dt.month == mes_alvo


def _processar_lancamentos(
    docs: list,
    user_id: str,
    inicio: datetime,
    ano_alvo: int,
    mes_alvo: int,
    dias_retroativos: Optional[int]
) -> tuple[list, dict, dict, float]:
    """Filtra e consolida lançamentos financeiros do usuário."""
    total_geral = 0.0
    por_cartao = {}
    por_categoria = {}
    todos_gastos = []

    for doc in docs:
        if not hasattr(doc, "to_dict"):
            continue
        data = doc.to_dict() or {}

        doc_user = data.get("userId") or data.get("user_id") or "daniel"
        if doc_user != user_id:
            continue

        if data.get("type") == "income":
            continue

        dt = _parse_data_transacao(data)
        if not _transacao_no_periodo(dt, inicio, ano_alvo, mes_alvo, dias_retroativos):
            continue

        try:
            valor = float(data.get("amount", 0.0))
        except (ValueError, TypeError):
            continue

        if valor <= 0:
            continue

        total_geral += valor
        metodo = data.get("payment_method") or data.get("paymentMethod") or "Outros"
        metodo_norm = normalizar_metodo_pagamento(metodo) or metodo
        por_cartao[metodo_norm] = por_cartao.get(metodo_norm, 0.0) + valor

        cat_formatada = (data.get("category") or "Geral").strip().title()
        por_categoria[cat_formatada] = por_categoria.get(cat_formatada, 0.0) + valor

        todos_gastos.append({
            "description": data.get("description", "Sem descrição"),
            "amount": valor,
            "category": cat_formatada,
            "payment_method": metodo_norm,
            "date": dt.strftime("%d/%m/%Y") if dt else ""
        })

    return todos_gastos, por_cartao, por_categoria, total_geral


def _fmt_moeda(v: float) -> str:
    """Formata valor em Real (BRL)."""
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _formatar_detalhe_categoria(gastos: list, target_cat: str, periodo: str) -> str:
    """Gera resposta formatada para uma categoria específica."""
    gastos_cat = [g for g in gastos if _match_category(g["category"], target_cat)]
    if not gastos_cat:
        return f"ℹ️ Não encontrei registros de gastos na categoria '{target_cat}' para {periodo} no seu banco de dados."

    total_cat = sum(g["amount"] for g in gastos_cat)
    linhas = [
        f"🏷️ **Gastos em {target_cat.title()} - {periodo}**",
        f"💰 **Total:** {_fmt_moeda(total_cat)} ({len(gastos_cat)} lançamento{'s' if len(gastos_cat) > 1 else ''})\n",
        "📋 **Detalhamento:**"
    ]
    for g in sorted(gastos_cat, key=lambda x: x["amount"], reverse=True):
        data_info = f" ({g['date']})" if g.get("date") else ""
        linhas.append(f"• **{g['description']}:** {_fmt_moeda(g['amount'])}{data_info} [{g['payment_method']}]")

    return "\n".join(linhas)


def _formatar_resumo_macro(gastos: list, por_cartao: dict, por_categoria: dict, total: float, periodo: str) -> str:
    """Gera resposta com visão consolidada por categorias e métodos de pagamento."""
    categorias_ordenadas = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)
    cartoes_ordenados = sorted(por_cartao.items(), key=lambda x: x[1], reverse=True)
    maiores_gastos = sorted(gastos, key=lambda x: x["amount"], reverse=True)[:3]

    linhas = [
        f"📊 **Resumo Financeiro - {periodo}**\n",
        f"💰 **Total Geral:** {_fmt_moeda(total)} ({len(gastos)} lançamentos)\n",
        "💳 **Por Cartão / Forma de Pagamento:**"
    ]

    for cartao, val in cartoes_ordenados:
        pct = (val / total) * 100
        linhas.append(f"• **{cartao}:** {_fmt_moeda(val)} ({pct:.1f}%)")

    linhas.append("\n🏷️ **Por Categoria:**")
    for cat, val in categorias_ordenadas:
        pct = (val / total) * 100
        linhas.append(f"• **{cat}:** {_fmt_moeda(val)} ({pct:.1f}%)")

    if maiores_gastos:
        linhas.append("\n🔝 **Principais Gastos:**")
        for idx, g in enumerate(maiores_gastos):
            linhas.append(f"{idx+1}. {g['description']}: {_fmt_moeda(g['amount'])} ({g['category']} - {g['payment_method']})")

    return "\n".join(linhas)


def consultar_resumo_gastos(
    mes: Optional[int] = None, 
    ano: Optional[int] = None, 
    categoria: Optional[str] = None,
    dias_retroativos: Optional[int] = None
) -> str:
    """
    Query expense summary or detailed expenses for a category from the database.

    Args:
        mes (int, optional): Month (1-12). Defaults to current month.
        ano (int, optional): Year (e.g. 2026). Defaults to current year.
        categoria (str, optional): Specific category to detail.
        dias_retroativos (int, optional): Days back to summarize instead of calendar month.
    """
    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."

    try:
        user_id = UserContext.get_user_id() or "daniel"
        agora = datetime.now(timezone.utc)
        inicio, fim, titulo_periodo, ano_alvo, mes_alvo = _calcular_intervalo_busca(agora, mes, ano, dias_retroativos)

        col = firebase.db.collection("finances")
        docs = _obter_documentos_financas(col, inicio, fim, dias_retroativos)
        todos_gastos, por_cartao, por_categoria, total_geral = _processar_lancamentos(
            docs, user_id, inicio, ano_alvo, mes_alvo, dias_retroativos
        )

        if categoria:
            return _formatar_detalhe_categoria(todos_gastos, categoria.strip(), titulo_periodo)

        if not todos_gastos or total_geral == 0:
            return f"ℹ️ Não encontrei registros de gastos para {titulo_periodo}."

        return _formatar_resumo_macro(todos_gastos, por_cartao, por_categoria, total_geral, titulo_periodo)

    except Exception as e:
        logger.error(f"Erro ao consultar resumo financeiro: {e}")
        return "Desculpe, ocorreu um erro ao consultar o resumo dos seus gastos. Tente novamente mais tarde."
