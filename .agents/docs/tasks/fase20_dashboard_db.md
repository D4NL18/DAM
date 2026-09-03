# Tarefa: Integração Real do Dashboard com Banco de Dados e Fim dos Mocks

**Status:** Em Execução (Orquestração 12 Passos)
**Data:** 03/09/2026
**Objetivo:** Eliminar 100% dos dados mockados do Dashboard Web (Angular) e conectá-lo exclusivamente aos dados reais do Firestore e Google Calendar via endpoints RESTful no backend.

---

## 1. Quebra de Escopo (Product Owner)
- **US-DASH-01:** Exposição de endpoints RESTful no Backend (`/api/v1/finance`, `/api/v1/health`, `/api/v1/agenda`) consultando diretamente o Firebase Firestore e Google Calendar.
- **US-DASH-02:** Habilitação de CORS irrestrito e seguro para o domínio `https://bot-dam-72ef2.web.app` e `localhost`.
- **US-DASH-03:** Refatoração do Frontend Angular para consumir os endpoints da nuvem sem fallbacks estáticos (eliminação de mocks de despesas, refeições e eventos fictícios).
- **US-DASH-04:** Implementação de Empty States elegantes no Bento Grid para quando o banco ainda não possuir registros para o período.

---

## 2. Especificação de Regras de Negócio (Analyst)
- **P-DASH-01 (Finanças Reais):** O endpoint deve consultar a coleção `finances` no Firestore. Se houver registros no mês/ano solicitados, agrupa por categoria e calcula o total gasto. Se a coleção estiver vazia, retorna `totalSpent: 0.0`, `expensesByCategory: []` e `recentTransactions: []`.
- **P-DASH-02 (Saúde Real):** O endpoint deve consultar a coleção `health_metrics` no Firestore. Calcula médias reais de frequência cardíaca, passos, calorias e sono. Se vazio, retorna métricas zeradas com status indicativo.
- **P-DASH-03 (Agenda Real):** O endpoint deve consultar a API do Google Calendar (`calendar_tool`) para recuperar os compromissos reais do dia. Se não houver eventos, retorna lista vazia com mensagem amigável de dia livre.
- **P-DASH-04 (Zero Mocks no Frontend):** O frontend NUNCA deve injetar valores artificiais (ex: R$ 3.500,00 ou "Supermercado Extra"). Em caso de ausência de dados, renderiza o componente de Empty State preservando a estética premium do Design System.

---

## 3. Projeto Técnico & Contratos de API (Architect & Designer)
### `GET /api/v1/finance/monthly-summary`
Query: `year` (int), `month` (int)
Response:
```json
{
  "totalSpent": 0.0,
  "currency": "BRL",
  "expensesByCategory": [],
  "recentTransactions": []
}
```

### `GET /api/v1/health/summary`
Query: `startDate` (str), `endDate` (str)
Response:
```json
{
  "stepCount": 0,
  "activeEnergyBurned": 0,
  "heartRateAvg": 0,
  "sleepHours": 0.0,
  "metrics": []
}
```

### `GET /api/v1/agenda`
Response:
```json
{
  "todayTotalEvents": 0,
  "totalMeetingHours": 0.0,
  "nextEvent": null,
  "upcomingEvents": [],
  "insights": [],
  "reminders": []
}
```

---

## 4. Modelagem e Validação de Dados (DBA)
- Coleção `finances`: campos `amount`, `category`, `description`, `date`, `created_at`.
- Coleção `health_metrics`: campos `data` (JSON do Health Auto Export), `created_at`.
- Coleção `notes_reminders`: campos `title`, `description`, `due_date`, `status`.
- Integração Google Calendar: consulta com Service Account OAuth2 GCP.

---

## 5. Checklist de Implementação (Developer)
- [ ] Criar `backend_ia/routers/dashboard.py` com os endpoints `/finance/monthly-summary`, `/health/summary`, `/agenda`.
- [ ] Configurar `CORSMiddleware` em `backend_ia/main.py`.
- [ ] Escrever suíte de testes TDD em `backend_ia/tests/test_dashboard_api.py`.
- [ ] Atualizar serviços Angular (`finance-api.service.ts`, `health-api.service.ts`, `agenda-api.service.ts`) apontando para `http://35.254.233.21:8000`.
- [ ] Remover fallbacks mockados de `finance-dashboard.component.ts`, `health-dashboard.component.ts` e `agenda-dashboard.component.ts`.
- [ ] Adicionar tratamento de Empty State no HTML/SCSS dos componentes.
- [ ] Validar testes unitários (100% de aprovação).
- [ ] Compilar frontend (`ng build`) e publicar no Firebase Hosting (`firebase deploy`).
- [ ] Sincronizar backend na VM (`dam-server`) e reiniciar container.
- [ ] Registrar auditoria SecOps e commit no Git.
