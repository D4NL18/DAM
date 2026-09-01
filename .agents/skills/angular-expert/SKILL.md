---
name: angular-expert
description: Especialista em Angular, focado em alta performance, Typescript rigoroso e SCSS.
---
# Habilidade: Angular Expert

## Propósito
Você é a autoridade técnica em desenvolvimento Angular no projeto. Garanta que o código siga as melhores práticas da comunidade, evitando anti-patterns.

## Diretrizes Obrigatórias
1. **Linguagens e Ferramentas:**
   - Obrigatório o uso de **TypeScript** com "Strict Mode" ativado. Tipagem explícita é mandatória.
   - **Técnica do Espelho (OBRIGATÓRIO):** Antes de escrever qualquer código, você DEVE ler o arquivo de exemplo em `.agents/skills/angular-expert/examples/angular-component.ts`. O seu código deve espelhar EXATAMENTE o estilo de documentação (JSDoc no topo e nas funções) e o uso de Signals demonstrado naquele arquivo.
   - Obrigatório o uso de **SCSS** para estilização. Evite CSS puro. 
   - **Estruturação do SCSS:** Utilize variáveis globais separadas (ex: `colors.scss`) e faça o import no arquivo principal (`styles.scss`) usando a diretiva `@forward 'colors';` (ou `@use`). Toda estilização global como scrollbars e outline de inputs deve viver no `styles.scss`.
2. **Arquitetura e Estrutura de Pastas (Obrigatória):**
   - **`src/app/core/`**: Interceptors, guards, e configurações globais singletons.
   - **`src/app/services/`**: Serviços para comunicação com APIs HTTP e regras de negócio.
   - **`src/app/shared/`**: Componentes reutilizáveis globalmente (ex: pipes, diretivas, e componentes como *toast* ou *modals*).
   - **`src/app/views/`**: Componentes de página inteira (telas que respondem diretamente a uma rota do router, ex: `home`, `admin`, `login`).
3. **Padrão Rigoroso de Tipagem (`types/`):**
   - Todos os modelos e interfaces devem viver na pasta **`src/app/types/`**.
   - As interfaces devem ser separadas por domínio em subpastas (ex: `types/auth/`, `types/products/`).
   - É **obrigatória** a nomenclatura `[Nome]Req.interface.ts` para requisições e `[Nome]Res.interface.ts` para respostas da API.
4. **Arquitetura de Componentes e Reatividade (RxJS / Signals):**
   - Adote o padrão *Smart Components* (Container) e *Dumb Components* (Apresentação).
   - Maximize o uso do `async` pipe nos templates HTML. Evite realizar `.subscribe()` manualmente nos componentes se não for estritamente necessário.
   - **Gestão de Estado de Submissão:** É obrigatório que TODOS os botões que enviam requisições (HTTP, formulários, salvamento) tenham seu estado alterado para desabilitado (`[disabled]="isLoading"`) durante o tempo da requisição, impedindo que o usuário clique múltiplas vezes e duplique chamadas à API. Se aplicável, adicione feedback visual (como um texto "Salvando...").
