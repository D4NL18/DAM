def get_briefing_prompt() -> str:
    """
    Regras do domínio de Briefing Matinal e Mensagem de Bom Dia.
    """
    return (
        "### DOMÍNIO DE BRIEFING MATINAL / MENSAGEM DE BOM DIA:\n"
        "- Quando o usuário perguntar sobre o seu briefing matinal, resumo do dia, ou o que está programado para a sua mensagem de bom dia (ex: 'qual seria minha mensagem de bom dia programada para hj?', 'o que tem no meu resumo matinal de hoje?'):\n"
        "  -> Chame OBRIGATORIAMENTE a ferramenta 'consultar_briefing_matinal'.\n"
        "  -> A mensagem de bom dia oficial é composta ESTRITAMENTE por 4 pilares: 1) Agenda e compromissos de hoje, 2) Tarefas e lembretes de hoje, 3) Jogos da FURIA Esports no dia e 4) Animes acompanhados que lançam novos episódios hoje.\n"
        "  -> REGRA MANDATÓRIA ABSOLUTA DE LEMBRETES: SE NÃO FOR PRA HOJE, NÃO É PRA MOSTRAR! Jamais exiba lembretes ou tarefas com datas futuras no resumo de hoje. Se não houver lembretes para o dia corrente, exiba estritamente 'Nenhuma tarefa pendente para hoje'.\n"
        "  -> É EXPRESSAMENTE PROIBIDO incluir informações sobre veículo (carro), banco de horas ou compromissos do dia seguinte na mensagem de bom dia.\n"
    )
