def get_billing_prompt() -> str:
    """
    Regras para monitoramento de nuvem, custos e billing do GCP (FinOps).
    """
    return (
        "### DOMÍNIO DE CUSTOS E BILLING DO GCP (FINOPS):\n"
        "- Quando o usuário perguntar sobre o seu faturamento, custos de nuvem, consumo do GCP, gastos com servidor ou billing (ex: 'como ta meu billing do gcp?', 'quanto gastei na nuvem?'):\n"
        "  -> Chame OBRIGATORIAMENTE a ferramenta 'consultar_gcp_billing'.\n"
        "  -> NUNCA diga que você não possui integração com o Google Cloud Platform ou que o usuário precisa acessar o console web.\n"
        "  -> Apresente o status do projeto bot-dam, a infraestrutura ativa (VM dam-server, Cloud Run, Firestore) e o monitoramento de orçamentos via Pub/Sub.\n"
    )
