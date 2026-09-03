# Fase 19: Calculadora Inteligente de Banco de Horas Semanal (Time Tracker & Work Hours Balance)

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 19, responsável pelo cálculo, acompanhamento e balanço de banco de horas a partir de horários trabalhados enviados pelo usuário no WhatsApp em linguagem natural.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1901 (Parser Flexível de Horários em Linguagem Natural):**
  - O sistema deve interpretar mensagens em texto ou áudio com horários fracionados ou quebrados informados pelo usuário.
  - Exemplos de entradas aceitas:
    - *"Segunda fiz 9h, Terça 7h30, Quarta 10h, Quinta 8h, Sexta 6h30"*
    - *"Ontem trabalhei 8:45 e hoje fiz 7h20"*
    - *"Segunda 9h, Terça 8h, Quarta 7h30"*
  - Formatos numéricos suportados: `"9h"`, `"7h30"`, `"7h30m"`, `"07:30"`, `"8.5h"`, `"8,5 horas"`, `"8 horas e 15 minutos"`.
  - Normalização estrita para minutos inteiros para evitar qualquer erro de arredondamento de ponto flutuante ou alucinação da LLM.

- **P-1902 (Cálculo Determinístico de Balanço de Horas):**
  - O cálculo de soma e saldo de horas é puramente algorítmico (sem confiar na aritmética da LLM).
  - Jornada de trabalho padrão de referência:
    - **Padrão diário:** 8 horas (480 minutos) por dia útil informado.
    - **Padrão semanal:** 40 horas (2.400 minutos) para semana cheia de 5 dias úteis (ou proporcional aos dias informados na mensagem pontual).
  - Fórmula de Balanço:
    $$\Delta = \text{Total Minutos Trabalhados} - \text{Total Minutos Esperados}$$
  - Se $\Delta > 0$: **Horas a receber / Saldo positivo (crédito no banco de horas)**.
  - Se $\Delta < 0$: **Horas devidas / Saldo devedor (horas a compensar)**.
  - Se $\Delta = 0$: **Banco de horas zerado (jornada exata cumprida)**.

- **P-1903 (Modo Instantâneo vs. Modo Incremental / Histórico):**
  - **Modo Instantâneo (Sem persistência obrigatória):** Se o usuário enviar apenas a soma de dias soltos (*"Calcule meu banco: Segunda fiz 9h, Terça 7h30, Quarta 10h"*), o assistente responde imediatamente com o relatório detalhado sem obrigar gravação em banco.
  - **Modo Incremental (Com persistência no Firestore):** Se o usuário optar por registrar o dia a dia (*"Hoje fiz 8h30"* ou *"Registrar 9h na segunda-feira"*), o sistema salva na coleção `work_hours` vinculada à data e semana ISO correspondente.

- **P-1904 (Formatação Clara e Humanizada no WhatsApp):**
  - O retorno no WhatsApp deve discriminar:
    1. Detalhamento de cada dia e tempo correspondente (ex.: *Segunda-feira: 9h00 (+1h00)*).
    2. Total de horas trabalhadas na semana/período.
    3. Total de horas esperadas para os dias contabilizados.
    4. Saldo consolidado destacado (ex.: 🟢 *Você tem 2h30 a receber* ou 🔴 *Você está devendo 45min*).

- **P-1905 (Configuração Opcional de Meta de Jornada):**
  - O usuário pode indicar uma jornada personalizada (ex.: *"Minha jornada é de 44h semanais"* ou *"Trabalho 6h por dia"*).
  - A preferência pode ser salva no perfil do usuário no Firestore (`user_settings`).

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 19

#### [ ] Task 19.1: Motor Matemático e Parser de Horários (`hours_calculator.py`)
- [ ] **Etapa 19.1.1:** Criar `backend_ia/services/hours_calculator.py` com funções puras de parsing regex/textual:
  - Extração de dias da semana e expressões de tempo.
  - Conversão bidirecional: strings temporais $\leftrightarrow$ minutos inteiros.
  - Formatação amigável de saída: `minutos_para_texto(minutos: int) -> str` (ex.: `510` -> `"8h30"`).
- [ ] **Etapa 19.1.2:** Implementar lógica de balanço determinístico (`calcular_saldo_banco_horas`).
- [ ] **Etapa 19.1.3:** Testes unitários com suíte exaustiva de casos (Pytest).

#### [ ] Task 19.2: Tool LLM `work_hours_tool.py` e Integração com Gemini
- [ ] **Etapa 19.2.1:** Criar `backend_ia/services/tools/work_hours_tool.py` com as funções:
  - `calcular_banco_horas_semanal(dias_horarios: dict, meta_diaria_minutos: int = 480)`
  - `consultar_resumo_banco_horas()`
- [ ] **Etapa 19.2.2:** Declarar os esquemas de *Function Calling* no `ai_service.py` do Gemini.
- [ ] **Etapa 19.2.3:** Integrar formatação da resposta com emojis intuitivos (🟢 positivo / 🔴 devedor / ⚪ zerado).

#### [ ] Task 19.3: Persistência Opcional no Firestore (`work_hours`)
- [ ] **Etapa 19.3.1:** Criar repositório `backend_ia/repositories/work_hours_repository.py`.
- [ ] **Etapa 19.3.2:** Modelar documento na coleção `work_hours`:
  - `id`, `date` (YYYY-MM-DD), `day_of_week`, `minutes_worked`, `target_minutes`, `balance_minutes`, `week_number`, `year`, `notes`, `created_at`.
- [ ] **Etapa 19.3.3:** Endpoint/Tool para fechamento e extrato consolidado semanal/mensal.

#### [ ] Task 19.4: Customização de Jornada de Trabalho
- [ ] **Etapa 19.4.1:** Permitir ao usuário definir sua jornada contratual no Firestore (`user_settings` ou parâmetro contextual na tool).
- [ ] **Etapa 19.4.2:** Suporte a jornadas padrão: 40h/semana (8h/dia), 44h/semana (8h48/dia) e 30h/semana (6h/dia).

---

## 3. Critérios de Aceite e Validação (QA)

- [ ] **Cenário 1 (Cálculo Instantâneo com Saldo Positivo):**
  - Usuário envia: *"Segunda fiz 9h, Terça 7h30, Quarta 10h"*.
  - O bot calcula: 3 dias informados = 24h esperadas (3 x 8h). Total feito: 9h + 7h30 + 10h = 26h30.
  - Resultado esperado: Retornar que o usuário trabalhou 26h30 de 24h esperadas e **tem 2h30 a receber (saldo positivo)**.

- [ ] **Cenário 2 (Cálculo Instantâneo com Saldo Devedor):**
  - Usuário envia: *"Essa semana fiz Segunda 7h, Terça 7h, Quarta 8h, Quinta 7h30, Sexta 6h30"*.
  - O bot calcula: 5 dias = 40h esperadas. Total feito: 36h00.
  - Resultado esperado: Retornar que o usuário trabalhou 36h00 de 40h esperadas e **está devendo 4h00 (saldo devedor)**.

- [ ] **Cenário 3 (Formatos Diversificados de Entrada):**
  - Usuário envia: *"Fiz 8h45 na segunda, 8.5h na terça e 7:15 na quarta"*.
  - O motor faz o parser correto de cada formato decimal e de relógio sem erro.

- [ ] **Cenário 4 (Jornada Customizada):**
  - Usuário especifica: *"Minha meta diária é de 6 horas. Segunda fiz 7h, Terça 5h30"*.
  - O bot calcula sobre a meta de 6h/dia (12h esperadas nos 2 dias, 12h30 realizadas = +30min de saldo positivo).
