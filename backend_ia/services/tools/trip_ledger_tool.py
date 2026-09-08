import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from config import firebase

logger = logging.getLogger(__name__)

# Fallback em memória caso Firestore não esteja inicializado
_MEMORY_TRIP_GROUPS: Dict[str, Dict[str, Any]] = {}
_MEMORY_TRIP_EXPENSES: List[Dict[str, Any]] = []

def _limpar_dados_memoria():
    """Auxiliar para testes unitários resetarem a memória."""
    _MEMORY_TRIP_GROUPS.clear()
    _MEMORY_TRIP_EXPENSES.clear()

def criar_grupo_viagem(nome_viagem: str, participantes: List[str]) -> str:
    """
    Cria um novo grupo de viagem para divisão de despesas.

    Args:
        nome_viagem (str): Nome identificador da viagem (ex: 'Floripa 2026', 'Carnaval Rio').
        participantes (list[str]): Lista com os nomes dos participantes da viagem.
    """
    nome_limpo = nome_viagem.strip()
    if not nome_limpo:
        return "Erro: O nome da viagem não pode ser vazio."

    participantes_limpos = list(dict.fromkeys([p.strip() for p in participantes if p and p.strip()]))
    if len(participantes_limpos) < 2:
        return "Erro: O grupo deve conter pelo menos 2 participantes para divisão de despesas."

    group_data = {
        "id": nome_limpo.lower(),
        "nome_viagem": nome_limpo,
        "participantes": participantes_limpos,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    # Salva em memória
    _MEMORY_TRIP_GROUPS[nome_limpo.lower()] = group_data

    # Salva no Firestore se disponível
    if firebase.db is not None:
        try:
            firebase.db.collection("trip_groups").document(nome_limpo.lower()).set(group_data)
            logger.info(f"Grupo de viagem '{nome_limpo}' salvo no Firestore.")
        except Exception as e:
            logger.error(f"Erro ao salvar grupo de viagem no Firestore: {e}")

    part_str = ", ".join(participantes_limpos)
    return (
        f"🌴 **Grupo de Viagem Criado com Sucesso!**\n"
        f"• Viagem: **{nome_limpo}**\n"
        f"• Participantes ({len(participantes_limpos)}): {part_str}\n"
        f"Agora você pode registrar gastos usando `adicionar_despesa_viagem`."
    )

def adicionar_despesa_viagem(
    nome_viagem: str, 
    descricao: str, 
    valor: float, 
    pagador: str, 
    participantes_divisao: Optional[List[str]] = None
) -> str:
    """
    Registra uma despesa de viagem paga por um participante e dividida entre membros do grupo.

    Args:
        nome_viagem (str): Nome da viagem.
        descricao (str): Descrição do gasto (ex: 'Jantar Frutos do Mar', 'Pedágio', 'Airbnb').
        valor (float): Valor total da despesa.
        pagador (str): Nome do participante que efetuou o pagamento.
        participantes_divisao (list[str], opcional): Lista dos participantes que devem dividir a conta.
                                                     Se omitido ou vazio, divide igualmente entre todos os membros do grupo.
    """
    nome_limpo = nome_viagem.strip()
    key = nome_limpo.lower()

    # Busca o grupo em memória ou no Firestore
    group = _MEMORY_TRIP_GROUPS.get(key)
    if not group and firebase.db is not None:
        try:
            doc = firebase.db.collection("trip_groups").document(key).get()
            if doc.exists:
                group = doc.to_dict()
                _MEMORY_TRIP_GROUPS[key] = group
        except Exception as e:
            logger.error(f"Erro ao buscar grupo de viagem no Firestore: {e}")

    if not group:
        return f"Erro: O grupo de viagem '{nome_limpo}' não foi encontrado. Crie-o primeiro com `criar_grupo_viagem`."

    if valor <= 0:
        return "Erro: O valor da despesa deve ser maior que zero."

    pagador_limpo = pagador.strip()
    membros_grupo = group.get("participantes", [])

    # Validação do pagador (insensível a maiúsculas/minúsculas)
    pagador_encontrado = next((m for m in membros_grupo if m.lower() == pagador_limpo.lower()), None)
    if not pagador_encontrado:
        # Se não estiver no grupo original, adiciona aos participantes
        pagador_encontrado = pagador_limpo
        membros_grupo.append(pagador_encontrado)
        group["participantes"] = membros_grupo

    # Define participantes da divisão
    if not participantes_divisao:
        divisao_final = list(membros_grupo)
    else:
        divisao_limpa = [p.strip() for p in participantes_divisao if p and p.strip()]
        # Faz correspondência com membros do grupo se possível
        divisao_final = []
        for p in divisao_limpa:
            m = next((item for item in membros_grupo if item.lower() == p.lower()), p)
            divisao_final.append(m)
        divisao_final = list(dict.fromkeys(divisao_final))

    if not divisao_final:
        return "Erro: É necessário ao menos um participante na divisão da despesa."

    expense_data = {
        "id": str(uuid.uuid4()),
        "nome_viagem": group.get("nome_viagem", nome_limpo),
        "descricao": descricao.strip(),
        "valor": round(float(valor), 2),
        "pagador": pagador_encontrado,
        "participantes_divisao": divisao_final,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    _MEMORY_TRIP_EXPENSES.append(expense_data)

    if firebase.db is not None:
        try:
            firebase.db.collection("trip_expenses").add(expense_data)
            logger.info(f"Despesa '{descricao}' salva no Firestore para a viagem '{nome_limpo}'.")
        except Exception as e:
            logger.error(f"Erro ao salvar despesa de viagem no Firestore: {e}")

    valor_por_pessoa = round(valor / len(divisao_final), 2)
    div_str = ", ".join(divisao_final)
    return (
        f"💸 **Despesa Registrada!**\n"
        f"• Viagem: **{group.get('nome_viagem', nome_limpo)}**\n"
        f"• Descrição: {descricao.strip()}\n"
        f"• Valor Total: R$ {valor:.2f}\n"
        f"• Pago por: **{pagador_encontrado}**\n"
        f"• Dividido entre ({len(divisao_final)}): {div_str} (~R$ {valor_por_pessoa:.2f} cada)"
    )

def calcular_fechamento_viagem(nome_viagem: str, chave_pix: Optional[str] = None) -> str:
    """
    Calcula o fechamento financeiro de uma viagem utilizando algoritmo determinístico
    de Debt Minimization (Minimização de Dívidas).
    Retorna o total gasto, saldos líquidos individuais e o menor número de liquidações Pix necessárias.

    Args:
        nome_viagem (str): Nome da viagem.
        chave_pix (str, opcional): Chave Pix para exibir nas instruções de pagamento.
    """
    nome_limpo = nome_viagem.strip()
    key = nome_limpo.lower()

    # Busca o grupo
    group = _MEMORY_TRIP_GROUPS.get(key)
    if not group and firebase.db is not None:
        try:
            doc = firebase.db.collection("trip_groups").document(key).get()
            if doc.exists:
                group = doc.to_dict()
                _MEMORY_TRIP_GROUPS[key] = group
        except Exception as e:
            logger.error(f"Erro ao buscar grupo de viagem no Firestore: {e}")

    # Coleta todas as despesas da viagem
    expenses = [e for e in _MEMORY_TRIP_EXPENSES if e.get("nome_viagem", "").strip().lower() == key]

    if firebase.db is not None:
        try:
            docs = firebase.db.collection("trip_expenses").where("nome_viagem", "==", group.get("nome_viagem", nome_limpo) if group else nome_limpo).stream()
            db_expenses = [d.to_dict() for d in docs]
            if db_expenses:
                expenses = db_expenses
        except Exception as e:
            logger.error(f"Erro ao buscar despesas do Firestore: {e}")

    if not expenses:
        return f"ℹ️ Nenhuma despesa encontrada para a viagem '{nome_limpo}'."

    # Mapeia participantes
    todos_participantes = set(group.get("participantes", [])) if group else set()
    total_viagem = 0.0

    # Inicializa saldos: saldo líquido = total pago - total devido
    pagos: Dict[str, float] = {}
    devidos: Dict[str, float] = {}

    for exp in expenses:
        val = float(exp["valor"])
        total_viagem += val
        pagador = exp["pagador"]
        divisao = exp["participantes_divisao"]

        todos_participantes.add(pagador)
        pagos[pagador] = pagos.get(pagador, 0.0) + val

        if divisao:
            valor_individual = val / len(divisao)
            for part in divisao:
                todos_participantes.add(part)
                devidos[part] = devidos.get(part, 0.0) + valor_individual

    saldos_liquidos: Dict[str, float] = {}
    for part in todos_participantes:
        saldo = pagos.get(part, 0.0) - devidos.get(part, 0.0)
        saldos_liquidos[part] = round(saldo, 2)

    # Debt Minimization Algorithm (Dois ponteiros guloso)
    # Devedores (saldo negativo, ou seja, pagaram menos do que consumiram)
    # Credores (saldo positivo, ou seja, pagaram mais do que consumiram)
    devedores: List[List[Any]] = []
    credores: List[List[Any]] = []

    for pessoa, saldo in saldos_liquidos.items():
        if saldo < -0.005:
            devedores.append([pessoa, abs(saldo)])
        elif saldo > 0.005:
            credores.append([pessoa, saldo])

    # Ordena devedores e credores pelo maior valor absoluto
    devedores.sort(key=lambda x: x[1], reverse=True)
    credores.sort(key=lambda x: x[1], reverse=True)

    transferencias = []
    i = 0
    j = 0
    while i < len(devedores) and j < len(credores):
        devedor_nome, devedor_valor = devedores[i]
        credor_nome, credor_valor = credores[j]

        pagamento = min(devedor_valor, credor_valor)
        pagamento = round(pagamento, 2)

        if pagamento > 0.005:
            transferencias.append((devedor_nome, credor_nome, pagamento))

        devedores[i][1] = round(devedor_valor - pagamento, 2)
        credores[j][1] = round(credor_valor - pagamento, 2)

        if devedores[i][1] <= 0.005:
            i += 1
        if credores[j][1] <= 0.005:
            j += 1

    # Construção do relatório
    nome_exibicao = group.get("nome_viagem", nome_limpo) if group else nome_limpo
    linhas = [
        f"📊 **Fechamento de Contas - {nome_exibicao}**\n",
        f"💰 **Total Gasto na Viagem:** R$ {total_viagem:.2f}\n",
        "👤 **Resumo por Participante:**"
    ]

    # Ordena participantes por nome
    for part in sorted(todos_participantes):
        total_pago = pagos.get(part, 0.0)
        saldo = saldos_liquidos.get(part, 0.0)
        if saldo < -0.005:
            saldo_str = f"-R$ {abs(saldo):.2f}"
        elif saldo > 0.005:
            saldo_str = f"+R$ {saldo:.2f}"
        else:
            saldo_str = "R$ 0.00"
        linhas.append(f"• **{part}**: Pagou R$ {total_pago:.2f} | Saldo líquido: **{saldo_str}**")

    linhas.append("\n🤝 **Liquidações Sugeridas (Menor número de Pix):**")
    if not transferencias:
        linhas.append("• ✅ Todas as contas estão perfeitamente quitadas! Nenhuma transferência necessária.")
    else:
        for devedor, credor, valor in transferencias:
            linhas.append(f"• 💳 **{devedor}** deve pagar **R$ {valor:.2f}** para **{credor}**")

    if chave_pix:
        linhas.append(f"\n🔑 **Chave Pix para Acertos:** `{chave_pix.strip()}`")

    return "\n".join(linhas)
