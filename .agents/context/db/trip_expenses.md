# Coleção: `trip_expenses`

## 📋 Propósito

Armazena as **despesas individuais** de cada grupo de viagem. Cada documento representa um gasto pago por um participante e dividido entre membros. Alimenta o algoritmo de Debt Minimization que calcula o menor número de transferências Pix para quitar todas as dívidas.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **FG-03 – Splitwise de Viagens** | Finanças | `adicionar_despesa_viagem()` grava; `calcular_fechamento_viagem()` faz query por `nome_viagem` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/trip_expenses/{auto_id}`

Document ID gerado automaticamente via `.add()`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | UUID v4 gerado pelo backend |
| `nome_viagem` | `String` | Sim | Nome da viagem — chave de relacionamento com `trip_groups` |
| `descricao` | `String` | Sim | Descrição do gasto (ex: `"Jantar Frutos do Mar"`) |
| `valor` | `Number (Float)` | Sim | Valor total arredondado para 2 casas decimais |
| `pagador` | `String` | Sim | Nome do participante que efetuou o pagamento |
| `participantes_divisao` | `Array<String>` | Sim | Nomes dos participantes que dividem este gasto |
| `created_at` | `String (ISO 8601)` | Sim | Data/hora do registro em UTC |

---

## 🔗 Relacionamentos

| Campo | Tipo | Descrição |
|---|---|---|
| `nome_viagem` | N:1 lógico | Referencia `trip_groups.nome_viagem` por igualdade de string |

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Valor > 0** | Despesas com valor <= 0 são rejeitadas |
| **Divisão igualitária por padrão** | Se `participantes_divisao` for omitido, divide entre todos os membros |
| **Valor arredondado** | `round(float(valor), 2)` antes de salvar |
| **Imutabilidade** | Despesas não podem ser editadas após registro |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `nome_viagem` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /trip_expenses/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Algoritmo **Debt Minimization** (dois ponteiros guloso) minimiza número de transferências Pix.
- Relacionamento por igualdade de string. Recomenda-se migrar para UUID de grupo em versões futuras.
