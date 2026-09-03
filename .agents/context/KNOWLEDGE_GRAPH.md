# Knowledge Graph & Memória de Contexto do DAM

Este arquivo armazena decisões definitivas e sumarizadas das funcionalidades concluídas.

## Fase 1: Fundação do Motor de IA e Mensageria
- **FastAPI Webhook:** Recebe payload da Evolution API (`POST /api/whatsapp/webhook`).
- **Function Calling:** Gemini 1.5 Pro/Flash com registry dinâmico de tools.
- **Segurança:** Autenticação via `WEBHOOK_TOKEN` no header `apikey` / `Authorization`.

## Fase 3: Pilares Base de Dados & Mensageria
- **Health Webhook (`US-3.1`, `US-3.2`):** Armazena dados do Health Auto Export em `health_metrics` e consulta via `health_tool.py`.
- **Finance Tool (`US-3.3`):** Grava receitas/despesas em `finances`.
- **Calendar Tool (`US-3.4`):** Agendamentos no Google Calendar via Service Account GCP.
- **Isolamento de Chat & Preservação de Notificações (`US-3.5`):**
  - Webhook valida estritamente `is_allowed_user` (comparando últimos 8 dígitos e DDD com `ALLOWED_PHONE_NUMBER`).
  - Fail-safe ativo: se `ALLOWED_PHONE_NUMBER` estiver vazio, nenhuma mensagem é processada.
  - Grupos (`@g.us`) e canais são sumariamente ignorados com HTTP 200 rápido e status `ignored`.
  - Evolution API configurada com `readMessages=false`, `readStatus=false`, `groupsIgnore=true`, `alwaysOnline=false` em `docker-compose.yml` e `conectar_whatsapp.py`, garantindo que nenhuma notificação do celular seja cancelada ou suprimida pelo bot.
- **Multimodalidade no WhatsApp (`US-3.6`):** Extração de `imageMessage` e `audioMessage` em Base64 no webhook repassando ao Gemini 1.5 com suporte nativo a visão e áudio.
- **Calendar Enriquecido (`US-3.7`):** Suporte a `descricao` e `localizacao` (Google Meet ou endereço físico) na criação e consulta de eventos no Google Calendar.
- **Integração Dashboard (`US-3.8`):** Build do Angular 17 validado com budgets expandidos e DTOs alinhados à Core API Spring Boot.

## Fase 4: Integrações Externas Avançadas
- **Veículo Fiat Fastback (`US-4.1`):** `vehicle_tool.py` com telemetria em tempo real (combustível, autonomia, pressão de pneus, bateria) e acionamento seguro de travas (`travar`/`destravar`).
- **Esports CS2 (`US-4.2`):** `esports_tool.py` integrado a dados competitivos HLTV para consulta de partidas, placares e confrontos (FURIA, MIBR, Imperial, etc.).

## Fase 5: Automação Residencial e Alertas de Nuvem
- **Alertas de Custo GCP (`US-5.1`):** Endpoint `/api/billing-alert` conectado ao Cloud Pub/Sub, calculando percentual gasto contra o orçamento e disparando notificações proativas no WhatsApp.
- **Automação Alexa (`US-5.2`):** `alexa_tool.py` para acionamento de rotinas, cenas e ambientes inteligentes da casa via chat.
