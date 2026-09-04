# ADR 008: Arquitetura de Cache de Prompts e Conversas com Otimização de Tokens (PC-08)

## Status
Aprovado

## Contexto
O assistente DAM processa dezenas de mensagens diárias via WhatsApp através do Google Gemini. Mensagens idênticas ou consultas informativas estáticas (como dúvidas sobre guerras no Clash of Clans ou lista de substituição Dietbox) consumiam chamadas completas de LLM, gerando custos desnecessários de tokens e latência de 2 a 5 segundos por requisição.
Ao mesmo tempo, certas consultas são altamente dinâmicas:
- O trânsito em tempo real varia a cada minuto e nunca pode ser servido por cache antigo.
- Os jogos de CS2 (FURIA) têm horários que podem sofrer alterações até poucas horas antes do evento ou prorrogações ao vivo, exigindo que o cache expire no máximo até 2 horas antes da partida.

## Decisão Arquitetural

1. **Roteador de Volatilidade Semântica (`ConversationCacheService`):**
   - Inspeciona o texto antes da chamada ao Gemini.
   - Categorias:
     - `REALTIME_VOLATILE` (Trânsito/Maps/Travas): Bypass imediato de cache.
     - `STATE_CHANGING_ACTION` (Escritas financeiras, lembretes, agenda, ponto): Bypass imediato de cache.
     - `CLASH_OF_CLANS` (Guerra / Capital): Cache com TTL de 1 hora.
     - `CS2_ESPORTS` (Counter-Strike / FURIA): Cache com TTL dinâmico ancorado no horário da partida mais próxima ($\le T_{match} - 2\text{h}$).
     - `STATIC_INFORMATIONAL` (Nutrição, Streaming, Cardápios, Conversões): Cache com TTL de 12h a 24h.

2. **Hierarquia de Armazenamento L1/L2:**
   - **L1 (In-Memory LRU Cache):** Dicionário thread-safe protegido por `threading.Lock`. Busca $O(1)$, latência < 1ms.
   - **L2 (Firestore `conversation_cache`):** Persistência remota opcional para sobrevivência a reinicializações de container.

3. **Integração Não-Invasiva:**
   - `AIService.process_message` consulta o cache imediatamente após os Guardrails de segurança.
   - Se houver `Cache Hit`, a resposta gravada é retornada imediatamente, poupando a invocação do `genai.GenerativeModel.start_chat` e todas as chamadas de funções.
   - Se houver `Cache Miss`, o fluxo normal do Gemini é executado. Ao final, a resposta gerada é avaliada e, se elegível, gravada no cache com seu respectivo TTL.

## Consequências
- Redução de até 60% no consumo de tokens para perguntas frequentes.
- Redução da latência de resposta de ~3s para ~2ms nos hits de cache.
- Segurança de dados: isolamento multi-tenant estrito por `remote_jid` e garantia de não cachear mutações de estado.
