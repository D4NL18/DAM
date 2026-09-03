# 📅 Funcionalidade: Google Calendar (Agendamento & Consulta Enriquecida)

## 1. Descrição Geral
Permite agendar novos compromissos e consultar a programação do dia ou da semana diretamente pelo WhatsApp, integrado à Google Calendar API via Service Account GCP, com suporte a horários, durações, localização e pauta detalhada.

---

## 2. Como Utilizar (Tutorial Passo a Passo)

### Agendando um Evento
Envie uma mensagem informal informando data, hora e opcionalmente local e pauta:
* *"Marque dentista amanhã às 14h na Av Paulista, levar exames"*
* *"Agende reunião com o time de engenharia na próxima segunda às 10h via Google Meet com duração de 45 minutos"*
* *"Marque almoço com o João na sexta às 12h30 no restaurante Fasano"*

### Consultando sua Agenda
* *"O que tenho marcado para hoje?"*
* *"Como está minha agenda amanhã?"*
* *"Quais são meus compromissos para os próximos 7 dias?"*

---

## 3. O que a Funcionalidade CONSEGUE Fazer
* Converter expressões temporais relativas (*"amanhã às 15h"*, *"próxima terça às 9h30"*) no formato exato ISO-8601 com timezone local.
* Preencher automaticamente os campos de `summary` (título), `start`, `end`, `location` (onde será) e `description` (pauta/notas).
* Retornar o link direto do evento no Google Calendar para o usuário clicar e visualizar.
* Listar os próximos eventos trazendo horários, títulos, locais e descrições cadastradas.

---

## 4. O que a Funcionalidade NÃO CONSEGUE Fazer
* **Convidar Automaticamente Participantes sem E-mail:** O bot não consegue adivinhar o e-mail de pessoas citadas a menos que o e-mail seja informado explicitamente.
* **Resolução de Conflitos Físicos:** O bot avisa sobre os horários, mas não bloqueia a criação se o usuário insistir em marcar dois eventos no mesmo horário.
* **Excluir Calendários Inteiros:** A tool tem escopo restrito a inserção e leitura de eventos no calendário principal configurado.
