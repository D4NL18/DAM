# Coleção: `gcp_billing_snapshots`

## 📋 Propósito

Armazena o **snapshot mais recente** dos dados de consumo e orçamento do Google Cloud Platform (GCP), recebidos via alertas do Pub/Sub. Funciona como cache singleton do último alerta de billing processado, permitindo que o motor de IA consulte custos atuais sem dependência de APIs externas.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **FG-04 – GCP Billing & Monitoramento FinOps** | Finanças | Webhook `/api/billing-alert` grava via `billing.py`; `gcp_billing_tool.py` lê o documento `latest` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/gcp_billing_snapshots/latest`

Coleção com **único documento** de ID fixo `"latest"` (singleton).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `cost_amount` | `Number (Float)` | Sim | Valor gasto atual no período do orçamento |
| `budget_amount` | `Number (Float)` | Sim | Valor total do orçamento configurado no GCP |
| `currency` | `String` | Sim | Moeda (ex: `"BRL"`, `"USD"`) |
| `budget_name` | `String` | Sim | Nome do orçamento no GCP Billing (ex: `"GCP Cloud"`) |
| `percentual` | `Number (Float)` | Sim | Percentual de consumo: `(cost_amount / budget_amount) * 100` |
| `updated_at` | `String (ISO 8601)` | Sim | Data/hora UTC da última atualização |

---

## 🔗 Relacionamentos

Coleção autônoma. Origem: **GCP Pub/Sub** → webhook FastAPI.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Documento singleton** | Apenas `"latest"`. Alertas novos sobrescrevem via `.set()` |
| **Sem histórico** | Apenas o último alerta é mantido. Histórico fica no GCP Console |
| **Proteção divisão por zero** | Se `budget_amount == 0`, `percentual` é calculado como `0` |

---

## 🗂️ Índices Necessários

Nenhum — acesso por Document ID fixo `"latest"`.

---

## 🔒 Regras de Segurança

```
match /gcp_billing_snapshots/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Alerta também dispara mensagem WhatsApp imediata via `WhatsAppService.send_text()`.
- Endpoint `/api/billing-alert` protegido pelo sistema de autenticação de webhooks.
