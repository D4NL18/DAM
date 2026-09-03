# Fase 5: Automação Residencial e Alertas de Custo GCP

## 1. Escopo das Tarefas

#### [x] Task 5.1: Notificação Proativa de Orçamento GCP Billing via Pub/Sub
- [x] **Etapa 5.1.1:** Criação do endpoint `/api/billing-alert` em `routers/billing.py` recebendo mensagens Pub/Sub Push.
- [x] **Etapa 5.1.2:** Decodificação segura em Base64, extração de percentual gasto vs limite estipulado e disparo de notificação proativa no WhatsApp do usuário.
- [x] **Etapa 5.1.3:** Registro do router no `main.py` e proteção com token de segurança.

#### [x] Task 5.2: Automação Residencial via Webhooks Alexa
- [x] **Etapa 5.2.1:** Criação da tool `acionar_rotina_alexa` em `services/tools/alexa_tool.py` com suporte a ambiente e rotina específica ("Modo Cinema", "Ligar luzes da sala").
- [x] **Etapa 5.2.2:** Registro no `AVAILABLE_TOOLS` do `ai_service.py`.

## 2. Critérios de Aceite e Validação (QA)
- [x] **Cenário 1 (Alerta de Custos):** Ao receber notificação de threshold (50%, 80%, 100%) do Cloud Billing, o bot envia mensagem formatada no WhatsApp alertando o valor gasto e a moeda.
- [x] **Cenário 2 (Automação Alexa):** O usuário pede no chat *"Coloque a sala no Modo Cinema"* ou *"Ligue as luzes do escritório"*. O bot aciona a rotina na Alexa e confirma no chat.
