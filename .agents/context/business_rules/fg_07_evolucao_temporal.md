# Regras de Negócio: FG-07 Evolução Temporal de Gastos & Receitas

**Código da Feature:** `FG-07`  
**Domínio:** Finanças & Gastos  
**Coleções Firestore:** `finances`

---

## 1. Regras de Negócio (P-XXX)

### Períodos e Seleção Temporal
- **P-014 (Seletor de Períodos Predefinidos):** O sistema DEVE disponibilizar cinco opções de período: `Mês atual`, `3 meses`, `6 meses`, `12 meses` e `Personalizar`. Ao selecionar qualquer período predefinido, o sistema recalcula instantaneamente os dados do gráfico e os KPIs sem recarregar a página inteira.
- **P-015 (Agrupamento Temporal Cronológico):** Para períodos multimensais (`3 meses`, `6 meses`, `12 meses` ou intervalo customizado), as transações DEVEM ser agrupadas mês a mês e ordenadas em ordem cronológica ascendente (do mês mais antigo para o mês atual/mais recente). Meses sem movimentações dentro do intervalo DEVEM ser preenchidos com valor 0.0 para manter a continuidade das curvas no gráfico.

### Métricas e KPIs do Período
- **P-016 (Métricas Superiores do Card):** O cabeçalho do card de evolução temporal DEVE consolidar três métricas fundamentais do período selecionado:
  1. `Receita`: Soma de todos os lançamentos com `type == 'income'`.
  2. `Gastos`: Soma de todos os lançamentos de despesa (`type == 'expense_variable'` ou `type == 'expense_fixed'` ou despesas sem tipo definido).
  3. `Saldo do período`: $\text{Receita Total} - \text{Gastos Totais}$. Se positivo, exibido com destaque verde; se negativo, exibido com destaque vermelho.
- **P-017 (Cálculo Comparativo com Período Anterior):** O sistema DEVE calcular as receitas e despesas ocorridas na janela de tempo imediatamente anterior de mesma duração (ex: para 12 meses, calcula os 12 meses anteriores).
  - Se houver dados no período anterior, exibe a variação percentual (ex: `+12% vs período anterior`, com seta de tendência condizente).
  - Se não houver dados no período anterior ($Total = 0$), exibe a mensagem amigável `"Sem período anterior"`.
- **P-018 (Modo de Privacidade com Asteriscos):** Quando o botão de alternância de privacidade (olho) estiver ativado (ocultando valores), os valores monetários de Receita, Gastos e Saldo do Período DEVEM ser mascarados estritamente com asteriscos `*****`, espelhando a interface de referência.

### Estilização e Interatividade do Gráfico
- **P-019 (Gráfico de Área Suave Spline):** O gráfico DEVE renderizar curvas bezier suaves (`smooth: true`):
  - Curva verde (`#16a34a`) com preenchimento em gradiente vertical translúcido para `Receita`.
  - Curva vermelha (`#dc2626`) com preenchimento em gradiente vertical translúcido para `Gastos`.
  - Eixo X com meses e anos formatados em português (`Mar 2026`, `Abr 2026`, etc.).
  - Eixo Y abreviado de forma limpa (ex: `0`, `45 mil`, `90 mil`, `135 mil`, `180 mil`).
  - Tooltip interativo com exibição precisa do mês, valor de receita, valor de gastos e saldo líquido ao passar o mouse ou tocar na tela.

### Segurança e Governança
- **P-020 (Isolamento Multi-Tenant):** O endpoint e a agregação DEVEM respeitar o header `X-User-Id` (Daniel e Lari), garantindo que um usuário nunca acesse dados ou históricos financeiros do outro.
