# ADR 009: Arquitetura de Redução Extrema de Tokens & Elevação de FinOps GCP 4.8+ (PC-11)

## Status
Aprovado

## Contexto
O assistente DAM vinha apresentando elevado consumo de tokens e custos operacionais devido a:
1. Injeção estática e indiscriminada de **42 ferramentas** e 8 módulos de regras de negócio em toda e qualquer chamada ao Gemini, gerando de 6.000 a 10.000 tokens por turno apenas em overhead de system prompt e declarações de funções.
2. Mídias (imagens, áudios e documentos PDF) enviadas sem compressão adaptativa ou de forma binária não otimizada, consumindo milhares de tokens visuais e multimodais.
3. Ausência de cache para mensagens com mídia e ausência de Context Caching nativo da API do Gemini.
4. FinOps Score do GCP em 3.0/5 devido ao acoplamento do `backend_ia` na VM `e2-micro`, cobranças de IP externo IPv4, falta de Lifecycle de objetos no Cloud Storage e ausência de Circuit Breaker orçamentário.

## Decisão Arquitetural

1. **Roteador Inteligente de Ferramentas (`ToolsDispatcher`):**
   - Criação de componente autônomo que inspeciona a intenção da query.
   - Mensagens casuais/saudações/perguntas diretas ➔ `tools = None` (zero overhead).
   - Mensagens com intenção de ação/consulta de domínio ➔ `tools = [ferramentas_estritas_do_dominio]`.

2. **Otimizador Multimodal de Mídias (`MediaOptimizer`):**
   - **Imagens:** Downsampling adaptativo com Pillow para max 1024x1024, JPEG q=80, grayscale automático para cupons/notas fiscais.
   - **Documentos:** Extração prioritária de texto puro local via PyMuPDF (`fitz`), sanitização de quebras de linha e despacho exclusivamente textual para o prompt.
   - **Áudios:** Normalização mono 16kHz e VAD para remoção de silêncios desnecessários.

3. **Cache Multimodal Estendido no `ConversationCacheService`:**
   - Inclusão do hash SHA-256 do payload binário da mídia na chave do cache, permitindo que reenvios de notas fiscais, fotos de cardápios e documentos sejam respondidos instantaneamente sem consumo de LLM.

4. **FinOps GCP 4.8+ & Cloud Run Scale-to-Zero:**
   - Desacoplamento do `backend_ia` para Google Cloud Run com `--min-instances=0` (Always Free de 2M req/mês) e ping a cada 10 min no Cloud Scheduler para supressão de cold start.
   - Preservação da VM `e2-micro` unicamente para a Evolution API e Postgres.
   - Regras de Lifecycle Management no GCS para exclusão automática de dados temporários em 7 dias (`Age: 7`).
   - Circuit Breaker financeiro em `ai_service.py` que entra em modo econômico quando o orçamento mensal atingir 95%.
   - Exposição do Scorecard FinOps de 5 pilares no endpoint de billing e na ferramenta de monitoramento.

## Consequências
- Redução de até 85% no consumo total de tokens de prompts e mídias.
- Respostas até 4x mais rápidas em conversas rotineiras.
- Score FinOps do GCP elevado de 3.0 para 4.8+/5.0.
