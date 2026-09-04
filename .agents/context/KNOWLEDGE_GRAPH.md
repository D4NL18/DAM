# Knowledge Graph & Memória de Contexto do DAM

Este arquivo armazena decisões definitivas e sumarizadas das funcionalidades concluídas.

## Fase 1: Fundação do Motor de IA e Mensageria
- **FastAPI Webhook:** Recebe payload da Evolution API (`POST /api/whatsapp/webhook`).
- **Function Calling:** Gemini Flash com registry dinâmico de tools.
- **Segurança:** Autenticação via `WEBHOOK_TOKEN` no header `apikey` / `Authorization`.

## Fase 2: Dashboard Web (Angular + Spring Boot)
- **Core API:** Spring Boot 3 com endpoints agregados.
- **Frontend:** Angular 17 Standalone Components, Design System Stitch (SCSS) e gráficos de métricas.

## Fase 3: Pilares Base de Dados & Mensageria
- **Health Webhook (`US-3.1`, `US-3.2`):** Armazena dados do Health Auto Export em `health_metrics` e consulta via `health_tool.py`.
- **Finance Tool (`US-3.3`):** Grava receitas/despesas em `finances`.
- **Calendar Tool (`US-3.4`):** Agendamentos no Google Calendar via Service Account GCP.
- **Isolamento de Chat & Preservação de Notificações (`US-3.5`):**
  - Webhook valida estritamente `is_allowed_user` (comparando últimos 8 dígitos e DDD com `ALLOWED_PHONE_NUMBER`).
  - Fail-safe ativo: se `ALLOWED_PHONE_NUMBER` estiver vazio, nenhuma mensagem é processada.
  - Grupos (`@g.us`) e canais são sumariamente ignorados com HTTP 200 rápido e status `ignored`.
  - Evolution API configurada com `readMessages=false`, `readStatus=false`, `groupsIgnore=true`, `alwaysOnline=false` em `docker-compose.yml` e `conectar_whatsapp.py`, garantindo que nenhuma notificação do celular seja cancelada ou suprimida pelo bot.
- **Multimodalidade no WhatsApp (`US-3.6`):** Extração de `imageMessage` e `audioMessage` em Base64 no webhook repassando ao Gemini com suporte nativo a visão e áudio.
- **Calendar Enriquecido (`US-3.7`):** Suporte a `descricao` e `localizacao` (Google Meet ou endereço físico) na criação e consulta de eventos no Google Calendar.
- **Integração Dashboard (`US-3.8`):** Build do Angular 17 validado com budgets expandidos e DTOs alinhados à Core API Spring Boot.

## Fase 4: Integrações Externas Avançadas
- **Veículo Fiat Fastback (`US-4.1`):** `vehicle_tool.py` com telemetria em tempo real (combustível, autonomia, pressão de pneus, bateria) e acionamento seguro de travas (`travar`/`destravar`).
- **Esports CS2 (`US-4.2`):** `esports_tool.py` integrado a dados competitivos HLTV para consulta de partidas, placares e confrontos (FURIA, MIBR, Imperial, etc.).

## Fase 5: Automação Residencial e Alertas de Nuvem
- **Alertas de Custo GCP (`US-5.1`):** Endpoint `/api/billing-alert` conectado ao Cloud Pub/Sub, calculando percentual gasto contra o orçamento e disparando notificações proativas no WhatsApp.
- **Automação Alexa (`US-5.2`):** `alexa_tool.py` para acionamento de rotinas, cenas e ambientes inteligentes da casa via chat.

## Fase 6: Segurança, Auditoria e Refinamento
- **SecOps (`security_service.py`):** Sanitização e mascaramento de CPFs, Bearer tokens, senhas e API keys em logs.
- **Proteção Timing-Safe:** Autenticação com `secrets.compare_digest` para neutralizar ataques de temporização.

## Fase 7: Refatoração UI/UX (Frontend Angular)
- **Agenda Bento Grid (`agenda-dashboard`):** Exibição de próximos eventos, linha do tempo, integração de reuniões (Meet), filtro por categorias e insights preditivos da IA.

## Fase 8: Mobilidade Urbana e Trânsito
- **Google Maps (`maps_tool.py`):** Cálculo de tempo real com tráfego, sugestão de rotas alternativas, tratamento de apelidos "Casa"/"Trabalho" e cálculo inteligente do horário de saída para compromissos.

## Fase 9: Gestão de Conhecimento e Lembretes
- **Anotações e Alertas (`notes_tool.py`):** Coleção Firestore `notes_reminders`, categorização por tags, busca semântica, lista de pendências e fechamento de lembretes.

## Fase 10: Curador de Presentes e Datas Especiais
- **Memória Afetiva (`gift_curator_tool.py`):** Coleção `gift_ideas`, captura de desejos ao longo do ano e alertas proativos configuráveis com semanas de antecedência a aniversários e datas comemorativas.

## Fase 11: Divisor Inteligente de Contas de Restaurante
- **Smart Split (`restaurant_split_tool.py`):** Rateio proporcional de itens individuais e compartilhados, aplicação justa da taxa de serviço de 10% com algoritmo de ajuste de centavos (*penny balancing*) e cobrança formatada com chave Pix.

## Fase 12: Memória Espacial ("Onde Guardei Isso?")
- **Localizador de Objetos (`item_finder_tool.py`):** Coleção `item_locations`, busca semântica e histórico cronológico de movimentação de itens.

## Fase 13: Cofre Seguro de Senhas e Credenciais
- **Password Vault (`password_vault_tool.py`):** Coleção `vault_credentials` com criptografia simétrica AES/Fernet e derivação PBKDF2HMAC (SHA-256), gerador criptográfico de senhas seguras (`secrets`) e máscara de exibição (`Abc****z9`).

## Fase 14: Guia de Streaming Direto ("Onde Assistir?")
- **Streaming Guide (`streaming_tool.py`):** Consulta a plataformas disponíveis no Brasil (Netflix, Max, Prime, Disney+, Apple TV+, Globoplay), diferenciação entre assinatura, aluguel e compra, integração TMDB/JustWatch e cache.

## Fase 15: Calculadora Inteligente de Churrasco e Eventos
- **BBQ Planner (`bbq_planner_tool.py`):** Dimensionamento per capita de carnes (bovina, linguiça, frango), bebidas (cerveja, refrigerante, água), carvão, sacos de gelo, acompanhamentos e checklist pronto para cópia.

## Fase 16: Tradutor e Guia Gastronômico de Cardápios ao Vivo
- **Menu Translator (`menu_translator_tool.py`):** Tradução contextual culinária internacional (Francês, Italiano, Alemão, Japonês, Espanhol, Inglês), técnicas gastronômicas, analogias culturais brasileiras e detecção de alérgenos/restrições.

## Fase 17: Conversor Universal Instantâneo
- **Unit Converter (`unit_converter_tool.py`):** Conversão determinística de alta precisão de distância (mi/km, ft/cm), temperatura (°F/°C com contexto culinário de forno), massa (lb/kg, oz/g) e volumes culinários (gal/L, fl oz/ml, xícaras/ml).

## Fase 18: "Splitwise" de Bolso para Viagens e Grupos
- **Trip Ledger (`trip_ledger_tool.py`):** Coleções `trip_groups` e `trip_expenses`, controle de gastos compartilhados e algoritmo de minimização de dívidas (*Debt Minimizer*) para menor número de transações Pix.

## Fase 19: Calculadora de Banco de Horas Semanal
- **Work Hours (`work_hours_tool.py`):** Coleção `work_hours`, parser determinístico de horários flexíveis ("8h", "7h30", "9h15", batidas de ponto), balanço diário e fechamento consolidado semanal de créditos/débitos.

## Fase 20: Central de Animes e Rastreamento AniList (Anime Tracker)
- **Anime Tracker (`anime_tracker_tool.py`):** Coleção `anime_watchlist`, integração direta com GraphQL pública do AniList, sincronização de perfil (`Watching`/`Planning`), contagem regressiva e horários em tempo real no fuso de Brasília, rastreamento de continuações/sequências (`relations`) e lançamentos sazonais (Winter, Spring, Summer, Fall).

## Fase 21: Morning Briefing Proativo Agendado
- **Morning Briefing (`briefing_service.py`, `routers/briefing.py`):** Disparo proativo diário às 08:00 no WhatsApp via Evolution API para `ALLOWED_PHONE_NUMBER`. Agrega 4 pilares: Google Calendar (eventos do dia), Lembretes/Tarefas do dia, Jogos da FURIA (resultado e placar para partidas da madrugada entre 00h e 08h; horário e adversário para partidas posteriores) e Animes da lista pessoal que lançam episódio no dia. Garantia de idempotência com a coleção Firestore `briefing_logs`.

## SB-04: Guia Nutricional & Lista de Substituição Inteligente (Dietbox)
- **Prescrição Estruturada (`nutrition_dietbox_data.py`):** Catálogo dos 135 alimentos do PDF oficial do Dietbox (Samuel Meller Silva - 05/10/2023) nos 7 grupos calóricos: Carboidratos (150 Kcal), Carnes e Ovos (190 Kcal), Frutas (70 Kcal), Laticínios (120 Kcal), Legumes e Verduras (15 Kcal), Leguminosas (55 Kcal) e Óleos e Gorduras (73 Kcal).
- **Ferramentas Nutricionais (`nutrition_tool.py`):**
  - `consultar_lista_substituicao`: Consulta por categoria ou alimento individual com listagem de porções caseiras, gramaturas e alternativas equivalentes no mesmo grupo.
  - `avaliar_substituicao_alimento`: Avaliação de substituição alimentar. Se o alimento desejado NÃO constar na lista oficial, aciona alerta mandatório em destaque (`⚠️ ALERTA: O alimento NÃO CONSTA na sua Lista de Substituição oficial do Dietbox!`), realiza busca de composição nutricional comparando com o item ou grupo prescrito e elenca pontos de atenção críticos (densidade calórica, sódio, índice glicêmico, gorduras saturadas).
- **Diretrizes de Prompt (`nutrition_rules.py`, `prompt_composer.py`):** Regras estritas garantindo que o assistente alerte de forma ostensiva sobre alimentos fora do plano e recomende validação com o nutricionista.

## FG-05: Resumo Consolidado de Gastos por Cartão e Categoria
- **Ferramenta `consultar_resumo_gastos` (`finance_tool.py`):** Consulta e agregação na coleção `finances` do Firestore com filtro temporal (mês/ano padrão corrente ou dias retroativos). Apresenta Total Geral, Subtotais por Cartão (Crédito Pessoal, Crédito Secundário, Débito/Pix) com valores e percentuais, Subtotais por Categoria em ordem decrescente, e destaque das Top 3 maiores compras sem poluir o chat.
- **Diretrizes de Prompt (`financial_rules.py`):** IA instruída a invocar obrigatoriamente a ferramenta ao receber dúvidas sobre gastos acumulados do mês ("como tão meus gastos?", "resumo financeiro"), sem alegar ausência de função de extrato.

## PC-08: Otimização de Tokens & Cache Inteligente de Conversas
- **Serviço de Cache (`cache_service.py`):** Motor semântico de cache L1 (Memória thread-safe com `threading.RLock`) e L2 (Firestore `conversation_cache`) integrado ao ciclo de vida de `AIService.process_message`.
- **Roteamento de Volatilidade:**
  - *Clash of Clans:* Reuso de respostas de guerra/raid (TTL 1h) eliminando chamadas repetidas à LLM no mesmo dia.
  - *CS2 Esports:* Expiração dinâmica calculada para até 2h antes da partida ($T_{jogo} - 2\text{h}$); bypass quando a menos de 2h ou ao vivo.
  - *Trânsito & Mobilidade:* Bypass compulsório (TTL 0) garantindo checagem sempre fresh em tempo real.
  - *Ações & Mutações:* Bypass compulsório para garantir execução determinística de escritas no banco.
  - *Informativos Estáticos:* Cache de 12h para consultas pesadas (Dietbox, TMDB, conversões).
- **Métricas:** Rastreamento acumulado de `hits`, `misses` e `tokens_saved_estimated`.




