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

## US-08: Gerenciador de Endereços & Locais Salvos
- **Persistência Firestore (`user_addresses`):** Coleção dedicada com schema enriquecido (`alias`, `address`, `formatted_address`, `latitude`, `longitude`, `details`, `updated_at`) e chave $O(1)$ particionada por `user_jid`.
- **Repositório (`address_repository.py`):** Normalização de apelidos com remoção de acentos (`unicodedata`), mapeamento fonético ("casa", "trabalho", "academia"), isolamento multi-tenant estrito e cache L1 thread-safe com `threading.RLock`.
- **Ferramentas de IA (`address_tool.py`):** `salvar_endereco`, `consultar_enderecos_salvos` e `remover_endereco` com validação/geocodificação via Google Maps Geocoding API.
- **Integração com Mobilidade (`maps_tool.py`):** `resolver_apelido_endereco` atualizado para priorizar locais salvos no banco sobre as variáveis estáticas do sistema, permitindo consultas transparentes de rotas como "tempo de casa pro trabalho" ou "rota até a academia".

## PC-09: Text-to-Speech & Respostas em Áudio (WhatsApp PTT)
- **Motor TTS (`tts_service.py`):** Síntese de voz com sanitização fonética rigorosa (remoção de marcadores markdown `*`, `_`, emojis, links e blocos de código) para dicção limpa e natural.
- **Detecção Inteligente de Voz (`should_reply_with_audio`):** Acionamento automático de resposta por voz quando o usuário envia mensagem de áudio ou pede explicitamente resposta em áudio no texto ("em áudio", "me manda áudio", "responde por voz").
- **Envio PTT Nativo (`whatsapp_service.py`):** Método `send_voice_note` via endpoint `/message/sendWhatsAppAudio/{instance}` da Evolution API, entregando o áudio como nota de voz gravada nativa com forma de onda no WhatsApp.
- **FinOps & Resiliência:** Cache L1 de áudios idênticos com chave SHA-256 e fallback automático e transparente para mensagem de texto caso a síntese de voz falhe.

## PC-10: Migração para WhatsApp Business Dedicado & Isolamento Inviolável
- **Conta Dedicada de Bot (+55 71 98171-8497):** Desacoplamento entre a conta pessoal do usuário e a conta do assistente. A instância `dam_bot` da Evolution API agora conecta com o WhatsApp Business do bot via QR Code gerado pelo script `conectar_whatsapp.py`.
- **Isolamento Inviolável (P-0601 / `ALLOWED_PHONE_NUMBER=5571991269995`):** O webhook FastAPI descarta sumariamente qualquer mensagem cujo remetente não coincida com os 8 dígitos e DDD do número pessoal do Daniel (`71 99126-9995`), blindando o bot contra mensagens acidentais, terceiros ou spams que entrem em contato com o WhatsApp Business.
- **Anti-Loop Abrangente (`fromMe: true`):** Em uma conta dedicada, qualquer evento de mensagem gerado com `key.fromMe == True` representa um envio realizado pela própria instância do bot (seja texto com `\u200b`, áudio PTT ou imagem). A guard clause no webhook intercepta e ignora essas mensagens imediatamente, eliminando riscos de eco e loops recursivos infinitos.
- **Automação de Conexão (`conectar_whatsapp.py`):** Script aprimorado com reset de chaves anteriores (`logout`), configuração automática do webhook (`/api/whatsapp/webhook`), aplicação de flags de privacidade (`groupsIgnore`, `readMessages=false`, `alwaysOnline=false`) e renderização de HTML com QR Code no navegador.

## EL-07: Repositório de Vídeos Salvos (TikTok, Instagram, YouTube) [P-0701]
- **Persistência Firestore (`saved_videos`):** Coleção dedicada com schema enriquecido (`url`, `plataforma`, `titulo`, `descricao`, `categoria`, `tags`, `status`, `assistido_em`, `created_at`, `updated_at`) e isolamento estrito por `userId` (Daniel e Lari).
- **Repositório (`saved_videos_repository.py`):** Singleton thread-safe com `threading.RLock`, persistência Firestore e fallback em memória. Algoritmo de busca tolerante a acentos (`unicodedata`) com priorização de correspondência de todos os tokens sobre correspondências parciais.
- **Ferramentas de IA (`saved_videos_tool.py`):**
  - `salvar_video`: Detecção automática da plataforma a partir da URL (TikTok, Instagram, YouTube, Outro), validação rigorosa de esquema http/https com sanitização de injeções (javascript/data), inferência de título sintético caso o usuário forneça apenas descrição ou link, e normalização de tags.
  - `consultar_videos_salvos`: Busca semântica por palavras-chave em descrição, título, categoria ou tags, filtros opcionais por plataforma e status (`pendente`/`assistido`), com paginação e formatação limpa no WhatsApp.
  - `marcar_video_assistido`: Atualização de status para 'assistido' com suporte a ID ou termo textual, e desambiguação amigável em caso de múltiplos candidatos.
  - `remover_video_salvo`: Exclusão segura com proteção contra remoção acidental.
- **Integração no Motor do DAM (`ai_service.py` & `system_base.py`):** Registro de ferramentas em `AVAILABLE_TOOLS` e instruções no prompt mestre para identificação de links enviados e recuperação contextual sob demanda.

## US-09: Conversor e Manipulador Universal de Arquivos e Documentos [P-0901 a P-0906]
- **Motor Central Determinístico (`file_converter_service.py`):**
  - *PDF para Word (.docx):* Conversão estrutural de texto e tabelas via `pdf2docx` em diretório temporário isolado.
  - *Word (.docx) para PDF:* Renderização determinística de estilos, parágrafos e tabelas via `python-docx` + `reportlab`.
  - *Imagens para PDF:* Combinação de uma ou múltiplas fotos (JPG/PNG/WEBP/BMP) em documento PDF unificado via `Pillow`.
  - *Fusão de PDFs (`merge_pdfs`):* União sequencial de múltiplos PDFs mantendo ordenação e metadados via `pypdf`.
  - *Fatiamento de PDF (`split_pdf`):* Extração por intervalos (ex: `1-3, 5`) com validação de limites via `pypdf`.
  - *PDF para Imagens (`pdf_to_images`):* Renderização de páginas em alta resolução (150 DPI) via `PyMuPDF` (`fitz`).
  - *Transcodificação de Imagens (`convert_image`):* Conversão entre PNG, JPEG e WEBP com controle de compressão via `Pillow`.
  - *Extração de Texto (`pdf_to_text`):* Extração direta de texto para leitura rápida no chat via `pypdf`.
- **Segurança & Defesa (P-0901 a P-0903):** Limite máximo de 25 MB por arquivo (50 MB total no merge), sanitização anti-traversal e ciclo de vida efêmero garantido via `tempfile.TemporaryDirectory` (zero vazamento em disco). PDFs protegidos por senha são interceptados com mensagem explicativa amigável (P-0906).
- **Persistência Firestore (`file_conversions`):** Auditoria de operações (`user_id`, `conversion_type`, tamanhos em bytes, status, duração em ms) com isolamento estrito por usuário e fallback em memória thread-safe (`file_conversion_repository.py`).
- **Interfaces & Integração:**
  - *RESTful API:* Router `/api/files` (`/convert`, `/supported-formats`, `/conversions/history`) com download imediato via stream.
  - *WhatsApp & IA:* Tool `gerenciar_arquivos` integrada em `AVAILABLE_TOOLS` do Gemini, suporte a `documentMessage` no webhook e envio de arquivos de volta via `WhatsAppService.send_document`.

## GP-04.1: Correções e Aprimoramentos do Morning Briefing [P-0410 a P-0418]
- **Lembretes Diários & Formatação (P-0410, P-0411):**
  - O resumo matinal exibe estritamente lembretes com status `pendente` agendados para a data corrente (fuso Brasília UTC-3), eliminando lembretes futuros distantes do briefing diário.
  - Sanitização de tags via `_formatar_tags_exibicao` com regex `[a-zA-Z0-9_\-]`, eliminando bugs de representação de listas brutas aninhadas (`#[['financas', 'claro']]`) e convertendo para formato limpo `[#financas #claro]`.
- **Filtros Estritos de Animes (P-0412 a P-0414):**
  - *Lançamento de episódios (hoje e grade semanal):* Considera ESTRITAMENTE animes com status `assistindo` (watching).
  - *Lançamento de temporadas / continuações / sequências:* Considera ESTRITAMENTE animes em `assistindo` ou `concluido` (completed). Veto absoluto a menções de animes `dropado` (dropped) ou `pausado` (paused/on hold).
  - *Animes para assistir:* A busca por animes na lista de planejamento (`planejo_assistir`/`plan_to_watch`) retorna animes em planning OU em watching onde o usuário ainda viu 0 episódios.
  - Mapeamento robusto na sincronização com AniList: `PAUSED` -> `pausado`, `DROPPED` -> `dropado`.
- **Clash of Clans & Capital do Clã (P-0415, P-0416):**
  - Trata o comportamento da API Supercell onde o array `members` de `capitalraidseasons` omite jogadores que ainda não atacaram. Quando `membro is None` em temporada `ongoing`, gera alerta com 5 ataques disponíveis.
  - Alertas de Guerra Regular/CWL e Raid Weekend coexistem no briefing matinal quando ambos estiverem ativos e com ataques pendentes.
- **Disparo Multi-Usuário & Isolamento de Contexto (P-0417, P-0418):**
  - Scheduler roda minuto a minuto avaliando as preferências de cada usuário ativo (`daniel`, `lari`, etc.) via `verificar_e_disparar_briefings_agendados`, disparando os briefings no horário exato configurado por cada um.
  - `montar_resumo_matinal` e `enviar_briefing_matinal` chaveiam o `UserContext.set_user(target_user_id)` com bloco seguro `try/finally`, assegurando que agenda, lembretes e dados de saúde de Daniel e Lari permaneçam 100% isolados sem vazamentos cruzados.

## GP-04.2: Lembretes Restritos ao Dia por Padrão e Próximo Anime em Tempo Real [P-0419 a P-0421]
- **Lembretes Diários por Padrão (P-0419):**
  - A ferramenta `listar_lembretes_pendentes` opera com `apenas_hoje=True` por padrão, garantindo que consultas gerais de lembretes tragam estritamente pendências do dia corrente (UTC-3), preservando a privacidade e relevância temporal. Listagem de tarefas futuras ou completas exige agora o parâmetro explícito `apenas_hoje=False`.
- **Higienização Defensiva de Tags na Ingestão (P-0420):**
  - Em `criar_lembrete` e `criar_anotacao`, toda entrada de tags (seja lista, string com vírgula ou string serializada de array como `"['financas', 'claro']"`) é sanitizada via regex `TAG_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9_\-]+")`, persistindo listas limpas no Firestore e exibindo formatação limpa `[#financas #claro #recorrente]`. Registros legados no Firestore foram higienizados.
- **Renovação Autônoma de Próximo Episódio via AniList (P-0421):**
  - `anime_tracker_tool.py` implementa `_renovar_proximos_episodios_expirados()` que detecta animes em exibição (`assistindo`) com `airing_at` vencido no passado e reconsulta autonomamente o endpoint GraphQL do AniList.
  - O Morning Briefing (`_obter_info_animes_briefing`) e a grade semanal (`grade_semanal_animes`) acionam a renovação dinâmica, selecionando com precisão os lançamentos reais de domingo (como `Seihantai na Kimi to Boku 2nd Season` às 05:00 e `Mushoku Tensei III` às 12:00) e eliminando qualquer exibição errônea de animes de meses posteriores (`Seishun Buta Yarou` em 15/10).

## FG-06: Dashboard Avançado de Gastos & Gestão de Categorias e Cartões [P-001 a P-013]
- **Design & Experiência Visual (P-001, P-002, P-006):**
  - Dashboard Angular reproduz com precisão o design moderno: saudação personalizada, título "Orçamento" com botão de olho para alternar visibilidade (ocultando com `••••••` para privacidade), seletor de mês `< Mês de Ano >` e abas em estilo pílula arredondada (`Receita`, `Despesa fixa`, `Despesa variável`).
  - Layout dividido em: tabela de lançamentos com badges de categoria coloridos e Donut Chart ECharts com raio customizado e legenda lateral em grid de 2 colunas com percentuais e cores consistentes. Barra inferior fixa com saldo do período em vermelho vibrante.
- **Granularidade e Filtro de Categorias (P-003, P-007, P-008):**
  - Paleta com mais de 12 categorias padrão de alta granularidade (Mercado, Carro, Oliver, Casa, Família, Christian, Farmácia, Karen, Gatos, Lazer, Mercadinho, iFood, etc.), com códigos hexadecimais unificados entre tabela e gráfico.
  - Filtro interativo por categoria via dropdown e clique direto nas fatias do Donut chart.
- **Gestão Completa de Categorias e Cartões (P-009 a P-012):**
  - Modal integrado permitindo adicionar novas categorias (com seletor/paleta de cores), renomear e excluir categorias com migração automática para 'Outros'.
  - Aba de cartões permitindo cadastrar, renomear e excluir métodos de pagamento com tipo (Crédito, Débito/Pix, Benefício, Outro).
  - Router `/api/v1/finance` no FastAPI com endpoints: `/dashboard` (agregação com suporte a ano, mês, tipo e categoria), `/transactions` (CRUD com suporte a tipo fixa/variável/receita, parcelas e titular), `/categories` (CRUD com fallback para defaults) e `/cards` (CRUD com fallback para defaults).
  - CORS atualizado permitindo `PUT` e `DELETE`.
  - Isolamento rigoroso por `X-User-Id` garantindo conformidade SecOps e prevenção contra IDOR.

## FG-07: Evolução Temporal de Gastos e Receitas por Períodos [P-014 a P-020]
- **Design & Experiência Visual (P-014 a P-017):**
  - Switcher no cabeçalho permitindo alternar fluidamente entre `Visão Mensal` (FG-06) e `Evolução Temporal` (FG-07).
  - Barra superior de períodos com pílulas arredondadas: `Mês atual`, `3 meses`, `6 meses`, `12 meses` e `Personalizar` (com modal para datas customizadas).
  - Card principal de tendências com três KPIs de topo: `● Receita` (bullet verde, valor, badge circular com seta verde, comparativo percentual ou 'Sem período anterior'), `● Gastos` (bullet vermelho, valor, badge circular com seta vermelha) e `Saldo do período`.
  - Respeito à alternância de privacidade: valores são mascarados com asteriscos `*****` mantendo a estética e cores do design original.
- **Gráfico de Curvas Suaves ECharts (P-018):**
  - Gráfico Spline Area com duas séries contínuas: Receitas (linha verde com gradiente de preenchimento vertical suave) e Gastos (linha vermelha com gradiente de preenchimento vertical suave).
  - Eixo X com siglas de meses em português e eixo Y abreviado em `mil` (ex: `10 mil`, `20 mil`).
  - Tooltip customizado e interativo com valores em moeda brasileira (`R$`).
- **Backend & Agregação Temporal (P-019, P-020):**
  - Endpoint `GET /api/v1/finance/trends` em `backend_ia/routers/finance.py` com agregação cronológica mês a mês, cálculo de balanço mensal e cálculo comparativo contra o período imediatamente anterior.
  - Isolamento estrito multi-usuário (`X-User-Id`), testes automatizados de unidade e segurança com 100% de cobertura.


