# Planejamento da Tarefa: PC-10 (Migração para WhatsApp Business Dedicado & Isolamento Inviolável)

## 1. Contexto e Motivação
Anteriormente, o bot operava na mesma conta do WhatsApp do usuário ("conversa comigo mesmo").
O usuário criou uma conta dedicada no **WhatsApp Business** com o número:
- **Número do Bot:** `+55 11 77777-7777`
- **Número Pessoal Autorizado:** `11 99999-9999` (`5511999999999`)

## 2. Regras de Negócio e Requisitos de Segurança
1. **RN-01 (Isolamento Inviolável):** O webhook FastAPI deve processar EXCLUSIVAMENTE mensagens vindas do número pessoal cadastrado em `ALLOWED_PHONE_NUMBER=5511999999999`. Qualquer mensagem recebida no WhatsApp Business do bot de outro número (terceiros, spams, clientes acidentais) deve ser sumariamente descartada com status `ignored`, motivo `unauthorized_user`, sem emitir resposta, sem marcar como lida e sem consumir tokens de IA.
2. **RN-02 (Anti-Loop e Eco de Mensagens do Bot):** Em uma conta dedicada de bot, quando o bot envia uma mensagem ou áudio para o usuário, a Evolution API gera um evento `messages.upsert` com `key.fromMe = true` e `remoteJid` apontando para o usuário. O webhook DEVE descartar mensagens onde `key.fromMe = true` (ou quando a mensagem contiver o caractere invisível de eco `\u200b`), prevenindo loops infinitos em texto, imagens e áudios.
3. **RN-03 (Tolerância ao 9º Dígito):** O número pessoal pode chegar do WhatsApp com ou sem o 9º dígito (`5511999999999@s.whatsapp.net` ou `551199999999@s.whatsapp.net`). A função `is_allowed_user` já tolera isso e deve ser rigorosamente testada.
4. **RN-04 (Configuração de Instância e Reconexão):** O script `conectar_whatsapp.py` deve realizar o logout da sessão anterior e gerar um QR Code limpo para ser escaneado com o aplicativo WhatsApp Business do número configurado.
5. **RN-05 (Configurações de Ambiente):** Registrar `BOT_PHONE_NUMBER=5511777777777` como referência opcional de documentação em `settings.py` e `.env.example`, mantendo `ALLOWED_PHONE_NUMBER=5511999999999`.

## 3. Checklist de Implementação
- [ ] Atualizar `.agents/context/ROADMAP.md` com a feature PC-10.
- [ ] Atualizar testes unitários em `backend_ia/tests/test_webhook_isolation.py` cobrindo:
  - Descarte de mensagens com `fromMe: true` (eco do próprio bot).
  - Aceitação da mensagem vinda de `5511999999999` (e com oscilação do 9º dígito).
  - Rejeição de mensagens vindas de qualquer outro número (ex: terceiros mandando mensagem para o bot).
  - Rejeição de grupos e canais.
- [ ] Refatorar `backend_ia/routers/webhook.py`:
  - Garantir a checagem de `fromMe: true` antes de qualquer processamento ou log como mensagem do usuário.
- [ ] Atualizar `backend_ia/config/settings.py` e `.env.example` com o suporte a `BOT_PHONE_NUMBER`.
- [ ] Refatorar `conectar_whatsapp.py` para garantir logout limpo, exibição amigável e confirmação de conexão.
- [ ] Executar suíte de testes completa garantindo 100% de aprovação.
