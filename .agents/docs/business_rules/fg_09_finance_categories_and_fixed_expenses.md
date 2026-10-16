# Regras de Negócio: FG-09 (Governança de Categorias, Registro de Receitas/Reembolsos e Recorrência de Despesas Fixas)

## Objetivo
Estabelecer a governança taxonômica rigorosa para transações financeiras no DAM, eliminando alucinações de categorias pelo bot no WhatsApp, fornecendo suporte nativo ao registro e saneamento de receitas e reembolsos como entradas financeiras (`type='income'`), e implementando a projeção automática de despesas fixas recorrentes mês a mês no Dashboard Web e séries temporais.

---

## Regras de Negócio (P-0900)

### P-0901: Alinhamento Estrito de Categorias do Bot & Anti-Alucinação Taxonômica
1. **Taxonomia Autorizada:** O bot e o motor de IA no WhatsApp são terminantemente proibidos de inventar, supor ou criar categorias financeiras arbitrárias (ex.: 'Reembolso', 'Alimentação', 'Presentes', 'Jogos', 'Assinaturas', 'Transporte') durante a classificação de gastos.
2. **Fonte Dinâmica de Categorias:**
   - Para cada usuário (`effective_user` / `UserContext.get_user_id()`), as categorias válidas DEVEM ser carregadas dinamicamente da coleção `finance_categories` no Firestore.
   - Caso o usuário não possua categorias cadastradas ou ocorra indisponibilidade temporária de consulta, o sistema DEVE utilizar como fallback imutável as `DEFAULT_CATEGORIES` oficiais do sistema:
     * `Mercado`, `Carro`, `Oliver`, `Casa`, `Família`, `Farmácia`, `Karen`, `Gatos`, `Lazer`, `Mercadinho`, `iFood`, `Receitas`, `Outros`.
3. **Normalização e Resolução Semântica de Sinônimos:**
   - A correspondência de categorias deve ser insensível a maiúsculas, minúsculas, espaços extras e acentuação gráfica.
   - Se a intenção do usuário referenciar termos análogos, o assistente DEVE mapear deterministicamente para a categoria cadastrada mais próxima:
     * Termos como "supermercado", "comida", "almoço", "jantar", "açougue", "padaria", "alimentação" -> `Mercado` ou `iFood` (se delivery);
     * Termos como "combustível", "gasolina", "etanol", "uber", "estacionamento", "veículo", "mecânico" -> `Carro`;
     * Termos como "remédio", "drogaria", "medicamento", "consulta" -> `Farmácia`;
     * Termos como "aluguel", "condomínio", "energia", "luz", "água", "internet", "moradia" -> `Casa`;
     * Termos como "cinema", "jogo", "games", "passeio", "viagem", "churrasco", "bar" -> `Lazer`.
4. **Resolução de Incerteza para 'Outros':**
   - Caso uma despesa não coincida com nenhuma categoria cadastrada ou seus sinônimos oficiais, ela DEVE ser categorizada obrigatoriamente como `Outros`.
   - É vedado ao bot salvar categorias criadas na hora. Novas categorias só podem ser criadas pelo usuário através do Dashboard Web.
5. **Injeção Factual no Prompt:**
   - As instruções de finanças (`financial_rules.py`) injetadas no Gemini DEVEM explicitar a lista fechada de categorias válidas do usuário para que o Function Calling do modelo gere apenas valores válidos.

---

### P-0902: Registro Nativo de Receitas e Reembolsos (`type='income'`, `category='Receitas'`)
1. **Natureza Contábil de Entrada:** Todas as operações financeiras que representem entrada de capital — incluindo reembolsos, estornos, devoluções de compras, salários, freelas, pagamentos recebidos e transferências Pix a favor do usuário — DEVEM ser tratadas estritamente como **Receitas**.
2. **Tool de Registro de Receita:**
   - O assistente no WhatsApp DEVE dispor de ferramenta nativa (ex.: `registrar_receita`) ou suporte a parâmetros contábeis com os seguintes campos persistidos na coleção `finances`:
     * `userId`: identificador isolado do usuário autenticado.
     * `description`: descrição clara da receita/reembolso (ex.: "Reembolso passagem aérea", "Salário", "Estorno compra duplicada").
     * `amount`: valor numérico positivo (`amount > 0`). É expressamente proibido registrar valores negativos.
     * `type`: obrigatoriamente fixado como `"income"`.
     * `category`: obrigatoriamente fixado como `"Receitas"`.
     * `payment_method` / `paymentMethod`: conta ou método de recebimento (ex.: "Conta Corrente", "Cartão de Débito", "Pix") com fallback para "Cartão de Débito / Pix".
     * `date` e `timestamp`: data e hora da operação no formato UTC/ISO 8601.
3. **Proibições Estruturais:**
   - É terminantemente proibido registrar reembolsos ou estornos como despesa com valor negativo (`amount < 0`).
   - É terminantemente proibido atribuir a categoria `"Reembolso"` ou criar uma categoria com este nome para classificar despesas.
4. **Comunicação no Chat:** O retorno ao usuário deve confirmar o registro da receita/reembolso de forma transparente, indicando que o valor foi somado às receitas e ao saldo líquido do Dashboard.

---

### P-0903: Saneamento Automático de Dados Legados Corrompidos (Self-Healing Migration)
1. **Detecção de Anomalias Legadas:**
   - O sistema DEVE conter rotina idempotente de auto-cura (migração/saneamento) que localize na coleção `finances` registros corrompidos pertencentes a qualquer uma das condições:
     * Documentos cuja `category` seja `"Reembolso"` (em qualquer variação de caixa/espaço);
     * Documentos cuja descrição mencione termos evidentes de reembolso/estorno (ex.: `"reembolso"`, `"estorno"`, `"devolução"`) e cujo `type` esteja como despesa (`expense_variable`, `expense_fixed`) ou ausente;
     * Documentos com `amount < 0`.
2. **Transformação Reparadora:**
   - A rotina de saneamento deve atualizar os documentos localizados no Firestore para:
     * `type` = `"income"`;
     * `category` = `"Receitas"`;
     * `amount` = `abs(float(amount))` (valor absoluto positivo).
3. **Idempotência e Segurança:**
   - A execução da rotina deve ser 100% segura e idempotente, podendo ser executada em background ou no startup sem alterar transações já sadias.
   - A rotina deve emitir log estruturado contendo a quantidade de registros migrados por `userId`, sem vazar PII nos logs.

---

### P-0904: Recorrência Automática de Despesas Fixas Mês a Mês no Dashboard e Tendências
1. **Conceito de Despesa Fixa:** Transações cadastradas com `type == "expense_fixed"` representam compromissos recorrentes e contínuos do usuário (ex.: aluguel, condomínio, internet, mensalidades, assinaturas).
2. **Projeção em Tempo de Consulta (Read-Time Projection):**
   - Nos endpoints `/api/v1/finance/dashboard` e `/api/v1/finance/trends`, qualquer despesa fixa ativa registrada em um mês $M_0$ (onde $M_0 \le M_{alvo}$) DEVE ser automaticamente projetada e incluída no cálculo do mês consultado $M_{alvo}$, mesmo que não tenha sido recadastrada fisicamente naquele mês.
3. **Prevenção de Duplicação:**
   - Se o usuário já tiver inserido uma ocorrência explícita daquela mesma despesa fixa no mês $M_{alvo}$ (mesmo ID ou identificador de recorrência), o sistema não deve duplicar o registro na agregação.
4. **Ciclo de Vida e Cancelamento:**
   - Se uma despesa fixa for marcada como inativa (`active == False`) ou excluída pelo usuário em um mês de encerramento $M_{fim}$, ela NÃO deve ser projetada para meses $M > M_{fim}$.
5. **Impacto Consolidado:**
   - As despesas fixas recorrentes devem ser somadas no `totalFixed`, impactar o `totalSpent`, ser deduzidas do `balance`, constar no Donut Chart (`expensesByCategory`) e ser listadas na tabela `transactions` do Dashboard com identificador visual de despesa fixa recorrente (`isRecurring: True`).
   - No endpoint `/trends`, as séries históricas e projeções mensais devem computar a carga de despesas fixas em cada mês correspondente a partir da data de início.
