# Coleção: `briefing_logs`

## 📋 Propósito

Garante a **idempotência do Morning Briefing** diário. Cada documento registra que o briefing de uma determinada data foi enviado com sucesso, impedindo duplicatas mesmo que o scheduler dispare múltiplas vezes.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **GP-04 – Morning Briefing Proativo** | Gestão Pessoal | `enviar_briefing_matinal()` verifica esta coleção antes de enviar e registra o sucesso após |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/briefing_logs/briefing_{YYYY-MM-DD}_{userId}` (com retrocompatibilidade para `briefing_{YYYY-MM-DD}` para Daniel).

Document ID determinístico: `"briefing_"` + data em `YYYY-MM-DD` + `"_"` + `userId` (ex: `"briefing_2026-09-08_daniel"`, `"briefing_2026-09-08_lari"`).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `data` | `String` | Sim | Data do briefing no formato `YYYY-MM-DD` (fuso Brasília) |
| `userId` | `String` | Sim | Identificador do usuário (`daniel` ou `lari`) |
| `enviado_em` | `String (ISO 8601)` | Sim | Data/hora UTC em que o briefing foi enviado |
| `destinatario` | `String` | Sim | Número de telefone do destinatário correspondente |
| `status` | `String (Enum)` | Sim | Status do envio: `"sucesso"` |

---

## 🔗 Relacionamentos

Coleção autônoma.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Document ID determinístico** | `briefing_{YYYY-MM-DD}` garante unicidade por dia |
| **Verificação em dois níveis** | Idempotência verificada em memória (`_MEMORY_BRIEFING_LOGS`) e depois no Firestore |
| **Fuso Brasília** | A `data` usa horário de Brasília (UTC-3), mesmo que `enviado_em` seja UTC |
| **Apenas sucesso gravado** | Em caso de falha no envio do WhatsApp, o documento NÃO é criado |

---

## 🗂️ Índices Necessários

Nenhum — acesso sempre por Document ID fixo.

---

## 🔒 Regras de Segurança

```
match /briefing_logs/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- `force=True` bypassa idempotência para reenvios manuais ou testes.
- `_MEMORY_BRIEFING_LOGS` é reiniciado a cada restart do servidor.
