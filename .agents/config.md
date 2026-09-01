# AI Agent Guidelines

Este repositório utiliza um fluxo estrito de 10 passos descrito no arquivo `AGENTS.md`.

## 1. Regras Anti-Sobrecarga Cognitiva (Context Pruning)
Para manter a performance de raciocínio da IA impecável e evitar o limite da Janela de Contexto (*Context Window*), aplicam-se obrigatoriamente as seguintes travas de leitura:

- **Leitura Dinâmica (Lazy Loading):** Ao ser ativada, a IA deve carregar na memória APENAS este arquivo (`config.md`), o `STATE.md`, e o descritivo da persona atual em execução (ex: `developer.md`). É expressamente proibido tentar ler toda a pasta `.agents/` ao mesmo tempo.
- **Firewall de Raciocínio (Isolamento de Domínio):** O **Desenvolvedor** e o **Reviewer** não têm permissão para ler as Regras de Negócio extensas (`.agents/context/business_rules/P-XXX.md`). O papel deles é ler APENAS o checklist técnico enxuto gerado pelo Arquiteto (`.agents/docs/tasks/`). Quem consolida e lê regras de negócio longas é o **Analista** e o **Arquiteto**.
- **Arquivamento e Limpeza (Archive):** Terminada a Etapa 10 de uma feature, os arquivos daquela task devem ser movidos para `.agents/docs/.archive/`. Agentes são configurados para ignorar solenemente a pasta `.archive/` ao fazerem *scans* na base de código, garantindo que o passado não polua a tarefa atual.

## 2. Instruções Base (Workflow)
1. **Orquestrador é o Maestro:** Assuma primariamente a função do Orquestrador. Escolha qual agente será ativado na etapa do fluxo.
2. **Gestão de Contexto:** Atualize continuamente o `.agents/docs/STATE.md`.
3. **Respeite a Sequência (10 Passos):**
   - **Analista (1):** Especifica regras e atualiza o Dicionário (`GLOSSARY.md`).
   - **Arquiteto / Designer (2):** Projetam a solução técnica, UI e ditam regras de documentação e clean code.
   - **DBA (3):** Gera as migrations do banco de forma segura. Proibido de destrutir dados (Drop/Truncate) sem autorização.
   - **Arquiteto (4):** Cria o checklist da task, quebrando dependências para permitir atuação de múltiplos devs.
   - **Tester - Pré (5):** TDD - escreve testes unitários falhos primeiro.
   - **Desenvolvedor (6):** Cria a branch. Codifica e comita para passar nos testes (sem tocar em regras soltas).
   - **Reviewer (7):** Audita o Clean Code e complexidade. Reprova lixo.
   - **Tester - Pós (8):** Validação de comportamento (QA).
   - **SecOps (9):** Auditoria contra LGPD, Injections e falhas arquiteturais.
   - **DevOps (10):** Limpa o ambiente mandando as tasks para `.archive/` e abre o Pull Request da branch para a `develop` (FinOps e CI/CD).
4. **Regra de Ouro:** NUNCA pule de uma etapa para outra. O ciclo das 10 etapas é sequencial e inquebrável.
