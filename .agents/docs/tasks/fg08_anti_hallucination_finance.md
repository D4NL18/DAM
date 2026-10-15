# Checklist de Tarefas: FG-08 (Governança Anti-Alucinação & Consulta Confiável de Gastos)

## Checklist de Execução

- [x] **Etapa 6: Desenvolver Testes Unitários (Tester - TDD)**
  - [x] Criar `backend_ia/tests/test_anti_hallucination_and_finance_query.py` cobrindo:
    - [x] Validação de que `system_base.py` e `financial_rules.py` contêm regras explícitas anti-alucinação.
    - [x] Validação de que `ToolsDispatcher` detecta intenção financeira para frases como:
      - "Faça um resumo dos valores de gastos por categoria em setembro"
      - "Quais gastos entraram como moradia?"
      - "Quanto gastei em alimentação em setembro de 2026?"
      - "Resumo dos gastos do mês"
    - [x] Validação de `consultar_resumo_gastos`:
      - Consulta sem categoria (retorna resumo macro idêntico ao dashboard com total, categorias e cartões).
      - Consulta com categoria específica (ex: "moradia" / "casa", listando transações individuais e total).
      - Consulta para período sem dados (retorna mensagem explícita informando ausência no banco de dados, sem mock).
      - Consulta com desconsideração de receitas (`income`).
      - Isolamento estrito de dados por usuário.

- [x] **Etapa 7: Executar (Desenvolvedor)**
  - [x] Atualizar `backend_ia/services/prompts/system_base.py` com regra mandatória de factualidade e proibição de alucinação.
  - [x] Atualizar `backend_ia/services/prompts/financial_rules.py` com orientações de uso de `consultar_resumo_gastos` com e sem categoria e proibição de inventar números.
  - [x] Atualizar `backend_ia/services/tools_dispatcher.py` com regex de finanças expandido para cobrir "gastos", "valores de gastos", "quais gastos", "por categoria", etc.
  - [x] Atualizar `backend_ia/services/tools/finance_tool.py`:
    - Adicionar suporte ao parâmetro `categoria: Optional[str] = None` em `consultar_resumo_gastos`.
    - Ajustar consulta para ser compatível com as datas e campos do Firestore usados pelo dashboard (`date`, `created_at`, `timestamp`).
    - Excluir transações do tipo `income`.
    - Suportar detalhamento por categoria e alias semântico (ex: moradia -> casa).
    - Retornar mensagens factual e sem alucinação quando não houver dados.

- [x] **Etapa 8: Code Review (Reviewer)**
  - [x] Revisão de Clean Code, tipagem, docstrings e aderência ao `GLOSSARY.md`.

- [x] **Etapa 9: UX Review (UX Reviewer)**
  - [x] Bypass aprovado (sem alterações em interface web).

- [x] **Etapa 10: Testar e Auto-Healer (Tester)**
  - [x] Executar suíte de testes com `pytest` e garantir 100% de sucesso nos novos testes e testes de finanças.

- [x] **Etapa 11: Auditoria de Segurança (SecOps)**
  - [x] Validar isolamento multi-tenant, sanitização e prevenção de bypass de prompt injection.

- [x] **Etapa 12: Release via Pull Request (DevOps)**
  - [x] Atualizar `STATE.md`, checklist e documentação.
