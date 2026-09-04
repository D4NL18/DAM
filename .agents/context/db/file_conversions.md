# Coleção: `file_conversions`

## 📋 Propósito
Armazena os **registros de auditoria, métricas de performance e histórico de conversão de arquivos** (PDF, Word, Imagens, fusões e fatiamentos) solicitados pelos usuários. Nenhum binário confidencial é persistido aqui — apenas metadados de execução, tempo gasto e status.

---

## 🧩 Features que utilizam esta coleção
| Feature | Domínio | Descrição |
|---|---|---|
| **US-09 – Conversor e Manipulador Universal de Arquivos** | Utilitários & Segurança | Registro de telemetria, tipo de conversão, tamanhos de arquivo e auditoria de erros. |

---

## 📑 Estrutura do Documento
**Path no Firestore:** `/file_conversions/{conversion_id}`

Document ID é o UUID v4 gerado pelo backend.

### Campos do Documento

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `id` | `String (UUID)` | Sim | Identificador único da conversão (UUID v4) |
| `userId` / `user_id` | `String` | Sim | Identificador do usuário proprietário (`"daniel"` ou `"lari"`) |
| `conversion_type` | `String (Enum)` | Sim | Tipo da conversão (`pdf_to_docx`, `docx_to_pdf`, `img_to_pdf`, `merge_pdfs`, `split_pdf`, `pdf_to_images`, `image_convert`, `pdf_to_text`) |
| `source_format` | `String` | Sim | Extensão/formato do arquivo original (ex: `"pdf"`, `"jpg"`, `"docx"`) |
| `target_format` | `String` | Sim | Extensão/formato resultante (ex: `"docx"`, `"pdf"`, `"png"`, `"txt"`) |
| `file_size_bytes` | `Number (Integer)` | Sim | Tamanho do arquivo original em bytes |
| `output_size_bytes` | `Number (Integer)` | Não | Tamanho do arquivo convertido resultante em bytes |
| `status` | `String (Enum)` | Sim | Status da operação: `"success"` ou `"failed"` |
| `error_message` | `String` | Não | Mensagem de erro caso a conversão tenha falhado |
| `execution_time_ms` | `Number (Integer)` | Sim | Duração do processamento em milissegundos |
| `created_at` | `String (ISO 8601)` | Sim | Data e hora da requisição em UTC |

---

## 📏 Constraints e Regras de Negócio
| Regra | Descrição |
|---|---|
| **Isolamento por Usuário** | Consultas sempre filtram por `userId == current_user_id` |
| **Limitação de Tamanho** | `file_size_bytes` <= 26.214.400 (25 MB) |
| **Enum de Status** | Válidos apenas `"success"` e `"failed"` |
| **Privacidade Total** | Nenhum conteúdo de documento ou imagem é salvo no banco de dados |

---

## 🗂️ Índices Necessários
Para consultas compostas no Firestore:
| Coleção | Campos | Tipo |
|---|---|---|
| `file_conversions` | `userId` (Ascendente), `created_at` (Descendente) | Composto |
| `file_conversions` | `userId` (Ascendente), `conversion_type` (Ascendente), `created_at` (Descendente) | Composto |
