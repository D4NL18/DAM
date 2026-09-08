# Coleção: `chat_logs`

## 📋 Propósito

Armazena o **histórico de conversas** entre o usuário e o assistente DAM via WhatsApp. Cada documento representa uma mensagem individual (enviada ou recebida). Esta coleção é a **memória de curto prazo** do motor de IA: seu conteúdo é injetado como contexto nas chamadas ao LLM (Gemini), permitindo que a IA mantenha coerência conversacional dentro do dia.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **PC-01 – Motor de IA Multimodal** | Plataforma Core | O `ChatRepository` lê os últimos logs do dia para montar o histórico de contexto antes de cada chamada ao LLM |
| **PC-02 – Gateway WhatsApp** | Plataforma Core | Cada mensagem recebida ou enviada é persistida pelo webhook via `ChatRepository.save_log()` |
| **PC-05 – Sanitização de Logs** | Plataforma Core | Os logs são gravados com mascaramento de dados sensíveis |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/chat_logs/{auto_id}`

Document ID gerado automaticamente via `.add()`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `remoteJid` | `String` | Sim | Identificador do usuário no WhatsApp: `5511999999999@s.whatsapp.net` |
| `fromMe` | `Boolean` | Sim | `true` se enviado pelo DAM; `false` se enviado pelo usuário |
| `text` | `String` | Sim | Conteúdo textual da mensagem |
| `timestamp` | `Timestamp` | Sim | Data e hora UTC do envio/recebimento |
| `messageId` | `String` | Opcional | ID original da mensagem na Evolution API |
| `tokensUsed` | `Number` | Opcional | Tokens consumidos no LLM (apenas para `fromMe = true`) |

---

## 🔗 Relacionamentos

Sem Foreign Keys explícitas. Relacionamento lógico via `remoteJid` que identifica o usuário.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Escopo Temporal** | Leitura aplica filtro `timestamp >= hoje_00:00 UTC`. Apenas mensagens do dia corrente são injetadas como contexto |
| **Limite de Registros** | `get_recent_history()` aplica `.limit(10)`: máximo 10 mensagens por consulta |
| **Ordenação** | Recuperados em `DESCENDING` por `timestamp` e revertidos para ordem cronológica antes de injetar no prompt |
| **Acesso Restrito** | Apenas o backend via Firebase Admin SDK possui acesso |

---

## 🗂️ Índices Necessários

Índice composto obrigatório:

| Campo | Ordem |
|---|---|
| `remoteJid` | Ascendente |
| `timestamp` | Descendente |

---

## 🔒 Regras de Segurança

```
match /chat_logs/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Dados históricos de meses anteriores permanecem no Firestore mas não são consultados pela IA (filtro por dia).
- O campo `messageId` é opcional — só existe quando a mensagem chega via webhook da Evolution API.
