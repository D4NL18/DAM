# Regras de Negócio: Conversor e Manipulador Universal de Arquivos (US-09)

## Visão Geral
Este documento define as regras de negócio canônicas que regem o comportamento de conversão, fusão, fatiamento e transcodificação de arquivos e documentos no ecossistema DAM.

---

## Regras Canônicas (Padrão P-09XX)

### P-0901: Limite e Validação de Tamanho do Arquivo
- O sistema **DEVE** rejeitar qualquer arquivo individual de entrada com tamanho superior a **25 MB** (26.214.400 bytes).
- Caso o arquivo exceda o limite, o sistema **DEVE** retornar um erro explícito informando o tamanho recebido e o limite máximo permitido.
- Para operações de junção (`merge`), a soma total dos arquivos não **DEVE** exceder **50 MB**.

### P-0902: Sanitização e Proteção Anti-Path-Traversal
- Todos os arquivos intermediários e finais **DEVEM** ser nomeados internamente utilizando identificadores únicos UUID v4 e extensões estritamente validadas.
- O sistema **NUNCA DEVE** utilizar nomes de arquivo fornecidos pelo usuário em chamadas diretas de escrita no sistema de arquivos. Caracteres especiais como `..`, `/`, `\`, `:` **DEVEM** ser neutralizados.
- As extensões de entrada e saída permitidas são restritas a: `.pdf`, `.docx`, `.doc`, `.png`, `.jpg`, `.jpeg`, `.webp`, `.bmp`, `.tiff`, `.txt`.

### P-0903: Ciclo de Vida Efêmero & Zero Vazamento de Disco
- Todo processamento de conversão em disco **DEVE** ocorrer dentro de diretórios temporários efêmeros gerenciados via context managers (`tempfile.TemporaryDirectory`).
- Nenhum arquivo de conversão **DEVE** persistir no servidor após a conclusão ou falha da requisição. A exclusão de temporários **DEVE** ser garantida em bloco `finally`.

### P-0904: Fidelidade Determinística e Isolamento de IA
- As conversões de arquivos **DEVEM** ser executadas exclusivamente por motores matemáticos e bibliotecas determinísticas de software (`pypdf`, `Pillow`, `pdf2docx`, `python-docx`, `reportlab`, `PyMuPDF`).
- O LLM (Gemini) **NUNCA DEVE** tentar simular ou gerar o binário do arquivo; ele atua estritamente como orquestrador da intenção do usuário, extraindo comandos e direcionando para as ferramentas de código nativo.

### P-0905: Auditoria, Métricas e Rastreabilidade Multi-Usuário
- Cada solicitação de conversão **DEVE** registrar um evento na coleção `file_conversions` no Firestore contendo:
  - `user_id`: Identificador do usuário solicitante (`daniel` ou `lari`).
  - `conversion_type`: Identificador do tipo de conversão (ex: `pdf_to_docx`, `images_to_pdf`, `merge_pdfs`, `split_pdf`, `image_convert`, `pdf_to_text`, `docx_to_pdf`).
  - `file_size_bytes`: Tamanho do arquivo original.
  - `status`: `success` ou `failed`.
  - `execution_time_ms`: Tempo de processamento em milissegundos.
  - `created_at`: Data e hora da requisição.
- Os logs **NÃO DEVEM** registrar o conteúdo privado dos documentos nem dados pessoais dos arquivos.

### P-0906: Tratamento de Documentos Criptografados e Corrompidos
- Se um PDF estiver protegido por senha (criptografia), o sistema **DEVE** interceptar a exceção de leitura e retornar mensagem clara: *"Este documento está protegido por senha. Por favor, envie uma versão sem senha para conversão."*
- Arquivos corrompidos ou com cabeçalho inválido **DEVEM** ser rejeitados imediatamente com mensagem amigável, sem causar crash no serviço.
