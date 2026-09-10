# Especificação Funcional & Tarefas: PC-11 (Otimização de Tokens & FinOps GCP 4.8+)

## 1. Descrição Funcional
Implementação do conjunto abrangente de otimizações de tokens no motor de IA do DAM (FastAPI + Gemini) e refatoração da governança de infraestrutura no Google Cloud Platform para elevação do Score FinOps de 3.0/5 para 4.8+/5.

---

## 3. Checklist Técnico de Desenvolvimento (Task Planning)

### Bloco 1: Roteamento Dinâmico de Ferramentas & Prompts Modulares
- [x] **Task 1.1:** Criar `backend_ia/services/tools_dispatcher.py` com o classificador de intenção `ToolsDispatcher` mapeando domínios (finanças, agenda, notas, mobilidade, anime, nutrição, clash, cs2, etc.) e retornando lista filtrada de ferramentas ou `None` para saudações e conversas diretas.
- [x] **Task 1.2:** Refatorar `backend_ia/services/prompts/prompt_composer.py` para aceitar a intenção detectada e injetar somente os módulos pertinentes ao turno da conversa.

### Bloco 2: Otimizador Multimodal de Mídias (Pillow & PyMuPDF)
- [x] **Task 2.1:** Criar `backend_ia/services/media_optimizer.py`:
  - Método `optimize_image(media_base64: str, max_dimension=1024, quality=80) -> tuple[str, str]`: downsample proporcional, remoção de canais alfa, compressão JPEG.
  - Método `extract_text_from_pdf(media_base64: str) -> Optional[str]`: extração local e limpa de texto via PyMuPDF (`fitz`), sanitização de quebras de linha e headers.
  - Método `compute_media_hash(media_base64: str) -> str`: cálculo de SHA-256 do binário para indexação de cache.

### Bloco 3: Extensão do Cache Semântico para Mídias & SHA-256
- [x] **Task 3.1:** Atualizar `ConversationCacheService` em `backend_ia/services/cache_service.py` para remover a trava de bypass de mídia e aceitar `media_hash`.
- [x] **Task 3.2:** Integrar o cache de mídias em `get_cached_response` e `save_response`.

### Bloco 4: Orquestração no AIService & Webhook
- [x] **Task 4.1:** Atualizar `backend_ia/services/ai_service.py` para invocar o `MediaOptimizer` e, em caso de PDF com texto extraível, converter a mensagem para texto puro dispensando envio multimodal pesado.
- [x] **Task 4.2:** Integrar o `ToolsDispatcher` no `ai_service.py` para instanciar o modelo com a lista enxuta de ferramentas ou `tools=None`.
- [x] **Task 4.3:** Integrar a verificação de Circuit Breaker econômico caso o consumo mensal esteja em situação crítica.

### Bloco 5: Scorecard FinOps 4.8+ & Governança GCP
- [x] **Task 5.1:** Atualizar `backend_ia/services/tools/gcp_billing_tool.py` para calcular e renderizar o Scorecard FinOps 4.8+/5.0 com avaliação detalhada dos 5 pilares da nuvem.
- [x] **Task 5.2:** Criar o script `deploy_cloud_run.ps1` com os parâmetros do Always Free e modelo de ping no Cloud Scheduler.
- [x] **Task 5.3:** Criar o arquivo de política de ciclo de vida do Cloud Storage `gcs_lifecycle.json` (auto-delete em 7 dias para temp).


