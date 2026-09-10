def get_financial_prompt() -> str:
    """Financial domain rules: payment methods and expense splitting."""
    return (
        "### FINANCIAL DOMAIN & PAYMENT METHODS:\n"
        "The user has exactly 3 payment methods:\n"
        "1. 'Cartão de Crédito Secundário' (shared/additional credit card)\n"
        "2. 'Cartão de Crédito Pessoal' (personal credit card)\n"
        "3. 'Cartão de Débito' (debit/checking account — Pix payments are ALWAYS classified here)\n\n"
        "RULES:\n"
        "- If user specifies payment method (or says Pix): call `registrar_gasto` immediately.\n"
        "- If user does NOT specify which card (and it's not Pix): ASK first, then register.\n"
        "- `consultar_resumo_gastos`: ALWAYS call when user asks about expense summary, monthly spending, or card statements. NEVER say this function is unavailable.\n\n"
        "### BILL SPLITTING & TRIPS:\n"
        "- Split reports (`dividir_conta_restaurante`, `calcular_fechamento_viagem`) MUST organize by PERSON NAME, never by Pix key.\n"
    )
