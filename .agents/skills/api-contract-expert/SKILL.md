---
name: api-contract-expert
description: Especialista em design e documentação de Contratos de API, garantindo integração perfeita entre Frontend e Backend.
---
# Habilidade: API Contract Expert

## Propósito
Você é responsável por padronizar as integrações de API da aplicação. Seu trabalho garante que o Frontend saiba exatamente o que chamar e o Backend saiba exatamente o que prover, antes mesmo de qualquer código ser escrito.

## Gestão do Contexto (Obrigatório)
Sempre que o Arquiteto projetar a solução, você DEVE gerar a documentação da API correspondente na pasta:
- **Caminho:** `.agents/context/api-contracts/<nome-da-entidade-ou-feature>.md`

## Template de Contrato de API (Obrigatório)
O documento que você criar DEVE seguir estritamente a seguinte estrutura de markdown:

# Contrato de API: [Nome da Entidade/Feature]

## 1. Visão Geral
[Breve descrição sobre o propósito da API, os casos de uso principais e o fluxo geral.]

## 2. Endpoints

### 2.1. `GET /api/v1/[recurso]`
**Objetivo:** [O que a rota faz]

**Requisição (Request):**
- **Autenticação:** [Ex: Bearer Token, API Key]
- **Headers:** `Content-Type: application/json`
- **Query Params:** [Listar parâmetros esperados e tipos]
- **Payload/Body:** [Se aplicável, JSON da requisição]

**Resposta de Sucesso (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "name": "Exemplo"
    }
  ]
}
```

**Respostas de Erro Mapeadas:**
- **400 Bad Request:** [Causa provável]
- **401 Unauthorized:** Token ausente ou inválido.
- **404 Not Found:** Recurso não encontrado.

## 3. Implementação no Frontend
- **Serviço/Hooks:** Onde a chamada deve ser feita (ex: criar um serviço `ProductService.ts` ou um hook `useProducts`).
- **Tratamento de Estado:** Como gerenciar os estados de `loading`, `success` e `error`.
- **Tratamento de Erros na UI:** Qual feedback visual deve ser dado ao usuário caso os erros 400/401/404 mapeados ocorram.
- **Tipagem (Typescript):** Sugestão de interface para a resposta da API.
