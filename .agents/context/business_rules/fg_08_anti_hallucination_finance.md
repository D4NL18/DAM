# Regras de Negócio: FG-08 (Governança Anti-Alucinação & Consulta Confiável de Gastos)

## Objetivo
Erradicar alucinações e respostas com dados fictícios no assistente DAM quando questionado sobre dados do usuário, garantindo que consultas financeiras (resumos por categoria, detalhamento de gastos) sejam atendidas com dados reais da coleção `finances` do Firestore, idênticos ao dashboard web.

---

## Regras de Negócio (P-0800)

### P-0801: Factualidade Absoluta e Proibição Terminante de Alucinação
1. O assistente DAM é estritamente proibido de inventar, supor, simular ou gerar dados fictícios/exemplos sobre finanças, transações, valores, tarefas, compromissos ou qualquer outro dado pessoal do usuário.
2. Sempre que o usuário fizer perguntas que dependem de registros do sistema, a IA deve invocar a ferramenta correspondente (`consultar_resumo_gastos`).
3. Se a ferramenta retornar que não há registros ou se a busca for vazia, a IA DEVE responder com clareza e honestidade que nenhum registro foi encontrado no banco de dados para os parâmetros solicitados.
4. É proibido inventar valores ou desculpar-se gerando exemplos fictícios sem solicitação explícita.

### P-0802: Roteamento Semântico Completo no ToolsDispatcher
1. O regex de intenção do domínio `finance` deve abranger todas as variações naturais de consultas de gastos:
   - "resumo dos valores de gastos por categoria"
   - "gastos em setembro" / "gastos no mês passado"
   - "quais gastos entraram como moradia?" / "o que gastei com alimentação?"
   - Termos: `gasto`, `gastos`, `gastando`, `gastei`, `despesa`, `despesas`, `categoria`, `categorias`, `fatura`, `extrato`, `valores de gastos`.
2. Ao detectar intenção financeira, o dispatcher deve:
   - Fornecer as ferramentas `consultar_resumo_gastos`, `registrar_gasto`, `dividir_conta_restaurante`.
   - Injetar as regras `financial_rules.py` via `PromptComposer`.

### P-0803: Motor de Consulta de Gastos Alinhado ao Dashboard (`consultar_resumo_gastos`)
1. **Fonte de Verdade Unificada:** A consulta deve ler a coleção `finances` e isolar os dados estritamente pelo usuário autenticado (`effective_user` / `UserContext.get_user_id()`).
2. **Critério Temporal Fiel ao Dashboard:**
   - Suporte a `mes` e `ano`. Se o usuário pedir "setembro" no ano de 2026, consultar `mes=9`, `ano=2026`.
   - Avaliar os campos `date`, `created_at` e `timestamp` com parsing resiliente (ISO 8601 string ou objeto datetime do Firestore).
3. **Filtro de Despesas:**
   - Excluir transações do tipo `income` (receitas), considerando apenas despesas (`expense_variable`, `expense_fixed` ou ausência de tipo).
4. **Detalhamento por Categoria:**
   - Adicionar o parâmetro opcional `categoria: Optional[str] = None` à ferramenta `consultar_resumo_gastos`.
   - Se `categoria` for especificada (ex: "moradia"):
     - Filtrar transações com correspondência insensível a maiúsculas/minúsculas e acentos (incluindo mapeamento semântico se aplicável, ex: "moradia" casa com "Casa" ou "Moradia").
     - Retornar o total gasto na categoria e a listagem de cada despesa (descrição, valor formatado em R$, data no formato dd/mm/aaaa, forma de pagamento).
     - Se nenhuma transação existir, retornar mensagem explícita: "ℹ️ Não encontrei registros de gastos na categoria '{categoria}' para {período}."
   - Se `categoria` for omitida:
     - Retornar o resumo macro idêntico ao dashboard: Total Geral gasto, Total por Categoria (valor e percentual ordenados do maior para o menor), Total por Forma de Pagamento e Maiores Gastos.
