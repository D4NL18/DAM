# Tarefa: Correção de Idempotência Multi-Usuário do Morning Briefing (GP-04.3)

## 📌 Descrição
Correção do bug crítico de idempotência em que o envio com sucesso da mensagem de bom dia (Morning Briefing) para um usuário com horário mais cedo (ex: \lari\ às 07:30) gravava uma chave diária legada global em memória (\_MEMORY_BRIEFING_LOGS\), fazendo com que o disparo agendado subsequente para outro usuário (ex: \daniel\ às 08:00) fosse erroneamente suprimido por falso positivo de idempotência.

---

## 🎯 Critérios de Aceite
- [x] A chave de idempotência em memória (`_MEMORY_BRIEFING_LOGS`) armazena estritamente o identificador individual `{data}_{userId}` (P-0422).
- [x] O envio com sucesso do briefing para `lari` não interfere nem bloqueia o envio posterior para `daniel` no mesmo dia.
- [x] O mecanismo de catch-up matinal avalia o estado de envio de forma estritamente isolada por `userId`.
- [x] Caso exista documento legado no Firestore para o usuário principal (`admin`/`daniel`), o registro em memória adiciona a chave individual `{data}_{userId}` para evitar poluição global.
- [x] Testes de regressão TDD comprovam que o fluxo sequencial (Lari às 07:30 -> Daniel às 08:00) dispara ambas as mensagens sem falso bloqueio.

---

## 🛠️ Checklist de Execução

### Passo 6: TDD (Testes Unitários)
- [x] Adicionar teste de regressão em `tests/test_morning_briefing_fixes.py` simulando o envio sequencial para Lari seguido de Daniel sem `force=True`.
- [x] Confirmar falha no teste antes da correção.

### Passo 7: Execução (Desenvolvimento)
- [x] Refatorar `services/briefing_service.py`:
  - Remover `_MEMORY_BRIEFING_LOGS.add(chave_dia_legada)` ao registrar sucesso.
  - Ajustar checagem de idempotência em memória para verificar exclusivamente `chave_dia_user in _MEMORY_BRIEFING_LOGS`.
  - Em leituras de Firestore para documentos legados do Daniel, adicionar `chave_dia_user` em vez de `chave_dia_legada` ao cache de memória.
  - Em `_disparar_briefing_se_horario_correto` (catch-up), verificar apenas `chave_user in _MEMORY_BRIEFING_LOGS`.

### Passo 8: Code Review
- [x] Validar Clean Code, tipagem, docstrings e ausência de efeitos colaterais.

### Passo 9: UX Review
- [x] Bypass aprovado: sem alterações visuais ou de interface (backend-only).

### Passo 10: Validação de QA & Auto-Healer
- [x] Executar suíte completa de testes com 100% de sucesso.

### Passo 11: Auditoria de Segurança (SecOps)
- [x] Garantir isolamento estrito de contexto multi-tenant e ausência de dados sensíveis em logs.

### Passo 12: DevOps & Release
- [x] Commit semântico seguindo Conventional Commits (`fix: [P-0419] ...`) e abertura de Pull Request para `main`.
