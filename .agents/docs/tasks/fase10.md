# Fase 10: Curador de Presentes e Datas Especiais (Memória Afetiva & Alertas Proativos)

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 10, responsável pela captura contínua de desejos e sugestões proativas de presentes para pessoas queridas.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1001 (Captura Contextual de Desejos):** Ao longo do ano, o usuário pode enviar menções informais e casuais no chat, por texto ou áudio (ex.: *"Minha namorada comentou que gostou de um perfume da loja X"*, *"Meu pai falou que quer uma furadeira da marca Y"*). O bot deve identificar a pessoa, o parentesco/relação, o item desejado e a anotação original literal.
- **P-1002 (Mapeamento de Datas Especiais):** Cada pessoa/relação cadastrada pode possuir datas comemorativas associadas (ex.: Aniversário, Dia dos Namorados, Natal, Dia das Mães, Bodas/Aniversário de Namoro).
- **P-1003 (Alerta Proativo Antecipado):** Com uma antecedência configurável (ex.: 20 a 30 dias antes da data), o bot deve enviar ativamente uma mensagem no WhatsApp lembrando a ocasião futura e resgatando a anotação exata feita no passado, fornecendo contexto e tempo hábil para comprar o presente.
- **P-1004 (Histórico e Status):** As ideias podem ser marcadas como `pendente` ou `comprado`, evitando que a mesma sugestão seja reiterada se já tiver sido presenteada.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 10

#### [ ] Task 10.1: Modelagem da Coleção `gift_ideas` e `special_dates`
- [ ] **Etapa 10.1.1:** Criar `backend_ia/repositories/gifts_repository.py` manipulando a coleção `gift_ideas` no Firestore.
- [ ] **Etapa 10.1.2:** Estruturar campos: `id`, `remote_jid`, `person_name`, `relationship`, `item_description`, `store_or_brand`, `special_date_ref` (ex: "aniversario", "dia_dos_namorados"), `original_quote`, `status` (`pending`, `purchased`), `created_at`.
- [ ] **Etapa 10.1.3:** Coleção complementar ou mapa de `special_dates` com as datas anuais (ex.: aniversário da namorada: 15/07).

#### [ ] Task 10.2: Tool LLM de Curadoria de Presentes
- [ ] **Etapa 10.2.1:** Criar `backend_ia/services/tools/gift_curator_tool.py` com funções:
  - `salvar_ideia_presente(pessoa: str, relacao: str, item: str, contexto_ou_loja: Optional[str] = None, data_especial: Optional[str] = None)`
  - `consultar_ideias_presente(pessoa: Optional[str] = None)`
  - `cadastrar_data_especial(pessoa: str, ocasiao: str, dia_mes: str)`
- [ ] **Etapa 10.2.2:** Registrar schemas no `ai_service.py` do Gemini para extração autônoma a partir de conversas.

#### [ ] Task 10.3: Motor de Alerta Proativo Pré-Datas
- [ ] **Etapa 10.3.1:** Criar rotina semanal/diária que varre datas especiais dos próximos 30 dias.
- [ ] **Etapa 10.3.2:** Ao detectar proximidade (ex: faltam 21 dias para o aniversário de fulana), buscar todas as ideias com status `pending` registradas para ela.
- [ ] **Etapa 10.3.3:** Enviar mensagem estruturada no WhatsApp:
  > *"🎁 Lembrete de Presente: O aniversário da sua namorada é daqui a 3 semanas (15/07). Em 12 de março você anotou: 'ela comentou que gostou de um perfume da loja X'."*

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Registro de Desejo Espontâneo):** O usuário envia: *"Minha namorada comentou que adorou uma bolsa caramelo da Arezzo"*. O bot reconhece a intenção de presente, associa à namorada e confirma o registro na memória.
- [ ] **Cenário 2 (Consulta de Presentes):** O usuário pergunta *"O que eu já anotei de ideias de presente para o meu pai?"*. O bot lista os itens pendentes com as datas em que foram comentados.
- [ ] **Cenário 3 (Disparo Proativo):** O sistema detecta a aproximação de uma data cadastrada e alerta o usuário no WhatsApp com o resgate literal da anotação histórica.
- [ ] **Cenário 4 (Atualização de Compra):** O usuário informa *"Já comprei o perfume da loja X"*. O bot marca a ideia como comprada para não alertar novamente.
