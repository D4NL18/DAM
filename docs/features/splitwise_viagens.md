# ✈️ Funcionalidade: Splitwise de Bolso para Viagens & Grupos

## 1. Descrição Geral
Funciona como um gestor de despesas coletivas em viagens, aluguéis de temporada ou churrascos entre amigos. Ao longo dos dias, o usuário envia fotos de comprovantes fiscais ou notas de gastos com a indicação de quem pagou e para quem foi a despesa. No fechamento, o DAM calcula o algoritmo de simplificação de dívidas com o mínimo de transferências Pix necessárias.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Registrando Gastos Durante a Viagem
* *"Almoço R$ 200, eu paguei, divide por 4 (Eu, Lucas, Ana e Bruno)"*
* *"O Lucas pagou a gasolina de R$ 180, divide entre todos"*
* *"Foto do cupom fiscal do mercado de R$ 450. A Ana pagou, divide por 3 (sem o Bruno)"*

### Solicitando o Fechamento da Viagem
No último dia, basta pedir:
* *"Faça o fechamento da viagem"*
* *"Quem deve quanto para quem nessa viagem?"*

O bot responde com o extrato simplificado:
```text
✈️ Fechamento da Viagem (Gastos Totais: R$ 830,00):

Resumo de quem gastou:
• Você pagou: R$ 200,00
• Lucas pagou: R$ 180,00
• Ana pagou: R$ 450,00
• Bruno pagou: R$ 0,00

Pix a serem feitos (Mínimo de transferências):
1. Bruno faz Pix de R$ 95,00 para Ana
2. Você faz Pix de R$ 7,50 para Ana
3. Lucas faz Pix de R$ 27,50 para Ana

✅ Com apenas 3 transferências, todas as contas da viagem ficam 100% quitadas!
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Manter um livro contábil da viagem ou evento em andamento.
* Aceitar entradas por foto de recibo, texto corrido ou áudio.
* Excluir participantes específicos de despesas em que eles não consumiram.
* Otimizar o grafo de liquidação para minimizar o número de transferências entre os amigos.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Disparar Pix Automaticamente:** Não debita as contas bancárias dos amigos (fornece a lista de transferências sugeridas).
* **Adivinhar Gastos Não Informados:** Se alguém pagar algo em dinheiro vivo e esquecer de avisar no chat, o cálculo não contemplará a despesa.
