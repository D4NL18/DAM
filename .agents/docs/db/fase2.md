# Modelagem de Banco de Dados (Fase 2)

## Decisão de Arquitetura: PostgreSQL vs Firestore

De acordo com o `ARCHITECTURE.md`, o banco de dados principal do projeto é o **Firebase Firestore (NoSQL)** utilizando o *Spark Plan* (gratuito). 
Embora o Spring Boot (Core API) tenha excelente integração com PostgreSQL (via Spring Data JPA) — o que facilitaria consultas analíticas (agregações, sumatórios, group by) —, a adoção do Firestore se mantém pelos seguintes motivos:
1. **Custo:** O plano Spark atende o escopo de uso pessoal sem custos de infraestrutura dedicados (diferente de uma instância Cloud SQL).
2. **Tempo Real e Escalabilidade:** O motor de IA (FastAPI) fará a ingestão de dados continuamente, e o Firestore lida bem com esse volume.
3. **Padrão Arquitetural:** Manteremos a fonte única de verdade no Firestore, acessada via **Firebase Admin SDK** no Spring Boot.

Como o Firestore é um banco NoSQL e não suporta agregações complexas de forma nativa e barata, o **Spring Boot deverá realizar em memória** (ou via caches) as sumarizações e filtros de data exigidas pelo Dashboard.

---

## Modelagem das Coleções (NoSQL)

Abaixo estão os documentos mapeados que o Spring Boot irá ler.

### 1. Coleção `health_metrics`
Armazena os registros de saúde diários/sincronizados, originados do Health Auto Export.

- **Document ID:** Gerado automaticamente ou chave composta (ex: `YYYY-MM-DD`).
- **Campos:**
  - `date` (Timestamp): Data de referência da métrica.
  - `activeEnergyBurned` (Number): Calorias ativas gastas.
  - `basalEnergyBurned` (Number): Calorias basais gastas.
  - `stepCount` (Number): Número de passos.
  - `heartRateAvg` (Number): Média de batimentos cardíacos.
  - `sleepAnalysis` (Map):
    - `inBed` (Number): Minutos na cama.
    - `asleep` (Number): Minutos dormindo.
  - `createdAt` (Timestamp): Momento da ingestão pelo motor de IA.

**Estratégia de Consulta (Spring Boot):**
O Spring Boot fará uma query por range de `date` (`whereGreaterThanOrEqualTo` e `whereLessThanOrEqualTo`) e agrupará os resultados em memória para retornar o payload do endpoint `/health/summary`.

---

### 2. Coleção `finances`
Armazena transações processadas pelo Agente Financeiro (IA).

- **Document ID:** Gerado automaticamente.
- **Campos:**
  - `date` (Timestamp): Data da transação.
  - `description` (String): Nome do estabelecimento ou descrição.
  - `amount` (Number): Valor da transação (positivo para receita, negativo para despesa).
  - `currency` (String): Moeda (ex: "BRL").
  - `category` (String): Categoria inferida pela IA (ex: "Alimentação", "Transporte").
  - `type` (String): "EXPENSE" ou "INCOME".
  - `receiptUrl` (String, Opcional): Link para o comprovante no Cloud Storage.
  - `createdAt` (Timestamp): Momento do registro.

**Estratégia de Consulta (Spring Boot):**
O Spring Boot fará queries filtrando por `date` (início e fim do mês corrente). O agrupamento por `category` para o endpoint `/finance/monthly-summary` será processado na camada de Service do Java.
Para lidar com o limite de leituras gratuitas do Firestore (50k/dia), recomenda-se o uso de **Caffeine Cache** ou **Redis** no Spring Boot, limitando as chamadas ao Firestore caso o Dashboard seja aberto frequentemente.
