# Entidade / Feature: Recepção Multimodal no WhatsApp (PC-01.1)

Este documento centraliza todo o planejamento, as especificações e as etapas de execução para a correção definitiva da recepção e processamento de imagens, áudios e documentos no assistente DAM.

## 1. Dúvidas Resolvidas (Especificação)
- **Dúvida:** Por que o Gemini respondia "não recebi a foto" ao receber uma imagem?
  - **Decisão:** Identificado que a Evolution API não envia Base64 no payload inicial do webhook. O backend repassava a mensagem com `media_base64=None`. Agora o backend busca ativamente no endpoint `/chat/getBase64FromMediaMessage/{instance}` antes de enviar ao Gemini.
- **Dúvida:** Como tratar áudios e codecs especiais como `audio/ogg; codecs=opus`?
  - **Decisão:** O MIME type deve ser sanitizado para a raiz estrita (`audio/ogg`), que é o formato exigido pela API do Gemini.
- **Dúvida:** Como agir caso a Evolution API falhe no download da mídia?
  - **Decisão:** Não acionar a IA cegamente com prompt de análise; responder diretamente ao usuário avisando sobre a instabilidade de carregamento da mídia e orientando o reenvio.

---

## 2. Tarefas e Etapas de Desenvolvimento

### Tarefa 1: Integração de Download sob Demanda na Evolution API & Sanitização Multimodal

**Descritivo Detalhado:**
Implementar o método de download de Base64 em `WhatsAppService`, conectar no fluxo do webhook em `routers/webhook.py` para imagens, áudios e documentos, higienizar prefixos Data URI e normalizar MIME types antes do repasse ao `AIService`.

**Critérios de Aceite:**
- [x] Quando uma mensagem com `imageMessage` chegar sem Base64 inline, o sistema deve requisitar o Base64 à Evolution API e enviar os bytes ao Gemini junto com a instrução do usuário.
- [x] Quando uma mensagem com `audioMessage` chegar, o Base64 deve ser obtido, o MIME type normalizado (`audio/ogg`) e enviado ao Gemini para transcrição/resposta.
- [x] Prefixos do tipo `data:image/jpeg;base64,` devem ser removidos defensivamente antes do `base64.b64decode`.
- [x] Logs do sistema não devem vazar a string Base64 em texto puro.
- [x] Em caso de falha de download na Evolution API, o sistema não deve chamar a IA com instruções cegas, e sim fornecer aviso claro de reenvio.

**Etapas de Execução (Checklist Técnico):**
- [x] **Etapa 1:** Implementar `WhatsAppService.get_base64_from_media_message` com timeout e tratamento de erros.
- [x] **Etapa 2:** Atualizar `routers/webhook.py` para invocar a extração sob demanda de mídia para imagens, áudios e documentos.
- [x] **Etapa 3:** Atualizar `services/ai_service.py` para sanitizar strings Base64 (remover Data URI e quebras de linha) e normalizar MIME types antes do envio ao Gemini.
- [x] **Etapa 4:** Adicionar suíte de testes TDD em `backend_ia/tests/test_multimodal.py`.

**Audit (Testes e Validação):**
- [ ] **Cenário 1:** Envio de imagem sem base64 inline no payload: o webhook deve acionar `get_base64_from_media_message`, obter os dados e repassar ao `AIService`.
- [ ] **Cenário 2:** Envio de áudio com `audio/ogg; codecs=opus`: o MIME type entregue ao Gemini deve ser `audio/ogg` e o áudio decodificado corretamente.
- [ ] **Cenário 3:** Base64 com prefixo `data:image/png;base64,iVBOR...`: o `AIService` deve decodificar sem erro de padding.
- [ ] **Cenário 4:** Falha na Evolution API ao obter mídia (retorno None): o sistema deve registrar log seguro e responder ao usuário sem acionar a IA cegamente.
