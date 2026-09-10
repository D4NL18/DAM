def get_billing_prompt() -> str:
    """GCP cloud billing and FinOps monitoring rules."""
    return (
        "### GCP BILLING & FINOPS DOMAIN:\n"
        "- When user asks about cloud billing, GCP costs, or server spending: ALWAYS call `consultar_gcp_billing`.\n"
        "- NEVER say you lack GCP integration or redirect user to the web console.\n"
        "- Present project bot-dam status, active infrastructure (VM dam-server, Cloud Run, Firestore) and budget monitoring via Pub/Sub.\n"
    )
