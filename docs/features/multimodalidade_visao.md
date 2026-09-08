# 🎙️ Funcionalidade: Mensageria Multimodal (Áudios & Imagens no WhatsApp)

## 1. Descrição Geral
Permite que o usuário interaja com o DAM enviando mensagens de voz naturais ou fotografias diretamente pelo WhatsApp. O sistema processa áudios e imagens através das capacidades multimodais nativas dos modelos Gemini 1.5.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Enviando Mensagens de Áudio
1. No WhatsApp, grave um áudio normalmente pelo botão de microfone.
2. Fale de forma clara sua solicitação (ex: *"DAM, anote que comprei R$ 80 de comida japonesa no crédito e marque reunião com o Pedro amanhã às 16h"*).
3. O bot escuta, transcreve, executa as ferramentas necessárias e responde por texto com a confirmação.

### Enviando Imagens
1. Fotografe um documento, nota fiscal, comprovante ou foto do dia a dia.
2. Se desejar, adicione uma legenda (ex: *"Registre este comprovante"* ou *"O que é este prato no cardápio?"*).
3. Envie a foto no chat. O bot analisa visualmente o conteúdo e responde.

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Transcrever áudios em português brasileiro com alta fidelidade a gírias, termos técnicos e números.
* Executar *Function Calling* a partir de comandos falados em áudio (ex: agendar reuniões ou lançar despesas).
* Ler comprovantes de pagamento e notas fiscais com OCR multimodal para extração de valores, datas e estabelecimentos.
* Interpretar fotos de itens, objetos, telas e textos impressos.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Responder em Áudio Sintetizado (TTS):** No momento, o bot ouve em áudio, mas sempre responde por **texto** no WhatsApp (respostas em áudio geradas por TTS estão previstas em fase posterior).
* **Vídeos Longos:** O pipeline processa fotos e áudios; vídeos pesados de longa duração não são suportados para evitar lentidão no webhook.
* **Fotos Borradas ou Ilegais:** Imagens completamente ilegíveis, escuras ou fora de foco podem dificultar a extração correta de dígitos em notas fiscais.
