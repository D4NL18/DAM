# Estado Atual da Orquestração (STATE.md)

## Status Global
- **Arquitetura:** Microsserviços e Serverless (FastAPI + Evolution API + Angular 17 + Spring Boot 3 + Firestore)
- **Estruturação:** **Multi-Usuário / Multi-Tenant Isolado** com 2 contas ativas (Daniel e Lari)
- **Segurança & Defesa:** Isolamento criptográfico e de partição por usuário, Guardrails contra Prompt Injection, Rate Limiter, Mascaramento LGPD, Autenticação de Dashboard e Anti-Loop WhatsApp.
- **Suíte de Testes:**
  - `backend_ia` (Python/FastAPI): 325 testes unitários e de integração aprovados (100% de sucesso).
  - `backend_core` (Java/Spring Boot): 8 testes unitários aprovados com Maven Surefire (100% de sucesso).
  - `frontend_dashboard` (Angular 17): Compilação de produção e bundles gerados com 0 erros.
- **Última Pipeline Concluída:**
  - **GP-01.1 – CRUD Completo do Google Calendar (Edição In-Place & Exclusão Segura) [100% CONCLUÍDO]**:
    - `excluir_evento`: Localização por termo/título e cancelamento efetivo via `service.events().delete()`.
    - `editar_evento`: Remarcação de horários e alteração de título/local/descrição via `service.events().patch()`, sem duplicação de eventos.
    - Desambiguação segura quando múltiplos eventos coincidem.
    - Governança multi-usuário estrita: Lari impedida de editar ou excluir eventos na agenda do Daniel.
  - **PC-11 – Multi-Usuário / Isolamento Total de Contas (Daniel & Lari) [100% CONCLUÍDO]**:
    - **Usuários Configurados:**
      1. **Daniel:** WhatsApp `+55 71 99126-9995` (`5571991269995`), Login Dashboard `Daniel` / `Dm12031994@@` (Admin).
      2. **Lari:** WhatsApp `+55 71 98327-8254` (`5571983278254`), Login Dashboard `Lari` / `Lilalink10` (User).
    - **Isolamento de Dados Estrito:**
      - Finanças, Saúde, Notas & Lembretes, Cofre de Senhas, Memória Espacial, Banco de Horas, Ideias de Presentes e Veículos completamente particionados por `userId`.
      - Retrocompatibilidade preservada para dados legados do Daniel (sem quebra de schema).
    - **Hobbies e Contas Individuais:**
      - AniList (Watchlist de animes) e Clash of Clans vinculados exclusivamente ao Daniel; Lari recebe avisos amigáveis caso pergunte sobre esses temas.
    - **Morning Briefing Personalizado por Usuário:**
      - Cada usuário configura seus próprios tópicos de interesse (`agenda`, `lembretes`, `saude`, `carro`, `animes`, `clash`, `furia`) e seu horário preferencial via chat ou tools (`configurar_preferencias_briefing`).
      - Idempotência de envio isolada por data e usuário (`briefing_{user_id}_{date}`).
    - **Veículo & Telemetria:**
      - Daniel mantém seu `Fiat Fastback Turbo 270` pré-configurado.
      - Lari possui espaço isolado (`user_vehicles`) e pode cadastrar/atualizar seu veículo a qualquer momento pelo chat (`cadastrar_ou_atualizar_veiculo`).
    - **Exceção Híbrida de Calendário:**
      - Mesma chave/API Google Service Account compartilhada.
      - Calendários individuais: Daniel pode consultar sua própria agenda e a da Lari (`usuario="lari"`).
      - Lari só tem permissão de consultar sua própria agenda (tentativas de consultar a do Daniel são barradas com mensagem de privacidade).
    - **Backend Core (Spring Boot):**
      - Endpoint `/api/auth/login` validando credenciais de Daniel e Lari.
      - Endpoints `/api/finance/summary` e `/api/health/summary` filtrando transações e métricas por `userId`.
      - Configuração de CORS aberta para o dashboard.
    - **Frontend Dashboard (Angular 17):**
      - `AuthService` com gerenciamento de sessão e persistência no `localStorage`.
      - `AuthGuard` protegendo todas as rotas internas contra acessos não autenticados.
      - Página de Login com estética Bento/Material 3 alinhada ao `DESIGN_SYSTEM.md`.
      - Header e Sidebar exibindo usuário conectado e botão de Logout.
      - Serviços de API (`FinanceApiService`, `HealthApiService`, `AgendaApiService`) propagando o `userId` ativo.

---

## Domínios Funcionais do Sistema
1. **Gestão Pessoal & Rotina:** Agenda Híbrida Multi-Usuário, Lembretes/Notas Particionados, Memória Espacial Isolada, Morning Briefing.
2. **Finanças & Gastos:** Classificação Multicartão, Resumo de Gastos Isolado por Usuário, Splitwise de Viagens, GCP Billing.
3. **Saúde & Bem-Estar:** Sono, Treinos, Webhook Apple Health particionado por `userId`.
4. **Entretenimento & Lazer:** Anime Tracker AniList, Streaming TMDB, FURIA CS2, Calculadora de Churrasco, Curador de Presentes.
5. **Utilitários & Segurança:** Cofre Criptografado por Usuário, Tradutor de Cardápios, Conversor Universal, Banco de Horas Semanal, Trânsito Google Maps, Gerenciador de Endereços Salvos.
6. **Plataforma & Core:** Motor IA Multimodal (Gemini Flash), Contexto de Usuário Dinâmico (`user_context.py`), Guardrails, Dashboard Web Angular com Login e Isolamento.