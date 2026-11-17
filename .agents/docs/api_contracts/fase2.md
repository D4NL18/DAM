# Contratos de API (Fase 2 - Dashboard)

Este documento define os contratos de API RESTful expostos pelo **Spring Boot (Core API)** e consumidos pelo **Angular (Frontend)**.

## Base URL
`/api/v1`

---

## 1. Módulo de Saúde (Health)

### 1.1 Obter Resumo de Saúde
Retorna os dados agregados de saúde para um período específico.

- **Endpoint:** `GET /health/summary`
- **Query Params:**
  - `startDate` (obrigatório, ISO-8601 YYYY-MM-DD)
  - `endDate` (obrigatório, ISO-8601 YYYY-MM-DD)
- **Response (200 OK):**
```json
{
  "totalSteps": 45000,
  "avgHeartRate": 72,
  "totalActiveEnergyBurned": 2100.5,
  "dailyRecords": [
    {
      "date": "2024-03-01",
      "steps": 10000,
      "activeEnergyBurned": 500
    },
    {
      "date": "2024-03-02",
      "steps": 8500,
      "activeEnergyBurned": 420
    }
  ]
}
```

---

## 2. Módulo de Finanças (Finance)

### 2.1 Obter Resumo Financeiro Mensal
Retorna a agregação de despesas por categoria e o total gasto no mês.

- **Endpoint:** `GET /finance/monthly-summary`
- **Query Params:**
  - `year` (obrigatório, numérico, ex: 2024)
  - `month` (obrigatório, numérico 1-12, ex: 3)
- **Response (200 OK):**
```json
{
  "totalSpent": 3500.75,
  "currency": "BRL",
  "expensesByCategory": [
    {
      "category": "Alimentação",
      "amount": 1200.00
    },
    {
      "category": "Transporte",
      "amount": 400.00
    },
    {
      "category": "Lazer",
      "amount": 600.00
    }
  ],
  "recentTransactions": [
    {
      "id": "tx_123",
      "date": "2024-03-05T14:30:00Z",
      "description": "Supermercado Extra",
      "amount": 250.00,
      "category": "Alimentação"
    }
  ]
}
```

### 2.2 Listar Transações
Retorna a lista de transações com paginação.

- **Endpoint:** `GET /finance/transactions`
- **Query Params:**
  - `page` (opcional, default 0)
  - `size` (opcional, default 20)
  - `category` (opcional, string)
- **Response (200 OK):**
```json
{
  "content": [
    {
      "id": "tx_123",
      "date": "2024-03-05T14:30:00Z",
      "description": "Supermercado Extra",
      "amount": 250.00,
      "category": "Alimentação",
      "type": "EXPENSE"
    }
  ],
  "page": 0,
  "size": 20,
  "totalElements": 45,
  "totalPages": 3
}
```

---

## Tratamento de Erros (Global)
Respostas de erro seguirão o padrão RFC 7807 (Problem Details for HTTP APIs).

- **Response (400 Bad Request / 500 Internal Server Error):**
```json
{
  "type": "about:blank",
  "title": "Invalid Request",
  "status": 400,
  "detail": "O parâmetro 'startDate' é obrigatório.",
  "instance": "/api/v1/health/summary"
}
```
