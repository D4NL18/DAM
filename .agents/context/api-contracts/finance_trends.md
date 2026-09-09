# Contrato de API REST: Tendências e Evolução Temporal de Finanças (FG-07)

## 1. Visão Geral
Este contrato define o endpoint REST para obtenção de séries históricas de receitas e gastos em múltiplos períodos (`current_month`, `3m`, `6m`, `12m`, `custom`), com comparativo do período anterior.

---

## 2. Endpoint `GET /api/v1/finance/trends`

### Parâmetros de Requisição
**Headers:**
- `X-User-Id` (string, opcional): Identificador do usuário (default: `'daniel'`).

**Query Params:**
- `period` (string, opcional, default: `'12m'`): Valores possíveis: `'current_month'`, `'3m'`, `'6m'`, `'12m'`, `'custom'`.
- `startDate` (string ISO, opcional): Data de início para períodos personalizados (ex: `'2026-01-01'`).
- `endDate` (string ISO, opcional): Data de término para períodos personalizados (ex: `'2026-12-31'`).

### Resposta Estruturada (200 OK)
```json
{
  "period": "12m",
  "periodLabel": "Últimos 12 meses",
  "totalIncome": 180000.0,
  "totalExpenses": 142000.0,
  "periodBalance": 38000.0,
  "currency": "BRL",
  "comparison": {
    "hasPreviousPeriod": true,
    "incomeChangePct": 12.5,
    "expenseChangePct": 8.0,
    "comparisonText": "comparado com os 12 meses anteriores"
  },
  "series": [
    {
      "label": "Mar 2026",
      "year": 2026,
      "month": 3,
      "income": 45000.0,
      "expenses": 32000.0,
      "balance": 13000.0
    },
    {
      "label": "Abr 2026",
      "year": 2026,
      "month": 4,
      "income": 62000.0,
      "expenses": 41000.0,
      "balance": 21000.0
    }
  ]
}
```
