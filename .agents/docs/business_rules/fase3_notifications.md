# Regras de Negócio - Fase 3: Notificações e Isolamento de Chat

- **P-305 (Isolamento Inviolável de Sessão):**
  1. O webhook do FastAPI deve filtrar sumariamente eventos que não sejam `messages.upsert`.
  2. Mensagens de grupos (`@g.us`) e canais (`@newsletter`) devem ser descartadas com status HTTP 200 sem persistência ou processamento.
  3. A variável de ambiente `ALLOWED_PHONE_NUMBER` é mandatória. Se estiver vazia ou ausente, o sistema entra em modo *fail-safe* e não processa mensagens de nenhum remetente.
  4. A validação do número deve sanitizar caracteres (removendo não-dígitos) e aceitar variações do 9º dígito brasileiro (DDI 55 + DDD + 8 ou 9 dígitos).
  5. Mensagens onde `is_me` for falso devem ser completamente ignoradas, sem chamar o LLM e sem alterar qualquer estado de leitura.

- **P-306 (Preservação de Notificações do Dispositivo Móvel):**
  1. A Evolution API deve ser configurada estritamente com `readMessages=false` e `readStatus=false` para evitar envio de *read receipts* que cancelam notificações no smartphone.
  2. Parâmetros em `docker-compose.yml` e scripts de provisionamento de instância devem desativar auto-leitura e presença contínua (`ALWAYS_ONLINE=false`).
