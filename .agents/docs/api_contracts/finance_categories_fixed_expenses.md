# Contrato de API: Governança de Categorias, Transações e Despesas Fixas (FG-09)

## 1. Visão Geral
Este contrato formaliza as interfaces de integração REST da API de Finanças (`/api/v1/finance`), contemplando a projeção dinâmica de despesas fixas recorrentes, a governança taxonômica de categorias, o registro de receitas/reembolsos e a rotina de saneamento.

Todas as respostas seguem o padrão rígido de Envelope:
```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-10-16T12:00:00Z",
    "version": "v1"
  }
}
```

---

## 2. Endpoints

### 2.1 Obter Dashboard Financeiro Mensal (com Projeção de Fixas)
Retorna os dados consolidados do mês especificado, incluindo receitas, despesas variáveis, despesas fixas (físicas e projetadas dinamicamente com `isRecurring=true`), saldo líquido e detalhamento por categoria.

- **Método:** `GET`
- **Caminho:** `/api/v1/finance/dashboard`
- **Headers:**
  - `X-User-Id` (opcional, string): Identificador do usuário (default: "daniel").
- **Query Parameters:**
  - `year` (int, default: ano corrente): Ano da competência (ex.: 2026).
  - `month` (int, default: mês corrente): Mês da competência (1 a 12).
  - `type` (string, opcional): Filtro por tipo (`income`, `expense_fixed`, `expense_variable`, `total`).
  - `category` (string, opcional): Filtro por categoria específica.

#### Resposta de Sucesso (HTTP 200 OK):
```json
{
  "data": {
    "totalSpent": 3450.50,
    "totalIncome": 8500.00,
    "totalFixed": 2100.00,
    "totalVariable": 1350.50,
    "balance": 5049.50,
    "currency": "BRL",
    "expensesByCategory": [
      {
        "category": "Casa",
        "amount": 2000.00,
        "percentage": 57.9,
        "color": "#15803d"
      },
      {
        "category": "Mercado",
        "amount": 950.50,
        "percentage": 27.5,
        "color": "#2563eb"
      },
      {
        "category": "Lazer",
        "amount": 500.00,
        "percentage": 14.6,
        "color": "#06b6d4"
      }
    ],
    "transactions": [
      {
        "id": "proj_abc123_2026_10",
        "date": "2026-10-05T12:00:00Z",
        "description": "Aluguel Apartamento",
        "amount": 2000.00,
        "category": "Casa",
        "categoryColor": "#15803d",
        "type": "expense_fixed",
        "paymentMethod": "Cartão de Débito / Pix",
        "installment": null,
        "owner": "",
        "isRecurring": true,
        "originId": "abc123"
      },
      {
        "id": "tx_var_987",
        "date": "2026-10-14T18:30:00Z",
        "description": "Compras do Mês",
        "amount": 950.50,
        "category": "Mercado",
        "categoryColor": "#2563eb",
        "type": "expense_variable",
        "paymentMethod": "Cartão de Crédito Pessoal",
        "installment": null,
        "owner": "",
        "isRecurring": false
      }
    ]
  },
  "meta": {
    "timestamp": "2026-10-16T12:00:00Z",
    "year": 2026,
    "month": 10,
    "totalTransactions": 2
  }
}
```

---

### 2.2 Criar Transação (Despesa ou Receita)
Registra uma nova transação financeira no banco de dados.

- **Método:** `POST`
- **Caminho:** `/api/v1/finance/transactions`
- **Headers:**
  - `X-User-Id` (opcional, string)
- **Request Body (JSON):**
```json
{
  "description": "Reembolso Deslocamento Cliente",
  "amount": 185.50,
  "category": "Receitas",
  "type": "income",
  "paymentMethod": "Cartão de Débito / Pix",
  "installment": null,
  "owner": null,
  "date": "2026-10-16T10:00:00Z"
}
```

#### Regras de Validação:
- `amount`: Deve ser estritamente maior que 0 (`amount > 0`). Valores negativos geram HTTP 422.
- `type`: Deve pertencer ao enum `["income", "expense_variable", "expense_fixed"]`.
- `category`: Deve coincidir com uma das categorias válidas do usuário ou ser normalizada deterministicamente. Se `type == "income"`, a categoria deve ser fixada como `"Receitas"`.

#### Resposta de Sucesso (HTTP 201 Created):
```json
{
  "data": {
    "id": "e932b12a-8994-4d2c-87d9-c3d3ec1209ff",
    "userId": "daniel",
    "description": "Reembolso Deslocamento Cliente",
    "amount": 185.50,
    "category": "Receitas",
    "type": "income",
    "paymentMethod": "Cartão de Débito / Pix",
    "installment": null,
    "owner": null,
    "date": "2026-10-16T10:00:00Z",
    "isRecurring": false,
    "created_at": "2026-10-16T12:05:00Z"
  },
  "meta": {
    "timestamp": "2026-10-16T12:05:00Z"
  }
}
```

---

### 2.3 Obter Tendências e Séries Temporais (com Projeção de Fixas)
Retorna séries cronológicas mensais de receitas, despesas e saldo líquido incluindo despesas fixas recorrentes projetadas nos períodos históricos e futuros.

- **Método:** `GET`
- **Caminho:** `/api/v1/finance/trends`
- **Headers:**
  - `X-User-Id` (opcional, string)
- **Query Parameters:**
  - `period` (string, default: `"12m"`): `"current_month"`, `"3m"`, `"6m"`, `"12m"`.

#### Resposta de Sucesso (HTTP 200 OK):
```json
{
  "data": {
    "period": "3m",
    "periodLabel": "Últimos 3 meses",
    "totalIncome": 25500.00,
    "totalExpenses": 10350.00,
    "periodBalance": 15150.00,
    "currency": "BRL",
    "comparison": {
      "hasPreviousPeriod": true,
      "incomeChangePct": 2.5,
      "expenseChangePct": -4.1,
      "comparisonText": "comparado com os 3 meses anteriores"
    },
    "series": [
      {
        "label": "Ago 2026",
        "year": 2026,
        "month": 8,
        "income": 8500.00,
        "expenses": 3450.00,
        "balance": 5050.00
      },
      {
        "label": "Set 2026",
        "year": 2026,
        "month": 9,
        "income": 8500.00,
        "expenses": 3450.00,
        "balance": 5050.00
      },
      {
        "label": "Out 2026",
        "year": 2026,
        "month": 10,
        "income": 8500.00,
        "expenses": 3450.00,
        "balance": 5050.00
      }
    ]
  },
  "meta": {
    "timestamp": "2026-10-16T12:00:00Z",
    "monthsCount": 3
  }
}
```

---

### 2.4 Executar Saneamento de Dados Legados (Manutenção Idempotente)
Endpoint de auto-cura para corrigir documentos legados que contenham categoria "Reembolso", despesas de estorno ou valores negativos.

- **Método:** `POST`
- **Caminho:** `/api/v1/finance/maintenance/sanitize`
- **Headers:**
  - `X-User-Id` (opcional, string)

#### Resposta de Sucesso (HTTP 200 OK):
```json
{
  "data": {
    "userId": "daniel",
    "totalScanned": 142,
    "remediated": 3,
    "alreadyClean": 139,
    "status": "COMPLETED"
  },
  "meta": {
    "timestamp": "2026-10-16T12:10:00Z"
  }
}
```
