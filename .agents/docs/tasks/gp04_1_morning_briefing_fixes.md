# Tarefa: Correções e Aprimoramentos do Morning Briefing (GP-04.1)

## 📌 Descrição
Correção e aprimoramento dos 4 pilares do Morning Briefing:
1. Filtro temporal estrito para lembretes pendentes (apenas do dia corrente) e sanitização de tags.
2. Filtro estrito de animes (episódios apenas `assistindo`, temporadas/continuações apenas `assistindo` ou `concluido` excluindo `pausado`/`dropado`, e watchlist "o que assistir" com `planejo_assistir` ou `assistindo` com 0 eps).
3. Coexistência de alertas de Guerra/CWL e Raid Weekend no Clash of Clans com suporte a membros com 0 ataques feitos na Capital.
4. Envio multi-usuário do briefing respeitando horários individuais configurados e isolamento estrito de `UserContext` para Lari.

---

## 🎯 Critérios de Aceite
- [x] Lembretes exibidos no briefing são estritamente do dia corrente no fuso de Brasília.
- [x] Tags de lembrete não são renderizadas como representação de array bruto.
- [x] Lançamento de episódios no briefing considera apenas animes em `assistindo`.
- [x] Consulta de temporadas e sequências ignora animes pausados ou dropados.
- [x] Consulta de animes para assistir traz apenas plan to watch ou watching com 0 eps.
- [x] Alerta de Raid Weekend é gerado mesmo se o jogador ainda não realizou ataques na season ativa.
- [x] Alertas de Raid e Guerra/CWL aparecem conjuntamente quando ambos estiverem ativos.
- [x] Briefing de Lari é gerado no contexto isolado de Lari e enviado para seu WhatsApp.
- [x] Scheduler verifica os horários personalizados de cada usuário ativo minuto a minuto.

---

## 🛠️ Checklist de Execução

### Passo 6: TDD (Testes Unitários)
- [x] Criar `tests/test_morning_briefing_fixes.py` cobrindo todos os cenários.
- [x] Executar pytest para confirmar falhas controladas antes da implementação.

### Passo 7: Execução (Desenvolvimento)
- [x] **Story 1:** Atualizar `services/tools/notes_tool.py` e `services/briefing_service.py` com filtro de data e sanitização de tags.
- [x] **Story 2:** Atualizar `services/tools/anime_tracker_tool.py`, `services/briefing_service.py` e `services/prompts/anime_rules.py` com regras de filtragem de status.
- [x] **Story 3:** Atualizar `services/tools/clash_of_clans_tool.py` e `services/briefing_service.py` para alertas simultâneos de CoC e tratamento de 0 ataques.
- [x] **Story 4:** Atualizar `services/briefing_service.py`, `main.py` e `routers/briefing.py` para loop multi-usuário por horário e chaveamento de `UserContext`.

### Passo 8: Code Review
- [x] Verificar aderência ao Clean Code, PEP 8, Early Returns e tipagem completa.

### Passo 9: UX Review
- [x] Validar visual e fluidez das mensagens no WhatsApp.

### Passo 10: Validação de QA & Auto-Healer
- [x] Rodar suíte completa de testes (377+ novos) com 100% de sucesso.

### Passo 11: Auditoria de Segurança
- [x] Verificar ausência de vazamento de dados entre Daniel e Lari.

### Passo 12: DevOps & Release
- [x] Preparar commit semântico e documentação de release para PR contra `develop`.
