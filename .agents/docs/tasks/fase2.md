# Fase 2: Dashboard Web (Spring Boot + Angular)

## 1. Especificação (Analista)

### Regras de Negócio e Escopo
- **P-001 (Consolidação de Dados):** O Dashboard tem o objetivo de servir como interface visual para o "DAM Assistant". Ele deve exibir de forma consolidada os dados de Saúde (coletados via Health Auto Export) e Finanças.
- **P-002 (Acesso Seguro):** O acesso à Core API deve ser seguro. O Spring Boot deverá fornecer endpoints com validação via token ou Firebase Auth.
- **P-003 (Read-Only Principal):** Inicialmente, a Core API terá foco em leitura para o Dashboard (Analytics). A inserção de dados continuará sendo feita pelo motor de IA (FastAPI) a partir do WhatsApp ou webhooks.
- **P-004 (Design System):** O Frontend deve utilizar Angular 17+ (ou superior) com Standalone Components e SCSS. Deve ter um design limpo e responsivo (Mobile-first).

### Casos de Uso
1. **Visualizar Saúde:** O usuário loga no Dashboard e visualiza um gráfico semanal de passos e gasto calórico.
2. **Visualizar Finanças:** O usuário loga no Dashboard e visualiza seus gastos mensais categorizados em um gráfico de pizza.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Backend (Core API - Spring Boot)
- [ ] **Task 2.1.1:** Inicializar projeto Spring Boot (Web, Actuator, Validation).
- [ ] **Task 2.1.2:** Configurar Firebase Admin SDK (Chaves via variáveis de ambiente/Secret Manager).
- [ ] **Task 2.1.3:** Criar estrutura de pacotes (`controller`, `service`, `repository`, `dto`, `model`).
- [ ] **Task 2.1.4:** Implementar Firestore Repositories para coleções `health_metrics` e `finances`.
- [ ] **Task 2.1.5:** Criar `HealthService` e `FinanceService` com regras de agregação (ex: soma de gastos por categoria no mês).
- [ ] **Task 2.1.6:** Implementar `HealthController` e `FinanceController` expondo os dados agregados.
- [ ] **Task 2.1.7:** Configurar Swagger/OpenAPI para documentação dos endpoints.
- [ ] **Task 2.1.8:** Adicionar testes unitários com JUnit e Mockito.

### Frontend (Dashboard - Angular)
- [ ] **Task 2.2.1:** Inicializar projeto Angular (Standalone, SCSS, Routing).
- [ ] **Task 2.2.2:** Configurar bibliotecas base (TailwindCSS ou Material, ECharts/Chart.js para gráficos).
- [ ] **Task 2.2.3:** Configurar Angular HTTP Client e Interceptors (para envio de token).
- [ ] **Task 2.2.4:** Criar services de integração com a Core API (`HealthApiService`, `FinanceApiService`).
- [ ] **Task 2.2.5:** Criar layout base (Sidebar, Header, Router Outlet).
- [ ] **Task 2.2.6:** Desenvolver componente `HealthDashboardComponent` (exibição de gráficos de saúde).
- [ ] **Task 2.2.7:** Desenvolver componente `FinanceDashboardComponent` (exibição de gráficos financeiros).
- [ ] **Task 2.2.8:** Garantir responsividade e testes E2E/Unitários (Karma/Jasmine ou Jest/Cypress).

### DevOps / Deploy
- [ ] **Task 2.3.1:** Containerizar o Spring Boot (Dockerfile) e criar pipeline para Google Cloud Run.
- [ ] **Task 2.3.2:** Configurar pipeline de build do Angular e deploy para Firebase Hosting.
