# Tarefa Técnica: FG-06 Dashboard Avançado de Gastos & Gestão de Categorias e Cartões

**Domínio:** Finanças & Gastos  
**Status:** Em Andamento  
**Responsável:** Equipe DAM  

---

## 1. Descrição Funcional & Critérios de Aceite

### Critérios de Aceite
- [x] **CA-01 (Fidelidade Visual):** O dashboard deve reproduzir os elementos da imagem fornecida: header com saudação, "Orçamento", ícone de olho para mascarar valores, seletor de mês `< Mês de Ano >`, abas em estilo pílula arredondada (`Receita`, `Despesa fixa`, `Despesa variável`), botões de ação (`Importar extrato`, `Limpar lançamentos`), tabela com colunas estilizadas e bullets coloridos, gráfico Donut com legenda de percentual e link `Gerenciar categorias`, e barra inferior com total do período.
- [x] **CA-02 (Ocultação de Valores):** Clicar no olho mascara todos os valores na tela com `••••••` e mantém o estado de privacidade até o próximo clique.
- [x] **CA-03 (Navegação Temporal Mensal):** Clicar nas setas `<` e `>` navega pelos meses e atualiza dinamicamente as transações e o gráfico.
- [x] **CA-04 (Abas Segmentadas):** Alternar entre `Receita`, `Despesa fixa` e `Despesa variável` filtra as transações correspondentes na tabela e no Donut.
- [x] **CA-05 (Filtro por Categorias):** Clicar em `Filtro` abre seletor com as categorias ativas para filtrar transações na tabela.
- [x] **CA-06 (Interatividade do Donut):** Clicar numa fatia do Donut ou num item da legenda filtra a tabela pela categoria selecionada.
- [x] **CA-07 (Gerenciador de Categorias):** Permitir adicionar novas categorias com escolha de cor, renomear existentes e excluir com migração segura para 'Outros'.
- [x] **CA-08 (Gerenciador de Cartões):** Permitir adicionar novos cartões, renomear e excluir cartões existentes.
- [x] **CA-09 (Adição e Edição de Transações):** Permitir adicionar novas transações (escolhendo tipo, valor, data, categoria, cartão, parcelas e titular) e editar transações existentes.

---

## 2. Checklist Técnico de Implementação

### Backend (FastAPI)
- [x] Criar rotas no `backend_ia/routers/finance.py`:
  - `GET /api/v1/finance/dashboard`: consolidação com parâmetros de ano, mês, tipo e categoria.
  - `POST /api/v1/finance/transactions`: inclusão de transação.
  - `PUT /api/v1/finance/transactions/{id}`: edição de transação.
  - `DELETE /api/v1/finance/transactions/{id}`: exclusão de transação.
  - `GET /api/v1/finance/categories`: listagem de categorias com fallback para defaults do sistema.
  - `POST /api/v1/finance/categories`: criação de categoria.
  - `PUT /api/v1/finance/categories/{id}`: renomeação e troca de cor.
  - `DELETE /api/v1/finance/categories/{id}`: exclusão com fallback seguro para 'Outros'.
  - `GET /api/v1/finance/cards`: listagem de cartões com fallback para defaults.
  - `POST /api/v1/finance/cards`: cadastro de novo cartão.
  - `PUT /api/v1/finance/cards/{id}`: renomeação de cartão.
  - `DELETE /api/v1/finance/cards/{id}`: exclusão de cartão.
- [x] Atualizar CORS em `backend_ia/main.py` para permitir `PUT` e `DELETE`.
- [x] Registrar router de finanças em `backend_ia/main.py`.
- [x] Criar testes unitários em `backend_ia/tests/test_finance_dashboard_v2.py` cobrindo 100% dos novos endpoints.

### Frontend (Angular)
- [x] Atualizar `finance-api.service.ts` com interfaces completas e métodos HTTP para todas as rotas acima.
- [x] Atualizar `finance-dashboard.component.ts`:
  - Lógica de controle de mês/ano.
  - Alternância de abas (`expense_variable`, `expense_fixed`, `income`).
  - Toggle de visibilidade com máscara `••••••`.
  - Configuração do gráfico Donut ECharts com raio estilizado, tooltip e paleta dinâmica.
  - Estados dos modais de Adicionar Transação, Editar Transação, Filtro de Categorias e Gerenciador de Categorias/Cartões.
- [x] Atualizar `finance-dashboard.component.html`:
  - Replicar fielmente o design do mockup com cards, pills, tabela estilizada, modais e barra inferior.
- [x] Atualizar `finance-dashboard.component.scss`:
  - Estilização moderna respeitando o `DESIGN_SYSTEM.md`, soft shadows, tipografia refinada e sem "cara de bootstrap".
