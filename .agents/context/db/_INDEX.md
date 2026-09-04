# Dicionario de Dados: Firebase Firestore (DAM)

## Visao Geral

O DAM (Digital Autonomous Manager) utiliza o **Firebase Firestore (NoSQL - Spark Plan)** como banco de dados principal.
O Firestore opera com **colecoes e documentos** ao inves de tabelas relacionais.
Nao existem migrations SQL tradicionais — o schema e flexivel e evolui com o codigo.

## Principios Arquiteturais

- **NoSQL Document Store:** Dados organizados em colecoes de documentos JSON.
- **Sem JOINs:** Relacionamentos sao resolvidos em memoria nas camadas de Service (Python/Java).
- **Sem Agregacoes Nativas:** SUM, AVG, GROUP BY sao feitos em memoria no FastAPI ou Spring Boot.
- **Admin SDK Only:** Todo acesso ao Firestore e feito exclusivamente pelos backends via Firebase Admin SDK. Clientes nao tem acesso direto.
- **Plano Spark (Gratuito):** Limite de 50.000 leituras/dia exige uso criterioso de cache.

---

## Catalogo de Colecoes

| Colecao | Dominio | Proposito Resumido |
|---|---|---|
| [`chat_logs`](./chat_logs.md) | Plataforma Core | Historico de conversas; contexto injetado no LLM |
| [`finances`](./finances.md) | Financas | Lancamentos financeiros (despesas e receitas) |
| [`health_metrics`](./health_metrics.md) | Saude | Metricas do Apple Health (passos, calorias, sono) |
| [`notes_reminders`](./notes_reminders.md) | Gestao Pessoal | Anotacoes pessoais e lembretes agendados |
| [`item_locations`](./item_locations.md) | Gestao Pessoal | Memoria espacial: localizacao de objetos fisicos |
| [`vault_credentials`](./vault_credentials.md) | Seguranca | Cofre de senhas criptografado (AES/Fernet) |
| [`trip_groups`](./trip_groups.md) | Financas | Grupos de viagem para rateio de despesas |
| [`trip_expenses`](./trip_expenses.md) | Financas | Despesas individuais por viagem (Debt Minimization) |
| [`gift_ideas`](./gift_ideas.md) | Entretenimento | Ideias de presentes vinculadas a pessoas e datas |
| [`anime_watchlist`](./anime_watchlist.md) | Entretenimento | Lista de animes sincronizada com AniList |
| [`user_addresses`](./user_addresses.md) | Utilitarios | Enderecos favoritos com apelidos semanticos |
| [`briefing_logs`](./briefing_logs.md) | Plataforma Core | Registro de idempotencia do Morning Briefing |
| [`conversation_cache`](./conversation_cache.md) | Plataforma Core | Cache L2 de respostas do LLM com TTL por dominio |
| [`gcp_billing_snapshots`](./gcp_billing_snapshots.md) | Financas/FinOps | Snapshot do ultimo alerta de billing do GCP |

---

## Colecoes de Cache Externas (Referencia)

| Colecao | Usado em | Descricao |
|---|---|---|
| `streaming_cache` | `streaming_tool.py` | Cache de disponibilidade de filmes/series no streaming |

---

## Mapeamento por Dominio Funcional

### Gestao Pessoal & Rotina
- `chat_logs` — Contexto de conversas
- `notes_reminders` — Notas e lembretes
- `item_locations` — Memoria espacial
- `briefing_logs` — Idempotencia do briefing

### Financas & Gastos
- `finances` — Transacoes financeiras
- `trip_groups` — Grupos de viagem
- `trip_expenses` — Despesas de viagem
- `gcp_billing_snapshots` — Custos de infraestrutura

### Saude & Bem-Estar
- `health_metrics` — Metricas do Apple Health

### Entretenimento & Lazer
- `anime_watchlist` — Tracker de animes
- `gift_ideas` — Curador de presentes

### Utilitarios & Seguranca
- `vault_credentials` — Cofre de senhas
- `user_addresses` — Enderecos favoritos

### Plataforma Core
- `conversation_cache` — Cache semantico do LLM

---

## Estrategia de Cache

O projeto usa **3 camadas de cache** para minimizar leituras faturadas ao Firestore:

1. **L1 — Memoria em Processo (Python dicts / threading.RLock):** Latencia microsegundos. Nao persiste entre restarts.
2. **L2 — Firestore Persistente:** Latencia milissegundos. Persiste entre restarts.
3. **L3 — Caffeine Cache (Spring Boot):** Reduz leituras do Java ao Firestore nos endpoints do Dashboard.

---

## Indices Compostos Criticos

| Colecao | Campos | Ordem | Feature |
|---|---|---|---|
| `chat_logs` | `remoteJid` + `timestamp` | ASC + DESC | PC-01, PC-02 |
| `finances` | `timestamp` | ASC | FG-01, FG-05 |
| `health_metrics` | `date` | ASC | SB-01, SB-02, SB-03 |
| `trip_expenses` | `nome_viagem` | ASC | FG-03 |
| `user_addresses` | `user_jid` | ASC | US-08 |

---

*Documentacao gerada em 04/09/2026 - DAM DBA Documentation v1.0*
