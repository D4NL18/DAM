# Checklist da Tarefa: FG-05 Resumo Consolidado de Gastos por Cartão e Categoria

## Informações Gerais
- **ID da Tarefa:** `TASK-FG05-001`
- **Domínio:** Finanças & Gastos
- **Status:** Em Andamento

---

## Checklist de Implementação

### 1. Suíte de Testes TDD (Tester)
- [ ] Criar `backend_ia/tests/test_finance_summary.py`:
  - [ ] Teste de agregação mensal com despesas distribuídas por múltiplos cartões e categorias.
  - [ ] Teste de cálculo percentual e soma total correta.
  - [ ] Teste de ordenação decrescente de categorias.
  - [ ] Teste de seleção das maiores compras (Top 3).
  - [ ] Teste de período sem gastos retornando mensagem informativa.
  - [ ] Teste de filtro por dias retroativos.
  - [ ] Teste de falha de conexão com Firestore (`db is None`).
  - [ ] Teste de integração do prompt `financial_rules` instruindo a chamada da nova tool.

### 2. Implementação da Ferramenta (Dev)
- [ ] Implementar `consultar_resumo_gastos` em `backend_ia/services/tools/finance_tool.py`:
  - [ ] Lógica de janela temporal (mês/ano padrão ou explícito, ou dias retroativos).
  - [ ] Agregação por `payment_method` normalizado.
  - [ ] Agregação por `category`.
  - [ ] Extração de Top 3 maiores gastos.
  - [ ] Formatação rica com emojis e percentuais para WhatsApp.
- [ ] Atualizar `backend_ia/services/prompts/financial_rules.py` para ensinar a IA a usar `consultar_resumo_gastos`.
- [ ] Registrar `consultar_resumo_gastos` em `AVAILABLE_TOOLS` em `backend_ia/services/ai_service.py`.

### 3. Validação e Qualidade (Reviewer, UX, QA, SecOps, DevOps)
- [ ] Code Review (tipagem, legibilidade, PEP 8).
- [ ] UX Reviewer (clareza da mensagem no WhatsApp).
- [ ] Execução completa do pytest (100% de sucesso).
- [ ] SecOps (auditoria de acesso a dados).
- [ ] DevOps (commit, push e deploy em produção na VM do GCP).
