# Coleção: `saved_videos`

## 📋 Propósito
Armazena **vídeos salvos das redes sociais** (TikTok, Instagram Reels/Posts, YouTube/Shorts e links externos) catalogados pelo usuário para assistir mais tarde ou para consulta futura por assunto, título ou categoria. Cada registro é isolado por usuário (`userId`).

---

## 🧩 Features que utilizam esta coleção
| Feature | Domínio | Descrição |
|---|---|---|
| **EL-07 – Repositório de Vídeos Salvos** | Entretenimento & Lazer | Salvamento, busca semântica, controle de status (pendente/assistido) e exclusão via WhatsApp. |

---

## 📑 Estrutura do Documento
**Path no Firestore:** `/saved_videos/{video_id}`

Document ID é o UUID v4 gerado pelo backend.

### Campos do Documento

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | Identificador único (UUID v4) |
| `userId` / `user_id` | `String` | Sim | Identificador do usuário proprietário (`"admin"` ou `"user"`) |
| `url` | `String` | Sim | URL completa do vídeo (validada com esquema http/https) |
| `plataforma` | `String (Enum)` | Sim | Plataforma detectada: `"TikTok"`, `"Instagram"`, `"YouTube"`, `"Outro"` |
| `titulo` | `String` | Sim | Título do vídeo ou resumo inicial do conteúdo |
| `descricao` | `String` | Não | Texto descritivo sobre o conteúdo/assunto do vídeo |
| `categoria` | `String` | Não | Categoria temática (ex: `"Culinária"`, `"Treino"`, `"Tecnologia"`, etc.) |
| `tags` | `Array<String>` | Não | Palavras-chave normalizadas em minúsculas |
| `status` | `String (Enum)` | Sim | Estado do vídeo: `"pendente"` ou `"assistido"` |
| `assistido_em` | `String (ISO 8601)` | Não | Data/hora em que foi marcado como assistido |
| `created_at` | `String (ISO 8601)` | Sim | Data e hora de inclusão em UTC |
| `updated_at` | `String (ISO 8601)` | Sim | Data e hora da última modificação em UTC |

---

## 📏 Constraints e Regras de Negócio
| Regra | Descrição |
|---|---|
| **Isolamento por Usuário** | Consultas sempre filtram por `userId == current_user_id` |
| **Normalização de Tags** | Tags armazenadas em minúsculas e sem espaços laterais (`tag.strip().lower()`) |
| **Enum de Status** | Válidos apenas `"pendente"` e `"assistido"` |
| **Detecção de Plataforma** | Baseada no domínio da URL |
| **Validação de URL** | Obrigatório iniciar com `http://` ou `https://` |

---

## 🗂️ Índices Necessários
Para consultas compostas no Firestore:
| Coleção | Campos | Tipo |
|---|---|---|
| `saved_videos` | `userId` (Ascendente), `created_at` (Descendente) | Composto |
| `saved_videos` | `userId` (Ascendente), `status` (Ascendente), `created_at` (Descendente) | Composto |
| `saved_videos` | `userId` (Ascendente), `plataforma` (Ascendente), `created_at` (Descendente) | Composto |
