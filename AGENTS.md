# Fluxo de Desenvolvimento com IA (AI Agents Workflow)

Este documento define o fluxo obrigatório para qualquer tarefa de desenvolvimento assistida por Inteligência Artificial neste projeto. O diretório `.agents/` contém o detalhamento individual de cada papel.

## Fluxo de Trabalho (Workflow - 11 Passos)

Todo prompt ou nova requisição deve obrigatoriamente seguir as seguintes etapas na ordem estabelecida.

1. **Quebra de Escopo (Product Owner)**
   - O **PO** recebe a demanda abstrata, fatiando-a em User Stories menores e gerenciáveis dentro do `ROADMAP.md`.

2. **Especificar (Specification)**
   - O **Analista** amarra regras de negócio (P-XXX) e define o escopo da Story selecionada pelo PO.

3. **Projetar (Design & Architecture)**
   - O **Arquiteto** define a arquitetura técnica, banco de dados, APIs (`api-contracts`).
   - O **Designer** (se envolver Frontend) projeta as diretrizes visuais (UI/UX).

4. **Modelagem de Dados Segura (DBA)**
   - O **DBA** traduz o design em arquivos de *Migrations* seguras, aplicando travas contra perda de dados.

5. **Planejar as Tarefas (Task Planning)**
   - O **Arquiteto** decompõe a solução no checklist da Tarefa (em `docs/tasks/`).

6. **Desenvolver Testes Unitários (TDD)**
   - O **Tester** cria a suíte de testes (em código) antes de qualquer lógica produtiva.

7. **Executar (Execution)**
   - O **Desenvolvedor** programa focado em fazer os testes passarem em uma branch isolada da feature.

8. **Code Review (Manutenibilidade)**
   - O **Reviewer** inspeciona o código caçando falhas de Clean Code, complexidade cognitiva (SonarQube) e violações do Dicionário (`GLOSSARY.md`).

9. **UX Review / Vibe Check (Frontend)**
   - O **UX Reviewer** valida se as implementações HTML/SCSS estão de acordo com o `DESIGN_SYSTEM.md`. Se faltarem animações ou tiverem "cara de bootstrap", ele devolve para o Desenvolvedor.

10. **Testar e Auto-Healer Loop (Validation)**
   - O **Tester** roda os testes automatizados e o plano de Auditoria manual para evitar regressões.
   - **Auto-Healer:** Se os testes quebrarem ou o código não compilar, o Orquestrador fará o Desenvolvedor conversar diretamente com o Tester para ler o *Stack Trace* e tentar corrigir o código de forma autônoma por até 3 vezes, antes de devolver para o usuário humano.

11. **Auditoria de Segurança (SecOps)**
    - O **Especialista de Segurança** varre o código aprovado atrás de vulnerabilidades e bloqueia se houver brechas (ex: Injections, LGPD).

12. **Release via Pull Request (DevOps)**
    - O **Engenheiro DevOps** configura os pipelines automáticos (CI/CD) e gera o PR da feature para a branch `develop`, com a descrição pré-preenchida. Commits diretos nas branches base são proibidos.

---

## Papéis dos Agentes

O **Orquestrador** não escreve código. Sua função é alternar entre os agentes e garantir que o `.agents/docs/STATE.md` esteja atualizado com o contexto atual.

- `.agents/agents/orchestrator.md`
- `.agents/agents/product_owner.md`
- `.agents/agents/analyst.md`
- `.agents/agents/architect.md`
- `.agents/agents/designer.md`
- `.agents/agents/dba.md`
- `.agents/agents/developer.md`
- `.agents/agents/reviewer.md`
- `.agents/agents/tester.md`
- `.agents/agents/security.md`
- `.agents/agents/devops.md`
- `.agents/agents/ai_specialist.md`
- `.agents/agents/ux_reviewer.md`

---

## Atalhos (Slash Commands)

Utilize os comandos abaixo no chat para invocar rapidamente os agentes e garantir que a IA assuma o contexto adequado para a tarefa:

- `/init`: Inicia a fase de Fundação do Projeto (Kickoff). O Orquestrador convocará o Arquiteto, o DBA, e as skills de Domain Expert e UI/UX Expert para fazer um Brainstorming Global com o usuário, fazendo perguntas e sugestões inclusive de modelagem de dados para definir o `ARCHITECTURE.md` (Stack/Padrões), `GLOSSARY.md` (regras de domínio) e o `DESIGN_SYSTEM.md` (estética e padrões de UI) base do projeto.
- `/orquestrador`: Inicia o fluxo completo de desenvolvimento. A IA atuará como Orquestrador, criará o `STATE.md` e conduzirá os 11 passos sequencialmente.
- `/po`: Atua isoladamente como Product Owner, fatiando demandas complexas em entregas menores no `ROADMAP.md`.
- `/analyst`: Atua isoladamente como Analista, guiando-se pelas regras de negócio.
- `/architect`: Atua isoladamente como Arquiteto, focando em modelagem e diagramação.
- `/designer`: Atua isoladamente como Designer de UI/UX.
- `/dba`: Atua isoladamente como DBA (foco em modelagem segura de banco e migrations).
- `/developer`: Atua isoladamente como Desenvolvedor (foco em código).
- `/reviewer`: Atua isoladamente como Revisor de Código.
- `/tester`: Atua isoladamente como Testador (QA/TDD).
- `/security`: Atua isoladamente focando em segurança (SecOps).
- `/devops`: Atua isoladamente na configuração de PRs e pipelines.
- `/ai_specialist`: Atua isoladamente como Especialista em IA, focando em Machine Learning, Visão Computacional e integração de LLMs.
