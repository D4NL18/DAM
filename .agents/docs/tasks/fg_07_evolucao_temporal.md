# Tarefa Técnica: FG-07 Evolução Temporal de Gastos & Receitas (Gráfico Histórico por Períodos)

**Domínio:** Finanças & Gastos  
**Status:** Concluído  
**Responsável:** Equipe DAM  

---

## 1. Descrição Funcional & Critérios de Aceite

### Critérios de Aceite
- [x] **CA-01 (Seletor de Períodos):** O componente deve apresentar botões em formato pílula para `Mês atual`, `3 meses`, `6 meses`, `12 meses` e `Personalizar`. A opção selecionada deve ser destacada visualmente.
- [x] **CA-02 (Card de KPIs):** Deve exibir três métricas: `● Receita` (com bullet verde e seta indicativa), `● Gastos` (com bullet vermelho e seta indicativa) e `Saldo do período` em destaque.
- [x] **CA-03 (Comparativo Temporal):** Abaixo de Receita e Gastos, exibir o percentual comparativo ou o texto `Sem período anterior` caso não haja registros no intervalo anterior.
- [x] **CA-04 (Máscara de Privacidade):** Respeitar a alternância de privacidade (olho): quando ativado, exibir `*****` nos valores de Receita, Gastos e Saldo.
- [x] **CA-05 (Gráfico de Curvas Suaves ECharts):** Gráfico de linha suave com gradientes de preenchimento verde para Receitas e vermelho para Gastos, eixo X com legendas de meses (`Mês Ano`) e eixo Y com valores abreviados em `mil`.
- [x] **CA-06 (Tooltip do Gráfico):** Exibir tooltip formatado com os valores exatos de Receita, Gastos e Saldo ao passar o cursor sobre os pontos.
- [x] **CA-07 (Isolamento Multi-Tenant):** Garantir que os dados pertençam exclusivamente ao usuário autenticado (`X-User-Id`).

---

## 2. Checklist Técnico de Implementação

### Backend (FastAPI)
- [x] Implementar endpoint `GET /api/v1/finance/trends` em `backend_ia/routers/finance.py`:
  - Processamento dos períodos: `current_month`, `3m`, `6m`, `12m` e `custom`.
  - Geração cronológica da lista de meses com preenchimento contínuo.
  - Agregação de `income` e `expenses` mês a mês.
  - Consulta do período anterior para cálculo de variação percentual.
  - Retorno estruturado com `series`, `totalIncome`, `totalExpenses`, `periodBalance`, `previousPeriodComparison`.
- [x] Escrever suíte de testes TDD em `backend_ia/tests/test_finance_trends.py`.

### Frontend (Angular)
- [x] Atualizar `finance-api.service.ts` com o método `getTrends(period, startDate, endDate)` e interfaces.
- [x] Atualizar `finance-dashboard.component.ts`:
  - Estado de período selecionado (`trendPeriod`: `'current_month' | '3m' | '6m' | '12m' | 'custom'`).
  - Configuração do gráfico ECharts de curvas suaves (Spline) com gradientes verticais.
  - Carregamento e recálculo reativo ao mudar o período.
- [x] Atualizar `finance-dashboard.component.html`:
  - Adicionar o seletor de períodos e o card de tendências com os KPIs e o gráfico de área suave.
- [x] Atualizar `finance-dashboard.component.scss`:
  - Estilização do seletor de períodos, cards de KPIs com bullets coloridos, setas circulares e responsividade.
