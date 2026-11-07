# Regras de Negócio: Lembretes Diários por Padrão e Próximo Anime em Tempo Real (GP-04.2)
**Domínio:** Gestão Pessoal & Rotina, Entretenimento (Animes)
**ID Épico:** GP-04.2

---

## 1. Visão Geral
Este documento estabelece as regras de negócio para a exibição de lembretes restritos exclusivamente ao dia corrente por padrão nas consultas do usuário, a higienização defensiva de tags no armazenamento do Firestore, e a renovação autônoma de episódios expirados da watchlist via AniList para seleção precisa do próximo lançamento de animes (ex: lançamentos de domingo).

---

## 2. Regras de Negócio Estruturadas (P-XXX)

### Domínio: Lembretes & Notas
- **P-0419 (Listagem Padrão de Lembretes Restrita ao Dia de Hoje):**
  - A ferramenta `listar_lembretes_pendentes` DEVE ter como comportamento padrão (`apenas_hoje=True`) filtrar e exibir exclusivamente os lembretes pendentes agendados para a data corrente no fuso de Brasília (`YYYY-MM-DD`).
  - Quando o usuário perguntar genericamente ("quais meus lembretes?", "lembretes", "o que tenho pendente?"), a resposta DEVE conter estritamente as tarefas do dia de hoje.
  - O parâmetro `apenas_hoje=False` DEVE ser acionado apenas se o usuário solicitar expressamente ("todos os lembretes", "lembretes futuros", "ver tudo").
  - Caso não haja lembretes para o dia corrente, a mensagem de resposta DEVE informar: `🎉 Nenhum lembrete pendente para hoje! Você está em dia.`

- **P-0420 (Higienização Defensiva de Tags na Ingestão de Notas e Lembretes):**
  - Em `criar_lembrete` e `criar_anotacao`, o processamento de tags DEVE utilizar extração determinística por tokens regex (`[a-zA-Z0-9_\-]+`), rejeitando colchetes, aspas ou caracteres especiais residuais de strings como `"['financas', 'claro', 'recorrente']"`.
  - As tags salvas no Firestore DEVEM ser listas limpas de strings (ex: `['financas', 'claro', 'recorrente']`).
  - A exibição visual DEVE produzir formato limpo sem duplicações de colchetes ou caracteres residuais: `[#financas #claro #recorrente]`.
  - Os documentos existentes corrompidos no Firestore (como o lembrete `5aa90606`) DEVEM ser higienizados para o novo padrão.

### Domínio: Animes (AniList Live Sync & Próximo Lançamento)
- **P-0421 (Renovação Dinâmica de Próximo Episódio via AniList):**
  - No Morning Briefing (`_obter_info_animes_briefing`), na grade semanal (`grade_semanal_animes`) e na consulta de próximo episódio (`consultar_proximo_episodio`), se os animes em `assistindo` possuírem `airing_at` anterior ao momento atual (episódio já transmitido no passado), o sistema DEVE atualizar autonomamente os dados de `nextAiringEpisode` consultando o AniList GraphQL.
  - O próximo anime agendado DEVE ser o anime com status `assistindo` que possua a menor data futura (`dt_ep > hoje`).
  - Lançamentos do final de semana corrente (ex: Domingo 13/09, `Seihantai na Kimi to Boku 2nd Season` às 05:00 e `Mushoku Tensei III` às 12:00) DEVEM ser devidamente identificados como o próximo lançamento, eliminando a exibição de animes distantes de planejamento (`Seishun Buta Yarou` em 15/10).
