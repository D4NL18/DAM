# Checklist da Tarefa: SB-04 Guia Nutricional & Lista de Substituição (Dietbox)

## Informações Gerais
- **ID da Tarefa:** `TASK-SB04-001`
- **Domínio:** Saúde & Bem-Estar
- **Agentes Envolvidos:** Todos (12 Etapas AGENTS.md)
- **Status:** Em Andamento

---

## Checklist de Implementação

### 1. Modelagem e Dados Oficiais (DBA & Dev)
- [x] Extração dos 132 alimentos oficiais em 7 grupos do PDF Dietbox.
- [ ] Criação do módulo `services/tools/nutrition_dietbox_data.py`:
  - [ ] Dicionário `GRUPOS_ALIMENTARES` com médias calóricas.
  - [ ] Lista `ALIMENTOS_DIETBOX` com porções, gramaturas e aliases.
  - [ ] Função `normalizar_termo_alimento(termo: str) -> str`.
  - [ ] Função `buscar_alimento_dietbox(nome: str)`.

### 2. Ferramentas de Nutrição & Consulta Web Sanitizada (Dev & Arquiteto)
- [ ] Criação do módulo `services/tools/nutrition_tool.py`:
  - [ ] Implementar `consultar_lista_substituicao(alimento_ou_grupo: str) -> str`.
  - [ ] Implementar `avaliar_substituicao_alimento(alimento_desejado: str, alimento_a_substituir: str = "") -> str`.
  - [ ] Mecanismo de busca externa de tabela nutricional para itens fora da lista.
  - [ ] Sanitização anti-SSRF e anti-injection nos termos pesquisados.
  - [ ] Formatação de alertas em destaque (`⚠️ ALERTA: ...`).
  - [ ] Elaboração dos 4 pilares de pontos de atenção.

### 3. Diretrizes de IA & Prompts Modulares (AI Specialist & Dev)
- [ ] Criação de `services/prompts/nutrition_rules.py`.
- [ ] Atualização de `services/prompts/prompt_composer.py` para injetar `get_nutrition_prompt()`.
- [ ] Registro das tools em `AVAILABLE_TOOLS` em `services/ai_service.py`.

### 4. Suíte de Testes TDD (Tester)
- [ ] Criação de `backend_ia/tests/test_nutrition_substitutions.py`.
- [ ] Teste de consulta por grupo (Carboidratos, Carnes, Frutas, Laticínios, Legumes, Leguminosas, Gorduras).
- [ ] Teste de consulta por alimento exato e alimento com alias (ex: 'arroz', 'filé de frango').
- [ ] Teste de equivalência válida no mesmo grupo.
- [ ] Teste de alerta mandatório para alimentos fora da lista (ex: 'chocolate', 'pizza').
- [ ] Teste de pontos de atenção na análise comparativa.
- [ ] Teste de integração com `PromptComposer`.
- [ ] Teste de sanitização contra termos maliciosos/injection.

### 5. Qualidade, Segurança e Finalização
- [ ] Execução de `pytest` (100% dos testes aprovados, zero regressões).
- [ ] Revisão de Código (Reviewer) e UX Reviewer (formatação WhatsApp).
- [ ] Auditoria SecOps.
- [ ] Fechamento DevOps, atualização de `STATE.md`, `ROADMAP.md` e `KNOWLEDGE_GRAPH.md`.
