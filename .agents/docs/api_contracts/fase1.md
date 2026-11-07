# API Contract - Motor IA (Fase 1)

## Base URL
`http://localhost:8000` (Dev)

## 1. Webhook Recebimento WhatsApp (Evolution API)
- **Method:** `POST`
- **Endpoint:** `/api/whatsapp/webhook`
- **Descrição:** Recebe as mensagens repassadas pela Evolution API.

### Request Body (Exemplo Evolution API v2 - Message Upsert)
```json
{
  "event": "messages.upsert",
  "instance": "DAM_Instance",
  "data": {
    "key": {
      "remoteJid": "5511999999999@s.whatsapp.net",
      "fromMe": false,
      "id": "BAE5ABCDEF12345"
    },
    "pushName": "Admin",
    "message": {
      "conversation": "Olá DAM, como estão meus servidores?"
    },
    "messageType": "conversation"
  }
}
```

### Response
- **Status 200 OK**: Retorna `{ "status": "processing" }` quase imediatamente para liberar o webhook.

---

## 2. Dependência Externa (Evolution API) - Envio de Mensagem
- **Method:** `POST`
- **Endpoint:** `{{EVOLUTION_URL}}/message/sendText/{{INSTANCE_NAME}}`
- **Headers:** `apikey: {{EVOLUTION_API_KEY}}`

### Request Body
```json
{
  "number": "5511999999999",
  "text": "Seus servidores estão operacionais. O faturamento está em R$ 120,00.",
  "delay": 1200
}
```
