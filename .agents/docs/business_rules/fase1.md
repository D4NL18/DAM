# Regras de Negócio - Fase 1 (Motor IA)

- **P-001 (Validação de Webhook):** O endpoint de webhook deve ignorar mensagens oriundas de grupos de WhatsApp, focando apenas em conversas diretas (`isGroup == false`), ou possuir um whitelist do número do administrador (o usuário).
- **P-002 (Limite de Tempo LLM):** Como a Evolution API espera retornos de webhook rápidos, a orquestração do LLM não deve bloquear a thread do Uvicorn (usar `BackgroundTasks` no FastAPI).
- **P-003 (Persistência do Histórico):** Para manter o contexto da conversa, o sistema deve buscar os últimos N (ex: 10) logs da coleção `chat_logs` referentes ao mesmo número de telefone e anexá-los ao prompt do Gemini.
- **P-004 (Graceful Degradation):** Se a API do Gemini falhar por limite de cota ou erro de rede, o sistema deve notificar o usuário com uma mensagem amigável via WhatsApp (ex: "Meus servidores estão indisponíveis no momento").
- **P-005 (Isolamento de Chaves):** As credenciais de produção nunca devem ser codificadas diretamente; a aplicação deve estourar erro fatal na inicialização se as variáveis de ambiente necessárias não estiverem preenchidas.
