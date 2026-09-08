def get_mobility_prompt() -> str:
    """
    Regras do domínio de mobilidade, trânsito e rotas.
    """
    return (
        "### DOMÍNIO DE MOBILIDADE & ROTAS:\n"
        "- Quando o usuário disser 'casa', utilize a residência configurada como ponto de referência.\n"
        "- Para qualquer outro destino informado em texto livre (ex: 'Shopping da Bahia', 'Farol da Barra', 'Aeroporto', ou qualquer endereço/ponto turístico), consulte a rota e o trânsito buscando diretamente pelo nome do local informado.\n"
    )
