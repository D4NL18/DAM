# Coleção: `finances`

## 📋 Propósito

Armazena os **lançamentos financeiros** do usuário registrados via WhatsApp pelo Agente Financeiro. Cada documento é uma transação com categoria, valor, forma de pagamento e data. Coleção central do domínio financeiro, consultada pelo Dashboard Web (Spring Boot) e pelo motor de IA para resumos e análises.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **FG-01 – Gestão Multicartão** | Finanças | Registra gastos via `registrar_gasto()` em `finance_tool.py` |
| **FG-05 – Resumo Consolidado de Gastos** | Finanças | `consultar_resumo_gastos()` agrega por cartão e categoria |
| **PC-07 – Dashboard Web Angular** | Plataforma Core | Spring Boot (`FinanceController`) lê para o endpoint `/finance/monthly-summary` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/finances/{auto_id}`

Document ID gerado automaticamente via `.add()`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String` | Sim | UUID v4 gerado pelo backend |
| `description` | `String` | Sim | Nome do estabelecimento ou descrição (ex: `"Almoço Ifood"`) |
| `amount` | `Number (Float)` | Sim | Valor da transação (positivo para despesas) |
| `category` | `String` | Sim | Categoria inferida pela IA (ex: `"Alimentação"`, `"Transporte"`) |
| `payment_method` | `String (Enum)` | Sim | Método de pagamento normalizado (3 valores possíveis) |
| `date` | `String (ISO 8601)` | Sim | Data em formato ISO string (legível por humanos) |
| `timestamp` | `Timestamp` | Sim | Timestamp Firestore nativo para range queries |

---

## 🔗 Relacionamentos

Coleção autônoma. Agrupamento feito em memória no Java/Python.

---

## 📏 Constraints e Regras de Negócio

### Enum: `payment_method`

| Valor Persistido | Mapeamentos de Entrada |
|---|---|
| `Cartão de Crédito Pessoal` | "credito", "crédito", "pessoal" |
| `Cartão de Crédito Secundário` | "one", "pai", "secundar", "compartilh", "familiar" |
| `Cartão de Débito` | "pix", "debito", "débito" |

> **Regra Inviolável:** Nenhum gasto é registrado sem identificação do método de pagamento.

| Regra | Descrição |
|---|---|
| **Valores Negativos Ignorados** | `amount <= 0` é descartado no resumo |
| **Dupla representação de data** | `date` (ISO string) para leitura humana; `timestamp` para queries |
| **Categorias livres** | Inferidas pela IA sem vocabulário controlado |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `timestamp` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /finances/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Campos `currency`, `type` (EXPENSE/INCOME) e `receiptUrl` previstos na Fase 2 ainda **não estão implementados**.
- O Spring Boot aplica Caffeine Cache para limitar chamadas ao Firestore (plano gratuito: 50k leituras/dia).
