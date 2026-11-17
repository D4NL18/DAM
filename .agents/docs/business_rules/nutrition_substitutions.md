# Regras de Negócio: Guia Nutricional & Lista de Substituição Inteligente (Dietbox)

**Código da Feature:** `SB-04`  
**Domínio:** Saúde & Bem-Estar  
**Referência do Plano:** Lista de Substituição (Novo modelo Dietbox - Samuel Meller Silva - 05/10/2023)

---

## 1. Visão Geral
O objetivo desta funcionalidade é permitir que o usuário consulte se pode consumir ou substituir determinados alimentos da sua dieta com segurança, transparência e rigor nutricional. O DAM deve usar como verdade absoluta a lista de 132 alimentos prescritos pelo nutricionista, alertando de forma ostensiva caso qualquer item sugerido não conste na lista oficial e fornecendo análises comparativas fundamentadas em dados nutricionais externos com pontos de atenção claros.

---

## 2. Regras de Negócio (RN-NUT)

### RN-NUT-001: Verificação de Pertinência na Lista Oficial
- Ao receber uma dúvida sobre consumo ou substituição alimentar, o sistema deve normalizar o termo (remover acentos, pontuação e converter para minúsculas) e buscar no catálogo dos 7 grupos oficiais da prescrição:
  1. **Carboidratos** (Média: 150 Kcal - 13 itens)
  2. **Carnes e Ovos** (Média: 190 Kcal - 17 itens)
  3. **Frutas** (Média: 70 Kcal - 33 itens)
  4. **Laticínios** (Média: 120 Kcal - 17 itens)
  5. **Legumes e Verduras** (Média: 15 Kcal - 36 itens)
  6. **Leguminosas** (Média: 55 Kcal - 6 itens)
  7. **Óleos e Gorduras** (Média: 73 Kcal - 10 itens)
- Se o alimento pertencer a um desses grupos, a equivalência é considerada **Válida e Prescrita**.

### RN-NUT-002: Cálculo de Equivalência no Mesmo Grupo
- A substituição padrão deve ocorrer preferencialmente entre itens do **mesmo grupo calórico**.
- A resposta deve informar:
  - Nome do alimento consultado.
  - Medida caseira oficial prescrita.
  - Gramatura ou volume oficial em g/ml.
  - Média calórica do grupo de referência.
  - Exemplos de 3 a 5 alternativas diretas do mesmo grupo com suas respectivas medidas caseiras e gramaturas.

### RN-NUT-003: Alerta Mandatório para Alimentos Fora da Lista
- Se o alimento **NÃO** for encontrado na lista oficial de substituição:
  - O sistema **NÃO PODE** simplesmente autorizar ou tratar o alimento como equivalente direto.
  - O sistema **DEVE** emitir um alerta explícito e imediato:
    `⚠️ ALERTA: O alimento "[Nome]" NÃO consta na sua Lista de Substituição oficial do Dietbox!`
  - O sistema deve deixar nítido que o item não faz parte da conduta nutricional prescrita no plano.

### RN-NUT-004: Pesquisa Nutricional Comparativa e Pontos de Atenção
- Para alimentos fora da lista, o sistema acionará automaticamente a busca/base de dados nutricionais confiáveis (ex: Tabela TACO / USDA / Web Search sanitizada).
- O sistema deve comparar os macronutrientes do alimento desejado com:
  - O alimento que o usuário pretendia substituir (se informado); ou
  - O grupo alimentar mais similar (ex: se pediu "chocolate", comparar com o grupo de Frutas/Carboidratos ou informar a discrepância calórica e de gorduras).
- O sistema deve elencar no mínimo 3 **Pontos de Atenção**, cobrindo quando aplicável:
  1. **Densidade Calórica & Volume:** Impacto na saciedade (ex: volume pequeno com muitas calorias).
  2. **Composição de Macronutrientes:** Excesso de gordura saturada, açúcares simples ou carência de proteínas/fibras.
  3. **Índice/Carga Glicêmica & Pico de Insulina:** Velocidade de absorção e oscilação de fome.
  4. **Sódio & Ultraprocessamento:** Conservantes, aditivos ou retenção hídrica.

### RN-NUT-005: Disclaimer e Segurança Clínica
- Toda e qualquer resposta envolvendo itens não prescritos ou substituições atípicas deve finalizar com um aviso clínico:
  *Obs: Esta é uma análise comparativa informativa baseada em composição nutricional média. Qualquer alteração ou inclusão fora do seu plano deve ser validada diretamente com o seu nutricionista.*
