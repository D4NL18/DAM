# Fase 3: Pilares Base de Dados (Saúde, Financeiro, Agenda e Dashboard)

Este documento centraliza as especificações, regras de negócio e o planejamento detalhado das tarefas da Fase 3 do projeto DAM Assistant.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-301 (Isolamento Estrito do WhatsApp):** O assistente deve atuar estritamente na conversa "comigo mesmo" (número permitido configurado em `ALLOWED_PHONE_NUMBER`). Qualquer mensagem originada de grupos (`@g.us`) ou de outros contatos individuais deve ser ignorada silenciosamente pelo webhook, sem marcar como lida e sem enviar requisições de status que possam suprimir ou consumir notificações no smartphone do usuário.
- **P-302 (Multimodalidade - Imagem e Áudio):** O bot deve processar tanto mensagens de texto quanto mídias recebidas (áudios de voz e imagens):
  - **Áudio:** Baixar o binário de áudio (formato OGG/Opus/MP3) via Evolution API e realizar transcrição/compreensão via Gemini Multimodal.
  - **Imagem:** Baixar a imagem (JPEG/PNG) via Evolution API e processar visualmente via Gemini Vision (ex.: extração de recibos/comprovantes financeiros ou leitura de dados de exames).
- **P-303 (Agendamento Enriquecido no Google Calendar):** Ao agendar compromissos via linguagem natural, a tool de calendário deve permitir a inserção de `descrição` detalhada e `localização` (endereço ou link de reunião), repassando esses dados à Google Calendar API v3.
- **P-304 (Integração Viva do Dashboard com Firestore):** O Dashboard Angular deve exibir métricas reais consumindo a Core API (Spring Boot), que lê as coleções `health_metrics` e `finances` do Firestore, eliminando dados estáticos/mockados.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 3

#### [x] Task 3.1: Endpoint de Métricas de Saúde (Health Auto Export)
- [x] Rota `/api/health-webhook` no FastAPI.
- [x] Parse do payload e gravação no Firestore (`health_metrics`).

#### [x] Task 3.2: Tool de Consulta de Saúde no LLM
- [x] Implementação de `health_tool.py` e registro no Function Calling do Gemini.

#### [x] Task 3.3: Agente e Tool Financeiro
- [x] Implementação de `finance_tool.py` e persistência de despesas/receitas em `finances`.

#### [x] Task 3.4: Integração Inicial com Google Calendar
- [x] Implementação de `calendar_tool.py` e agendamento básico com Service Account GCP.

#### [x] Task 3.5: Fix de Conflito de Notificações no WhatsApp & Isolamento Estrito
- [x] **Etapa 3.5.1:** Revisar filtros de evento no `routers/webhook.py` para garantir que apenas `messages.upsert` do chat consigo mesmo seja processado.
- [x] **Etapa 3.5.2:** Garantir que nenhuma mensagem de outros contatos/grupos acione chamadas que alterem o status da mensagem (evitando a remoção indevida de notificações no celular).
- [x] **Etapa 3.5.3:** Validar compatibilidade da configuração da instância na Evolution API (desativar auto-leitura automática global de mensagens se estiver ativada).

#### [x] Task 3.6: Recepção e Processamento Multimodal (Áudio e Imagem)
- [x] **Etapa 3.6.1:** Mapear tipos de mensagens na Evolution API (`audioMessage`, `imageMessage`) no payload do webhook.
- [x] **Etapa 3.6.2:** Implementar download de mídia da Evolution API (Base64 / URL temporária) em `services/whatsapp_service.py`.
- [x] **Etapa 3.6.3:** Integrar dados binários/base64 no `services/ai_service.py` utilizando as capacidades multimodais do Gemini (Vision e Audio).
- [x] **Etapa 3.6.4:** Encaminhar comprovantes de pagamento e notas fiscais recebidas como foto diretamente para o fluxo de categorização financeira da `finance_tool.py`.

#### [x] Task 3.7: Enriquecimento do Google Calendar (Descrição e Localização)
- [x] **Etapa 3.7.1:** Atualizar assinatura da tool `agendar_evento` em `services/tools/calendar_tool.py` para incluir os parâmetros `descricao: Optional[str] = None` e `localizacao: Optional[str] = None`.
- [x] **Etapa 3.7.2:** Mapear os campos `description` e `location` no payload enviado para o método `service.events().insert()`.
- [x] **Etapa 3.7.3:** Atualizar docstrings e declaração da tool no Function Calling do Gemini para guiar a extração de local e descrição do texto do usuário.

#### [x] Task 3.8: Integração Completa do Dashboard Web com o Banco de Dados
- [x] **Etapa 3.8.1:** Ajustar a Core API (Spring Boot) para expor endpoints consolidados lendo do Firestore (`/api/health/summary`, `/api/finances/summary`).
- [x] **Etapa 3.8.2:** Atualizar os serviços Angular (`HealthApiService`, `FinanceApiService`) para consumir a Core API conectada ao Firestore.
- [x] **Etapa 3.8.3:** Conectar componentes visuais (gráficos e tabelas do Dashboard) ao fluxo reativo de dados reais.

---

## 3. Critérios de Aceite e Validação (QA)
- [x] **Cenário 1 (Notificações Celular):** Mensagens recebidas no celular de contatos terceiros ou grupos geram notificações normais no aparelho e não geram qualquer resposta ou leitura pelo bot.
- [x] **Cenário 2 (Áudio no WhatsApp):** O usuário envia uma mensagem de áudio falando "Marque dentista amanhã às 14h na Av Paulista". O bot compreende o áudio e agenda o evento com título, horário e localização corretos.
- [x] **Cenário 3 (Imagem no WhatsApp):** O usuário envia uma foto de um comprovante Pix. O bot analisa a imagem, extrai valor, data e favorecido e registra em `finances`.
- [x] **Cenário 4 (Calendar Enriquecido):** O evento criado no Google Calendar possui título, horário de início, duração, descrição detalhada e o campo "Onde / Local" devidamente preenchido.
- [x] **Cenário 5 (Dashboard Integrado):** O usuário abre o Dashboard Angular e os gráficos exibem valores correspondentes aos registros salvos no Firestore.
