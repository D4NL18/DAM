# Tasks: Fase 1 (Motor de IA)

- [ ] **1. Setup do Projeto Python:**
  - Criar ambiente virtual (`python -m venv venv`).
  - Instalar dependências (`fastapi`, `uvicorn`, `firebase-admin`, `google-generativeai`, `python-dotenv`, `requests`).
  - Configurar arquivo `requirements.txt`.
- [ ] **2. Configuração Firebase:**
  - Criar o arquivo `config/firebase.py` para inicializar o `firebase-admin` usando um JSON de credencial local (via variável de ambiente `FIREBASE_CREDENTIALS_PATH`).
  - Implementar repository pattern em `repositories/chat_repository.py` para salvar e buscar de `chat_logs`.
- [ ] **3. Integração Gemini API:**
  - Criar `services/ai_service.py` com o Google GenAI SDK.
  - Implementar a função que constrói o prompt injetando o histórico da coleção `chat_logs`.
- [ ] **4. Integração Mensageria (Evolution API):**
  - Criar `services/whatsapp_service.py` para fazer POST no endpoint `/message/sendText` da Evolution API.
- [ ] **5. FastAPI Webhook Router:**
  - Criar `routers/webhook.py` com a rota `POST /api/whatsapp/webhook`.
  - Configurar injeção de dependência e `BackgroundTasks` para processar a mensagem no `ai_service` sem prender o HTTP Response 200.
- [ ] **6. Ponto de Entrada (main.py):**
  - Configurar app FastAPI e registrar os routers.
