# 🩺 Funcionalidade: Saúde & Métricas Corporais

## 1. Descrição Geral
Centraliza a ingestão automática e a consulta inteligente dos dados biométricos do usuário. Os dados são exportados automaticamente do Apple Health (iOS) para o DAM via aplicativo *Health Auto Export* e armazenados na coleção `health_metrics` do Firestore. O usuário pode consultar seus dados corporais a qualquer momento pelo WhatsApp em linguagem natural.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Configuração Inicial (Uma única vez)
1. No aplicativo **Health Auto Export** no iPhone, configure uma automação de sincronização para a URL do seu webhook:
   * **URL:** `http://35.254.233.21:8000/api/health-webhook`
   * **Headers:** `apikey: <SUA_CHAVE_WEBHOOK>`
   * **Frequência:** Automática ao longo do dia ou a cada hora.

### Consultando no WhatsApp
Basta enviar mensagens no seu chat privado do WhatsApp como se estivesse conversando com um treinador ou assistente:
* *"Quantos passos eu dei hoje?"*
* *"Como estão minhas calorias ativas esta semana?"*
* *"Qual foi minha média de batimentos cardíacos ontem?"*
* *"Dormi bem essa semana? Mostre meu resumo de sono."*

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Receber dados em segundo plano de passos (`step_count`), energia ativa gasta (`active_energy`), batimentos cardíacos (`heart_rate`) e sono (`sleep_analysis`).
* Formatar automaticamente respostas com médias diárias e semanais.
* Responder a perguntas informais e flexíveis sem necessidade de comandos fixos.
* Persistir séries temporais no Firestore para alimentação visual de gráficos no Dashboard Web.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Diagnóstico Médico:** O DAM não prescreve remédios, não fornece diagnósticos clínicos e não substitui consultas com médicos ou nutricionistas.
* **Leitura Manual sem Exportador:** O DAM não se conecta diretamente ao Apple Watch sem o app intermediário *Health Auto Export* configurado.
* **Modificação de Dados de Saúde:** O bot não altera ou exclui registros históricos no seu Apple Health (a via de ingestão é estritamente unidirecional).
* **Alertas de Emergência Médica:** Não monitora batimentos em tempo real para disparar socorro imediato.
