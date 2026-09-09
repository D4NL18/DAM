# Regras de Negócio: FG-06 Dashboard Avançado de Gastos & Gestão de Categorias e Cartões

**Código da Feature:** `FG-06`  
**Domínio:** Finanças & Gastos  
**Coleções Firestore:** `finances`, `finance_categories`, `finance_cards`

---

## 1. Regras de Negócio (P-XXX)

### Temporalidade e Visualização
- **P-001 (Navegação Mensal Padrão):** O sistema DEVE carregar inicialmente os dados correspondentes ao mês e ano correntes. A navegação por meio dos botões `<` e `>` deve avançar ou retroceder exatamente um mês civil por clique, recalculando instantaneamente transações, fatias do gráfico e saldos totais.
- **P-002 (Ocultação de Valores / Modo Privacidade):** O botão de alternância de visibilidade (ícone de olho) DEVE mascarar todos os valores monetários da tela com caracteres protegidos (`••••••`) e restaurá-los com o valor real (`R$ X.XXX,XX`) ao ser desativado.

### Tipagem de Transações & Abas
- **P-003 (Separação Rígida de Abas):** O dashboard DEVE oferecer 3 abas principais: `Receita`, `Despesa fixa` e `Despesa variável`.
  - Ao selecionar `Despesa variável`, a tabela e o gráfico de categorias devem listar exclusivamente itens com `type == 'expense_variable'`.
  - Ao selecionar `Despesa fixa`, devem listar exclusivamente itens com `type == 'expense_fixed'`.
  - Ao selecionar `Receita`, devem listar exclusivamente transações de entrada (`type == 'income'`).
- **P-004 (Cálculo do Saldo do Período):** O rodapé do dashboard DEVE exibir o saldo líquido do mês selecionado:
  $$\text{Saldo} = \text{Total Receitas} - (\text{Total Despesas Fixas} + \text{Total Despesas Variáveis})$$
  Se o valor for negativo, DEVE ser formatado com sinal negativo e tipografia em destaque vermelho (ex: `- R$ 17.914,39`). Se positivo ou zero, em tom neutro ou positivo.
- **P-005 (Campos Auxiliares de Transação):** Cada transação DEVE suportar:
  - `date`: Data do lançamento (formato ISO / YYYY-MM-DD).
  - `description`: Nome/descrição da despesa/receita.
  - `amount`: Valor numérico positivo.
  - `category`: Nome da categoria associada.
  - `payment_method`: Nome do cartão ou forma de pagamento (ex: `Cartão de Crédito Pessoal`, `Débito/Pix`).
  - `installment` (opcional): Indicador de parcelamento (ex: `2/3`, `2/9`).
  - `owner` / `user_tag` (opcional): Identificador do titular ou responsável (ex: `Christian`, `Daniel`).

### Granularidade e Filtros de Categorias
- **P-006 (Granularidade e Cores Consistentes):** Cada categoria DEVE possuir uma cor hexadecimal associada. A cor utilizada no bullet da tabela (`● Categoria`) DEVE ser rigorosamente idêntica à cor utilizada no arco correspondente do gráfico Donut e na legenda lateral.
- **P-007 (Filtro por Categorias):** O botão `Filtro` DEVE abrir uma seleção permitindo filtrar uma ou múltiplas categorias simultaneamente. Ao aplicar o filtro, a tabela e o total acumulado devem refletir exclusivamente as categorias selecionadas.
- **P-008 (Interatividade Donut-Tabela):** O clique em qualquer segmento do gráfico Donut ou em qualquer item da legenda DEVE alternar o filtro para destacar apenas aquela categoria na tabela de transações.

### Gestão de Categorias e Cartões
- **P-009 (Adição de Categoria):** O usuário DEVE poder adicionar uma nova categoria informando nome obrigatório (não vazio) e selecionando uma cor a partir de uma paleta de cores ou seletor hexadecimal. Não são permitidas categorias duplicadas com o mesmo nome para o mesmo usuário.
- **P-010 (Renomeação de Categoria):** Ao renomear uma categoria, o sistema DEVE atualizar o nome e a cor correspondentes.
- **P-011 (Exclusão Segura de Categoria):** Ao excluir uma categoria, o sistema DEVE solicitar confirmação. Se houver transações vinculadas à categoria excluída, essas transações NÃO devem ser apagadas; sua categoria DEVE ser migrada para `"Outros"`.
- **P-012 (Gestão de Cartões / Formas de Pagamento):** O usuário DEVE poder cadastrar, renomear e excluir cartões/métodos de pagamento (com tipo: Crédito, Débito, Benefício ou Outro).
- **P-013 (Isolamento Multi-Tenant):** Todas as categorias customizadas, cartões e transações DEVEM ser rigorosamente isoladas pelo `userId` do usuário autenticado.
