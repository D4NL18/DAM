# Regras de Negócio: Otimização Extrema de Tokens & FinOps Score 4.8+ GCP (PC-11)

## Visão Geral
Este documento estabelece as regras canônicas de negócio para redução drástica no consumo de tokens do modelo Google Gemini (prompts, ferramentas, imagens, áudios e documentos) e elevação do Score FinOps do Google Cloud Platform de 3.0/5 para 4.8+/5 no DAM.

---

## Regras Canônicas (Padrão P-11XX)

### P-1101: Dynamic Tool Pruning & Dispatching (Roteamento de Ferramentas)
- O sistema **DEVE** analisar a mensagem do usuário antes de instanciar o modelo Gemini para selecionar estritamente as ferramentas (`AVAILABLE_TOOLS`) compatíveis com a intenção.
- Se a mensagem do usuário for de conversação geral, saudação, agradecimento ou pergunta factual simples sem necessidade de mutação ou consulta externa, o sistema **NÃO DEVE** registrar nenhuma ferramenta (`tools=None`), eliminando o custo de schema JSON de até 7.500 tokens por turno.
- Se a intenção pertencer a um domínio específico (ex: finanças, agenda, notas, mobilidade, anime, nutrição), o sistema **DEVE** despachar unicamente o subconjunto de ferramentas atreladas ao domínio correspondente.

### P-1102: Composição Modular do System Prompt (Core + On-Demand)
- O System Prompt base **DEVE** ser limitado a um núcleo essencial (*Core Base*) contendo unicamente persona, fuso horário oficial de Brasília e diretrizes de isolamento inviolável de dados multi-usuário.
- Diretrizes extensas de regras de domínio (como regras completas do Dietbox, regras do Anilist, regras do Google Calendar e regras financeiras) **NÃO DEVEM** ser concatenadas estaticamente no prompt padrão. Elas **DEVEM** ser injetadas sob demanda apenas quando o classificador de intenção detectar a ativação do respectivo módulo.

### P-1103: Otimização e Downsampling Adaptativo de Imagens
- Todas as imagens recebidas via WhatsApp (JPEG, PNG, WEBP) **DEVEM** passar por pré-processamento com Pillow antes do encaminhamento ao Gemini.
- Imagens com resolução superior a 1024x1024 pixels **DEVEM** ser redimensionadas proporcionalmente para respeitar o teto de 1024px no maior lado, preservando a legibilidade de notas fiscais, cupons e cardápios.
- Imagens em formatos não comprimidos **DEVEM** ser reprocessadas para JPEG com fator de qualidade `quality=80`.
- Documentos escaneados e notas fiscais identificadas **DEVEM** ser convertidas para escala de cinza com aumento de contraste dinâmico, reduzindo a cota de tokens visuais em até 80%.

### P-1104: Extração Textual Local Prioritária para PDFs (PyMuPDF)
- Ao receber documentos no formato PDF, o sistema **DEVE** tentar realizar a extração direta do texto digital das páginas utilizando a biblioteca local `PyMuPDF` (`fitz`), a custo computacional e de tokens zero.
- Se o documento contiver texto extraível legível, o sistema **DEVE** enviar apenas o texto puro sanitizado e formatado para a LLM, sendo **TERMINANTEMENTE PROIBIDO** enviar o arquivo PDF cru como imagem multimodal quando o texto for diretamente extraível.
- Se o documento ultrapassar 3 páginas, o sistema **DEVE** aplicar chunking seletivo filtrando as seções relevantes à solicitação do usuário antes de injetar no prompt.

### P-1105: Filtragem de Áudio, VAD e Normalização Fonética
- Mensagens de voz e arquivos de áudio recebidos **DEVEM** passar por corte de silêncio (Voice Activity Detection - VAD) no início e final do arquivo, eliminando segundos mortos que geram cobrança de tokens multimodais.
- O áudio **DEVE** ser normalizado para canal mono em taxa de amostragem de 16 kHz antes do envio.

### P-1106: Cache Multimodal com Hash Criptográfico SHA-256
- O serviço de cache semântico (`ConversationCacheService`) **DEVE** suportar mensagens contendo mídias (fotos, notas de voz e documentos).
- A chave de cache para mídias **DEVE** ser composta pelo hash SHA-256 do payload binário da mídia combinado com o texto do comando e o `remote_jid` do usuário remetente.
- Se uma mesma imagem, nota fiscal ou documento for reenviado com a mesma solicitação dentro da janela de validade do cache, o sistema **DEVE** retornar a resposta armazenada no cache L1/L2 sem acionar a LLM.

### P-1107: Gemini Context Caching para Dados Estáticos
- Para sessões com histórico longo ou bases documentais volumosas que ultrapassem o limiar de tokens do Gemini, o sistema **DEVE** utilizar o `genai.caching.CachedContent` com TTL programado.
- Os tokens lidos do Context Cache usufruem do desconto de até 75-90% de tarifa em relação a tokens convencionais de entrada.

### P-1108: Arquitetura Cloud Run Scale-to-Zero & Free Tier First
- O microsserviço `backend_ia` **DEVE** ser empacotado e executado no **Google Cloud Run** com configuração estrita de `--min-instances=0`, garantindo consumo zero de CPU e memória durante períodos sem requisições.
- O sistema **DEVE** aproveitar a cota gratuita vitalícia (Always Free Tier) do Cloud Run (2 milhões de requisições e 360.000 GB-segundos mensais).
- A VM `e2-micro` existente no Compute Engine **DEVE** ser mantida exclusivamente para a Evolution API e PostgreSQL Alpine.

### P-1109: Lifecycle Management no Cloud Storage (Auto-Cleanup em 7 Dias)
- Todos os buckets do Google Cloud Storage vinculados a uploads de mídias, conversões temporárias e arquivos intermediários **DEVEM** possuir regra de Lifecycle Management ativa de expiração (`Delete`) após 7 dias de criação (`Age: 7`).
- Backups de bancos de dados ou artefatos permanentes **DEVEM** ser transicionados para a classe `Nearline` após 30 dias e `Coldline` após 90 dias.

### P-1110: Governança de Logs e Circuit Breaker Orçamentário
- O Google Cloud Logging **DEVE** configurar filtro de exclusão no Log Sink para descartar mensagens de severidade inferior a `WARNING` originadas dos containers de aplicação, prevenindo custos de ingestão além da cota de 50 GiB/mês.
- O sistema **DEVE** monitorar continuamente as notificações de faturamento (`/api/billing-alert`). Se o consumo acumulado do mês atingir ou superar 95% do teto orçamentário configurado, o sistema **DEVE** ativar automaticamente o *Circuit Breaker Orçamentário*, operando em modo econômico e notificando os administradores via WhatsApp.
