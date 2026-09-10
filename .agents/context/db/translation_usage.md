# Coleção: `translation_usage` e `translation_logs`

## 📋 Propósito
Armazena a **telemetria FinOps de consumo da cota gratuita da Google Cloud Translation API** (500.000 caracteres mensais) e o histórico de requisições de tradução (sem guardar o texto privado do usuário, garantindo privacidade e LGPD).

---

## 🧩 Features que utilizam esta coleção
| Feature | Domínio | Descrição |
|---|---|---|
| **US-10 – Tradutor Universal Multimodal** | Utilitários & Segurança | Rastreamento FinOps da cota gratuita de 500k caracteres/mês e auditoria de tipos de mídia traduzidos (texto, imagem, áudio). |

---

## 📑 1. Estrutura do Documento de Cota Mensal: `translation_usage`
**Path no Firestore:** `/translation_usage/{month}`  
*(Exemplo de Document ID: `"2026-09"`)*

### Campos do Documento

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `month` | `String` | Sim | Mês de referência no formato `YYYY-MM` (ex: `"2026-09"`) |
| `total_characters` | `Number (Integer)` | Sim | Total acumulado de caracteres traduzidos no mês |
| `monthly_limit` | `Number (Integer)` | Sim | Limite do Free Tier (padrão: `500000`) |
| `requests_count` | `Number (Integer)` | Sim | Total de requisições de tradução atendidas no mês |
| `last_reset_at` | `String (ISO 8601)` | Sim | Data do início do ciclo mensal |
| `updated_at` | `String (ISO 8601)` | Sim | Data e hora da última atualização |

---

## 📑 2. Estrutura do Documento de Log de Auditoria: `translation_logs`
**Path no Firestore:** `/translation_logs/{log_id}`

### Campos do Documento

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | Identificador único da requisição (UUID v4) |
| `userId` / `user_id` | `String` | Sim | Identificador do usuário solicitante (`"daniel"` ou `"lari"`) |
| `input_type` | `String (Enum)` | Sim | Tipo da entrada: `"text"`, `"image"` ou `"audio"` |
| `source_language` | `String` | Sim | Código ISO do idioma de origem detectado ou informado (ex: `"en"`, `"es"`, `"ja"`) |
| `target_language` | `String` | Sim | Código ISO do idioma de destino (ex: `"pt"`, `"en"`) |
| `characters_count` | `Number (Integer)` | Sim | Quantidade de caracteres traduzidos nesta chamada |
| `provider` | `String` | Sim | Provedor utilizado (`"google_cloud_translation_v2"` ou `"fallback"`) |
| `status` | `String (Enum)` | Sim | `"success"` ou `"failed"` |
| `created_at` | `String (ISO 8601)` | Sim | Data e hora da tradução em UTC |

---

## 📏 Constraints e Regras de Segurança
| Regra | Descrição |
|---|---|
| **Hard Cap FinOps** | Se `total_characters >= monthly_limit`, bloqueia chamadas cobradas na nuvem |
| **Privacidade & LGPD** | **NUNCA** armazenar o conteúdo do texto ou áudio do usuário nos logs |
| **Isolamento por Usuário** | Consultas individuais filtram por `userId == current_user_id` |

---

## 🧪 Mock Seeds (Dados de Teste)
```json
[
  {
    "_collection": "translation_usage",
    "_id": "2026-09",
    "month": "2026-09",
    "total_characters": 1250,
    "monthly_limit": 500000,
    "requests_count": 8,
    "last_reset_at": "2026-09-01T00:00:00Z",
    "updated_at": "2026-09-09T20:00:00Z"
  },
  {
    "_collection": "translation_logs",
    "_id": "e8a931c5-8f4b-4a57-b18c-32b0a1d49e1a",
    "id": "e8a931c5-8f4b-4a57-b18c-32b0a1d49e1a",
    "user_id": "daniel",
    "input_type": "text",
    "source_language": "en",
    "target_language": "pt",
    "characters_count": 45,
    "provider": "google_cloud_translation_v2",
    "status": "success",
    "created_at": "2026-09-09T20:00:00Z"
  }
]
```
