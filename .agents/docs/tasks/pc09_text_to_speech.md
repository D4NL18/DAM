# Checklist da Tarefa: PC-09 Text-to-Speech & Síntese de Voz / Respostas em Áudio

- **ID da Tarefa:** `TASK-PC09-001`
- **Domínio:** 6. Plataforma, Segurança & Core
- **Status:** Concluído (100%)

---

## Checklist de Implementação

### 1. Suíte de Testes TDD (Tester)
- [x] Criar `backend_ia/tests/test_tts_service.py`:
  - [x] Teste de sanitização de texto para fala (remoção de `*`, `_`, emojis, formatações markdown, blocos de código).
  - [x] Teste de substituição amigável de links/URLs ("http...").
  - [x] Teste de pontuação e pausas em listas fonéticas.
  - [x] Teste do detector de intenção de áudio `should_reply_with_audio`:
    - [x] Mensagem recebida do tipo `audioMessage` -> True.
    - [x] Mensagem de texto pedindo áudio ("me responda por áudio", "mande áudio", "fale comigo") -> True.
    - [x] Mensagem de texto comum ("quanto gastei no mercado?") -> False.
  - [x] Teste de síntese de voz (geração de bytes de áudio com mock de provedor TTS).
  - [x] Teste de cache L1 de áudios (evitando chamadas repetidas de síntese para o mesmo texto).
  - [x] Teste de fallback gracioso: quando a síntese falha, o sistema envia mensagem de texto padrão sem quebrar.
  - [x] Teste de envio de nota de voz PTT em `WhatsAppService.send_voice_note`.

### 2. Implementação do Motor de TTS e Integrações (Dev)
- [x] Criar `backend_ia/services/tts_service.py`:
  - [x] Classe `TTSService`.
  - [x] Método `sanitize_text_for_speech(text: str) -> str`.
  - [x] Método `should_reply_with_audio(incoming_text: str, message_type: str) -> bool`.
  - [x] Método `synthesize_speech(text: str) -> Optional[bytes]` com cache L1 em memória e geração de áudio (MP3/OGG).
- [x] Atualizar `backend_ia/services/whatsapp_service.py`:
  - [x] Adicionar método `send_voice_note(remote_jid: str, audio_bytes: bytes, mime_type: str = "audio/ogg")`.
- [x] Atualizar `backend_ia/routers/webhook.py`:
  - [x] Integrar `should_reply_with_audio` e `TTSService.synthesize_speech` no `process_and_reply`.

### 3. Validação e Qualidade (Reviewer, UX, QA, SecOps, DevOps)
- [x] Code Review (Clean Code, tipagem, PEP 8, controle de timeouts).
- [x] UX Reviewer (preservação de dicção limpa sem leitura de código markdown).
- [x] Execução completa do pytest (10/10 testes aprovados).
- [x] SecOps (proteção contra Command Injection / Path Traversal).
- [x] DevOps (atualização de estado e baseline).

