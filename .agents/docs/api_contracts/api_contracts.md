# Contratos de API RESTful (API Contracts)

Esta documentação define os contratos formais de integração para todas as rotas e endpoints RESTful expostos pelo motor de IA do DAM (`backend_ia`).

---

## 1. Webhook do WhatsApp

### `POST /api/whatsapp/webhook`
Recebe payloads de eventos e mensagens vindos da instância Evolution API.

* **Headers Obrigatórios:**
  * `Content-Type: application/json`
  * `Authorization` ou `apikey`: Token de webhook configurado (`WEBHOOK_TOKEN`).
* **Request Body Exemplo:**
  ```json
  {
    "event": "messages.upsert",
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "3EB0ABC123"
      },
      "message": {
        "conversation": "Quanto gastei este mês no cartão pessoal?"
      },
      "messageType": "conversation"
    }
  }
  ```
* **Respostas:**
  * `200 OK`: `{"status": "processing"}`
  * `401 Unauthorized`: Token de webhook ausente ou inválido.
  * `429 Too Many Requests`: Limite de taxa excedido.

---

## 2. Monitoramento & Saúde

### `GET /health` e `GET /`
Verificação de liveness do serviço para balanceadores de carga e orquestradores Cloud Run.

* **Resposta `200 OK`:**
  ```json
  {
    "status": "ok",
    "service": "DAM Motor IA"
  }
  ```

### `POST /api/health-webhook`
Recebe métricas exportadas por apps de saúde (ex: Health Auto Export do iOS).

* **Headers:** `Authorization` ou `apikey`
* **Request Body:**
  ```json
  {
    "date": "2026-09-03",
    "metrics": {
      "sleep_hours": 8.0,
      "steps": 9500,
      "active_energy_kcal": 450
    }
  }
  ```
* **Respostas:**
  * `200 OK`: `{"status": "success", "message": "Health data received"}`
  * `400 Bad Request`: Payload corrompido ou formato inválido.

---

## 3. Alertas de Billing (GCP FinOps)

### `POST /api/billing/alert`
Endpoint receptor de notificações de orçamento do Google Cloud Billing.

* **Headers:** `Authorization: Bearer <TOKEN>`
* **Request Body:**
  ```json
  {
    "costAmount": 12.50,
    "budgetAmount": 50.00,
    "currencyCode": "BRL"
  }
  ```
* **Respostas:**
  * `200 OK`: `{"status": "alert_processed", "notified": true}`
  * `401 Unauthorized`: Token inválido.

---

## 4. Morning Briefing

### `POST /api/briefing/morning`
Disparo manual ou via Cloud Scheduler do resumo matinal das 08:00.

* **Headers:** `Authorization: Bearer <TOKEN>`
* **Respostas:**
  * `200 OK`:
    ```json
    {
      "status": "success",
      "message": "Briefing matinal enviado com sucesso para 5511****9999",
      "data": "2026-09-03"
    }
    ```
  * `200 OK (Idempotente)`:
    ```json
    {
      "status": "already_sent",
      "message": "O briefing matinal de hoje já foi enviado previamente.",
      "data": "2026-09-03"
    }
    ```

### `GET /api/briefing/preview`
Retorna a pré-visualização do texto consolidado do briefing sem persistir ou disparar no WhatsApp.

* **Resposta `200 OK`:**
  ```json
  {
    "data": "2026-09-03",
    "preview": "🌅 *BOM DIA! SEU BRIEFING MATINAL*..."
  }
  ```

---

## 5. Dashboard Web REST APIs

### `GET /api/v1/finance/monthly-summary`
Retorna as estatísticas consolidadas de gastos do mês para gráficos do Dashboard Bento Grid.

* **Query Parameters:**
  * `year` (int, default: ano corrente)
  * `month` (int, default: mês corrente)
* **Resposta `200 OK`:**
  ```json
  {
    "year": 2026,
    "month": 9,
    "total_spent": 1450.80,
    "categories": {
      "Alimentação": 820.00,
      "Transporte": 330.80,
      "Lazer": 300.00
    },
    "recent_transactions": [
      {
        "id": "doc123",
        "date": "2026-09-02",
        "description": "Supermercado Pão de Açúcar",
        "amount": 184.50,
        "category": "Alimentação"
      }
    ]
  }
  ```

### `GET /api/v1/health/weekly-summary`
Retorna os dados dos últimos 7 dias de sono e treinos para os cartões de bem-estar.

* **Resposta `200 OK`:**
  ```json
  {
    "days": 7,
    "sleep_average_hours": 7.6,
    "workouts_count": 4,
    "logs": [ ... ]
  }
  ```

### `GET /api/v1/agenda/upcoming-events`
Retorna os próximos compromissos da agenda do Google Calendar para o widget da Sidebar/Bento Grid.

* **Query Parameters:**
  * `limit` (int, default: 5)
* **Resposta `200 OK`:**
  ```json
  {
    "events": [
      {
        "id": "cal_evt_1",
        "summary": "Reunião de Alinhamento de Produto",
        "start": "2026-09-04T10:00:00-03:00",
        "end": "2026-09-04T11:00:00-03:00"
      }
    ]
  }
  ```
