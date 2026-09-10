# 🚗 Funcionalidade: Telemetria e Controle do Veículo (Fiat Fastback)

## 1. Descrição Geral
Permite ao usuário acompanhar a saúde mecânica e a telemetria do seu Fiat Fastback (Turbo 270) e enviar comandos de segurança remotos (travar e destravar portas) através do WhatsApp, integrando à API de serviços conectados Uconnect.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Consultando o Status do Carro
Envie perguntas naturais sobre seu carro:
* *"Como está o carro?"*
* *"Quanto tenho de gasolina no Fastback?"*
* *"Qual a autonomia do carro agora?"*
* *"Os pneus estão calibrados e as portas trancadas?"*

O bot responde com o relatório consolidado:
```text
🚗 Status do Veículo (Fiat Fastback Turbo 270):
• Combustível: 68% (Tanque)
• Autonomia estimada: 485 km
• Travas das portas: Trancadas 🔒
• Vidros: Totalmente fechados
• Pressão dos pneus: 32 PSI (Todos calibrados)
• Tensão da bateria: 12.6V (Saudável)
• Hodômetro: 14.820 km
• Localização: Garagem Residencial
```

### Comandos de Travas
* *"Trave as portas do carro"* $\rightarrow$ Envia o comando e confirma: `Portas do Fiat Fastback foram travadas com sucesso! 🔒`
* *"Destrave as portas do Fastback"* $\rightarrow$ Confirma a abertura: `Portas do Fiat Fastback foram destravadas com sucesso! 🔓`

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Informar porcentagem atual do tanque de combustível e quilômetros estimados de autonomia.
* Monitorar pressão individual dos pneus, estado da bateria de 12V e hodômetro total.
* Executar trancamento e destrancamento remoto das portas com validação de segurança.
* Rejeitar comandos fora do escopo ou inseguros (*"Ação inválida"*).

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Ligar o Motor ou Dirigir Remotamente:** Não é possível dar partida remota ou movimentar o veículo via chat por motivos de segurança e integridade física.
* **Operar sem Cobertura Celular:** Se o veículo estiver em um subsolo profundo sem sinal de operadora (telemetria embarcada offline), os comandos remotos não serão recebidos pelo módulo do carro.
* **Destravar com o Carro em Movimento:** O sistema não executa comandos de trava enquanto o veículo estiver engatado ou rodando em via pública.
