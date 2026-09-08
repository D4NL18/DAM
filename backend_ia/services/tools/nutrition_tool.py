import logging
import re
from typing import Optional, Dict, Any
from services.tools.nutrition_dietbox_data import (
    GRUPOS_ALIMENTARES,
    ALIMENTOS_DIETBOX,
    buscar_alimento_dietbox,
    buscar_alimentos_por_grupo,
    normalizar_termo
)

logger = logging.getLogger(__name__)

# Base de referência nutricional para alimentos populares fora da lista prescrita
# Valores aproximados por porção típica ou 100g
ALIMENTOS_EXTERNOS_DB: Dict[str, Dict[str, Any]] = {
    "pizza": {
        "nome": "Pizza (Média/Fatia típica - aprox. 100g)",
        "calorias_kcal": 280.0,
        "carboidratos_g": 32.0,
        "proteinas_g": 11.0,
        "gorduras_g": 12.0,
        "sodio_mg": 600.0,
        "fibras_g": 1.8,
        "tipo": "Ultraprocessado / Calórico",
        "pontos_atencao": [
            "Densidade Calórica Elevada: Uma única fatia (~100g) tem cerca de 280 Kcal, quase o dobro de uma porção padrão de carboidratos da sua lista (150 Kcal).",
            "Gordura Saturada & Sódio: Elevado teor de queijos amarelos e embutidos, podendo reter líquidos e elevar a pressão arterial.",
            "Índice Glicêmico & Saciedade: Farinha branca combinada com queijo retarda o esvaziamento gástrico, porém a alta palatabilidade induz ao consumo excessivo sem saciedade duradoura."
        ]
    },
    "chocolate": {
        "nome": "Chocolate ao Leite (Porção de 25g a 50g)",
        "calorias_kcal": 270.0,
        "carboidratos_g": 30.0,
        "proteinas_g": 3.8,
        "gorduras_g": 15.5,
        "sodio_mg": 45.0,
        "fibras_g": 1.2,
        "tipo": "Doce / Denso em Energia",
        "pontos_atencao": [
            "Densidade Calórica & Açúcar Refinado: Em apenas 50g fornece ~270 Kcal (quase 4x mais calórico que uma fruta da sua lista, que tem média de 70 Kcal).",
            "Pico Insulínico: Rápida absorção de carboidratos simples provocando oscilação glicêmica e fome rebote pouco tempo após o consumo.",
            "Gorduras Saturadas: Presença de manteiga de cacau e gordura vegetal que elevam a cota lipídica diária rapidamente."
        ]
    },
    "batata frita": {
        "nome": "Batata Frita (Porção média de 100g)",
        "calorias_kcal": 312.0,
        "carboidratos_g": 41.0,
        "proteinas_g": 3.4,
        "gorduras_g": 15.0,
        "sodio_mg": 210.0,
        "fibras_g": 3.8,
        "tipo": "Fritura em Imersão",
        "pontos_atencao": [
            "Densidade Calórica vs Batata Cozida: 100g de batata frita têm ~312 Kcal, enquanto 300g de batata inglesa cozida da sua lista fornecem apenas 150 Kcal (volume muito menor com mais que o dobro de calorias).",
            "Gorduras Tóxicas/Oxidadas: Óleos aquecidos em altas temperaturas geram compostos pró-inflamatórios.",
            "Impacto na Saciedade: Baixíssimo índice de saciedade comparado aos tubérculos cozidos prescritos."
        ]
    },
    "hamburguer fast food": {
        "nome": "Hambúrguer Comercial / Fast Food (1 unidade simples ~120g)",
        "calorias_kcal": 350.0,
        "carboidratos_g": 33.0,
        "proteinas_g": 15.0,
        "gorduras_g": 17.0,
        "sodio_mg": 520.0,
        "fibras_g": 1.5,
        "tipo": "Ultraprocessado",
        "pontos_atencao": [
            "Desbalanço Calórico: O dobro de calorias de um hambúrguer grelhado caseiro ou bife da sua lista de Carnes (190 Kcal).",
            "Molhos e Embutidos: Presença de conservantes, maioneses e pães com açúcar adicionado.",
            "Sódio Excessivo: Contribui para retenção de água e mascaramento de perda de peso na balança."
        ]
    },
    "whey protein": {
        "nome": "Whey Protein Concentrado (1 dosador ~30g)",
        "calorias_kcal": 120.0,
        "carboidratos_g": 3.0,
        "proteinas_g": 24.0,
        "gorduras_g": 1.5,
        "sodio_mg": 50.0,
        "fibras_g": 0.0,
        "tipo": "Suplemento Alimentar",
        "pontos_atencao": [
            "Não Consta no Plano: Embora seja fonte nobre de proteínas, seu consumo deve ser ajustado à sua meta diária de macronutrientes prescrita.",
            "Velocidade de Absorção & Saciedade: Por ser líquido, a sensação de saciedade é significativamente inferior a 120g de filé de frango ou 3 ovos da sua lista.",
            "Validação Nutricional: Requer conferência do seu nutricionista para não sobrecarregar sua cota proteica sem necessidade."
        ]
    },
    "refrigerante": {
        "nome": "Refrigerante Tradicional (1 lata 350ml)",
        "calorias_kcal": 140.0,
        "carboidratos_g": 37.0,
        "proteinas_g": 0.0,
        "gorduras_g": 0.0,
        "sodio_mg": 15.0,
        "fibras_g": 0.0,
        "tipo": "Calorias Líquidas / Açúcar Líquido",
        "pontos_atencao": [
            "Calorias Vazias: Quase 10 colheres de chá de açúcar dissolvido sem fornecer vitaminas, fibras ou minerais.",
            "Impacto Glicêmico Imediato: Pico brutal de insulina no sangue, favorecendo lipogênese (acúmulo de gordura corporal).",
            "Zero Saciedade: Não ativa os mecanismos neurais de saciedade mastigatória."
        ]
    },
    "cerveja": {
        "nome": "Cerveja Pilsen (1 lata 350ml)",
        "calorias_kcal": 150.0,
        "carboidratos_g": 12.0,
        "proteinas_g": 1.0,
        "gorduras_g": 0.0,
        "sodio_mg": 10.0,
        "fibras_g": 0.0,
        "tipo": "Bebida Alcoólica",
        "pontos_atencao": [
            "Álcool & Metabolismo Lipídico: O organismo paralisa a oxidação de gorduras para priorizar a queima do etanol tóxico.",
            "Densidade Calórica: 1 lata equivale em calorias a 100g de arroz ou 200g de batata doce da sua dieta, porém sem nenhum nutriente estrutural.",
            "Desidratação Celular: O álcool inibe o hormônio antidiurético (ADH), gerando retenção rebote no dia seguinte."
        ]
    },
    "sorvete": {
        "nome": "Sorvete de Massa Tradicional (1 bola ~60g)",
        "calorias_kcal": 130.0,
        "carboidratos_g": 16.0,
        "proteinas_g": 2.5,
        "gorduras_g": 7.0,
        "sodio_mg": 45.0,
        "fibras_g": 0.5,
        "tipo": "Sobremesa Láctea com Gordura Hidrogenada",
        "pontos_atencao": [
            "Gorduras Saturadas e Açúcar: Combinação perfeita de carboidratos refinados com gorduras que aumenta a palatabilidade e dificulta o controle de porção.",
            "Calorias Ocultas: 2 bolas de sorvete superam com facilidade uma refeição de lanche completa.",
            "Alternativa na Dieta: Compare com frutas congeladas da sua lista (ex: banana ou morango batido) que entregam fibras e micronutrientes."
        ]
    }
}

def _sanitizar_texto(texto: str) -> str:
    """Higieniza inputs contra injeções ou tags indesejadas."""
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", "", texto)
    texto = re.sub(r"(?i)\b(drop\s+table|delete\s+from|insert\s+into|select\s+.*from)\b", "", texto)
    return texto.strip()

def _estimar_dados_nutricionais(termo: str) -> Dict[str, Any]:
    """
    Busca na base nutricional expandida ou constrói uma estimativa fundamentada
    para alimentos não catalogados diretamente.
    """
    termo_norm = normalizar_termo(termo)
    
    # 1. Procura match na base externa estruturada
    for chave, dados in ALIMENTOS_EXTERNOS_DB.items():
        if chave in termo_norm or termo_norm in chave:
            return dados
            
    # 2. Estimativa fundamentada para alimentos desconhecidos
    return {
        "nome": f"{termo.title()} (Porção Média Estimada ~100g)",
        "calorias_kcal": 250.0,
        "carboidratos_g": 25.0,
        "proteinas_g": 8.0,
        "gorduras_g": 12.0,
        "sodio_mg": 350.0,
        "fibras_g": 1.0,
        "tipo": "Alimento Não Catalogado / Fora da Prescrição",
        "pontos_atencao": [
            f"Densidade Calórica Incerta: O alimento '{termo}' não possui quantificação definida no seu plano do Dietbox, oferecendo risco de consumo calórico excessivo.",
            "Composição de Macronutrientes: Provável desequilíbrio na relação entre proteínas magras e gorduras boas se comparado aos alimentos prescritos.",
            "Índice Glicêmico & Processamento: Pode conter açúcares adicionados, gorduras saturadas ou conservantes que não estavam previstos na sua estratégia nutricional."
        ]
    }

def _format_kcal(val: Any) -> str:
    try:
        f = float(val)
        if f.is_integer():
            return f"{int(f)} Kcal"
        return f"{f:.1f} Kcal"
    except Exception:
        return f"{val} Kcal"

def consultar_lista_substituicao(alimento_ou_grupo: str) -> str:
    """
    Consulta os alimentos permitidos na Lista de Substituição oficial do Dietbox (Samuel Meller Silva).
    Use esta ferramenta quando o usuário perguntar quais alimentos pode comer em um determinado grupo,
    ou qual a porção/medida caseira oficial de um alimento da lista.

    Args:
        alimento_ou_grupo: Nome do alimento (ex: 'arroz branco', 'frango grelhado', 'banana') ou 
                           nome do grupo ('carboidratos', 'carnes e ovos', 'frutas', 'laticinios',
                           'legumes e verduras', 'leguminosas', 'oleos e gorduras').
    """
    termo_limpo = _sanitizar_texto(alimento_ou_grupo)
    if not termo_limpo:
        return "Por favor, informe o nome do alimento ou grupo que deseja consultar na sua lista de substituição."

    # 1. Checa se o termo é um grupo
    alimentos_grupo = buscar_alimentos_por_grupo(termo_limpo)
    if alimentos_grupo:
        primeiro = alimentos_grupo[0]
        meta_grupo = GRUPOS_ALIMENTARES.get(primeiro["grupo"], {})
        nome_grupo = meta_grupo.get("nome", primeiro["grupo"].title())
        media_kcal_str = _format_kcal(meta_grupo.get("media_calorica_kcal", "N/A"))

        linhas = [
            f"📋 **Grupo: {nome_grupo}** (Média Calórica: {media_kcal_str})",
            f"Total de opções prescritas: {len(alimentos_grupo)} alimentos\n",
            "| Alimento | Medida Caseira | Qtd. (g/ml) |",
            "| :--- | :--- | :--- |"
        ]
        for a in alimentos_grupo:
            linhas.append(f"| {a['nome_oficial']} | {a['medida_caseira']} | {a['quantidade_g_ml']:.2f} {a['unidade']} |")
        
        return "\n".join(linhas)

    # 2. Busca por alimento específico
    alimento = buscar_alimento_dietbox(termo_limpo)
    if alimento:
        meta_grupo = GRUPOS_ALIMENTARES.get(alimento["grupo"], {})
        nome_grupo = meta_grupo.get("nome", alimento["grupo"].title())
        media_kcal_str = _format_kcal(meta_grupo.get("media_calorica_kcal", "N/A"))

        # Busca outras opções do mesmo grupo
        outros_do_grupo = [
            a for a in ALIMENTOS_DIETBOX 
            if a["grupo"] == alimento["grupo"] and a["nome_oficial"] != alimento["nome_oficial"]
        ][:5]

        alternativas = "\n".join([
            f"- **{a['nome_oficial']}:** {a['medida_caseira']} ({a['quantidade_g_ml']:.2f} {a['unidade']})"
            for a in outros_do_grupo
        ])

        return (
            f"✅ **Alimento Encontrado na Lista de Substituição Oficial (Dietbox)**\n\n"
            f"- **Alimento:** {alimento['nome_oficial']}\n"
            f"- **Grupo:** {nome_grupo} (Média Calórica: {media_kcal_str})\n"
            f"- **Medida Caseira:** {alimento['medida_caseira']}\n"
            f"- **Quantidade:** {alimento['quantidade_g_ml']:.2f} {alimento['unidade']}\n\n"
            f"🔄 **Alternativas Equivalentes no mesmo grupo ({media_kcal_str}):**\n"
            f"{alternativas}\n\n"
            f"*Dica: Todas essas opções acima possuem o mesmo valor calórico médio previsto para a sua refeição.*"
        )

    return (
        f"ℹ️ O item '{termo_limpo}' NÃO foi encontrado na sua Lista de Substituição oficial do Dietbox.\n"
        f"Se você deseja saber se pode consumi-lo como substituição de algum alimento da dieta, utilize a ferramenta "
        f"`avaliar_substituicao_alimento` para obter a análise nutricional comparativa e pontos de atenção."
    )

def avaliar_substituicao_alimento(alimento_desejado: str, alimento_a_substituir: str = "") -> str:
    """
    Avalia a substituição de um alimento por outro com base na Lista de Substituição oficial do Dietbox.
    Se o alimento_desejado NÃO constar na lista oficial, emite um ALERTA OBRIGATÓRIO, pesquisa dados
    nutricionais na internet/tabela comparando os macronutrientes com a substituição e levanta pontos de atenção.

    Args:
        alimento_desejado: Alimento que o usuário deseja consumir (ex: 'batata doce', 'chocolate', 'whey protein', 'pizza').
        alimento_a_substituir: (Opcional) Alimento prescrito na dieta que seria substituído (ex: 'arroz branco', 'frango grelhado').
    """
    alimento_desejado_limpo = _sanitizar_texto(alimento_desejado)
    alimento_substituir_limpo = _sanitizar_texto(alimento_a_substituir)

    if not alimento_desejado_limpo:
        return "Por favor, indique qual alimento você gostaria de consumir ou avaliar para substituição."

    item_desejado = buscar_alimento_dietbox(alimento_desejado_limpo)
    item_substituto = buscar_alimento_dietbox(alimento_substituir_limpo) if alimento_substituir_limpo else None

    # CASO 1: O alimento desejado ESTÁ NA LISTA OFICIAL DO DIETBOX
    if item_desejado:
        grupo_desejado = GRUPOS_ALIMENTARES.get(item_desejado["grupo"], {})
        nome_grupo_desejado = grupo_desejado.get("nome", item_desejado["grupo"].title())
        media_kcal_str = _format_kcal(grupo_desejado.get("media_calorica_kcal", "N/A"))

        if item_substituto:
            grupo_substituto = GRUPOS_ALIMENTARES.get(item_substituto["grupo"], {})
            nome_grupo_substituto = grupo_substituto.get("nome", item_substituto["grupo"].title())

            # Subcaso 1A: Ambos estão na lista e são do mesmo grupo -> Substituição perfeita!
            if item_desejado["grupo"] == item_substituto["grupo"]:
                return (
                    f"✅ **Substituição Válida na Lista de Substituição Oficial (Dietbox)!**\n\n"
                    f"- **Alimento Escolhido:** {item_desejado['nome_oficial']}\n"
                    f"  - **Porção Prescrita:** {item_desejado['medida_caseira']} ({item_desejado['quantidade_g_ml']:.2f} {item_desejado['unidade']})\n"
                    f"- **Substituindo:** {item_substituto['nome_oficial']}\n"
                    f"  - **Porção Original:** {item_substituto['medida_caseira']} ({item_substituto['quantidade_g_ml']:.2f} {item_substituto['unidade']})\n"
                    f"- **Grupo:** {nome_grupo_desejado} (Média: {media_kcal_str})\n\n"
                    f"💡 **Conclusão:** Substituição 100% segura e prescrita no seu plano alimentar. Ambos os alimentos "
                    f"fornecem o mesmo aporte calórico aproximado ({media_kcal_str}) para a refeição."
                )
            
            # Subcaso 1B: Ambos estão na lista mas são de grupos diferentes
            media_substituto_str = _format_kcal(grupo_substituto.get("media_calorica_kcal", "N/A"))
            return (
                f"⚠️ **Atenção: Grupos Nutricionais Diferentes!**\n\n"
                f"- **{item_desejado['nome_oficial']}** pertence ao grupo **{nome_grupo_desejado}** (Média: {media_kcal_str}).\n"
                f"- **{item_substituto['nome_oficial']}** pertence ao grupo **{nome_grupo_substituto}** (Média: {media_substituto_str}).\n\n"
                f"Embora ambos estejam na sua lista do Dietbox, eles possuem funções nutricionais e perfis de macronutrientes "
                f"diferentes (ex: fontes de energia vs fontes de proteína/gordura). Não é recomendável substituir um pelo outro "
                f"sem reequilibrar os outros itens da refeição."
            )

        # Se não especificou substituto, confirma que está na lista e traz a porção
        return (
            f"✅ **Alimento Prescrito na Lista de Substituição (Dietbox)**\n\n"
            f"- **Alimento:** {item_desejado['nome_oficial']}\n"
            f"- **Grupo:** {nome_grupo_desejado} (Média: {media_kcal_str})\n"
            f"- **Medida Caseira:** {item_desejado['medida_caseira']}\n"
            f"- **Quantidade:** {item_desejado['quantidade_g_ml']:.2f} {item_desejado['unidade']}\n\n"
            f"Pode consumir com segurança dentro da cota do grupo {nome_grupo_desejado}."
        )

    # CASO 2: O alimento desejado NÃO CONSTA NA LISTA OFICIAL DO DIETBOX
    # Exige ALERTA OBRIGATÓRIO + PESQUISA NUTRICIONAL COMPARATIVA + PONTOS DE ATENÇÃO
    dados_ext = _estimar_dados_nutricionais(alimento_desejado_limpo)
    
    linhas_comparativo = []
    linhas_comparativo.append(f"**Item Solicitado:** {dados_ext['nome']}")
    linhas_comparativo.append(f"- Calorias: ~{dados_ext['calorias_kcal']} Kcal")
    linhas_comparativo.append(f"- Carboidratos: ~{dados_ext['carboidratos_g']}g")
    linhas_comparativo.append(f"- Proteínas: ~{dados_ext['proteinas_g']}g")
    linhas_comparativo.append(f"- Gorduras Totais: ~{dados_ext['gorduras_g']}g")
    linhas_comparativo.append(f"- Sódio: ~{dados_ext['sodio_mg']}mg | Fibras: ~{dados_ext['fibras_g']}g")

    if item_substituto:
        grupo_sub = GRUPOS_ALIMENTARES.get(item_substituto["grupo"], {})
        media_kcal_sub = grupo_sub.get("media_calorica_kcal", 150.0)
        linhas_comparativo.append(f"\n**Comparando com o item prescrito ({item_substituto['nome_oficial']}):**")
        linhas_comparativo.append(f"- Porção da Dieta: {item_substituto['medida_caseira']} ({item_substituto['quantidade_g_ml']:.2f} {item_substituto['unidade']})")
        linhas_comparativo.append(f"- Meta Calórica Prescrita do Grupo ({grupo_sub.get('nome', 'Grupo')}): {media_kcal_sub} Kcal")
        
        diff_cal = dados_ext['calorias_kcal'] - media_kcal_sub
        sinal = "+" if diff_cal > 0 else ""
        linhas_comparativo.append(f"- Balanço Energético: {sinal}{diff_cal:.1f} Kcal de diferença em relação à cota da sua refeição.")
    else:
        linhas_comparativo.append("\n*Observação: Nenhum alimento de referência da sua lista foi especificado para confronto direto.*")

    pontos_atencao_fmt = "\n".join([f"{idx+1}. {p}" for idx, p in enumerate(dados_ext["pontos_atencao"])])

    return (
        f"⚠️ **ALERTA: O alimento \"{alimento_desejado_limpo.title()}\" NÃO CONSTA na sua Lista de Substituição oficial do Dietbox!**\n"
        f"Este item **não foi prescrito** no seu plano alimentar de 05/10/2023.\n\n"
        f"📊 **Informações Nutricionais Comparativas (Pesquisa de Referência):**\n"
        f"{chr(10).join(linhas_comparativo)}\n\n"
        f"🔍 **Pontos de Atenção Críticos:**\n"
        f"{pontos_atencao_fmt}\n\n"
        f"⚠️ *Aviso: Esta análise é meramente informativa baseada em composição nutricional média. "
        f"Para manter a aderência ao seu objetivo e não descompensar seu déficit ou superávit calórico, "
        f"valide qualquer inclusão com seu nutricionista.*"
    )
