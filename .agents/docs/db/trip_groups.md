# Coleção: `trip_groups`

## 📋 Propósito

Armazena **grupos de viagem** para divisão de despesas ao estilo Splitwise. Cada documento representa um grupo com participantes. Funciona com `trip_expenses` para o algoritmo de Debt Minimization.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **FG-03 – Splitwise de Viagens** | Finanças | `criar_grupo_viagem()` grava; `adicionar_despesa_viagem()` e `calcular_fechamento_viagem()` lêem |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/trip_groups/{nome_viagem_lower}`

Document ID é o nome da viagem em minúsculas (ex: `"floripa 2026"`).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String` | Sim | Mesmo valor do Document ID |
| `nome_viagem` | `String` | Sim | Nome com capitalização original (ex: `"Floripa 2026"`) |
| `participantes` | `Array<String>` | Sim | Lista de nomes. Mínimo 2 participantes |
| `created_at` | `String (ISO 8601)` | Sim | Data/hora de criação em UTC |

---

## 🔗 Relacionamentos

| Relação | Tipo | Descrição |
|---|---|---|
| `trip_groups` → `trip_expenses` | 1:N lógico | Relacionamento por `trip_expenses.nome_viagem == trip_groups.nome_viagem` |

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Mínimo 2 participantes** | Criação com menos de 2 participantes é rejeitada |
| **Deduplicao de participantes** | Lista passa por `dict.fromkeys()` para remover duplicatas |
| **Upsert por nome** | `.set()` sobrescreve grupo existente se mesmo nome for usado |
| **Correspondência case-insensitive** | Comparação de participantes feita em lowercase |

---

## 🗂️ Índices Necessários

Nenhum — buscas por Document ID.

---

## 🔒 Regras de Segurança

```
match /trip_groups/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Lista de participantes pode crescer dinamicamente: pagadores não-membros são adicionados automaticamente.
- Cache em memória `_MEMORY_TRIP_GROUPS` reduz leituras ao Firestore por sessão.
