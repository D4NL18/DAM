# Roadmap do Projeto: Assistente DAM (Inteligência Artificial)

## Visão Geral
Assistente pessoal via WhatsApp focado em ser uma central de vida automatizada baseada em IA, utilizando Microsserviços (FastAPI, Spring Boot, Angular) hospedados no GCP e Firebase.

## Fase 1: Fundação do Motor de IA e Mensageria
- **[ ] US-1.1:** Setup inicial do Firebase Firestore e criação da base do projeto FastAPI.
- **[ ] US-1.2:** Integração com a API do LLM (Gemini/OpenAI) e arquitetura de *Function Calling* base.
- **[ ] US-1.3:** Setup e Integração com o WhatsApp via Evolution API (ou similar) recebendo/enviando mensagens de texto e áudio.
- **[ ] US-1.4:** Deploy inicial do FastAPI no Google Cloud Run (Configuração CI/CD).

## Fase 2: Dashboard Web (Angular + Spring Boot)
- **[ ] US-2.1:** Setup da Core API em Spring Boot 3 (Java 17+) com documentação OpenAPI/Swagger.
- **[ ] US-2.2:** Setup do projeto Angular (Standalone Components, SCSS) e padronização do Design System.
- **[ ] US-2.3:** Integração da Core API com Firebase Admin SDK para acesso ao Firestore (Dados de Saúde e Finanças).
- **[ ] US-2.4:** Criação dos Endpoints RESTful no Spring Boot para leitura e agregação dos dados no Dashboard.
- **[ ] US-2.5:** Desenvolvimento dos componentes de UI (Gráficos/Tabelas) no Angular consumindo a Core API.
- **[ ] US-2.6:** Configuração de CI/CD para deploy da Core API no Cloud Run e do Frontend no Firebase Hosting.

## Fase 3: Pilares Base de Dados (Saúde e Financeiro)
- **[ ] US-3.1 [PARALLEL]:** (Pilar 1) Criar endpoint `/api/health-webhook` no FastAPI, formatar dados do Health Auto Export e salvar no Firestore.
- **[ ] US-3.2 [PARALLEL]:** (Pilar 1) Desenvolver a *tool* LLM para consultar dados de saúde via chat.
- **[ ] US-3.3 [PARALLEL]:** (Pilar 4) Desenvolver o agente/tool de Gestão Financeira, para processar comprovantes/textos e gravar na coleção `finances`.

## Fase 4: Integrações Externas Avançadas
- **[ ] US-4.1:** (Pilar 2) Integração Uconnect API para o veículo (Fiat Fastback) e ferramentas de controle (autonomia, travas).
- **[ ] US-4.2:** (Pilar 3) Integração HLTV API/Scraper e tools de placar de CS2.
- **[ ] US-4.3:** (Pilar 5) Integração Google Calendar API (Agent de agendamentos).

## Fase 5: Automação Residencial e Alertas
- **[ ] US-5.1:** (Pilar 6) Configurar GCP Billing Budgets + Pub/Sub e webhook para alertas de custo.
- **[ ] US-5.2:** (Pilar 7) Integração Webhooks para acionamento de rotinas Alexa.

## Fase 6: Segurança, Auditoria e Refinamento
- **[ ] US-6.1:** Auditoria de segurança em todos os endpoints e Firebase Rules.
- **[ ] US-6.2:** Refinamento de prompts, Auto-Healer e testes E2E do sistema integrado.
