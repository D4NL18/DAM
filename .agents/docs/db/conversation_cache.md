# Coleção: `conversation_cache`

## 📋 Propósito

Implementa a **camada L2 de cache semântico** de respostas do motor de IA. Evita chamadas redundantes ao LLM (Gemini) para perguntas repetidas dentro do TTL, economizando tokens e reduzindo latência. Cada documento armazena a resposta de uma query com metadados de validade e domínio de volatilidade.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **PC-08 – Otimização de Tokens & Cache Inteligente** | Plataforma Core | `CacheService` (L2 Firestore) armazena e recupera respostas via `cache_service.py` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/conversation_cache/{cache_key}`

Document ID: hash SHA-256 truncado de `{remote_jid}:{query_normalized}`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `remote_jid` | `String` | Sim | JID do usuário associado à resposta cacheada |
| `query_normalized` | `String` | Sim | Texto da query normalizado (sem acentos, lowercase) |
| `media_hash` | `String (SHA-256)` | Não | Hash SHA-256 do binário da imagem/áudio/doc quando houver mídia |
| `response_text` | `String` | Sim | Texto completo da resposta gerada pelo LLM |
| `domain` | `String (Enum)` | Sim | Domínio de volatilidade da query |
| `created_at` | `String (ISO 8601)` | Sim | Data/hora de criação |
| `expires_at` | `String (ISO 8601)` | Sim | Data/hora de expiração |
| `ttl_seconds` | `Number (Integer)` | Sim | TTL em segundos aplicado à entrada |

---

## 🔗 Relacionamentos

Coleção autônoma. Relacionamento lógico com usuário via `remote_jid`.

---

## 📏 Constraints e Regras de Negócio

### Enum: `domain` (QueryVolatility)

| Valor | TTL | Descrição |
|---|---|---|
| `"static_informational"` | 43.200s (12h) | Informações estáticas: conversão, receitas, curiosidades |
| `"clash_of_clans"` | 3.600s (1h) | Status de guerras e raids do Clash of Clans |
| `"cs2_esports"` | Dinâmico | TTL calculado pelo horário do próximo jogo. Zero se jogo a menos de 2h |
| `"realtime_volatile"` | 0 (nunca) | Trânsito em tempo real — bypass obrigatório |
| `"state_changing_action"` | 0 (nunca) | Ações de escrita — bypass obrigatório |

| Regra | Descrição |
|---|---|
| **Bypass inviolável** | Trânsito e ações de escrita NUNCA são cacheadas |
| **Invalidação por expiração** | Entradas expiradas ignoradas e removidas on-read em L1 |
| **Não-bloqueante** | Gravação no Firestore com try/except fail-safe |

---

## 🗂️ Índices Necessários

Nenhum — buscas por Document ID.

---

## 🔒 Regras de Segurança

```
match /conversation_cache/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Cache em dois níveis: **L1 memória** (microsegundos) e **L2 Firestore** (milissegundos, persistente).
- Estimativa de tokens economizados: ~1000 tokens por hit + tokens da query e resposta.
- Documentos expirados acumulam no Firestore. Recomenda-se Firestore TTL Policy para limpeza automática.

---
