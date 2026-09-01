---
name: springboot-expert
description: Especialista em Java Spring Boot, estruturação de APIs e injeção de dependências.
---
# Habilidade: Java Spring Boot Expert

## Propósito
Garantir o desenvolvimento de aplicações Java Spring Boot robustas, escaláveis e limpas, seguindo os padrões do ecossistema Java corporativo.

## Diretrizes Obrigatórias
1. **Estrutura de Pacotes (Obrigatória):**
   O projeto DEVE seguir esta exata organização de pacotes:
   - **`controllers`**: Apenas lidam com requisições HTTP, rotas e delegação.
   - **`dtos`**: Divididos rigorosamente nas subpastas **`requests`** e **`responses`**.
   - **`entities`**: Modelos mapeados do banco de dados (ex: JPA `@Entity`).
   - **`enums`**: Enumerações padronizadas do sistema.
   - **`exceptions`**: Classes de exceções customizadas de domínio.
   - **`infra`**: Configurações gerais da infraestrutura (ex: `config`, `security`, e global exception handlers).
   - **`mappers`**: Classes responsáveis pela tradução de DTOs para Entidades e vice-versa.
   - **`repositories`**: Interfaces do banco de dados (ex: Spring Data JPA).
   - **`services`**: Onde a regra de negócio vive.
   - **`utils`**: Funções utilitárias e validações reutilizáveis.
2. **Isolamento de Banco e Mappers:**
   - A API (Controllers) NUNCA pode transacionar `Entities`. Todo o fluxo de entrada e saída passa obrigatoriamente pelas classes do pacote `mappers/` para ser transformado em `RequestDTO` ou `ResponseDTO`.
   - **Imutabilidade:** Para DTOs, prefira utilizar a estrutura `record` do Java 14+ para garantir imutabilidade absoluta nas respostas e requisições.
3. **Linguagens e Ferramentas:**
   - **Java 17+** e framework **Spring Boot 3+**.
   - **Técnica do Espelho (Obrigatório):** ANTES de criar um Controller, você DEVE ler o arquivo `.agents/skills/springboot-expert/examples/springboot-controller.java`. Imite rigorosamente o cabeçalho JavaDoc do topo do arquivo, a injeção com `@RequiredArgsConstructor` e as anotações completas do Swagger (`@Operation`, `@Tag`).
   - Uso intensivo de anotações do Lombok (`@Data`, `@Builder`, `@RequiredArgsConstructor`, `@NoArgsConstructor`, `@AllArgsConstructor`) para reduzir verbosidade.
   - **Tratamento de Exceções Globais:** Centralize o tratamento de erros dentro do pacote `infra/exceptions` e/ou `exceptions`, utilizando `@ControllerAdvice`.
   - As respostas de erro DEVEM retornar entidades JSON estruturadas utilizando `ResponseEntity<Object>` (ex: `{ "status": 400, "message": "..." }`).
4. **Injeção de Dependência:**
   - Priorize a injeção via Construtor em vez de usar `@Autowired` diretamente em propriedades.
