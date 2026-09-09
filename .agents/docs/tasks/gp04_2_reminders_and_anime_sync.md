# Tarefa: Lembretes Restritos ao Dia por Padrão e Próximo Anime em Tempo Real (GP-04.2)

## 📌 Descrição
Correção e aprimoramento de dois fluxos essenciais solicitados pelo usuário:
1. **Lembretes Diários por Padrão:** Alterar o comportamento padrão de `listar_lembretes_pendentes` para `apenas_hoje=True`, garantindo que perguntas como "quais meus lembretes?" retornem estritamente as pendências de hoje (UTC-3), deixando a exibição de lembretes futuros apenas para pedidos explícitos. Blindar a ingestão de tags em `criar_lembrete` e `criar_anotacao` com extração por tokens regex, prevenindo strings corrompidas no banco.
2. **Próximo Anime Atualizado Dinamicamente:** Implementar renovação autônoma de dados de episódios no Anime Tracker (`anime_tracker_tool.py` e `briefing_service.py`). Se um anime ativo tiver `airing_at` expirado (no passado), o sistema consulta a API AniList em tempo real, atualizando a grade e garantindo que lançamentos de domingo (`Seihantai na Kimi to Boku 2nd Season` às 05:00 e `Mushoku Tensei III` às 12:00) sejam exibidos como o próximo lançamento no briefing matinal, nunca um anime distante ou de planejamento.

---

## 🎯 Critérios de Aceite
- [x] `listar_lembretes_pendentes()` sem argumentos retorna exclusivamente lembretes pendentes da data corrente no fuso de Brasília.
- [x] `listar_lembretes_pendentes(apenas_hoje=False)` permite listar todos os lembretes futuros quando expressamente solicitado.
- [x] Criação de lembretes e anotações higieniza automaticamente tags em formatos malformados (ex: `"['financas', 'claro']"` -> `['financas', 'claro']`).
- [x] Formatação de tags não exibe colchetes duplicados nem aspas (`[#financas #claro #recorrente]`).
- [x] Quando um anime em exibição tiver episódio com timestamp passado, o sistema atualiza autonomamente o `nextAiringEpisode` com o AniList.
- [x] O Morning Briefing (`_obter_info_animes_briefing`) seleciona o anime de domingo (menor data futura entre os animes em `assistindo`) como próximo lançamento quando não houver episódios no dia.
- [x] Animes em status `planejo_assistir` (como `Seishun Buta Yarou` em 15/10) JAMAIS aparecem como próximo lançamento de episódios semanais no briefing.
- [x] Testes unitários cobrindo todos os cenários passam com 100% de sucesso.

---

## 🛠️ Checklist de Execução

### Passo 6: TDD (Testes Unitários)
- [x] Adicionar testes em `tests/test_reminders_and_anime_sync.py` cobrindo:
  - `listar_lembretes_pendentes` com default `apenas_hoje=True`
  - `listar_lembretes_pendentes(apenas_hoje=False)` para todos os itens
  - `criar_lembrete` e `criar_anotacao` com strings malformadas de tags
  - Auto-renovação de episódios expirados no AniList
  - `_obter_info_animes_briefing` escolhendo o anime de domingo correto
  - Garantia de que `planejo_assistir` não seja selecionado como próximo lançamento

### Passo 7: Execução (Desenvolvimento)
- [x] **Story 1 (Lembretes):** Atualizar `services/tools/notes_tool.py`, `services/prompts/system_base.py` e `services/ai_service.py`.
- [x] **Story 2 (Animes):** Atualizar `services/tools/anime_tracker_tool.py` e `services/briefing_service.py`.

### Passo 8: Code Review
- [x] Revisão de código, Clean Code, type hints e complexidade cognitiva.

### Passo 9: UX Review
- [x] Bypass justificado (Nenhuma alteração em componentes de Frontend Web).

### Passo 10: Testar & Auto-Healer
- [x] Rodar pytest completo e verificar 100% de aprovação.

### Passo 11: Auditoria de Segurança
- [x] Verificação de sanitização e ausência de vazamento de contexto.

### Passo 12: DevOps & Release
- [x] Commit e documentação do PR contra `develop`.
