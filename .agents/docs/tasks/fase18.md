# Fase 18: "Splitwise" de Bolso para Viagens e Grupos (Group Ledger & Debt Minimizer)

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 18, responsável pela gestão contínua de despesas compartilhadas em viagens e eventos com liquidação final inteligente via Pix.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1801 (Gestão de Viagens / Grupos Ativos):**
  - O usuário pode abrir uma viagem/evento a qualquer momento pelo WhatsApp (ex.: *"Iniciar viagem Floripa com Eu, João, Maria e Pedro"*).
  - Pode haver uma viagem ativa por padrão, ou o usuário pode alternar entre viagens caso participe de mais de um grupo.
- **P-1802 (Lançamento Rápido e Incremental de Gastos):**
  - Durante os dias da viagem, qualquer gasto pode ser enviado por texto, áudio ou foto do cupom fiscal. Exemplos:
    - *"Almoço R$ 200, eu paguei, divide por 4."*
    - *"Pedro pagou R$ 120 no posto de combustível, divide entre todos."*
    - *"Maria pagou R$ 90 nas bebidas do mercado, divide só entre Eu, Maria e Pedro (João não bebeu)."*
  - Comprovantes em foto passam pelo OCR do Gemini Vision para extração automática do valor total e estabelecimento caso o usuário apenas fotografe e diga *"Eu paguei, divide por todos"*.
- **P-1803 (Algoritmo de Minimização de Transações / Debt Simplification):**
  - O sistema calcula o saldo líquido de cada participante: `Saldo Líquido = Total Pago - Total Devido`.
  - Em vez de dezenas de pequenas transferências cruzadas entre todos, o algoritmo de liquidação ganancioso (*greedy debt settlement*) resolve os débitos com o menor número possível de transações Pix.
  - Exemplo: se João deve R$ 50 para Maria e Maria deve R$ 50 para Pedro, João transfere R$ 50 diretamente para Pedro.
- **P-1804 (Fechamento da Viagem e Relatório no WhatsApp):**
  - Quando o usuário solicitar *"Fechar viagem Floripa"* ou *"Quanto ficou a conta da viagem?"*, o bot gera:
    1. Total gasto na viagem e gasto médio por pessoa.
    2. Extrato consolidado dos gastos cadastrados.
    3. **Resumo das transferências Pix:** lista simplificada de quem deve transferir quanto para quem.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 18

#### [ ] Task 18.1: Modelagem no Firestore (`trip_groups` e `trip_expenses`)
- [ ] **Etapa 18.1.1:** Criar repositório `backend_ia/repositories/trip_repository.py`.
- [ ] **Etapa 18.1.2:** Estrutura da coleção `trip_groups`:
  - `id`, `name`, `members` (lista de nomes/apelidos), `created_by`, `status` (`active`, `closed`), `created_at`, `closed_at`.
- [ ] **Etapa 18.1.3:** Estrutura da coleção `trip_expenses`:
  - `id`, `trip_id`, `payer`, `amount`, `description`, `split_between` (lista de membros), `receipt_url`, `created_at`.

#### [ ] Task 18.2: Algoritmo de Liquidação de Saldos (Debt Simplifier)
- [ ] **Etapa 18.2.1:** Implementar em `backend_ia/services/settlement_service.py`:
  - Calcular crédito/débito de cada membro.
  - Algoritmo de resolução de transferências mínimas (Minimizing Cash Flow Problem).
  - Validação estrita de centavos para garantir que a soma dos pagamentos equilibre perfeitamente o saldo zerado.

#### [ ] Task 18.3: Tool LLM `trip_ledger_tool.py`
- [ ] **Etapa 18.3.1:** Criar `backend_ia/services/tools/trip_ledger_tool.py` com as funções:
  - `iniciar_viagem(nome: str, participantes: List[str])`
  - `lancar_despesa(descricao: str, valor: float, pagador: str, participantes_divisao: Optional[List[str]] = None)`
  - `consultar_resumo_viagem(trip_id_ou_nome: Optional[str] = None)`
  - `fechar_viagem_e_calcular_acerto(trip_id_ou_nome: Optional[str] = None)`
- [ ] **Etapa 18.3.2:** Integrar recepção de imagem para ler cupom e registrar na despesa ativa.
- [ ] **Etapa 18.3.3:** Registrar os schemas no `ai_service.py` do Gemini.

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Abertura de Viagem):** Usuário envia "Criar viagem Praia com João, Maria e Pedro". O bot confirma a criação do grupo e lista os 4 participantes.
- [ ] **Cenário 2 (Lançamento Rápido de Gasto):** Usuário envia "Almoço R$ 200, eu paguei, divide por 4". O bot registra que cada um deve R$ 50 e Você tem crédito de R$ 150.
- [ ] **Cenário 3 (Lançamento por Outro Membro):** Usuário diz "Pedro pagou R$ 100 de gasolina, divide por todos". O bot registra o crédito de Pedro e atualiza os saldos.
- [ ] **Cenário 4 (Fechamento e Minimização de Pix):** Usuário pede "Fechamento da viagem". O bot calcula os saldos líquidos e exibe a lista exata com o menor número de transferências Pix necessárias para zerar as contas do grupo.
