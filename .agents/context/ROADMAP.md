# Roadmap Funcional do Projeto: Assistente DAM (Inteligência Artificial)

## Visão Geral
O DAM (Digital Autonomous Manager) é um assistente pessoal inteligente operando no WhatsApp e integrado a um Dashboard Web (Angular 17), concebido para ser a central de automação, finanças, saúde, entretenimento e rotina do usuário.

Todas as entregas e capacidades do sistema estão organizadas por **Domínios Funcionais**:

---

## 1. Domínio: Gestão Pessoal & Rotina

- **[x] GP-01 (Google Calendar):** Integração com Google Calendar API para agendamento de eventos, consultas com descrição, localização e suporte a fusos horários.
- **[x] GP-02 (Notas e Lembretes Rápidos):** Modelagem Firestore da coleção `notes_reminders`, criação e busca semântica de notas e lembretes com controle de pendências via WhatsApp.
- **[x] GP-03 (Memória Espacial / Onde Guardei Isso?):** Registro de localizações de objetos físicos e documentos na coleção `item_locations`, mantendo histórico de movimentações.
- **[x] GP-04 (Morning Briefing Proativo das 08:00):** Consolidação matinal automatizada às 08h trazendo Agenda, Tarefas pendentes de hoje, Partidas da FURIA (com regras temporais) e Lançamentos de Animes do dia com idempotência no Firestore (`briefing_logs`).

---

## 2. Domínio: Finanças & Gastos

- **[x] FG-01 (Gestão Multicartão & Classificação):** Suporte estrito aos métodos de pagamento (Cartão de Crédito Pessoal, Secundário e Débito/Pix), confirmação obrigatória de método e gravação na coleção `finances`.
- **[x] FG-02 (Divisão Inteligente de Contas de Restaurante):** Rateio proporcional de itens consumidos com taxa de serviço calculada centavo a centavo, organizado estritamente por nomes de pessoas e chave Pix para pagamento.
- **[x] FG-03 (Splitwise de Viagens e Grupos):** Criação de grupos e despesas compartilhadas nas coleções `trip_groups` e `trip_expenses`, com algoritmo de minimização de dívidas (*Debt Minimization*).
- **[x] FG-04 (GCP Billing & Monitoramento FinOps):** Endpoint de webhook para alertas de orçamentos e monitoramento de custos de nuvem.

---

## 3. Domínio: Saúde & Bem-Estar

- **[x] SB-01 (Métricas de Sono e Qualidade):** Registro de horas de sono, qualidade subjetiva e consolidação de médias semanais.
- **[x] SB-02 (Acompanhamento de Treinos e Atividades):** Registro de modalidades esportivas, intensidade e contagem semanal de treinos.
- **[x] SB-03 (Webhook Apple Health / Health Auto Export):** Endpoint `/api/health-webhook` para recepção contínua de passos, energia ativa e frequência cardíaca.

---

## 4. Domínio: Entretenimento & Lazer

- **[x] EL-01 (Anime Tracker & AniList Bi-direcional):** Integração completa com GraphQL do AniList (`Tonho123`), permitindo adicionar animes, incrementar episódios vistos (+1), listar o que está assistindo e concluir séries com nota.
- **[x] EL-02 (Calendário de Animes & Novas Temporadas):** Consulta a próximas temporadas, estreias sazonais e cálculo de contagem regressiva para episódios futuros em horário de Brasília.
- **[x] EL-03 (Guia de Streaming TMDB - Onde Assistir?):** Catálogo de onde assistir filmes e séries no Brasil (Netflix, Max, Prime Video, Disney+, etc.), distinguindo assinatura, aluguel e compra.
- **[x] EL-04 (CS2 Esports & FURIA):** Consulta de placares ao vivo, próximos confrontos e resultados de jogos da FURIA Esports.
- **[x] EL-05 (Calculadora de Churrasco & Eventos):** Cálculo determinístico per capita de carnes, cervejas, bebidas não alcoólicas, gelo, carvão e acompanhamentos.
- **[x] EL-06 (Curador de Ideias de Presentes):** Captura contextual de desejos de presentes vinculados a pessoas e datas comemorativas (`gift_ideas`).

---

## 5. Domínio: Utilitários & Segurança

- **[x] US-01 (Cofre Criptografado de Senhas AES-256):** Criptografia simétrica com chave mestre em `vault_credentials`, senhas mascaradas por padrão e gerador criptograficamente seguro de senhas fortes.
- **[x] US-02 (Tradutor e Guia Gastronômico de Cardápios):** Tradução e explicação culinária de pratos internacionais com alertas de alergias e analogias gastronômicas.
- **[x] US-03 (Conversor Universal Instantâneo):** Conversor determinístico com precisão matemática para distância, temperatura, peso, volume culinário e interpretação em linguagem natural.
- **[x] US-04 (Calculadora de Banco de Horas Semanal):** Leitura de jornadas flexíveis e batidas de ponto com cálculo de saldos líquidos diários e fechamento semanal.
- **[x] US-05 (Mobilidade Urbana & Google Maps):** Consulta de tempo estimado com trânsito em tempo real, rotas e cálculo de horário ideal de saída.
- **[x] US-06 (Automação Residencial Alexa):** Acionamento de rotinas e cenas residenciais via Voice Monkey API.
- **[x] US-07 (Gestão Veicular):** Registro de abastecimentos, manutenções e controle de consumo por km (`vehicle_expenses`).

---

## 6. Domínio: Plataforma, Segurança & Core

- **[x] PC-01 (Motor de IA Multimodal):** Orquestração com Google Gemini 1.5/3.6 Flash, suporte a processamento de imagens e transcrição/resposta a áudios do WhatsApp.
- **[x] PC-02 (Gateway WhatsApp & Isolamento):** Integração Evolution API com isolamento inviolável para o número pessoal do usuário (`ALLOWED_PHONE_NUMBER`).
- **[x] PC-03 (Guardrails contra Prompt Injection):** `GuardrailsService` com interceptação de jailbreaks, delimitação semântica de mensagens (`<user_message>`) e sanitização de caracteres invisíveis.
- **[x] PC-04 (Rate Limiter & Security Headers Middleware):** Middleware de Sliding Window por IP (100 req/min e 200 req/min para webhooks) e injeção de headers defensivos HTTP (`nosniff`, `DENY`, `HSTS`).
- **[x] PC-05 (Sanitização de Logs & Zero Leaks):** Erradicação de fallbacks de segredos no código, mascaramento de telefones/JIDs e proteção timing-safe (`hmac.compare_digest`).
- **[x] PC-06 (Modular Prompting):** Decomposição de instruções de sistema em `services/prompts/` estruturadas pelo `PromptComposer`.
- **[x] PC-07 (Dashboard Web Angular Bento Grid):** Interface moderna e responsiva no Firebase Hosting consumindo APIs RESTful do Firestore.
