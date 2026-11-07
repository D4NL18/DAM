# Coleção: `anime_watchlist`

## 📋 Propósito

Armazena a **lista de animes** do usuário, sincronizada bidireccionalmente com o AniList (perfil `Tonho123`). Cada documento representa um anime com status de progresso, data do próximo episódio e metadados do AniList. Consultada pelo briefing matinal para alertas de lançamentos.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **EL-01 – Anime Tracker & AniList** | Entretenimento | Sincronização completa, incremento de episódios e conclusão via `anime_tracker_tool.py` |
| **EL-02 – Calendário de Animes** | Entretenimento | Consulta de próximos episódios e contagem regressiva |
| **GP-04 – Morning Briefing** | Gestão Pessoal | `briefing_service.py` lista animes com lançamentos no dia |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/anime_watchlist/{doc_id}`

Document ID composto como `anilist_{anilist_id}` (ex: `"anilist_21"`).

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `anilist_id` | `Number (Integer)` | Sim | ID numérico do anime no AniList |
| `titulo_principal` | `String` | Sim | Título principal (preferência: romaji) |
| `titulo_ingles` | `String` | Opcional | Título em inglês |
| `status_transmissao` | `String (Enum)` | Sim | `"RELEASING"`, `"FINISHED"`, `"NOT_YET_RELEASED"`, `"CANCELLED"`, `"HIATUS"` |
| `total_episodios` | `Number (Integer)` | Opcional | Total de episódios (null para séries em andamento) |
| `status_usuario` | `String (Enum)` | Sim | `"assistindo"`, `"planejo_assistir"`, `"concluido"`, `"pausado"` |
| `ultimo_episodio_visto` | `Number (Integer)` | Sim | Número do último episódio assistido |
| `nota_usuario` | `Number (Float)` | Opcional | Nota do usuário (escala AniList: 0-100) |
| `proximo_episodio` | `Map` | Opcional | Dados do próximo episódio (null se não houver) |
| `site_url` | `String` | Opcional | URL da página do anime no AniList |
| `origem` | `String` | Sim | `"AniList Sync"` ou `"Manual"` |
| `updated_at` | `String (ISO 8601)` | Sim | Data/hora da última sincronização |

### Sub-documento: `proximo_episodio`

| Campo | Tipo | Descrição |
|---|---|---|
| `episodio` | `Number (Integer)` | Número do próximo episódio |
| `airing_at` | `Number (Unix Timestamp)` | Timestamp Unix do horário de exibição |
| `data_formatada` | `String` | Data formatada no fuso de Brasília (ex: `"04/09 às 14:30"`) |
| `tempo_restante_segundos` | `Number (Integer)` | Segundos restantes até o lançamento |

---

## 🔗 Relacionamentos

Coleção autônoma. Relacionamento externo com **AniList GraphQL API** via `anilist_id`.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Sincronização via AniList** | Importa automaticamente todas as entradas da lista do usuário. Dados sobrescritos a cada sync |
| **Upsert por `doc_id`** | `.set()` sobrescreve documento existente |
| **Alerta de lançamento** | Briefing compara `proximo_episodio.data_formatada` com a data de hoje |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `status_usuario` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /anime_watchlist/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Cache em memória `_MEMORY_WATCHLIST` sincronizado com o Firestore.
- `proximo_episodio` é null para animes finalizados ou sem data confirmada.
