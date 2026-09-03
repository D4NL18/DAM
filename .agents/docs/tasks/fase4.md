# Fase 4: Integrações Externas Avançadas (Veículo e Esports)

## 1. Escopo das Tarefas

#### [x] Task 4.1: Integração Uconnect API (Fiat Fastback)
- [x] **Etapa 4.1.1:** Criação da tool `consultar_status_veiculo` em `services/tools/vehicle_tool.py` retornando telemetria em tempo real (combustível, autonomia estimada, odômetro, bateria, pneus e travas).
- [x] **Etapa 4.1.2:** Criação da tool de comando seguro `acionar_travas_veiculo(acao: str)` para trancar e destrancar remotamente as portas.
- [x] **Etapa 4.1.3:** Registro no `AVAILABLE_TOOLS` do `ai_service.py` e mapeamento de intenção em linguagem natural.

#### [x] Task 4.2: Integração HLTV Scraper / API de Counter-Strike 2
- [x] **Etapa 4.2.1:** Criação da tool `consultar_jogos_cs2` em `services/tools/esports_tool.py` com suporte a filtro por time (FURIA, MIBR, Imperial, paiN) ou visão geral de torneios.
- [x] **Etapa 4.2.2:** Registro no `AVAILABLE_TOOLS` do `ai_service.py`.

## 2. Critérios de Aceite e Validação (QA)
- [x] **Cenário 1 (Veículo Status):** O usuário pergunta *"Quanto tem de gasolina no Fastback?"* ou *"Como está o carro?"*. O assistente consulta `vehicle_tool` e responde autonomia, porcentagem de tanque e estado das travas.
- [x] **Cenário 2 (Veículo Travas):** O usuário pede *"Trave as portas do carro"*. O bot envia o comando com segurança e confirma a ação. Comandos inválidos são rejeitados graciosamente.
- [x] **Cenário 3 (CS2 HLTV):** O usuário pergunta *"Quando a FURIA joga de novo?"*. O bot responde o próximo confronto, horário e campeonato.
