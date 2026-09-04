# Roadmap Funcional do Projeto: Assistente DAM (Inteligência Artificial)

## Visão Geral
O DAM (Digital Autonomous Manager) é um assistente pessoal inteligente operando no WhatsApp e integrado a um Dashboard Web (Angular 17), concebido para ser a central de automação, finanças, saúde, entretenimento e rotina do usuário.

Todas as entregas e capacidades do sistema estão organizadas por **Domínios Funcionais**:

---

## 1. Domínio: Gestão Pessoal & Rotina

- **[x] GP-01 (Google Calendar):** Integração com Google Calendar API para agendamento de eventos, consultas com descrição, localização e suporte a fusos horários.
  - **[x] GP-01.1 (CRUD Completo: Edição In-Place e Exclusão Segura no Google Calendar):**
    - **[x] Story 1 (Exclusão Segura de Eventos):** Localização do evento por título/termo e execução de `service.events().delete()` com tratamento de desambiguação e retorno confirmatório.
    - **[x] Story 2 (Edição e Remarcação de Eventos sem Duplicação):** Localização do evento e execução de `service.events().patch()` alterando horários, títulos, locais e descrições sem criar novos eventos.
    - **[x] Story 3 (Permissões Multi-Usuário em Edição/Exclusão):** Governança estrita onde Lari só pode alterar/excluir seus próprios eventos, e Daniel gerencia sua própria agenda.
- **[x] GP-02 (Notas e Lembretes Rápidos):** Modelagem Firestore da coleção `notes_reminders`, criação e busca semântica de notas e lembretes com controle de pendências via WhatsApp.
- **[x] GP-03 (Memória Espacial / Onde Guardei Isso?):** Registro de localizações de objetos físicos e documentos na coleção `item_locations`, mantendo histórico de movimentações.
- **[x] GP-04 (Morning Briefing Proativo das 08:00):** Consolidação matinal automatizada às 08h trazendo Agenda, Tarefas pendentes de hoje, Partidas da FURIA (com regras temporais) e Lançamentos de Animes do dia com idempotência no Firestore (`briefing_logs`).

---

## 2. Domínio: Finanças & Gastos

- **[x] FG-01 (Gestão Multicartão & Classificação):** Suporte estrito aos métodos de pagamento (Cartão de Crédito Pessoal, Secundário e Débito/Pix), confirmação obrigatória de método e gravação na coleção `finances`.
- **[x] FG-02 (Divisão Inteligente de Contas de Restaurante):** Rateio proporcional de itens consumidos com taxa de serviço calculada centavo a centavo, organizado estritamente por nomes de pessoas e chave Pix para pagamento.
- **[x] FG-03 (Splitwise de Viagens e Grupos):** Criação de grupos e despesas compartilhadas nas coleções `trip_groups` e `trip_expenses`, com algoritmo de minimização de dívidas (*Debt Minimization*).
- **[x] FG-04 (GCP Billing & Monitoramento FinOps):** Endpoint de webhook para alertas de orçamentos e monitoramento de custos de nuvem.
- **[x] FG-05 (Resumo Consolidado de Gastos por Cartão e Categoria):** Ferramenta `consultar_resumo_gastos` com agregação mensal/temporal de despesas no Firestore, agrupadas por cartões (Crédito Pessoal, Crédito Secundário, Débito/Pix) e categorias com subtotais, percentuais e destaques sintéticos no WhatsApp.

---

## 3. Domínio: Saúde & Bem-Estar

- **[x] SB-01 (Métricas de Sono e Qualidade):** Registro de horas de sono, qualidade subjetiva e consolidação de médias semanais.
- **[x] SB-02 (Acompanhamento de Treinos e Atividades):** Registro de modalidades esportivas, intensidade e contagem semanal de treinos.
- **[x] SB-03 (Webhook Apple Health / Health Auto Export):** Endpoint `/api/health-webhook` para recepção contínua de passos, energia ativa e frequência cardíaca.
- **[x] SB-04 (Guia Nutricional & Lista de Substituição Inteligente):** Motor de consulta nutricional estrito baseado na Lista de Substituição oficial do Dietbox (135 alimentos em 7 grupos calóricos). Alerta compulsório com busca de dados nutricionais, comparação de macronutrientes e pontos de atenção quando o usuário solicitar alimentos fora da lista.

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
- **[x] US-08 (Gerenciador de Endereços & Locais Salvos):** Armazenamento dinâmico de endereços e locais favoritos no Firestore (`user_addresses`), permitindo consultas de trânsito e rotas por apelidos (casa, trabalho, academia, etc.) sem especificar o local exato.
  - **[x] Story 1 (Modelagem Firestore & Repositório):** Coleção `user_addresses` com isolamento por usuário e chave $O(1)$, normalização de apelidos com remoção de acentos e cache L1 thread-safe.
  - **[x] Story 2 (Tools de Endereços no Assistente):** Ferramentas `salvar_endereco`, `consultar_enderecos_salvos` e `remover_endereco` registradas na IA com validação/geocoding via Google Maps API.
  - **[x] Story 3 (Resolução Dinâmica em Mobilidade & Rotas):** Integração do `resolver_apelido_endereco` no `maps_tool.py` consultando o Firestore com fallback transparente para `settings.py`.


---

## 6. Domínio: Plataforma, Segurança & Core

- **[x] PC-01 (Motor de IA Multimodal):** Orquestração com Google Gemini 1.5/3.6 Flash, suporte a processamento de imagens e transcrição/resposta a áudios do WhatsApp.
- **[x] PC-02 (Gateway WhatsApp & Isolamento):** Integração Evolution API com isolamento inviolável para o número pessoal do usuário (`ALLOWED_PHONE_NUMBER`).
- **[x] PC-03 (Guardrails contra Prompt Injection):** `GuardrailsService` com interceptação de jailbreaks, delimitação semântica de mensagens (`<user_message>`) e sanitização de caracteres invisíveis.
- **[x] PC-04 (Rate Limiter & Security Headers Middleware):** Middleware de Sliding Window por IP (100 req/min e 200 req/min para webhooks) e injeção de headers defensivos HTTP (`nosniff`, `DENY`, `HSTS`).
- **[x] PC-05 (Sanitização de Logs & Zero Leaks):** Erradicação de fallbacks de segredos no código, mascaramento de telefones/JIDs e proteção timing-safe (`hmac.compare_digest`).
- **[x] PC-06 (Modular Prompting):** Decomposição de instruções de sistema em `services/prompts/` estruturadas pelo `PromptComposer`.
- **[x] PC-07 (Dashboard Web Angular Bento Grid):** Interface moderna e responsiva no Firebase Hosting consumindo APIs RESTful do Firestore.
- **[x] PC-08 (Otimização de Tokens & Cache Inteligente de Conversas):** Motor de cache semântico de respostas de prompts com roteamento por volatilidade (reuso de guerra no Clash of Clans, expiração dinâmica de CS2 até 2h antes da partida, bypass compulsório de trânsito em tempo real e ações de escrita).
- **[x] PC-09 (Text-to-Speech & Síntese de Voz / Respostas em Áudio):** Conversão inteligente de respostas textuais do DAM em mensagens de áudio para envio nativo no WhatsApp e streaming de voz.
  - **[x] Story 1 (TTS Service Engine):** Serviço de síntese fonética em `TTSService` gerando stream de áudio com fallback resiliente.
  - **[x] Story 2 (Sanitização de Texto & Normalização Fonética):** Remoção de código markdown (`*`, `_`, emojis, links, tabelas) para dicção limpa e natural.
  - **[x] Story 3 (Gatilhos de Envio & Integração WhatsApp):** Detecção automática de intenção de voz (`should_reply_with_audio`) e envio como nota de voz gravada PTT (`sendWhatsAppAudio`).
  - **[x] Story 4 (Cache de Áudios & FinOps):** Cache L1 em memória de áudios sintetizados com chave hash SHA-256 para zero redundância e economia de custos.
- **[x] PC-10 (Migração para WhatsApp Business Dedicado & Isolamento Inviolável):** Conexão do bot em conta dedicada de WhatsApp Business (+55 71 98171-8497) com isolamento estrito para o número pessoal do usuário (+55 71 99126-9995) e proteção anti-loop para mensagens e áudios enviados pelo bot (`key.fromMe == True`).
  - **[x] Story 1 (Desassociação de Sessão & Conexão do Bot):** Procedimento de logout limpo na Evolution API e emissão de novo QR Code para o WhatsApp Business.
  - **[x] Story 2 (Isolamento Inviolável de Remetente):** Descarte sumário de mensagens de terceiros que entrarem em contato com o WhatsApp Business do bot.
  - **[x] Story 3 (Anti-Loop Robusto com fromMe):** Interceptação no webhook de mensagens originadas pela própria instância do bot para prevenir auto-respostas e loops infinitos.




