# Modelagem de Banco de Dados (Firestore) - Fase 1

## Visão Geral
O banco de dados escolhido é o **Firebase Firestore** (NoSQL). Não temos tabelas e migrations SQL tradicionais, mas regras de modelagem de documentos e coleções para garantir escalabilidade e redução de leituras faturáveis (Spark Plan).

## Coleção: `chat_logs`

### Objetivo
Armazenar o histórico de mensagens trocadas entre o usuário e a IA para injetar como contexto nas chamadas do LLM.

### Estrutura do Documento
**Path:** `/chat_logs/{messageId}`

```json
{
  "messageId": "string (Evolution Message ID)",
  "remoteJid": "string (5511999999999@s.whatsapp.net)",
  "fromMe": "boolean (true se foi enviado pelo DAM, false se foi do Usuário)",
  "text": "string (O conteúdo da mensagem)",
  "timestamp": "timestamp (Data e hora do envio/recebimento)",
  "tokensUsed": "number (Opcional - para log de uso do LLM no caso de fromMe = true)"
}
```

### Índices Necessários (Firestore Indexes)
Para recuperar eficientemente os últimos N logs de um usuário:
- **Coleção:** `chat_logs`
- **Campos do Índice Composto:**
  1. `remoteJid` (Ascendente)
  2. `timestamp` (Descendente)

### Regras de Segurança (Firestore Rules - Conceitual)
- Apenas a Service Account de Backend (FastAPI / Spring Boot) terá permissão de leitura e escrita nesta coleção. Acesso de clientes (Frontend) será negado para logs de conversa.
