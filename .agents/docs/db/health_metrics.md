# Coleção: `health_metrics`

## 📋 Propósito

Armazena as **métricas de saúde** do usuário sincronizadas pelo app **Health Auto Export** (iOS). Cada documento representa um registro de dados fisiológicos — passos, calorias ativas, calorias basais, frequência cardíaca e análise de sono. Fonte de verdade do domínio de Saúde & Bem-Estar.

---

## 🧩 Features que utilizam esta coleção

| Feature | Domínio | Descrição |
|---|---|---|
| **SB-01 – Métricas de Sono** | Saúde | Consome `sleepAnalysis` para médias semanais de sono |
| **SB-02 – Acompanhamento de Treinos** | Saúde | Usa `activeEnergyBurned` e `stepCount` |
| **SB-03 – Webhook Apple Health** | Saúde | Endpoint `/api/health-webhook` grava documentos nesta coleção |
| **PC-07 – Dashboard Web Angular** | Plataforma Core | Spring Boot (`HealthController`) lê para `/health/summary` |

---

## 📑 Estrutura do Documento

**Path no Firestore:** `/health_metrics/{auto_id}`

Document ID gerado automaticamente via `.add()`.

### Campos

| Campo | Tipo Firestore | Obrigatório | Descrição |
|---|---|---|---|
| `date` | `Timestamp` | Sim | Data de referência da métrica (enviada pelo Health Auto Export) |
| `activeEnergyBurned` | `Number (Float)` | Opcional | Calorias ativas gastas em kcal |
| `basalEnergyBurned` | `Number (Float)` | Opcional | Calorias basais em kcal |
| `stepCount` | `Number (Integer)` | Opcional | Número de passos |
| `heartRateAvg` | `Number (Float)` | Opcional | Média de batimentos cardíacos por minuto (bpm) |
| `sleepAnalysis` | `Map` | Opcional | Subdocumento de análise de sono |
| `sleepAnalysis.inBed` | `Number (Float)` | Opcional | Minutos deitado na cama |
| `sleepAnalysis.asleep` | `Number (Float)` | Opcional | Minutos dormindo efetivamente |
| `createdAt` | `Timestamp` | Sim | Momento da ingestão pelo motor de IA |

---

## 🔗 Relacionamentos

Coleção autônoma. Dados originados exclusivamente do **Health Auto Export** via webhook.

---

## 📏 Constraints e Regras de Negócio

| Regra | Descrição |
|---|---|
| **Imutabilidade** | Registros sempre inseridos via `.add()`, nunca atualizados |
| **Agregação em memória** | SUM/AVG não suportados nativamente — feitos em memória no Spring Boot ou FastAPI |
| **Range query por data** | `whereGreaterThanOrEqualTo` e `whereLessThanOrEqualTo` no campo `date` |

---

## 🗂️ Índices Necessários

| Campo | Ordem |
|---|---|
| `date` | Ascendente |

---

## 🔒 Regras de Segurança

```
match /health_metrics/{docId} {
  allow read, write: if false;
}
```

---

## 📌 Observações Técnicas

- Endpoint `/api/health-webhook` protegido por Bearer Token (`WEBHOOK_TOKEN`).
- O DTO Java `HealthMetric.java` é simplificado — expõe apenas `id`, `steps`, `activeCalories` e `date`.
- Campos `basalEnergyBurned`, `heartRateAvg` e `sleepAnalysis` ainda não são expostos pelo Spring Boot.
