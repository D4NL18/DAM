import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

def _format_currency(value: float) -> str:
    """Formata valor float para o padrão de moeda brasileira (R$ 1.234,56)."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dividir_conta_restaurante(
    consumo_participantes: List[Dict[str, Any]], 
    taxa_servico_percent: float = 10.0, 
    chave_pix: Optional[str] = None
) -> str:
    """
    Split restaurant bills fairly and proportionally among participants with tip/service fee calculation.

    Args:
        consumo_participantes (list[dict]): List of participants and items consumed (keys: 'nome', 'itens' with 'nome'/'valor').
        taxa_servico_percent (float, optional): Service fee/tip percentage (default 10.0).
        chave_pix (str, optional): Pix payment key for reimbursement summary.
    """
    # Suporte caso o modelo ou chamador passe como string JSON
    if isinstance(consumo_participantes, str):
        try:
            consumo_participantes = json.loads(consumo_participantes)
        except Exception as e:
            return f"Erro ao processar dados dos participantes: {e}"

    if not consumo_participantes or not isinstance(consumo_participantes, list):
        return "Nenhum consumo informado para divisão da conta."

    # Normalizar percentual da taxa
    try:
        taxa_percent = float(taxa_servico_percent)
        if taxa_percent < 0:
            taxa_percent = 0.0
    except (ValueError, TypeError):
        taxa_percent = 10.0

    parsed_participants = []
    subtotal_geral = 0.0

    for idx, p in enumerate(consumo_participantes):
        nome = str(p.get("nome", f"Participante {idx + 1}")).strip()
        raw_itens = p.get("itens", [])
        itens_limpos = []
        subtotal_pessoa = 0.0

        for item in raw_itens:
            item_nome = str(item.get("nome", "Item")).strip()
            raw_valor = item.get("valor", 0.0)
            try:
                if isinstance(raw_valor, str):
                    raw_valor = raw_valor.replace("R$", "").replace(" ", "").replace(",", ".")
                valor_float = round(float(raw_valor), 2)
            except (ValueError, TypeError):
                valor_float = 0.0

            itens_limpos.append({"nome": item_nome, "valor": valor_float})
            subtotal_pessoa += valor_float

        subtotal_pessoa = round(subtotal_pessoa, 2)
        subtotal_geral += subtotal_pessoa

        parsed_participants.append({
            "idx": idx,
            "nome": nome,
            "itens": itens_limpos,
            "subtotal": subtotal_pessoa
        })

    subtotal_geral = round(subtotal_geral, 2)

    if subtotal_geral == 0.0:
        return "O valor total do consumo da mesa é R$ 0,00. Nada a dividir."

    # Cálculo da taxa de serviço total e total geral da conta
    taxa_servico_total = round(subtotal_geral * (taxa_percent / 100.0), 2)
    total_geral_conta = round(subtotal_geral + taxa_servico_total, 2)

    # Cálculo preliminar proporcional por participante
    for p in parsed_participants:
        if subtotal_geral > 0:
            servico_ind = round(p["subtotal"] * (taxa_percent / 100.0), 2)
        else:
            servico_ind = 0.0
        p["servico"] = servico_ind
        p["total"] = round(p["subtotal"] + servico_ind, 2)

    # Ajuste de centavos (Penny Balancing) para garantir fechamento perfeito
    soma_totais = round(sum(p["total"] for p in parsed_participants), 2)
    diff_centavos = int(round((total_geral_conta - soma_totais) * 100))

    if diff_centavos != 0 and parsed_participants:
        # Ordenar participantes com maior consumo para receber o ajuste de 1 centavo
        indices_ordenados = sorted(
            range(len(parsed_participants)), 
            key=lambda i: parsed_participants[i]["subtotal"], 
            reverse=True
        )
        
        passo = 1 if diff_centavos > 0 else -1
        ajustes_restantes = abs(diff_centavos)
        
        ptr = 0
        while ajustes_restantes > 0:
            idx_p = indices_ordenados[ptr % len(indices_ordenados)]
            parsed_participants[idx_p]["servico"] = round(parsed_participants[idx_p]["servico"] + (passo * 0.01), 2)
            parsed_participants[idx_p]["total"] = round(parsed_participants[idx_p]["subtotal"] + parsed_participants[idx_p]["servico"], 2)
            ajustes_restantes -= 1
            ptr += 1

    # Formatação do demonstrativo elegante para WhatsApp
    linhas = [
        "🧾 *Divisão de Conta - Restaurante*",
        "━━━━━━━━━━━━━━━━━━━━━━"
    ]

    for p in parsed_participants:
        linhas.append(f"👤 *{p['nome']}*")
        if p["itens"]:
            for item in p["itens"]:
                linhas.append(f"  • {item['nome']}: {_format_currency(item['valor'])}")
        else:
            linhas.append("  • (Nenhum item individual registrado)")

        linhas.append(f"  ↳ Subtotal: {_format_currency(p['subtotal'])}")
        if taxa_percent > 0:
            linhas.append(f"  ↳ Serviço ({taxa_percent:g}%): {_format_currency(p['servico'])}")
        linhas.append(f"  👉 *Total a pagar: {_format_currency(p['total'])}*")
        linhas.append("")

    linhas.append("━━━━━━━━━━━━━━━━━━━━━━")
    linhas.append(f"💰 *Subtotal Geral:* {_format_currency(subtotal_geral)}")
    if taxa_percent > 0:
        linhas.append(f"🏷️ *Taxa de Serviço ({taxa_percent:g}%):* {_format_currency(taxa_servico_total)}")
    linhas.append(f"💵 *TOTAL DA CONTA:* {_format_currency(total_geral_conta)}")

    if chave_pix and chave_pix.strip():
        linhas.append("━━━━━━━━━━━━━━━━━━━━━━")
        linhas.append("📱 *Chave Pix para Pagamento:*")
        linhas.append(f"`{chave_pix.strip()}`")
        linhas.append("_(Copie a chave acima para efetuar a transferência)_")

    return "\n".join(linhas).strip()
