# Fase 1: Fundação do Motor de IA e Mensageria

## Descrição Funcional
A Fase 1 visa estabelecer a estrutura base do backend em Python (FastAPI). Este serviço será o "cérebro" do DAM, responsável por receber mensagens do WhatsApp através de um Webhook da Evolution API, processá-las utilizando a API do Gemini (com suporte a Function Calling) e salvar o histórico de logs no Firebase Firestore.

## Critérios de Aceite
1. **Endpoint de Webhook (WhatsApp):** O FastAPI deve ter uma rota POST `/api/whatsapp/webhook` que receba o payload da Evolution API.
2. **Processamento Assíncrono:** A resposta ao webhook deve ser imediata (HTTP 200) para evitar timeouts da Evolution API, processando a mensagem com o LLM em background.
3. **Integração LLM (Gemini):** O texto recebido deve ser enviado ao Gemini 1.5 Pro/Flash usando o Google GenAI SDK.
4. **Respostas (Evolution API):** A resposta gerada pelo LLM deve ser enviada de volta ao usuário via requisição HTTP POST para a Evolution API.
5. **Logs no Firestore:** Cada mensagem recebida e enviada deve ser armazenada em uma coleção `chat_logs` no Firestore.
6. **Configuração de Variáveis de Ambiente:** O sistema deve usar `.env` (python-dotenv) para gerenciar credenciais (Chave do Gemini, Evolution API URL/Token, Firebase Credentials JSON).
