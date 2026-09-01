---
name: git-expert
description: Habilidade responsável por aplicar o Padrão de Commits, controle de Branches e regras de Pull Requests (PRs) no repositório.
---
# Habilidade: Git Conventions Expert

## Propósito
Garantir o controle de versão rigoroso e rastreabilidade no projeto. Evita commits genéricos e protege o código de produção contra quebras acidentais.

## 1. Proteção de Branches (Bloqueio)
**É EXPRESSAMENTE PROIBIDO** realizar commits diretos nas branches base: `develop`, `qa`, e `main`/`master`. Todo o desenvolvimento DEVE ocorrer isoladamente em novas branches criadas especificamente para a tarefa.

## 2. Padrão de Branches (Desenvolvedor)
Para toda nova tarefa, crie uma branch isolada a partir da `develop`.
- **Formato:** `tipo/P-XXX-descrição-curta` (Onde P-XXX é a regra de negócio principal que está sendo atendida).
- **Exemplo Válido:** `feature/P-001-valida-maioridade`, `fix/P-002-corrige-token`

## 3. Conventional Commits (Desenvolvedor)
O formato obrigatório para commits é: `<tipo>: [<referência P-XXX>] <descrição no imperativo>`
- **Tipos Permitidos:**
  - `feat`: Uma nova funcionalidade ou regra implementada.
  - `fix`: Correção de bug.
  - `test`: Adição ou refatoração de testes (passo de TDD).
  - `refactor`: Melhorias de clean code apontadas pelo Reviewer.
  - `docs`: Atualizações de documentação.
- **Exemplos Válidos:** 
  - `feat: [P-001] adiciona validação de maioridade na criação do cadastro`
  - `refactor: [P-001] extrai lógicas de envio de email para serviço próprio`

## 4. Padrão de Pull Requests (DevOps)
Quando a tarefa estiver concluída e validada por toda a pipeline (Code Review, QA, SecOps), o Pull Request DEVE ser aberto.
- **Regra de Ouro do PR:** O Pull Request deve ser gerado **sempre contra a branch `develop`**. Nunca aponte um PR de feature direto para a `main`.
- **Template Obrigatório:** O corpo do Pull Request DEVE obrigatoriamente seguir a seguinte estrutura em Markdown:
```markdown
## O que mudou?
- Breve resumo das alterações.
- [ ] Regras de Negócio atendidas (P-XXX)

## Screenshots ou Vídeos
- [Insira imagens se houver mudanças visuais]

## Passos para testar localmente
1. Exemplo de comando...
```
