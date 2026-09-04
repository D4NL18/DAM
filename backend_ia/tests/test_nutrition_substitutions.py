import pytest
from services.prompts.prompt_composer import PromptComposer

def test_catalogo_dietbox_integridade():
    """Valida se o catálogo estruturado possui exatamente os 7 grupos e os 132 alimentos do Dietbox."""
    from services.tools.nutrition_dietbox_data import GRUPOS_ALIMENTARES, ALIMENTOS_DIETBOX
    
    assert len(GRUPOS_ALIMENTARES) == 7
    assert "carboidratos" in GRUPOS_ALIMENTARES
    assert "carnes_e_ovos" in GRUPOS_ALIMENTARES
    assert "frutas" in GRUPOS_ALIMENTARES
    assert "laticinios" in GRUPOS_ALIMENTARES
    assert "legumes_e_verduras" in GRUPOS_ALIMENTARES
    assert "leguminosas" in GRUPOS_ALIMENTARES
    assert "oleos_e_gorduras" in GRUPOS_ALIMENTARES
    
    # 135 alimentos extraídos do documento PDF oficial
    assert len(ALIMENTOS_DIETBOX) == 135
    
    # Validações amostrais de dados do PDF
    arroz = next((a for a in ALIMENTOS_DIETBOX if "Arroz Branco Cozido" in a["nome_oficial"]), None)
    assert arroz is not None
    assert arroz["medida_caseira"] == "4 Colheres de Sopa"
    assert arroz["quantidade_g_ml"] == 100.0

    frango = next((a for a in ALIMENTOS_DIETBOX if "Filé de Frango Grelhado" in a["nome_oficial"]), None)
    assert frango is not None
    assert frango["medida_caseira"] == "1 Filé Médio"
    assert frango["quantidade_g_ml"] == 120.0

def test_consultar_lista_substituicao_por_grupo():
    """Testa consulta geral de um grupo calórico prescrito."""
    from services.tools.nutrition_tool import consultar_lista_substituicao
    
    res = consultar_lista_substituicao("carboidratos")
    assert "Grupo: Carboidratos" in res
    assert "150 Kcal" in res
    assert "Arroz Branco Cozido" in res
    assert "Batata Doce Cozida" in res
    assert "Pão Francês" in res

def test_consultar_lista_substituicao_por_alimento():
    """Testa consulta de alimento individual na lista com alternativas equivalentes."""
    from services.tools.nutrition_tool import consultar_lista_substituicao
    
    res = consultar_lista_substituicao("Batata Doce Cozida")
    assert "Batata Doce Cozida" in res
    assert "2 Pedaços Médios" in res
    assert "200,00" in res or "200.00" in res or "200" in res
    assert "150 Kcal" in res
    assert "Alternativas Equivalentes no mesmo grupo" in res

def test_consultar_lista_substituicao_com_alias():
    """Testa busca por termo simplificado ou alias (ex: 'frango', 'banana')."""
    from services.tools.nutrition_tool import consultar_lista_substituicao
    
    res = consultar_lista_substituicao("frango")
    assert "Filé de Frango Grelhado" in res or "Peito de frango assado" in res
    assert "Carnes e Ovos" in res

def test_consultar_lista_substituicao_item_inexistente():
    """Testa consulta de item que não existe na lista."""
    from services.tools.nutrition_tool import consultar_lista_substituicao
    
    res = consultar_lista_substituicao("sorvete de pistache")
    assert "NÃO foi encontrado" in res or "não consta" in res.lower()
    assert "avaliar_substituicao_alimento" in res

def test_avaliar_substituicao_mesmo_grupo():
    """Testa substituição válida entre dois itens do mesmo grupo calórico."""
    from services.tools.nutrition_tool import avaliar_substituicao_alimento
    
    res = avaliar_substituicao_alimento(alimento_desejado="Batata Inglesa Cozida", alimento_a_substituir="Arroz Branco Cozido")
    assert "Substituição Válida" in res
    assert "Batata Inglesa Cozida" in res
    assert "1 Unidade e 1/2" in res
    assert "300" in res
    assert "Arroz Branco Cozido" in res
    assert "Carboidratos" in res

def test_avaliar_substituicao_grupos_distintos():
    """Testa tentativa de substituição entre alimentos de grupos calóricos distintos."""
    from services.tools.nutrition_tool import avaliar_substituicao_alimento
    
    res = avaliar_substituicao_alimento(alimento_desejado="Filé de Frango Grelhado", alimento_a_substituir="Arroz Branco Cozido")
    assert "Grupos Nutricionais Diferentes" in res or "Atenção: Grupos Diferentes" in res
    assert "Carnes e Ovos" in res
    assert "Carboidratos" in res

def test_avaliar_substituicao_fora_da_lista_alerta_mandatorio():
    """Testa que alimentos fora da lista acionam o ALERTA mandatório e a pesquisa comparativa com pontos de atenção."""
    from services.tools.nutrition_tool import avaliar_substituicao_alimento
    
    res = avaliar_substituicao_alimento(alimento_desejado="Pizza de Calabresa", alimento_a_substituir="Pão Francês")
    # Alerta obrigatório
    assert "ALERTA" in res
    assert "NÃO CONSTA" in res or "NÃO consta" in res
    assert "Dietbox" in res
    
    # Análise nutricional comparativa
    assert "Informações Nutricionais" in res or "Comparativo Nutricional" in res
    assert "Kcal" in res or "calorias" in res.lower()
    
    # Pontos de atenção
    assert "Pontos de Atenção" in res
    assert "Densidade Calórica" in res or "Gordura" in res or "Sódio" in res or "Índice Glicêmico" in res

def test_avaliar_substituicao_fora_da_lista_sem_substituto_definido():
    """Testa alimento fora da lista sem alimento de referência."""
    from services.tools.nutrition_tool import avaliar_substituicao_alimento
    
    res = avaliar_substituicao_alimento(alimento_desejado="Chocolate ao Leite")
    assert "ALERTA" in res
    assert "NÃO CONSTA" in res or "NÃO consta" in res
    assert "Pontos de Atenção" in res

def test_sanitizacao_input_malicioso():
    """Garante que entradas com caracteres perigosos ou injeções são devidamente higienizadas."""
    from services.tools.nutrition_tool import avaliar_substituicao_alimento
    
    res = avaliar_substituicao_alimento(alimento_desejado="<script>alert(1)</script> pizza; DROP TABLE;", alimento_a_substituir="")
    assert "<script>" not in res
    assert "DROP TABLE" not in res
    assert "ALERTA" in res

def test_prompt_composer_inclui_regras_nutricionais():
    """Testa se as instruções de sistema do PromptComposer contêm as regras do Dietbox e ferramentas de nutrição."""
    prompt = PromptComposer.compose_system_instruction("2026-09-03 20:00")
    assert "DOMÍNIO DE NUTRIÇÃO" in prompt
    assert "Lista de Substituição Oficial (Dietbox)" in prompt
    assert "consultar_lista_substituicao" in prompt
    assert "avaliar_substituicao_alimento" in prompt
    assert "ALERTA" in prompt
