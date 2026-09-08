# Fase 21: Morning Briefing Proativo Agendado (Resumo Matinal Diário às 8h)

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 21, responsável pelo disparo proativo diário às 08:00 da manhã no WhatsApp do usuário com seu briefing consolidado.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-2101 (Compromissos do Dia - Google Calendar):**
  - Consultar a agenda do usuário no Google Calendar (`calendar_tool.py`) para a data de hoje.
  - Listar reuniões e eventos com horário de início e fim, título e link do Meet/localização (se houver). Se não houver eventos, informar: *"Nenhum compromisso agendado para hoje"*.

- **P-2102 (Tarefas e Lembretes do Dia):**
  - Consultar anotações do tipo `lembrete` com status `pendente` na coleção `notes_reminders` (`notes_tool.py`).
  - Listar lembretes cuja data agendada seja hoje (ou atrasados), com caixas de seleção `[ ]`. Se não houver, informar: *"Nenhuma tarefa pendente para hoje"*.

- **P-2103 (Jogos da FURIA CS2 no Dia com Regra Temporal Específica):**
  - Consultar partidas da FURIA marcadas para a data de hoje (`esports_tool.py`).
  - **Regra de Horário:**
    - **Se a partida ocorreu entre 00:00 e 08:00:** o bot deve apresentar o **resultado final / placar** (ex: *"FURIA 2 x 0 NAVI - Vitória! 🏆"*).
    - **Se a partida ainda vai acontecer (após as 08:00):** o bot deve apresentar **apenas o horário e o adversário** (ex: *"FURIA vs FaZe Clan às 14:30 (MD3)"*).
    - **Se não houver jogo da FURIA hoje:** informar: *"Nenhum jogo da FURIA programado para hoje"*.

- **P-2104 (Lançamentos de Animes Acompanhados no Dia):**
  - Consultar os animes cadastrados na watchlist do usuário (`anime_watchlist`).
  - Filtrar animes que possuem `nextAiringEpisode` com data de exibição para a data de hoje (fuso horário de Brasília).
  - Listar anime, número do episódio e horário de transmissão na Crunchyroll (ex: *"Solo Leveling (Ep. 9) às 13:30"*). Se não houver, informar: *"Nenhum episódio novo dos seus animes hoje"*.

- **P-2105 (Disparo e Idempotência às 8h da Manhã):**
  - Disparo proativo executado todo dia às 08:00 (America/Sao_Paulo).
  - Envio através da Evolution API para `ALLOWED_PHONE_NUMBER`.
  - Idempotência: Registrar log na coleção Firestore `briefing_logs` com id `briefing_YYYY-MM-DD`. Caso o trigger seja chamado mais de uma vez no mesmo dia, não reenviar a menos que seja forçado (`force=true`).

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 21
- [ ] **Task 21.1:** Criação do módulo `backend_ia/services/briefing_service.py` com a lógica de agregação dos 4 pilares (Calendar, Lembretes, FURIA CS2 e Animes).
- [ ] **Task 21.2:** Criação do endpoint seguro `POST /api/briefing/morning` em `backend_ia/routers/briefing.py` com validação de token e suporte a agendador.
- [ ] **Task 21.3:** Agendador automático em background (BackgroundScheduler ou tarefa assíncrona diária no FastAPI Lifespan).
- [ ] **Task 21.4:** Suíte de testes TDD em `backend_ia/tests/test_fase21_morning_briefing.py`.
- [ ] **Task 21.5:** Validação e homologação completa com 100% de testes passando.
