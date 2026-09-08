# Regras de Negócio: Aprimoramentos do Morning Briefing (GP-04.1)
**Domínio:** Gestão Pessoal & Rotina, Entretenimento (Animes e CoC) e Multi-Tenancy
**ID Épico:** GP-04.1

---

## 1. Visão Geral
Este documento estabelece as regras de negócio estritas para a consolidação matinal (Morning Briefing), filtros comportamentais de animes, alertas do Clash of Clans e a entrega multi-usuário personalizada e isolada.

---

## 2. Regras de Negócio Estruturadas (P-XXX)

### Domínio: Lembretes & Tarefas Diárias
- **P-0410 (Filtro Temporal Estrito de Lembretes):** O bloco "Tarefas & Lembretes" do Morning Briefing DEVE listar única e exclusivamente os lembretes pendentes agendados para o dia de exibição da mensagem (data corrente no fuso de Brasília, `YYYY-MM-DD`). Lembretes agendados para datas futuras (ex: dias, semanas ou meses posteriores) NÃO DEVEM ser exibidos no briefing diário. Caso não haja lembretes para o dia, deve exibir mensagem indicando nenhuma tarefa para hoje.
- **P-0411 (Formatação Segura de Tags de Lembretes):** As categorias/tags associadas aos lembretes DEVEM ser formatadas visualmente como `#tag1 #tag2` ou `[#tag1 #tag2]`. É terminantemente proibido renderizar representações brutas de arrays ou strings como `#[['financas', 'claro']]`.

### Domínio: Animes (AniList Tracker)
- **P-0412 (Filtro de Episódios Apenas para Animes em Andamento):** Na mensagem matinal e nas consultas de grade de lançamentos de episódios (hoje e próximo episódio), o sistema DEVE considerar estritamente os animes com status `assistindo` (`watching`/`CURRENT`). Animes com status `planejo_assistir`, `concluido`, `pausado` ou `dropado` NÃO DEVEM ser exibidos como episódios a serem acompanhados no dia a dia.
- **P-0413 (Filtro de Temporadas e Continuações):** Consultas de novas temporadas, continuações, sequências ou estreias futuras DEVEM considerar exclusivamente os animes que o usuário já acompanhou ou finalizou, isto é, status `assistindo` ou `concluido`. É expressamente proibido sugerir continuações de animes com status `pausado` (*on hold*) ou `dropado` (*dropped*).
- **P-0414 (Lista de Desejos - O que Quero Assistir):** Quando o usuário perguntar o que tem para assistir ("animes que quero assistir", "o que tenho pendente para começar"), o sistema DEVE retornar exclusivamente animes com status `planejo_assistir` (*planning*) OU animes com status `assistindo` (*watching*) cujo progresso seja 0 episódios vistos (`ultimo_episodio_visto == 0`).

### Domínio: Clash of Clans
- **P-0415 (Tratamento de 0 Ataques Realizados no Raid Weekend):** Durante o Raid Weekend (estado `ongoing`), caso o jogador cadastrado não conste na lista `members` do endpoint da Capital do Clã da Supercell API, o sistema DEVE interpretar que o jogador ainda não realizou nenhum ataque na temporada atual, computando 5 ataques disponíveis e disparando o alerta de ataques pendentes.
- **P-0416 (Coexistência de Alertas de Guerra e Raid):** Os alertas de Guerra Regular (ou CWL) e Raid Weekend NÃO SÃO mutuamente exclusivos. Se ambos estiverem ativos com ataques pendentes, o bloco de Clash of Clans na mensagem de bom dia DEVE exibir ambos os tópicos de alerta de forma clara e independente.

### Domínio: Multi-Usuário & Scheduler
- **P-0417 (Disparo Agendado por Usuário e Horário Personalizado):** A rotina de envio matinal em background DEVE rodar em base minuto a minuto, iterando sobre todos os usuários ativos (`daniel`, `lari`, etc.) e disparando o resumo matinal no momento em que a hora/minuto corrente no fuso de Brasília coincidir com a preferência `horario` cadastrada para aquele usuário.
- **P-0418 (Isolamento Inviolável de Contexto por Usuário no Briefing):** A geração e montagem do Morning Briefing de cada usuário DEVE ser executada estritamente dentro do `UserContext` correspondente (`UserContext.set_user(target_user_id)`). Nenhuma informação de agenda, lembretes, saúde ou finanças de Daniel pode ser incluída na mensagem de Lari, e vice-versa. O envio deve ser direcionado para o número de WhatsApp cadastrado de cada usuário.
