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

def consultar_resumo_gastos(mes: Optional[int] = None, ano: Optional[int] = None, dias_retroativos: Optional[int] = None) -> str:
    """
    Query expense summary grouped by payment method and category.

    Args:
        mes (int, optional): Month (1-12). Defaults to current month.
        ano (int, optional): Year (e.g. 2026). Defaults to current year.
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
            docs_query = firebase.db.collection("finances").where("timestamp", ">=", inicio)
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
            
            docs_query = firebase.db.collection("finances").where("timestamp", ">=", inicio).where("timestamp", "<", fim)

        docs = list(docs_query.stream())

        # Filtra estritamente pelo usuário ativo (retrocompatibilidade: se sem user_id, pertence ao daniel)
        docs = [d for d in docs if (d.to_dict().get("userId") or d.to_dict().get("user_id") or "daniel") == user_id]

        if not docs:
            return f"ℹ️ Não encontrei registros de gastos para {titulo_periodo}."


        total_geral = 0.0
        por_cartao = {}
        por_categoria = {}
        todos_gastos = []

        for doc in docs:
            data = doc.to_dict()
            try:
                valor = float(data.get("amount", 0.0))
            except (ValueError, TypeError):
                continue

            if valor <= 0:
                continue

            total_geral += valor
            
            metodo = data.get("payment_method") or "Outros"
            metodo_norm = normalizar_metodo_pagamento(metodo) or metodo
            por_cartao[metodo_norm] = por_cartao.get(metodo_norm, 0.0) + valor
            
            cat_raw = data.get("category") or "Geral"
            categoria = cat_raw.strip().title()
            por_categoria[categoria] = por_categoria.get(categoria, 0.0) + valor
            
            todos_gastos.append({
                "description": data.get("description", "Sem descrição"),
                "amount": valor,
                "category": categoria,
                "payment_method": metodo_norm
            })

        if total_geral == 0:
            return f"ℹ️ Não encontrei registros de gastos válidos para {titulo_periodo}."

        # Ordenar categorias do maior para o menor
        categorias_ordenadas = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)
        # Ordenar cartões do maior para o menor
        cartoes_ordenados = sorted(por_cartao.items(), key=lambda x: x[1], reverse=True)
        # Ordenar maiores despesas
        maiores_gastos = sorted(todos_gastos, key=lambda x: x["amount"], reverse=True)[:3]

        def _fmt_moeda(v: float) -> str:
            return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

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
