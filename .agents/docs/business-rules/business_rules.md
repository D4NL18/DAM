# Catálogo Unificado de Regras de Negócio (Business Rules)

Este documento consolida as regras de negócio do DAM Assistant, indexadas e agrupadas estritamente por seus **6 Domínios Funcionais**.

---

## Domínio 1: Gestão Pessoal & Rotina

* **P-0101 (Google Calendar):** Consultas de agenda padrão consideram as próximas 24 horas (`dias=1`) a partir do instante atual.
* **P-0102 (Fuso Horário Padrão):** Todos os eventos e compromissos devem ser calculados e apresentados no fuso oficial de Brasília (`America/Sao_Paulo` / UTC-3).
* **P-0103 (Lembretes Pendentes):** Lembretes criados recebem status inicial `pendente` e só passam a `concluido` mediante comando explícito do usuário.
* **P-0104 (Memória Espacial - Onde Guardei):** Ao registrar a localização de um objeto já existente, a localização anterior não é descartada, sendo automaticamente arquivada no histórico de movimentações (`historico`).
* **P-0105 (Morning Briefing - Horário e Disparo):** O resumo matinal deve ser montado e despachado proativamente todos os dias às 08:00 no fuso de Brasília.
* **P-0106 (Morning Briefing - Regra Temporal da FURIA):** Caso a FURIA tenha jogado entre 00:00 e 08:00, o briefing deve exibir o resultado/placar final; se a partida estiver agendada para após as 08:00, deve informar unicamente o horário de início e o adversário.
* **P-0107 (Morning Briefing - Idempotência Estrita):** O sistema deve registrar a chave da data (`YYYY-MM-DD`) em `briefing_logs`. É proibido disparar mais de um briefing para o mesmo dia, mesmo que o container seja reiniciado.
* **P-0108 (Exclusão Efetiva de Eventos Google Calendar):** A exclusão de compromissos no Google Calendar deve ser executada chamando `service.events().delete()`. A busca do evento pelo título/termo deve analisar o resumo do evento na data de referência (ou próximos 30 dias se omitido). Caso haja mais de um evento com o mesmo nome na data, o bot deve solicitar desambiguação ao usuário ao invés de deletar às cegas.
* **P-0109 (Edição In-Place de Eventos Google Calendar):** A edição de compromissos (remarcação de horário, alteração de título, local ou descrição) DEVE ser efetuada via `service.events().patch()`, mantendo o mesmo `eventId` no Google Calendar. É terminantemente proibido criar um novo evento via `agendar_evento` quando o objetivo for editar ou remarcar.
* **P-0110 (Governança e Permissões de Calendário em Edição/Exclusão):** A Lari só possui permissão para editar e excluir eventos da sua própria agenda. Tentativas de alterar a agenda do Daniel devem ser bloqueadas com mensagem de segurança. Daniel pode gerenciar sua própria agenda e gerenciar eventos na agenda da Lari mediante especificação explícita (`usuario='lari'`).

---

## Domínio 2: Finanças & Gastos

* **P-0201 (Taxonomia Estrita de Cartões):** O sistema suporta exclusivamente 3 métodos de pagamento:
  1. *Cartão de Crédito Pessoal*
  2. *Cartão de Crédito Secundário*
  3. *Cartão de Débito* (onde pagamentos via Pix são compulsoriamente classificados).
* **P-0202 (Confirmação Obrigatória de Cartão):** Se o usuário informar um gasto sem especificar o cartão (e a despesa não for Pix), o assistente é terminantemente proibido de registrar a despesa de imediato. Deve primeiro perguntar educadamente: *"Foi no seu cartão de crédito pessoal, no secundário ou no débito?"*.
* **P-0203 (Classificação Automática de Pix):** Qualquer transação mencionada como "Pix" deve ser automaticamente atribuída ao método *"Cartão de Débito"*, sem necessidade de confirmação prévia de método.
* **P-0204 (Rateio por Nomes de Pessoas):** Na divisão de contas de restaurante e grupos de viagem, o demonstrativo financeiro e a partição dos valores DEVEM ser agrupados estritamente pelo nome de cada participante (ex: *Você, João, Maria*). É proibido agrupar contas por chaves Pix.
* **P-0205 (Ajuste de Centavos no Rateio):** O cálculo proporcional da taxa de serviço (ex: 10%) deve somar exatamente o total final da conta, ajustando os centavos residuais sem arredondamentos que provoquem déficits ou sobras.
* **P-0206 (Splitwise de Viagens - Minimização de Dívidas):** O cálculo de fechamento de viagens deve aplicar o algoritmo de liquidação líquida (*Debt Minimization*), gerando o menor número possível de transferências entre os participantes.

---

## Domínio 3: Saúde & Bem-Estar

* **P-0301 (Registro de Sono):** Registros de sono devem aceitar quantidade de horas (decimais ou inteiros) e qualificador de qualidade (*ótima, boa, regular, ruim*).
* **P-0302 (Controle de Treinos):** Deve registrar modalidade (musculação, corrida, natação, etc.), duração em minutos e intensidade.
* **P-0303 (Consolidação Semanal):** O resumo de saúde calcula a média de horas dormidas nos últimos 7 dias e o número de treinos executados na semana.

---

## Domínio 4: Entretenimento & Lazer

* **P-0401 (AniList Bi-direcional):** Todas as alterações de status de animes (adicionar, avançar episódio, concluir) devem ser espelhadas em tempo real na conta oficial do AniList (`Tonho123`) via mutação GraphQL `SaveMediaListEntry`.
* **P-0402 (Avanço Incremental de Episódios):** Quando o usuário diz *"vi mais um ep"* ou *"assisti outro episódio"* sem especificar número, o assistente deve avançar exatamente `+1` episódio a partir do último progresso registrado.
* **P-0403 (Conclusão de Anime):** Ao marcar como concluído, o progresso deve ser ajustado para o total de episódios da temporada, o status no AniList alterado para `COMPLETED` e a nota informada pelo usuário (0 a 10) deve ser registrada.
* **P-0404 (Próximos Lançamentos em Brasília):** Datas de episódios futuros retornados pela API do AniList devem ser convertidas e formatadas com a contagem de tempo restante em dias/horas/minutos até a exibição.
* **P-0405 (Calculadora de Churrasco):** O cálculo de insumos deve aplicar as métricas consagradas: ~400g de carne por adulto (4h), 1.5L a 2L de cerveja por adulto que bebe, 1L de não-alcoólicos por pessoa, 1kg de carvão por kg de carne e 1 saco de gelo para cada 3 a 4 pessoas.

---

## Domínio 5: Utilitários & Segurança

* **P-0501 (Cofre Criptografado AES-256):** Senhas devem ser salvas criptografadas com chave mestre derivada via Fernet/AES. Nenhuma senha em texto puro pode ser persistida no banco de dados.
* **P-0502 (Mascaramento Padrão de Senhas):** Ao consultar credenciais do cofre, o assistente deve exibir a senha mascarada (ex: `Abc****z9`). Somente quando o usuário solicitar expressamente (`revelar_senha=True`) o segredo é entregue decodificado.
* **P-0503 (Cálculo Determinístico de Banco de Horas):** Registros de horas de trabalho e conversões de unidades DEVEM ser executados por funções matemáticas e determinísticas em Python, nunca delegados a estimativas ou alucinações do modelo generativo.
* **P-0504 (Rotas e Trânsito Dinâmico):** Quando o usuário mencionar "casa", o assistente utiliza o endereço residencial configurado; para qualquer outro destino, realiza geocodificação direta via Google Maps Directions API.
* **P-0505 (Gerenciamento Dinâmico de Endereços - US-08):** O usuário pode cadastrar, listar e excluir endereços com apelidos amigáveis ("casa", "trabalho", "academia", "pais"). Os endereços são salvos no Firestore (`user_addresses`) com coordenadas lat/long obtidas via Google Geocoding. Apelidos salvos têm precedência sobre os fallbacks estáticos em qualquer consulta de rotas ou mobilidade.

---

## Domínio 6: Plataforma & Core

* **P-0601 (Isolamento Inviolável de Usuário):** Apenas mensagens originadas do número pessoal autorizado (`ALLOWED_PHONE_NUMBER`) são processadas. Qualquer mensagem externa é sumariamente descartada sem emitir resposta e sem gastar tokens.
* **P-0602 (Timing-Safe Authentication):** Validações de tokens de webhook e endpoints protegidos devem utilizar `hmac.compare_digest` para neutralizar ataques de temporização.
* **P-0603 (Bloqueio Ativo de Prompt Injection):** Qualquer entrada de usuário contendo padrões de jailbreak, desativação de regras éticas ou tentativas de extração do prompt do sistema deve ser interceptada pelo `GuardrailsService` com resposta defensiva padrão.
* **P-0604 (Mascara Obrigatória em Logs):** É estritamente proibido imprimir em logs ou saídas padrão números de telefone, JIDs completos, tokens, senhas ou CPFs desmascarados.
* **P-0605 (Text-to-Speech & Respostas em Áudio PTT - PC-09):** Quando o usuário enviar um áudio ou solicitar explicitamente resposta por voz, o DAM sintetiza a resposta de texto usando serviço TTS, aplicando sanitização fonética (remoção de asteriscos, markdown, urls e excesso de emojis) e enviando como nota de voz gravada (`sendWhatsAppAudio` / PTT). O motor possui cache local para respostas idênticas frequentes e fallback automático para mensagem de texto caso a síntese falhe.

