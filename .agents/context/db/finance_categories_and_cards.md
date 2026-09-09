# Coleções: `finance_categories` e `finance_cards` (FG-06)

## 📋 Propósito
Armazena as categorias customizadas e cartões/métodos de pagamento de cada usuário do sistema, permitindo personalização, edição de nomes e associação de cores para gráficos e badges.

---

## 1. Coleção `finance_categories`
**Path no Firestore:** `/finance_categories/{doc_id}`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | String | Identificador único |
| `name` | String | Nome da categoria (ex: "Mercado", "Carro", "Oliver") |
| `color` | String | Código hexadecimal da cor (ex: "#3B82F6") |
| `userId` | String | Identificador do usuário proprietário |
| `created_at` | String / Timestamp | Data de cadastro |

---

## 2. Coleção `finance_cards`
**Path no Firestore:** `/finance_cards/{doc_id}`

| Campo | Tipo | Descrição |
|---|---|---|
| `id` | String | Identificador único |
| `name` | String | Nome do cartão/conta (ex: "Nubank Ultravioleta", "Itaú Débito") |
| `type` | String | Tipo: `"credito"`, `"debito"`, `"beneficio"` ou `"outro"` |
| `userId` | String | Identificador do usuário proprietário |
| `created_at` | String / Timestamp | Data de cadastro |
