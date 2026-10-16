# Entidade / Feature: FG-09 - Governança de Categorias, Registro de Receitas/Reembolsos e Recorrência de Despesas Fixas

Este documento centraliza todo o planejamento, as especificações e as etapas de execução para as tarefas relacionadas à feature FG-09.

## 1. Dúvidas Resolvidas (Especificação)

- **Dúvida 1:** Como lidar com novas categorias que o usuário cria no Dashboard Web via modal? O bot do WhatsApp deve conhecê-las?
  - **Decisão:** Sim. O bot deve carregar dinamicamente as categorias ativas do usuário na coleção `finance_categories` (`userId == effective_user`) com fallback para as `DEFAULT_CATEGORIES`. Dessa forma, se o usuário criar "Investimentos" no dashboard, o bot saberá utilizá-la sem hardcode.
- **Dúvida 2:** O que fazer quando o usuário pedir para registrar um gasto com termo vago ou inexistente (ex.: "comprei um jogo por R$ 50")?
  - **Decisão:** O bot NÃO pode alucinar ou criar a categoria "Jogos" se ela não existir. Ele aplica sinônimos pré-definidos (jogo -> `Lazer`). Se não houver sinônimo plausível, categoriza obrigatoriamente como `Outros` (regra P-0901).
- **Dúvida 3:** Como reembolsos corporativos ou estornos de cartão devem ser computados contabilmente? Devem subtrair da despesa ou somar em receita?
  - **Decisão:** Pela regra P-0902, serão registrados como `type="income"` e `category="Receitas"`, com valor positivo. No Dashboard e no backend, o Saldo líquido é `totalIncome - totalSpent`, mantendo a consistência matemática e eliminando anomalias contábeis de valores negativos no banco.
- **Dúvida 4:** Para a recorrência automática de despesas fixas (P-0904), devemos gerar novos documentos físicos no Firestore para cada mês futuro ou projetar na leitura?
  - **Decisão:** Projeção dinâmica em tempo de consulta (read-time projection) nos endpoints `/dashboard` e `/trends`. Isso evita poluir o banco de dados com centenas de documentos pré-gerados, garante que qualquer alteração de valor na despesa fixa se reflita imediatamente nos meses futuros e simplifica o ciclo de vida.

---

## 2. Tarefas e Etapas de Desenvolvimento

### Tarefa 1 (Story 1): Alinhamento Estrito de Categorias no Bot & Anti-Alucinação Taxonômica (P-0901)

**Descritivo Detalhado:**
Garantir que a IA no WhatsApp classifique transações financeiras exclusivamente dentro do catálogo oficial do usuário (`finance_categories`) ou das categorias padrão do sistema (`DEFAULT_CATEGORIES`). Adicionar dicionário de sinônimos/aliases robusto e fallback obrigatório para "Outros" em caso de termos não reconhecidos. Atualizar os prompts em `financial_rules.py` com a lista fechada de categorias e proibição explícita de inventar categorias como "Reembolso", "Alimentação", "Presentes" ou "Jogos".

**Critérios de Aceite:**
- [x] O assistente nunca inventa categorias que não estejam no cadastro do usuário ou nas categorias padrão.
- [x] Frases com termos como "almoço", "mercado", "supermercado" são mapeadas para "Mercado" (ou "iFood" se delivery).
- [x] Frases com termos desconhecidos são mapeadas deterministicamente para "Outros".
- [x] A ferramenta `registrar_gasto` valida a categoria informada contra a lista autorizada e normaliza antes de persistir.
- [x] O prompt do domínio de finanças instrui taxativamente a lista autorizada de categorias.

**Etapas de Execução (Checklist Técnico):**
- [x] **Etapa 1:** Criar função auxiliar `obter_categorias_usuario(user_id)` em `backend_ia/services/tools/finance_tool.py` lendo `finance_categories` com fallback para `DEFAULT_CATEGORIES`.
- [x] **Etapa 2:** Implementar normalizador determinístico de categorias com aliases semânticos expandidos e fallback para "Outros".
- [x] **Etapa 3:** Atualizar `backend_ia/services/prompts/financial_rules.py` com a lista exata de categorias válidas e restrição anti-alucinação taxonômica.

**Audit (Testes e Validação):**
- [x] **Cenário 1:** Chamar `registrar_gasto` com categoria "Supermercado"; deve gravar "Mercado".
- [x] **Cenário 2:** Chamar `registrar_gasto` com categoria inexistente "Jogos"; deve gravar "Lazer" (ou "Outros").
- [x] **Cenário 3:** Usuário sem categorias customizadas; o sistema utiliza as 13 `DEFAULT_CATEGORIES`.

---

### Tarefa 2 (Story 2): Registro e Classificação de Receitas e Reembolsos & Sanitização de Dados Legados (P-0902 e P-0903)

**Descritivo Detalhado:**
Implementar no bot o suporte nativo ao registro de receitas e reembolsos, adicionando a ferramenta `registrar_receita` em `finance_tool.py` e mapeando intenções de recebimento ("recebi pix", "reembolso da empresa", "estorno", "salário") no `ToolsDispatcher`. As transações devem ser gravadas com `type="income"`, `category="Receitas"` e valor positivo. Desenvolver script/serviço de migração e auto-cura para sanear documentos legados corrompidos (category="Reembolso" ou valores negativos).

**Critérios de Aceite:**
- [x] Nova ferramenta `registrar_receita` disponível no WhatsApp registrando com `type="income"`, `category="Receitas"` e `amount > 0`.
- [x] `ToolsDispatcher` captura intenções de receita e reembolso com regex semântico expandido e despacha a ferramenta correta.
- [x] Proibido registrar reembolso como despesa negativa ou criar categoria "Reembolso".
- [x] Rotina de saneamento executável de forma idempotente corrigindo documentos com categoria "Reembolso" ou descrições correlatas para `type="income"` e `category="Receitas"`.

**Etapas de Execução (Checklist Técnico):**
- [x] **Etapa 1:** Implementar a tool `registrar_receita(descricao, valor, metodo_recebimento)` em `finance_tool.py`.
- [x] **Etapa 2:** Registrar a tool no `ToolsDispatcher` e expandir o regex de intenção para palavras como "recebi", "reembolso", "estorno", "salario", "renda".
- [x] **Etapa 3:** Criar script/função de migração `sanear_transacoes_legadas(user_id)` em `backend_ia/services/finance_migration_service.py` corrigindo registros legados.
- [x] **Etapa 4:** Acionar a migração segura no startup da aplicação ou endpoint autenticado de manutenção.

**Audit (Testes e Validação):**
- [x] **Cenário 1:** Mensagem "Recebi reembolso de 120 da passagem via pix"; bot invoca `registrar_receita` com `amount=120.0`, `type='income'`, `category='Receitas'`.
- [x] **Cenário 2:** Registro legado com `category="Reembolso"` e `amount=-50.0`; após saneamento, torna-se `type="income"`, `category="Receitas"` e `amount=50.0`.
- [x] **Cenário 3:** Execução repetida do saneamento não altera transações já saneadas.

---

### Tarefa 3 (Story 3 [PARALLEL]): Recorrência Automática de Despesas Fixas Mês a Mês no Dashboard & Tendências (P-0904)

**Descritivo Detalhado:**
Aprimorar a agregação de dados no endpoint `/api/v1/finance/dashboard` e `/api/v1/finance/trends` em `backend_ia/routers/finance.py`. Ao consultar um mês $M_{alvo}$, o sistema deve buscar despesas ativas do tipo `expense_fixed` cadastradas em qualquer mês anterior ou corrente ($M_0 \le M_{alvo}$) e projetá-las automaticamente para o mês consultado, computando-as em `totalFixed`, `totalSpent`, `balance`, `expensesByCategory` e incluindo na lista de `transactions`.

**Critérios de Aceite:**
- [x] Despesa fixa cadastrada em mês anterior aparece automaticamente no dashboard dos meses subsequentes sem recadastro.
- [x] Valores de despesas fixas projetadas são somados em `totalFixed`, `totalSpent` e deduzidos de `balance`.
- [x] Donut Chart de despesas por categoria reflete o valor das despesas fixas projetadas no mês alvo.
- [x] Despesas fixas excluídas ou desativadas não continuam sendo projetadas para meses após sua inativação.
- [x] Endpoint `/trends` computa as despesas fixas recorrentes em cada mês da série histórica.

**Etapas de Execução (Checklist Técnico):**
- [x] **Etapa 1:** Modificar a lógica de consulta do Firestore em `get_finance_dashboard` para coletar despesas fixas históricas ($date \le data\_fim\_mes\_alvo$) e deduplicar ocorrências já existentes no mês alvo.
- [x] **Etapa 2:** Incluir as fixas projetadas nos acumuladores (`total_fixed`, `category_map`, `transactions` com flag `isRecurring=True`).
- [x] **Etapa 3:** Adaptar `get_finance_trends` para incorporar despesas fixas em cada nó mensal da série histórica.

**Audit (Testes e Validação):**
- [x] **Cenário 1:** Cadastrar despesa fixa "Aluguel R$ 2.000" em Janeiro/2026; ao consultar Fevereiro/2026 e Março/2026, "Aluguel" deve constar com R$ 2.000 em `totalFixed`.
- [x] **Cenário 2:** Consultar filtro `type="expense_fixed"`; despesas fixas recorrentes aparecem listadas na tabela.
- [x] **Cenário 3:** Despesa variável de mês anterior NÃO é projetada para meses seguintes.

---

### Tarefa 4 (Story 4): Validação Integrada, TDD, SecOps e QA

**Descritivo Detalhado:**
Desenvolver suíte de testes automatizados com `pytest` cobrindo todas as 4 regras de negócio (P-0901 a P-0904), garantindo isolamento estrito multi-tenant por `userId`, validação de regressão na API de dashboard e tendências, e auditoria de segurança SecOps.

**Critérios de Aceite:**
- [x] Testes unitários para normalização de categorias e proibição de categorias arbitrárias (P-0901).
- [x] Testes para registro de receita e saneamento idempotente de dados legados (P-0902 e P-0903).
- [x] Testes de projeção de despesas fixas recorrentes em `/dashboard` e `/trends` (P-0904).
- [x] Isolamento de dados multi-tenant validado (dados de `daniel` nunca projetados ou saneados para outros usuários).

**Etapas de Execução (Checklist Técnico):**
- [x] **Etapa 1:** Criar `backend_ia/tests/test_finance_categories_and_fixed_expenses.py` com cenários de teste TDD.
- [x] **Etapa 2:** Executar suíte completa do pytest e garantir 100% de aprovação.
- [x] **Etapa 3:** Atualizar `STATE.md` marcando a etapa do Analista como concluída.

**Audit (Testes e Validação):**
- [x] **Cenário 1:** `pytest backend_ia/tests/test_finance_categories_and_fixed_expenses.py` passa sem erros.
- [x] **Cenário 2:** Suíte de regressão de finanças `backend_ia/tests/test_anti_hallucination_and_finance_query.py` continua 100% verde.
