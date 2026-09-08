# Fase 8: Mobilidade Urbana e Trânsito (Google Maps Directions API)

Este documento centraliza as especificações, regras de negócio e o planejamento de execução para a Fase 8, dedicada à integração com a Google Maps Platform (Directions API).

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-801 (Consulta de Rotas e Trânsito em Tempo Real):** O assistente deve ser capaz de receber solicitações de deslocamento (ex.: "quanto tempo até o trabalho?", "qual a melhor rota para o aeroporto agora?", "como está o trânsito na Marginal?") e consultar a Google Maps Directions API considerando o trânsito atual (`departure_time=now`, `traffic_model=best_guess`).
- **P-802 (Resumo Inteligente e Legível):** A resposta no WhatsApp deve ser concisa e amigável, informando tempo estimado com trânsito, distância total em km, principal via/trajeto recomendado e alertas de lentidão ou incidentes caso existam.
- **P-803 (Locais Frequentes / Favoritos):** O bot deve reconhecer apelidos de destinos comuns do usuário (ex.: "Casa", "Trabalho", "Academia"), cujas coordenadas/endereços podem ser configurados nas variáveis de ambiente ou preferências de usuário no Firestore.
- **P-804 (Sinergia com Google Calendar):** Quando o usuário perguntar sobre a próxima reunião ou compromisso com localização preenchida na agenda, o bot deve oferecer a opção de calcular o tempo de trajeto e sugerir o horário ideal de saída.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 8

#### [ ] Task 8.1: Setup da Google Maps Platform e Credenciais
- [ ] **Etapa 8.1.1:** Habilitar a Directions API no console do Google Cloud Platform (GCP).
- [ ] **Etapa 8.1.2:** Configurar variável de ambiente `GOOGLE_MAPS_API_KEY` com restrições adequadas de segurança (API restrictions).
- [ ] **Etapa 8.1.3:** Adicionar dependência oficial ou cliente HTTP (`googlemaps` ou chamadas `httpx`/`requests`) no `requirements.txt`.

#### [ ] Task 8.2: Desenvolvimento da Tool LLM de Trânsito e Rotas
- [ ] **Etapa 8.2.1:** Criar `backend_ia/services/tools/maps_tool.py`.
- [ ] **Etapa 8.2.2:** Implementar a função `consultar_rota(origem: str, destino: str, modo: str = 'driving')` que consulta a Directions API com dados de trânsito em tempo real.
- [ ] **Etapa 8.2.3:** Formatar o resultado em uma resposta amigável (duração normal vs duração com trânsito, distância, principais vias).
- [ ] **Etapa 8.2.4:** Suporte a resolução de endereços favoritos pré-configurados (ex.: Casa, Trabalho).

#### [ ] Task 8.3: Registro no Function Calling e Agente WhatsApp
- [ ] **Etapa 8.3.1:** Declarar os schemas da tool no Gemini (`backend_ia/services/ai_service.py`).
- [ ] **Etapa 8.3.2:** Habilitar o LLM a acionar a tool de rotas em perguntas naturais de mobilidade.
- [ ] **Etapa 8.3.3:** Testar fluxos de conversação no chat do WhatsApp.

#### [ ] Task 8.4: Integração com Google Calendar (Horário de Saída)
- [ ] **Etapa 8.4.1:** Criar lógica para cruzar eventos futuros do Google Calendar com campo `location` preenchido e a tool de rotas.
- [ ] **Etapa 8.4.2:** Permitir que o usuário pergunte: "Que horas devo sair para meu próximo compromisso?".

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Consulta de Rota Básica):** Usuário pergunta "Quanto tempo levo da Av Paulista até o Aeroporto de Guarulhos de carro?". O bot responde com tempo estimado considerando o trânsito atual e a distância aproximada.
- [ ] **Cenário 2 (Alerta de Lentidão):** Se houver trecho congestionado, o bot destaca que a rota está com tráfego intenso e indica a via alternativa sugerida pelo Maps.
- [ ] **Cenário 3 (Endereço Favorito):** Usuário pergunta "Como está o trânsito até o trabalho?". O bot substitui "trabalho" pelo endereço configurado e retorna a rota a partir do ponto de partida padrão ou informado.
- [ ] **Cenário 4 (Alerta de Saída para Compromisso):** O bot identifica que o próximo evento da agenda começa às 15h em determinado endereço e avisa que o tempo de deslocamento atual é de 45 minutos, recomendando sair por volta de 14h10.
