# Roadmap do Projeto: Assistente DAM (Inteligência Artificial)

## Visão Geral
Assistente pessoal via WhatsApp focado em ser uma central de vida automatizada baseada em IA, utilizando Microsserviços (FastAPI, Spring Boot, Angular) hospedados no GCP e Firebase.

## Fase 1: Fundação do Motor de IA e Mensageria
- **[ ] US-1.1:** Setup inicial do Firebase Firestore e criação da base do projeto FastAPI.
- **[ ] US-1.2:** Integração com a API do LLM (Gemini/OpenAI) e arquitetura de *Function Calling* base.
- **[ ] US-1.3:** Setup e Integração com o WhatsApp via Evolution API (ou similar) recebendo/enviando mensagens de texto e áudio.
- **[ ] US-1.4:** Deploy inicial do FastAPI no Google Cloud Run (Configuração CI/CD).

## Fase 2: Dashboard Web (Angular + Spring Boot)
- **[ ] US-2.1:** Setup da Core API em Spring Boot 3 (Java 17+) com documentação OpenAPI/Swagger.
- **[ ] US-2.2:** Setup do projeto Angular (Standalone Components, SCSS) e padronização do Design System.
- **[ ] US-2.3:** Integração da Core API com Firebase Admin SDK para acesso ao Firestore (Dados de Saúde e Finanças).
- **[ ] US-2.4:** Criação dos Endpoints RESTful no Spring Boot para leitura e agregação dos dados no Dashboard.
- **[ ] US-2.5:** Desenvolvimento dos componentes de UI (Gráficos/Tabelas) no Angular consumindo a Core API.
- **[ ] US-2.6:** Configuração de CI/CD para deploy da Core API no Cloud Run e do Frontend no Firebase Hosting.

## Fase 3: Pilares Base de Dados (Saúde e Financeiro)
- **[x] US-3.1 [PARALLEL]:** (Pilar 1) Criar endpoint `/api/health-webhook` no FastAPI, formatar dados do Health Auto Export e salvar no Firestore.
- **[x] US-3.2 [PARALLEL]:** (Pilar 1) Desenvolver a *tool* LLM para consultar dados de saúde via chat.
- **[x] US-3.3 [PARALLEL]:** (Pilar 4) Desenvolver o agente/tool de Gestão Financeira, para processar comprovantes/textos e gravar na coleção `finances`.
- **[x] US-3.4 [PARALLEL]:** (Pilar 5) Integração Google Calendar API (Agent de agendamentos).
- **[x] US-3.5:** Fix de Notificações do WhatsApp & Isolamento Estrito do Chat "Comigo Mesmo" (garantir que o bot não intercepte, marque como lido ou suprima notificações de outros chats/grupos no celular).
- **[x] US-3.6:** Suporte a Mensagens Multimodais (Processamento de Imagens e Áudios do WhatsApp via Gemini).
- **[x] US-3.7:** Enriquecimento do Google Calendar Tool (Suporte a Descrição e Localização na criação de eventos).
- **[x] US-3.8:** Integração do Dashboard Web com o Banco de Dados (Conexão ponta a ponta do Frontend Angular com dados reais do Firestore).

## Fase 4: Integrações Externas Avançadas
- **[x] US-4.1:** (Pilar 2) Integração Uconnect API para o veículo (Fiat Fastback) e ferramentas de controle (autonomia, travas).
- **[x] US-4.2:** (Pilar 3) Integração HLTV API/Scraper e tools de placar de CS2.

## Fase 5: Automação Residencial e Alertas
- **[x] US-5.1:** (Pilar 6) Configurar GCP Billing Budgets + Pub/Sub e webhook para alertas de custo.
- **[x] US-5.2:** (Pilar 7) Integração Webhooks para acionamento de rotinas Alexa.

## Fase 6: Segurança, Auditoria e Refinamento
- **[ ] US-6.1:** Auditoria de segurança em todos os endpoints e Firebase Rules.
- **[ ] US-6.2:** Refinamento de prompts, Auto-Healer e testes E2E do sistema integrado.

## Fase 7: Refatoração UI/UX (Design System Stitch -> SCSS)
- **[ ] US-7.1 [PARALLEL]:** Configurar Tokens de Design (Cores, Fontes Inter, Material Symbols) em SCSS Puro.
- **[ ] US-7.2 [PARALLEL]:** Implementar o novo Layout Geral (SideNavBar e Header).
- **[ ] US-7.3:** Implementar as páginas Bento Grid (Dashboard Financeiro, Saúde, Agenda).

## Fase 8: Mobilidade Urbana e Trânsito (Google Maps Directions API)
- **[ ] US-8.1:** Configuração da Google Maps Platform (Directions API) e credenciais de API Key no GCP/FastAPI.
- **[ ] US-8.2:** Desenvolvimento da Tool LLM de Rotas e Trânsito (`maps_tool.py`) para consultar tempo estimado, distância, rotas alternativas e condições de trânsito em tempo real.
- **[ ] US-8.3:** Integração no Agente WhatsApp para consultas em linguagem natural de trajetos, tempo de deslocamento e melhor rota.
- **[ ] US-8.4:** Cruzamento inteligente entre Google Calendar (eventos com localização) e Google Maps para avisos de horário de saída.

## Fase 9: Gestão de Conhecimento e Lembretes (Anotações e Alertas Estruturados)
- **[ ] US-9.1:** Modelagem no Firestore da coleção `notes_reminders` contendo título, data/hora, descrição, status e tags.
- **[ ] US-9.2:** Desenvolvimento da Tool LLM de Anotações e Lembretes (`notes_tool.py`) para criação, consulta, busca semântica e exclusão via linguagem natural.
- **[ ] US-9.3:** Mecanismo de disparo de lembretes ativos no WhatsApp no momento agendado (agendamento assíncrono / Cloud Tasks ou rotina periódica no FastAPI).

## Fase 10: Curador de Presentes e Datas Especiais (Memória Afetiva & Alertas Proativos)
- **[ ] US-10.1:** Modelagem no Firestore da coleção `gift_ideas` (pessoa, relação, ideia/desejo, data especial de referência, tags e anotação original).
- **[ ] US-10.2:** Desenvolvimento da Tool LLM `gift_curator_tool.py` para capturar e categorizar comentários casuais e desejos ao longo do ano ("Minha namorada comentou que gostou de um perfume da loja X").
- **[ ] US-10.3:** Sistema de alerta proativo com antecedência configurável (ex.: 2 a 4 semanas antes de aniversários, Dia dos Namorados, etc.), resgatando a anotação exata e sugerindo ações de compra via WhatsApp.

## Fase 11: Divisor Inteligente de Contas de Restaurante (Receipt OCR & Smart Split)
- **[ ] US-11.1:** Pipeline de OCR e extração estruturada de nota fiscal/comanda de restaurante via Gemini Vision (itens, preços unitários, quantidades, subtotal e taxa de serviço/10%).
- **[ ] US-11.2:** Desenvolvimento do motor de interpretação de rateio em linguagem natural ("Eu comi o hambúrguer, o João bebeu as cervejas e a Maria dividiu a pizza comigo").
- **[ ] US-11.3:** Algoritmo de cálculo de rateio matemático proporcional, incorporando os 10% da taxa de serviço de forma justa para cada participante.
- **[ ] US-11.4:** Formatação e envio do demonstrativo de fechamento no WhatsApp com valores individuais discriminados e inclusão automática da chave Pix do usuário para recebimento.

## Fase 12: Memória Espacial e Localizador de Objetos ("Onde Guardei Isso?")
- **[ ] US-12.1:** Modelagem no Firestore da coleção `item_locations` (item, categoria, local_armazenado, detalhes/referência e timestamp).
- **[ ] US-12.2:** Desenvolvimento da Tool LLM `item_finder_tool.py` para registrar localização de objetos a partir de mensagens cotidianas de texto ou áudio ("Guardei o passaporte na gaveta de cima do armário").
- **[ ] US-12.3:** Mecanismo de busca semântica e recuperação contextual para responder com precisão a perguntas como "Onde está meu passaporte?" ou "Cadê a chave reserva do carro?".
- **[ ] US-12.4:** Histórico de movimentações (atualizar o local atual do item mantendo o histórico de locais anteriores caso o usuário mude de lugar).

## Fase 13: Cofre Seguro de Senhas e Credenciais (Criptografia AES-256 & SecOps)
- **[ ] US-13.1:** Arquitetura de segurança do cofre com criptografia simétrica AES-256-GCM, gerenciamento seguro de chave mestra (GCP Secret Manager) e sanitização estrita de logs (impedir vazamento de senhas em `chat_logs` ou console).
- **[ ] US-13.2:** Modelagem no Firestore da coleção segura `vault_credentials` com payload criptografado (ciphertext, iv, tag, service_name, username/login).
- **[ ] US-13.3:** Desenvolvimento da Tool LLM `password_vault_tool.py` para cadastrar, consultar e atualizar senhas com autenticação/confirmação prévia no chat.
- **[ ] US-13.4:** Políticas de SecOps: gerador de senhas fortes embutido, máscara de exibição e proteção contra visualização não autorizada.

## Fase 14: Guia de Streaming Direto ("Onde Assistir?")
- **[ ] US-14.1:** Integração com APIs de catálogo audiovisual e provedores de streaming (TMDB API v3 / Watch Providers alimentado por JustWatch).
- **[ ] US-14.2:** Desenvolvimento da Tool LLM `streaming_tool.py` para busca de filmes/séries e identificação de plataformas disponíveis no Brasil (Netflix, Max, Prime Video, Disney+, Apple TV+, etc.), diferenciando assinatura, compra e aluguel.
- **[ ] US-14.3:** Registro no Function Calling do Gemini para perguntas naturais ("Onde passa o filme Interestelar?", "Em qual streaming tem a série Succession?").
- **[ ] US-14.4:** Mecanismo de cache leve no Firestore para títulos consultados recentemente, otimizando tempo de resposta e consumo de requisições.

## Fase 15: Calculadora Inteligente de Churrasco e Eventos
- **[ ] US-15.1:** Engenharia de regras de cálculo e consumo per capita para eventos (adultos que bebem, adultos que não bebem, crianças, duração do evento em horas).
- **[ ] US-15.2:** Desenvolvimento da Tool LLM `bbq_planner_tool.py` para cálculo volumétrico detalhado: carnes por tipo (bovina, suína, linguiça, frango em kg), carvão (kg), fardos/latas de cerveja, refrigerante, água e gelo (sacos).
- **[ ] US-15.3:** Geração de checklist de compras estruturado e pronto para cópia no WhatsApp a partir de comandos em linguagem natural ("Vou fazer um churrasco para 12 adultos, 8 bebem cerveja, e 4 crianças, das 14h às 20h").

## Fase 16: Tradutor e Guia Gastronômico de Cardápios ao Vivo (Vision OCR & Contexto Cultural)
- **[ ] US-16.1:** Pipeline de visão computacional com Gemini Vision para fotos de cardápios internacionais (inglês, espanhol, francês, italiano, alemão, japonês, etc.).
- **[ ] US-16.2:** Desenvolvimento do serviço de tradução contextual e explicação culinária (além da tradução literal, detalhar ingredientes, modo de preparo e analogias com a gastronomia brasileira).
- **[ ] US-16.3:** Tool LLM `menu_translator_tool.py` e formatação amigável no WhatsApp, incluindo alertas opcionais de alérgenos ou restrições alimentares configuradas pelo usuário.

## Fase 17: Conversor Universal Instantâneo (Medidas, Pesos e Temperaturas)
- **[ ] US-17.1:** Motor de cálculo determinístico e conversão matemática de alta precisão (livre de alucinações de LLM) para unidades imperiais e métricas.
- **[ ] US-17.2:** Suporte completo aos pares de conversão:
  - Distância/Comprimento: Milhas (mi) <-> Quilômetros (km), Pés (ft) <-> Centímetros/Metros (cm/m), Polegadas (in) <-> Centímetros (cm).
  - Temperatura: Fahrenheit (°F) <-> Celsius (°C) para clima e regulagem de fornos/fogões.
  - Massa/Peso: Libras (lb) <-> Quilogramas (kg), Onças (oz) <-> Gramas (g).
- **[ ] US-17.3:** Desenvolvimento da Tool LLM `unit_converter_tool.py` para respostas instantâneas no chat a perguntas cotidianas ("Quantos KM dá 35 milhas?", "180 Fahrenheit é quanto no forno daqui?", "150 libras em kg").

## Fase 18: "Splitwise" de Bolso para Viagens e Grupos (Group Ledger & Debt Minimizer)
- **[ ] US-18.1:** Modelagem no Firestore das coleções `trip_groups` (grupos de viagem, participantes, status ativo/encerrado) e `trip_expenses` (despesas lançadas, pagador, valor, participantes da divisão, comprovante).
- **[ ] US-18.2:** Tool LLM `trip_ledger_tool.py` para gerenciamento de viagens e lançamento de despesas incrementais por texto, áudio ou foto de cupom fiscal ("Almoço R$ 200, eu paguei, divide por 4", "Pedro pagou R$ 120 de gasolina, divide por todos").
- **[ ] US-18.3:** Algoritmo de minimização e compensação de dívidas (calcula o saldo líquido de cada pessoa e reduz ao menor número de transferências Pix necessárias).
- **[ ] US-18.4:** Geração de fechamento consolidado da viagem no WhatsApp com extrato detalhado e lista de liquidação direta ("Fulano faz Pix de R$ X para Ciclano").

## Fase 19: Calculadora Inteligente de Banco de Horas Semanal (Time Tracker & Work Hours Balance)
- **[ ] US-19.1:** Motor Determinístico de Parser e Cálculo de Horas (Interpretação e normalização de horários flexíveis como "9h", "7h30", "10h", "8.5h", conversão precisa em minutos e cálculo de saldo positivo/negativo com base na jornada alvo padrão de 8h/dia ou 40h/semana sem alucinação matemática).
- **[ ] US-19.2:** Tool LLM `work_hours_tool.py` e Resumo no WhatsApp (Cálculo pontual e instantâneo via mensagem única enviada pelo usuário no chat, discriminando horas diárias, total acumulado da semana e balanço final: horas a receber ou saldo devedor).
- **[ ] US-19.3:** Lançamentos Incrementais Diários e Histórico no Firestore (Permitir registrar horas dia a dia ao longo da semana na coleção `work_hours`, possibilitando fechamentos consolidados periódicos ex.: "Quanto fechei essa semana?" ou "Como está meu banco de horas este mês?").
- **[ ] US-19.4:** Configuração Customizada de Jornada de Trabalho (Permitir ao usuário personalizar suas metas de jornada contratual, ex.: 40h ou 44h semanais, 6h diárias ou jornadas flexíveis).
