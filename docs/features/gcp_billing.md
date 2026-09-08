# 🚨 Funcionalidade: FinOps & Alertas de Custos GCP (Billing Pub/Sub)

## 1. Descrição Geral
Sistema de governança financeira em nuvem (FinOps) que monitora o consumo da infraestrutura do DAM no Google Cloud Platform. Através do Cloud Billing Budgets conectado a um tópico do Cloud Pub/Sub, o endpoint `/api/billing-alert` do FastAPI recebe notificações e dispara alertas automáticos no WhatsApp do usuário sempre que os limites de gastos (50%, 80%, 100%) são atingidos.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Operação Automática
Esta funcionalidade opera de forma 100% autônoma e proativa. Você não precisa pedir nada:
1. Quando a fatura acumulada do mês atinge um dos percentuais configurados no GCP (ex: 50%, 80% ou 100% de R$ 100,00), o Google Cloud envia uma mensagem para o webhook do DAM.
2. O DAM processa a notificação e envia instantaneamente no seu WhatsApp:

```text
🚨 Alerta de Orçamento GCP (DAM Cloud Budget)!
• Consumo atual: BRL 85.50
• Limite estipulado: BRL 100.00
• Percentual atingido: 85.5%

Verifique o console do Google Cloud para detalhes de custos e FinOps.
```

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Receber eventos do Cloud Pub/Sub via requisição autenticada com token de segurança.
* Decodificar dados codificados em Base64 contendo valores em reais (BRL) e orçamento alvo.
* Notificar proativamente o usuário no WhatsApp sem necessidade de polling manual.
* Prevenir surpresas na fatura mensal do cartão de crédito do projeto.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Desligar Servidores Automaticamente:** O bot não desliga VMs ou derruba bancos de dados sem autorização expressa, evitando indisponibilidade de serviços essenciais.
* **Isenção de Cobranças da Google:** O bot apenas monitora e alerta; eventuais disputas ou cancelamentos de serviços devem ser feitos no Console do GCP.
* **Previsão em Tempo Real Segundo a Segundo:** O Google Cloud Billing atualiza os dados de consumo em intervalos periódicos (geralmente algumas vezes ao dia), portanto o alerta reflete os dados mais recentes consolidados pelo faturamento do GCP.
