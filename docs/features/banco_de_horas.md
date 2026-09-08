# ⏱️ Funcionalidade: Calculadora Inteligente de Banco de Horas Semanal

## 1. Descrição Geral
Permite aos profissionais acompanharem sua jornada de trabalho semanal, registrando batidas de ponto e paradas para almoço. O DAM calcula o saldo acumulado (positivo ou negativo) frente à meta contratual semanal (ex: 40h ou 44h semanais) e avisa exatamente a que horas é possível encerrar o expediente na sexta-feira para zerar a meta.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Registrando as Batidas Diárias
Ao iniciar e encerrar suas atividades:
* *"Ponto: entrei às 08:50, saí para almoço às 12:15, voltei às 13:20 e encerrei às 18:30"*
* *"Hoje trabalhei das 09h às 19h com 1 hora de almoço"*
* *"Entrei às 09:12"* (o bot vai acumulando as batidas parciais do dia)

### Consultando o Saldo e Previsão de Sexta-feira
* *"Quanto tenho de banco de horas essa semana?"*
* *"Que horas posso sair hoje na sexta-feira para fechar minhas 40 horas?"*

O bot responde:
```text
⏱️ Banco de Horas Semanal (Meta: 40h00):

• Segunda-feira: 08h35 trabalhadas (+00h35)
• Terça-feira: 08h50 trabalhadas (+00h50)
• Quarta-feira: 08h15 trabalhadas (+00h15)
• Quinta-feira: 08h40 trabalhadas (+00h40)

Acumulado até quinta: 34h20min (+02h20 de saldo positivo acumulado)
Faltam para fechar a semana: 05h40min

🎯 Sexta-feira: Se você entrar às 09:00 e fizer 1h de almoço, poderá bater o ponto de encerramento exatamente às 15:40!
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Calcular horas líquidas trabalhadas descontando automaticamente o intervalo intrajornada (almoço).
* Considerar tolerâncias normativas da CLT ou regras contratuais acordadas.
* Projetar horários flexíveis de saída na sexta-feira com base no saldo acumulado ao longo da semana.
* Aceitar registros diários por texto ou áudio de voz.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Substituir o Relógio de Ponto Eletrônico Oficial (REP/eSocial):** A funcionalidade é um controle pessoal do funcionário; ela não substitui sistemas oficiais de ponto da empresa (ex: PontoTel, Flash, ADP).
* **Assinar Holerites ou Espelho de Ponto:** Não emite recibos de comprovação jurídica sem integração direta com o software de RH contratado.
