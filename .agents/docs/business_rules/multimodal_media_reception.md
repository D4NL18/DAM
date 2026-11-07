# Regras de Negócio - PC-01.1: Recepção Multimodal Resiliente (Imagens, Áudios e Documentos)

Este documento especifica as regras de negócio mandatárias para a recepção, processamento e encaminhamento de mídias recebidas via WhatsApp através da Evolution API para os modelos multimodais Gemini.

---

## Regras de Negócio (P-307)

### **P-307.1 (Extração de Mídia sob Demanda via Evolution API):**
1. Ao receber um evento `messages.upsert` com tipo de mensagem multimodal (`imageMessage`, `audioMessage` ou `documentMessage`):
   - O sistema DEVE primeiro verificar se o campo `base64` já foi fornecido diretamente no payload (`message.base64` ou `data.base64`).
   - Caso o `base64` NÃO esteja presente no payload (comportamento padrão da Evolution API), o sistema DEVE obrigatoriamente realizar uma requisição HTTP POST para o endpoint `/chat/getBase64FromMediaMessage/{instance}` da Evolution API utilizando o ID da mensagem (`key.id`) e o payload da mensagem.
   - O timeout da requisição deve ser de no máximo 15 segundos para não travar a esteira do webhook.

### **P-307.2 (Sanitização Defensiva de Base64 e Proteção de Memória):**
1. O Base64 retornado pela Evolution API pode vir acompanhado de prefixos Data URI (ex.: `data:image/jpeg;base64,...`) e espaços/quebras de linha.
2. O sistema DEVE higienizar o Base64 removendo qualquer cabeçalho Data URI antes de decodificar para bytes (`base64.b64decode`).
3. É terminantemente proibido imprimir a string Base64 completa nos logs do sistema para evitar estouro de buffers e vazamento de dados privados. Apenas o tamanho da mídia em bytes e o MIME type podem ser registrados.

### **P-307.3 (Normalização Rigorosa de MIME Types para Gemini Multimodal):**
1. Modelos Gemini (`gemini-1.5-flash`, `gemini-3.6-flash`) exigem formatos MIME types estritos sem parâmetros de codec (ex.: `audio/ogg`, `audio/mp3`, `audio/wav`, `image/jpeg`, `image/png`, `application/pdf`).
2. Qualquer MIME type contendo especificações de codec (ex.: `audio/ogg; codecs=opus`, `audio/ogg; codecs="opus"`) DEVE ser sanitizado extraindo apenas a raiz do tipo (`media_mimetype.split(";")[0].strip()`).
3. Se o MIME type for omitido, o sistema deve assumir:
   - `image/jpeg` para `imageMessage`.
   - `audio/ogg` para `audioMessage`.
   - `application/pdf` para `documentMessage`.

### **P-307.4 (Resiliência e Feedback Gracioso em Falhas de Mídia):**
1. Se a Evolution API falhar ao recuperar a mídia (ex.: erro 400, timeout ou mensagem expirada), o sistema NÃO DEVE chamar o Gemini com o texto cego padrão pedindo para "analisar esta imagem" (evitando que a IA responda "você não me mandou nada").
2. Em caso de falha comprovada no download da mídia:
   - Se for imagem: o bot deve responder educadamente via WhatsApp informando que não foi possível carregar a imagem no momento e solicitar que o usuário reenvie.
   - Se for áudio: o bot deve responder informando que não foi possível processar o áudio no momento e sugerir o reenvio ou texto.
3. Essa tratativa evita que chamadas desnecessárias de tokens sejam desperdiçadas no Gemini sem o binário correspondente.
