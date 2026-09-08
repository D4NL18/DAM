# Fase 9: Gestão de Conhecimento e Lembretes (Anotações e Alertas Estruturados)

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 9, dedicada a anotações e lembretes estruturados.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-901 (Estrutura de Anotações e Lembretes):** Cada registro deve conter obrigatoriamente `título`, `descrição` e opcionalmente `data_hora_lembrete` (ISO-8601), além de tags e status (`active`, `done`, `archived`).
- **P-902 (Linguagem Natural no WhatsApp):** O usuário pode criar anotações e lembretes através de comandos em texto ou áudio (ex.: *"Anote uma ideia de projeto: criar um dashboard de viagens com os amigos"*, *"Me lembre de pagar o IPVA dia 20 de outubro às 10h"*).
- **P-903 (Busca e Consulta Inteligente):** O bot deve permitir recuperar anotações por palavra-chave ou contexto (ex.: *"Quais anotações eu tenho sobre o projeto X?"*, *"Quais lembretes tenho para esta semana?"*).
- **P-904 (Disparo Proativo de Notificações):** Caso um item tenha data e hora de lembrete, o sistema deve enviar uma mensagem ativa no WhatsApp no momento exato agendado (ou via rotina de verificação por polling/scheduler).

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 9

#### [ ] Task 9.1: Modelagem e Persistência no Firestore
- [ ] **Etapa 9.1.1:** Criar repositório `backend_ia/repositories/notes_repository.py` manipulando a coleção `notes_reminders`.
- [ ] **Etapa 9.1.2:** Estruturar campos: `id`, `remote_jid`, `title`, `description`, `reminder_at`, `status`, `tags`, `created_at`, `notified`.
- [ ] **Etapa 9.1.3:** Criar índices no Firestore para consultas eficientes por `remote_jid`, `status` e `reminder_at`.

#### [ ] Task 9.2: Tool LLM de Anotações e Lembretes
- [ ] **Etapa 9.2.1:** Criar `backend_ia/services/tools/notes_tool.py` com funções:
  - `criar_anotacao_ou_lembrete(titulo: str, descricao: str, data_hora_lembrete: Optional[str] = None, tags: Optional[List[str]] = None)`
  - `consultar_anotacoes(termo_busca: Optional[str] = None, apenas_pendentes: bool = True)`
  - `concluir_lembrete(id_ou_titulo: str)`
- [ ] **Etapa 9.2.2:** Registrar os schemas no `backend_ia/services/ai_service.py` para Function Calling do Gemini.

#### [ ] Task 9.3: Mecanismo de Notificação Ativa (Lembretes)
- [ ] **Etapa 9.3.1:** Implementar job agendado ou background worker no FastAPI (ex: APScheduler ou rotina assíncrona) que verifica lembretes onde `reminder_at <= now` e `notified == False`.
- [ ] **Etapa 9.3.2:** Disparar a notificação de lembrete via `WhatsAppService.send_text(remote_jid, texto)` e marcar o campo `notified = True`.

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Criação de Anotação Simples):** O usuário envia "Anota aí que o tamanho da minha camiseta é M". O sistema confirma o salvamento com título resumido e descrição completa.
- [ ] **Cenário 2 (Lembrete com Data/Hora):** O usuário diz "Me lembre de ligar para o médico amanhã às 09:30". O sistema agenda e confirma a data e hora do alarme.
- [ ] **Cenário 3 (Notificação Ativa):** No horário agendado, o bot envia proativamente no WhatsApp: "⏰ Lembrete: Ligar para o médico - Descrição: ...".
- [ ] **Cenário 4 (Consulta de Anotações):** O usuário pergunta "O que eu anotei sobre camiseta?". O bot responde informando que o tamanho é M.
