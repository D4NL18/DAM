# Checklist da Tarefa: PC-08 Otimização de Tokens & Cache Inteligente de Conversas

## Informações Gerais
- **ID da Tarefa:** `TASK-PC08-001`
- **Domínio:** Plataforma, Segurança & Core
- **Status:** Concluído (100%)

---

## Checklist de Implementação

### 1. Suíte de Testes TDD (Tester)
- [x] Criar `backend_ia/tests/test_token_prompt_cache.py`:
  - [x] Teste de normalização semântica de queries e geração de hash determinístico.
  - [x] Teste de isolamento multi-tenant por `remote_jid` (usuários diferentes não compartilham cache).
  - [x] Teste de classificação de volatilidade:
    - [x] Perguntas sobre trânsito/rotas retornam `REALTIME_VOLATILE` (bypass).
    - [x] Comandos de escrita (gastos, lembretes, ponto) retornam `STATE_CHANGING_ACTION` (bypass).
    - [x] Perguntas sobre Clash of Clans retornam `CLASH_OF_CLANS` (cacheável).
    - [x] Perguntas sobre CS2 retornam `CS2_ESPORTS` (cacheável dinâmico).
  - [x] Teste de reuso de resposta para Clash of Clans (segunda chamada não invoca LLM).
  - [x] Teste de expiração dinâmica de CS2:
    - [x] Jogo agendado a mais de 2h: cache expira 2h antes da partida.
    - [x] Jogo a menos de 2h ou ao vivo: cache tem TTL 0 / bypass.
  - [x] Teste de trânsito em tempo real: chamada duplicada é sempre reavaliada fresh.
  - [x] Teste de invalidação forçada por palavras-chave ("atualizar", "forçar").
  - [x] Teste de métricas de tokens economizados e hits/misses.
  - [x] Teste de resiliência a falhas no Firestore (`db is None`).

### 2. Implementação do Serviço de Cache (Dev)
- [x] Implementar `backend_ia/services/cache_service.py`:
  - [x] Enumerador `QueryVolatility` (REALTIME_VOLATILE, STATE_CHANGING_ACTION, CLASH_OF_CLANS, CS2_ESPORTS, STATIC_INFORMATIONAL, UNKNOWN).
  - [x] Detector semântico de intenção e volatilidade.
  - [x] Normalizador de queries e gerador de chave segura.
  - [x] Lógica de cálculo dinâmico de TTL para CS2 e estático para os demais domínios.
  - [x] Métodos `get(remote_jid, text)` e `set(remote_jid, text, response, domain, ttl)`.
  - [x] Armazenamento L1 thread-safe em memória (com `threading.RLock`) e L2 no Firestore com tratamento de erro.
  - [x] Métricas acumuladas (`get_metrics()`).
- [x] Parser de horários e integração com `esports_tool.py`:
  - [x] `extract_game_time_from_text` com suporte a datas absolutas e relativas ("Hoje às HH:MM", "Amanhã às HH:MM").
- [x] Integrar no ciclo de vida em `backend_ia/services/ai_service.py`:
  - [x] Verificar cache logo após os Guardrails.
  - [x] Gravar no cache após resposta do Gemini (se elegível).

### 3. Validação e Qualidade (Reviewer, UX, QA, SecOps, DevOps)
- [x] Code Review (Clean Code, tipagem, PEP 8, zero vazamento de memória).
- [x] UX Reviewer (preservação íntegra da formatação de WhatsApp sem degradação).
- [x] Execução completa do pytest (277 testes no total, 100% aprovados).
- [x] SecOps (auditoria de isolamento multi-tenant e proteção contra vazamento de dados sensíveis).
- [x] DevOps (atualização do `STATE.md`, `ROADMAP.md`, e documentação técnica).
