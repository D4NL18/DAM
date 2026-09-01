# Dicionário de Domínio (Linguagem Ubíqua)

Este glossário define os termos oficiais que DEVEM ser usados no código e na documentação.

## 1. Core & Mensageria
- **Assistant / DAM:** O projeto como um todo. A entidade de inteligência artificial.
- **Message:** Representação unificada de uma comunicação (texto ou áudio recebido/enviado).
- **Tool / Function:** As capacidades do LLM para interagir com os pilares externos (ex: buscar_dados).

## 2. Pilar 1: Saúde (Health)
- **HealthMetric:** Registro genérico de saúde.
- **SleepRecord:** Métrica específica de tempo e qualidade de sono.
- **StepCount:** Contagem de passos diária.
- **HRV (Heart Rate Variability):** Variabilidade da Frequência Cardíaca.

## 3. Pilar 2: Veículo (Vehicle)
- **Vehicle:** Representação lógica do Fiat Fastback.
- **Autonomy:** Quantidade de combustível / distância restante.
- **Command:** Ação remota enviada ao veículo (ex: Lock Doors, Start Engine).

## 4. Pilar 3: Esports
- **Match:** Partida de CS2 (pode estar em andamento ou agendada).
- **Team:** Time participante.
- **Scoreboard:** O placar em tempo real.

## 5. Pilar 4: Finanças (Finances)
- **Expense / Gasto:** Saída de dinheiro (nunca usar `Transaction` solto, seja específico).
- **Category:** Classificação do gasto (ex: Alimentação, Transporte).
- **Receipt / Comprovante:** Imagem ou texto bruto que originou o registro.

## 6. Pilar 5: Agenda (Calendar)
- **Event:** Um compromisso no Google Calendar.
- **TimeSlot:** Espaço livre ou ocupado na agenda.

## 7. Pilar 6 & 7: Infraestrutura & Casa
- **BillingAlert:** Notificação de que o custo da nuvem aumentou.
- **Routine:** Uma automação residencial da Alexa.
