# Regras de Negócio: Otimização de Tokens & Cache Inteligente de Conversas

**Código da Feature:** `PC-08`  
**Domínio:** Plataforma, Segurança & Core  
**Objetivo:** Reduzir o custo de tokens e a latência de resposta do DAM por meio de um sistema de cache semântico de conversas e prompts, respeitando estritamente a volatilidade dos dados de cada domínio funcional.

---

## 1. Regras de Negócio (RN-CACHE)

### RN-CACHE-001: Roteamento Semântico de Volatilidade de Consultas
Antes de despachar uma mensagem para o modelo de linguagem (Gemini), o sistema deve inspecionar e classificar a mensagem do usuário em uma das seguintes categorias de volatilidade:
1. **`REALTIME_VOLATILE` (Trânsito, Mobilidade Urbana e Status de Atuadores):**
   - *Escopo:* Perguntas sobre trânsito, rota, tempo de percurso, tráfego, horário ideal de saída, status de travas ou sensores do carro.
   - *Comportamento:* **Bypass total de cache** (`cacheable = False`, TTL = 0). O sistema DEVE consultar os serviços externos (Google Maps Directions, etc.) e processar em tempo real.
2. **`STATE_CHANGING_ACTION` (Ações de Escrita e Mutações de Estado):**
   - *Escopo:* Comandos para registrar despesas, criar lembretes ou notas, agendar eventos, salvar credenciais, disparar rotinas da Alexa, fechar viagens ou registrar ponto.
   - *Comportamento:* **Bypass total de cache**. Ações que geram efeitos colaterais no banco de dados ou em dispositivos físicos nunca podem ser respondidas a partir de um cache anterior.
3. **`CLASH_OF_CLANS` (Guerra de Clãs e Capital / Raid Weekend):**
   - *Escopo:* Dúvidas se há guerra no Clash hoje, status de ataques da Guerra de Clãs ou Raids da Capital.
   - *Comportamento:* **Reuso de resposta** (`cacheable = True`). Se o usuário perguntar 2 ou mais vezes sobre guerra no Clash of Clans dentro do período de validade (TTL padrão: 3600 segundos / 1 hora), o DAM deve devolver a mesma resposta sem acionar a LLM e sem consumir tokens.
4. **`CS2_ESPORTS` (Partidas de Counter-Strike 2 / FURIA):**
   - *Escopo:* Consultas sobre jogos agendados, horários de partidas ou próximos confrontos no CS2.
   - *Comportamento:* **Expiração dinâmica de até 2 horas antes da partida**:
     - O sistema obtém o horário do jogo agendado mais próximo ($T_{jogo}$).
     - Se $T_{jogo} - \text{agora} > 2\text{ horas}$, o cache expira exatamente em $T_{jogo} - 2\text{ horas}$ (limitado a um teto máximo de 2 horas).
     - Se faltar menos de 2 horas para o início da partida ou o jogo já estiver ao vivo/em andamento, o cache é **desativado** (TTL = 0), pois horários, mapas e placares mudam dinamicamente.
5. **`STATIC_INFORMATIONAL` (Nutrição Dietbox, Streaming, Conversões, Cardápios, Ideias):**
   - *Escopo:* Consultas informativas de alto consumo de tokens (ex: lista de substituição de alimentos Dietbox, onde assistir filmes/séries, conversões matemáticas de medidas, explicações de pratos).
   - *Comportamento:* **Cache de longa duração** (TTL: 43200 a 86400 segundos / 12h a 24h).

---

### RN-CACHE-002: Normalização e Chave de Cache Segura
- A chave de cache deve ser gerada deterministicamente por função hash SHA-256 sobre a tupla `(remote_jid, normalized_text)`.
- A normalização de texto converte para minúsculas, remove acentos, pontuações, espaços múltiplos e stopwords irrelevantes.

---

### RN-CACHE-003: Isolamento Inviolável por Usuário (Multi-Tenant Zero Leak)
- Entradas de cache de um usuário (`remote_jid_A`) **JAMAIS** podem ser servidas a outro usuário (`remote_jid_B`).
- Cada chave de cache é estritamente vinculada ao `remote_jid` do remetente autorizado.

---

### RN-CACHE-004: Invalidação Sob Demanda e Palavras de Forçamento
- Se a mensagem do usuário contiver palavras explícitas de forçamento de atualização (ex: "atualiza", "atualizar", "novamente", "forçar", "tempo real", "ao vivo", "agora"), o sistema deve invalidar qualquer entrada de cache existente para a query e executar uma chamada fresca.

---

### RN-CACHE-005: Resiliência e Fail-Safe
- Se o backend de cache (L1 memória ou L2 Firestore) falhar ou lançar exceção, o fluxo principal de processamento de IA prossegue normalmente com a chamada ao Gemini.

---

### RN-CACHE-006: Métricas e Transparência
- O serviço de cache monitora `hits`, `misses` e `tokens_saved_estimated`.
