# Contrato de API REST: Dashboard Financeiro, Transações, Categorias e Cartões (FG-06)

## 1. Visão Geral
Este contrato define os endpoints REST expostos pelo Backend IA (`backend_ia`) consumidos pelo Dashboard Web Angular (`frontend_dashboard`), garantindo isolamento por `X-User-Id` e tipagem completa.

---

## 2. Endpoints

### 2.1. `GET /api/v1/finance/dashboard`
**Objetivo:** Retorna o resumo consolidado mensal com transações filtradas e agrupamento de categorias para o gráfico Donut.

**Headers:**
- `X-User-Id` (string, opcional): ID do usuário autenticado (padrão: `'daniel'`).

**Query Params:**
- `year` (int, default: ano corrente)
- `month` (int, default: mês corrente)
- `type` (string, opcional): `'expense_variable'`, `'expense_fixed'`, `'income'`, ou omitido para todos.
- `category` (string, opcional): Filtrar por categoria específica.

**Response (200 OK):**
```json
{
  "totalSpent": 17914.39,
  "totalIncome": 25000.00,
  "totalFixed": 8500.00,
  "totalVariable": 9414.39,
  "balance": 7085.61,
  "currency": "BRL",
  "expensesByCategory": [
    { "category": "Mercado", "amount": 5374.32, "percentage": 30.0, "color": "#3B82F6" },
    { "category": "Carro", "amount": 4478.60, "percentage": 25.0, "color": "#EAB308" }
  ],
  "transactions": [
    {
      "id": "tx-123",
      "date": "2026-04-01",
      "description": "Financiamento Song",
      "amount": 2823.00,
      "category": "Carro",
      "categoryColor": "#EAB308",
      "type": "expense_variable",
      "paymentMethod": "Cartão de Crédito Pessoal",
      "installment": null,
      "owner": "Christian"
    }
  ]
}
```

---

### 2.2. `POST /api/v1/finance/transactions`
**Objetivo:** Adicionar nova transação financeira.

**Request Body:**
```json
{
  "description": "Financiamento Song",
  "amount": 2823.00,
  "category": "Carro",
  "type": "expense_variable",
  "paymentMethod": "Cartão de Crédito Pessoal",
  "date": "2026-04-01",
  "installment": "2/3",
  "owner": "Christian"
}
```
**Response (201 Created):** Objeto com a transação salva incluindo o `id` gerado.

---

### 2.3. `PUT /api/v1/finance/transactions/{id}`
**Objetivo:** Editar uma transação existente.

**Request Body:** Mesma estrutura do POST.
**Response (200 OK):** Objeto atualizado.

---

### 2.4. `DELETE /api/v1/finance/transactions/{id}`
**Objetivo:** Excluir uma transação.
**Response (200 OK):** `{"success": true, "id": "..."}`.

---

### 2.5. Gestão de Categorias
- `GET /api/v1/finance/categories`: Retorna lista de categorias cadastradas do usuário (com fallback para as padrão).
- `POST /api/v1/finance/categories`: Cria nova categoria `{"name": "...", "color": "#hex"}`.
- `PUT /api/v1/finance/categories/{id}`: Atualiza nome ou cor `{"name": "...", "color": "#hex"}`.
- `DELETE /api/v1/finance/categories/{id}`: Remove categoria (migrando transações existentes para 'Outros').

---

### 2.6. Gestão de Cartões
- `GET /api/v1/finance/cards`: Retorna cartões do usuário (com fallback para os 3 padrões).
- `POST /api/v1/finance/cards`: Cria novo cartão `{"name": "...", "type": "credito|debito|outro"}`.
- `PUT /api/v1/finance/cards/{id}`: Atualiza nome ou tipo `{"name": "...", "type": "..."}`.
- `DELETE /api/v1/finance/cards/{id}`: Remove cartão.
