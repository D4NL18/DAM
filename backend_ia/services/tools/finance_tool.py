from typing import Optional
import uuid
import logging
from datetime import datetime, timezone, timedelta
from config import firebase
from services.user_context import UserContext

logger = logging.getLogger(__name__)

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
        user_id = UserContext.get_user_id()
        data_to_save = {
            "id": str(uuid.uuid4()),
            "userId": user_id,
            "user_id": user_id,
            "description": descricao,
            "amount": valor,
            "category": categoria,
            "payment_method": metodo_normalizado,
            "date": datetime.now(timezone.utc).isoformat(),
            "timestamp": datetime.now(timezone.utc)
        }
        
        firebase.db.collection("finances").add(data_to_save)
        logger.info(f"Gasto registrado para [{user_id}]: {descricao} - R$ {valor:.2f} [{metodo_normalizado}]")
        return (
            f"Sucesso! Registrei o gasto de R$ {valor:.2f} com '{descricao}' "
            f"na categoria {categoria} no cartão **{metodo_normalizado}**."
        )
    
    except Exception as e:
        logger.error(f"Erro ao registrar finanças: {e}")
        return "Desculpe, ocorreu um erro ao salvar seu gasto. Tente novamente mais tarde."

def _normalize_str(s: str) -> str:
    """Normaliza string para comparação sem acentos e em minúsculas."""
    import unicodedata
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower().strip()

def _match_category(item_cat: str, target_cat: str) -> bool:
    """Compara categorias tratando variações de escrita e sinônimos comuns."""
    i_norm = _normalize_str(item_cat)
    t_norm = _normalize_str(target_cat)
    if not i_norm or not t_norm:
        return False
    if t_norm in i_norm or i_norm in t_norm:
        return True
    
    # Aliases semânticos usuais
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
        categoria (str, optional): Specific category to detail (e.g. 'Moradia', 'Alimentação', 'Mercado'). If provided, lists each individual expense in that category.
        dias_retroativos (int, optional): Days back to summarize instead of calendar month.
    """
    if firebase.db is None:
        return "Erro: O banco de dados não está disponível no momento."

    try:
        user_id = UserContext.get_user_id()
        agora = datetime.now(timezone.utc)
        
        # 1. Definir intervalo de datas
        if dias_retroativos and dias_retroativos > 0:
            inicio = agora - timedelta(days=dias_retroativos)
            titulo_periodo = f"últimos {dias_retroativos} dias"
        else:
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
            titulo_periodo = f"{nome_mes}/{ano_alvo}"

        col = firebase.db.collection("finances")
        docs = []

        # Tenta consulta via .where (suporte a mocks estruturados e índices Firestore)
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

        # Se não obteve via .where, faz streaming direto da coleção (Firestore real ou mock de coleção direta)
        if not docs and hasattr(col, "stream"):
            try:
                candidate_stream = list(col.stream())
                if candidate_stream and any(hasattr(d, "to_dict") and isinstance(d.to_dict(), dict) and "amount" in d.to_dict() for d in candidate_stream):
                    docs = candidate_stream
            except Exception:
                pass

        total_geral = 0.0
        por_cartao = {}
        por_categoria = {}
        todos_gastos = []

        for doc in docs:
            if not hasattr(doc, "to_dict"):
                continue
            data = doc.to_dict() or {}
            
            # Isolamento estrito por usuário
            doc_user = data.get("userId") or data.get("user_id") or "daniel"
            if doc_user != user_id:
                continue

            # Exclui receitas (income), processa apenas despesas
            tx_type = data.get("type") or "expense_variable"
            if tx_type == "income":
                continue

            # Parsing e validação temporal da transação
            dt_raw = data.get("date") or data.get("created_at") or data.get("timestamp")
            dt = None
            if isinstance(dt_raw, datetime):
                dt = dt_raw
            elif isinstance(dt_raw, str) and dt_raw:
                try:
                    clean_dt = dt_raw.replace("Z", "+00:00")
                    dt = datetime.fromisoformat(clean_dt)
                except Exception:
                    pass

            if dt:
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dias_retroativos and dias_retroativos > 0:
                    if dt < inicio:
                        continue
                else:
                    if dt.year != ano_alvo or dt.month != mes_alvo:
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
            
            cat_raw = data.get("category") or "Geral"
            cat_formatada = cat_raw.strip().title()
            por_categoria[cat_formatada] = por_categoria.get(cat_formatada, 0.0) + valor
            
            todos_gastos.append({
                "description": data.get("description", "Sem descrição"),
                "amount": valor,
                "category": cat_formatada,
                "payment_method": metodo_norm,
                "date": dt.strftime("%d/%m/%Y") if dt else ""
            })

        def _fmt_moeda(v: float) -> str:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        # Se foi solicitado detalhamento de uma categoria específica
        if categoria:
            target_cat = categoria.strip()
            gastos_categoria = [g for g in todos_gastos if _match_category(g["category"], target_cat)]
            if not gastos_categoria:
                return f"ℹ️ Não encontrei registros de gastos na categoria '{target_cat}' para {titulo_periodo} no seu banco de dados."

            total_cat = sum(g["amount"] for g in gastos_categoria)
            linhas = [
                f"🏷️ **Gastos em {target_cat.title()} - {titulo_periodo}**",
                f"💰 **Total:** {_fmt_moeda(total_cat)} ({len(gastos_categoria)} lançamento{'s' if len(gastos_categoria) > 1 else ''})\n",
                "📋 **Detalhamento:**"
            ]
            for g in sorted(gastos_categoria, key=lambda x: x["amount"], reverse=True):
                data_info = f" ({g['date']})" if g.get("date") else ""
                linhas.append(f"• **{g['description']}:** {_fmt_moeda(g['amount'])}{data_info} [{g['payment_method']}]")

            return "\n".join(linhas)

        # Se for o resumo geral de gastos
        if not todos_gastos or total_geral == 0:
            return f"ℹ️ Não encontrei registros de gastos para {titulo_periodo}."

        # Ordenar categorias do maior para o menor
        categorias_ordenadas = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)
        # Ordenar cartões do maior para o menor
        cartoes_ordenados = sorted(por_cartao.items(), key=lambda x: x[1], reverse=True)
        # Ordenar maiores despesas
        maiores_gastos = sorted(todos_gastos, key=lambda x: x["amount"], reverse=True)[:3]

        linhas = [
            f"📊 **Resumo Financeiro - {titulo_periodo}**\n",
            f"💰 **Total Geral:** {_fmt_moeda(total_geral)} ({len(todos_gastos)} lançamentos)\n",
            "💳 **Por Cartão / Forma de Pagamento:**"
        ]

        for cartao, val in cartoes_ordenados:
            pct = (val / total_geral) * 100
            linhas.append(f"• **{cartao}:** {_fmt_moeda(val)} ({pct:.1f}%)")

        linhas.append("\n🏷️ **Por Categoria:**")
        for cat, val in categorias_ordenadas:
            pct = (val / total_geral) * 100
            linhas.append(f"• **{cat}:** {_fmt_moeda(val)} ({pct:.1f}%)")

        if maiores_gastos:
            linhas.append("\n🔝 **Principais Gastos:**")
            for idx, g in enumerate(maiores_gastos):
                linhas.append(f"{idx+1}. {g['description']}: {_fmt_moeda(g['amount'])} ({g['category']} - {g['payment_method']})")

        return "\n".join(linhas)

    except Exception as e:
        logger.error(f"Erro ao consultar resumo financeiro: {e}")
        return "Desculpe, ocorreu um erro ao consultar o resumo dos seus gastos. Tente novamente mais tarde."
