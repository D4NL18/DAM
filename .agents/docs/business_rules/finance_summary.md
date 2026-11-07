# Regras de Negócio: FG-05 Resumo Consolidado de Gastos por Cartão e Categoria

**Código da Feature:** `FG-05`  
**Domínio:** Finanças & Gastos  
**Coleção Firestore:** `finances`

---

## 1. Visão Geral
Atender prontamente a dúvidas do usuário sobre o estado financeiro do mês corrente ou de períodos específicos, fornecendo um resumo executivo sintetizado, agrupado por métodos de pagamento (cartões) e por categorias, sem sobrecarregar a interface do WhatsApp com listas extensas de compras.

---

## 2. Regras de Negócio (RN-FIN)

### RN-FIN-005: Determinação da Janela Temporal
- Quando o usuário fizer uma pergunta aberta (ex: *"como tão meus gastos esse mês?"*, *"quanto gastei?"*), o sistema deve utilizar automaticamente o **mês e ano correntes**.
- Se o usuário especificar um mês anterior (ex: *"gastos de julho"* ou *"mês 7"*), o sistema deve filtrar as despesas daquele intervalo mensal.
- Se o usuário solicitar dias recentes (ex: *"últimos 10 dias"*), o sistema deve calcular a partir do timestamp atual subtraindo a quantidade de dias.

### RN-FIN-006: Consolidação por Forma de Pagamento / Cartão
- Todos os registros do período devem ser totalizados nas modalidades estritas do usuário:
  1. `Cartão de Crédito Pessoal`
  2. `Cartão de Crédito Secundário`
  3. `Cartão de Débito` (inclui pagamentos Pix)
- Deve exibir o valor total e o percentual correspondente sobre o montante do período.

### RN-FIN-007: Consolidação por Categoria
- Agrupar e somar as despesas por categoria (`Alimentação`, `Transporte`, `Lazer`, `Serviços`, `Saúde`, etc.).
- Exibir a listagem ordenada de forma decrescente pelo volume financeiro (as categorias com maior gasto primeiro).

### RN-FIN-008: Formatação Sintética e Resumida
- **Proibição de despejo de extrato completo:** Para não poluir o chat do WhatsApp, a ferramenta não deve retornar uma lista completa de todas as compras.
- Deve apresentar:
  - Cabeçalho com o mês de referência.
  - Total geral gasto e quantidade de lançamentos.
  - Bloco de divisão por cartões.
  - Bloco de divisão por categorias.
  - Destaque rápido das **Top 3 maiores despesas** (descrição e valor).
- Caso o período não possua registros, retornar aviso amigável:
  `ℹ️ Não encontrei registros de gastos para o período solicitado.`
