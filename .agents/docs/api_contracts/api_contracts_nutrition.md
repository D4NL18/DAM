# Contratos de Integração: SB-04 Ferramentas Nutricionais

## 1. Ferramenta `consultar_lista_substituicao`

### Assinatura Python
```python
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
```

### Formato de Retorno Esperado
- Se grupo: Cabeçalho com o nome do grupo, média calórica e listagem com medidas caseiras e gramaturas.
- Se alimento: Nome do alimento, grupo pertencente, medida caseira, gramatura e lista de 3 a 5 alternativas diretas no mesmo grupo calórico.
- Se não encontrado: Mensagem informativa avisando que o item não foi encontrado na lista com sugestão de avaliar substituição.

---

## 2. Ferramenta `avaliar_substituicao_alimento`

### Assinatura Python
```python
def avaliar_substituicao_alimento(alimento_desejado: str, alimento_a_substituir: str = "") -> str:
    """
    Avalia a substituição de um alimento por outro com base na Lista de Substituição oficial do Dietbox.
    Se o alimento_desejado NÃO constar na lista oficial, emite um ALERTA OBRIGATÓRIO, pesquisa dados
    nutricionais na internet/tabela comparando os macronutrientes com a substituição e levanta pontos de atenção.

    Args:
        alimento_desejado: Alimento que o usuário deseja consumir (ex: 'batata doce', 'chocolate', 'whey protein', 'pizza').
        alimento_a_substituir: (Opcional) Alimento prescrito na dieta que seria substituído (ex: 'arroz branco', 'frango grelhado').
    """
```

### Formato de Retorno Esperado (Item na Lista)
```markdown
✅ **Substituição Válida na Lista de Substituição Oficial (Dietbox)**

- **Alimento Desejado:** Batata Doce Cozida (Grupo: Carboidratos - Média: 150 Kcal)
- **Porção Prescrita:** 2 Pedaços Médios (200,00 g)
- **Substituindo:** Arroz Branco Cozido (4 Colheres de Sopa / 100,00 g)
- **Equivalência Calórica:** Ambos fornecem a mesma cota calórica (~150 Kcal) do grupo de Carboidratos.
```

### Formato de Retorno Esperado (Item Fora da Lista)
```markdown
⚠️ **ALERTA: O alimento "[Nome]" NÃO CONSTA na sua Lista de Substituição oficial do Dietbox!**
Este item não faz parte dos alimentos prescritos no seu plano alimentar.

📊 **Comparativo Nutricional:**
...

🔍 **Pontos de Atenção:**
1. Densidade Calórica...
2. Macronutrientes...
3. Impacto Glicêmico/Sódio...

⚠️ *Aviso: Esta análise é meramente informativa. Valide qualquer troca fora do plano com seu nutricionista.*
```
