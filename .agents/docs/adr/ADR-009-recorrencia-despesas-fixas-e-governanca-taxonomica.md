# ADR-009: Projeção em Tempo de Leitura de Despesas Fixas e Governança Taxonômica de Categorias

## Status
Aprovado

## Data
2026-10-16

## Contexto
O ecossistema financeiro do DAM opera com duas frentes principais:
1. Interação conversacional no WhatsApp via LLM (Google Gemini 3.6 Flash) e tools determinísticas.
2. Visualização analítica no Dashboard Web (Angular 17) via API REST no FastAPI (`/api/v1/finance`).

Identificamos três desafios arquiteturais críticos:
1. **Proliferação e Alucinação de Categorias pelo Bot:** O modelo por vezes criava categorias arbitrárias (ex.: 'Reembolso', 'Alimentação', 'Jogos', 'Presentes') ao registrar despesas, desalinhando os gráficos do Dashboard e gerando fragmentação taxonômica.
2. **Tratamento Contábil Inadequado de Reembolsos/Estornos:** Reembolsos corporativos e estornos de cartão eram registrados ora como despesas negativas (`amount < 0`), ora com categoria "Reembolso", quebrando a métrica contábil de Receitas e distorcendo os cálculos de `totalIncome` e `balance`.
3. **Despesas Fixas Estáticas no Dashboard:** Despesas cadastradas como `expense_fixed` (ex.: Aluguel, Internet) ficavam restritas ao mês em que foram criadas fisicamente, exigindo que o usuário recadastrasse mensalmente os mesmos compromissos para que constassem no Dashboard dos meses seguintes.

---

## Decisões Técnicas

### 1. Projeção Dinâmica em Tempo de Leitura (Read-Time Projection) vs. Clonagem Física
- **Decisão:** Adotamos a **projeção dinâmica em tempo de consulta (Read-Time Projection)** nos endpoints `/api/v1/finance/dashboard` e `/api/v1/finance/trends`.
- **Mecanismo:** Ao consultar um mês $M_{alvo}$, o serviço busca despesas ativas do tipo `expense_fixed` cadastradas em qualquer mês $M_0 \le M_{alvo}$. Se não houver registro físico da despesa naquele mês, o backend sintetiza o objeto com `isRecurring = True` e ID idempotente `proj_{originId}_{year}_{month}`.
- **Alternativa Rejeitada:** Criação de rotina Cron/Cloud Scheduler que clona e insere documentos físicos na coleção `finances` todo dia 1º de cada mês.
  * *Motivo da rejeição:* Causa inchaço desnecessário no Firestore (custo FinOps), risco de duplicação caso a rotina falhe ou seja reexecutada, e impossibilidade de refletir retroativamente atualizações de valor ou exclusão em meses futuros sem migrações em massa.

### 2. Governança Taxonômica Dinâmica com Cache L1 em Memória
- **Decisão:** As categorias válidas são resolvidas dinamicamente da coleção `finance_categories` para o usuário ativo (`userId`), com cache L1 em memória (TTL de 300 segundos) e fallback para `DEFAULT_CATEGORIES`.
- **Mecanismo de Aliases:** O assistente aplica normalização fonética e semântica de sinônimos (ex.: "almoço" -> "Mercado"; "gasolina" -> "Carro"; "remédio" -> "Farmácia").
- **Fallback Estrito:** Termos não reconhecidos são deterministicamente mapeados para `"Outros"`. É vedado ao bot criar ou sugerir novas categorias em tempo de execução. Novas categorias só podem ser criadas pelo usuário via Dashboard Web.

### 3. Registro e Padronização Contábil de Receitas e Reembolsos
- **Decisão:** Criação da ferramenta nativa `registrar_receita` em `finance_tool.py` e exposição no `ToolsDispatcher`.
- **Mecanismo:** Toda entrada financeira (reembolsos, salários, freelas, estornos, devoluções) é persistida com `type = "income"`, `category = "Receitas"` e `amount > 0`. Valores negativos são terminantemente rejeitados (`amount = abs(amount)`).

### 4. Saneamento Idempotente de Legados (Self-Healing Migration)
- **Decisão:** Criação de serviço isolado `finance_migration_service.py` que varre transações corrompidas do usuário (categoria "Reembolso", descrições de estorno com tipo despesa ou valores negativos) e as atualiza de forma idempotente para `type = "income"`, `category = "Receitas"` e `amount = abs(amount)`.

---

## Consequências

### Positivas:
- **Consistência Contábil:** O saldo líquido `totalIncome - totalSpent` reflete fielmente as entradas e saídas sem distorções de valores negativos.
- **Dashboard Sempre Atualizado:** Despesas fixas (como aluguel e contas essenciais) já aparecem no primeiro dia de cada mês sem intervenção humana.
- **Zero Alucinação Taxonômica:** O bot opera com lista fechada de categorias, preservando a harmonia das cores e gráficos do frontend.
- **FinOps Otimizado:** Sem inserção em lote de transações futuras no banco de dados; leitura eficiente com cache em memória.

### Negativas / Mitigações:
- **Sobrecarga de Consulta no Dashboard:** A leitura precisa consultar despesas fixas históricas além das transações do mês.
  * *Mitigação:* As despesas fixas de um usuário raramente ultrapassam algumas dezenas de registros; a filtragem em memória no backend FastAPI é executada em $< 5\text{ ms}$.
