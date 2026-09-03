# 💡 Funcionalidade: Automação Residencial (Alexa Smart Home)

## 1. Descrição Geral
Permite controlar dispositivos inteligentes da casa e disparar rotinas da Amazon Alexa através de mensagens no WhatsApp. O usuário pode ligar luzes, acionar cenas ("Modo Cinema", "Boa Noite") ou controlar aparelhos por cômodo ou ambiente.

---

## 2. Como Configurar a Conexão Real (Voice Monkey - 3 Minutos)

O DAM utiliza o **Voice Monkey API v2** para enviar gatilhos da nuvem para a sua Alexa física sem você precisar abrir portas de roteador nem ter servidor local.

### Passo 1: Ativar a Skill no Celular
1. Abra o aplicativo **Amazon Alexa** no seu celular.
2. Vá em **Mais $\rightarrow$ Skills e Jogos** e pesquise por **Voice Monkey**.
3. Toque em **Ativar para uso** e faça login com sua conta da Amazon.

### Passo 2: Pegar o Token de API
1. No seu navegador, acesse [**https://voicemonkey.io**](https://voicemonkey.io) e faça login com a mesma conta Amazon.
2. No menu lateral, acesse **API** e copie o seu **API Token**.
3. No painel **Monkeys**, crie gatilhos virtuais com os nomes que desejar (ex: `modo-cinema`, `luzes-sala`, `desligar-tudo`).

### Passo 3: Colocar o Token no DAM
Basta adicionar a variável no `.env` do DAM:
```env
VOICE_MONKEY_API_TOKEN=seu_token_aqui
```

### Passo 4: Criar a Rotina no App Alexa
No app da Alexa:
1. Vá em **Mais $\rightarrow$ Rotinas $\rightarrow$ + (Criar Rotina)**.
2. **Quando isto acontecer:** Escolha **Casa Inteligente $\rightarrow$ Seu Monkey (ex: `modo-cinema`)**.
3. **Adicionar Ação:** Escolha o que a Alexa deve fazer (ex: regular luzes para 20%, ligar TV, fechar persianas).
4. Salve! A partir desse momento, quando você pedir no WhatsApp do DAM, a Alexa executa a rotina imediatamente.

---

## 3. Como Utilizar pelo WhatsApp (Exemplos Práticos)

### Acionando Cenas e Aparelhos
* *"DAM, ative o modo cinema na sala"*
* *"Ligue as luzes do escritório"*
* *"Desligue tudo, vou dormir"*

### Fazendo a Alexa Falar um Anúncio (TTS)
* *"Mande a Alexa falar 'O almoço está na mesa' na cozinha"*
* *"Diga na Alexa do quarto: 'Hora de acordar!'"*

---

## 4. O que a Funcionalidade CONSEGUE Fazer
* Disparar rotinas complexas da Alexa (luzes, ar-condicionado, TV, persianas, música) a partir de mensagens de texto ou áudio no WhatsApp.
* Enviar anúncios de voz em tempo real (Text-to-Speech) para alto-falantes Echo Dot específicos ou para a casa toda.
* Funcionar mesmo quando você estiver fora de casa via internet móvel.
* Operar em modo simulação caso o token do Voice Monkey ainda não tenha sido inserido no `.env`.

---

## 5. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Controlar Dispositivos Offline:** Dispositivos inteligentes fora da tomada ou sem conexão Wi-Fi na residência não responderão.
* **Cadastrar Novos Aparelhos Físicos:** O pareamento de novas lâmpadas ou interruptores inteligentes deve ser feito previamente pelo aplicativo Alexa.
* **Ouvir Conversas Físicas da Sala:** A integração é estritamente unidirecional para disparos e anúncios; ela não transmite o microfone do ambiente de volta para o servidor.
