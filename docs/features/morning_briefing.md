# Funcionalidade: Morning Briefing Matinal Proativo (08:00)

## 1. Visão Geral
O **Morning Briefing** é um serviço proativo de consolidação matinal que envia diariamente às 08:00 (horário de Brasília) uma mensagem executiva e formatada no WhatsApp do usuário autorizado com os 4 pilares do seu dia:

1. **Agenda do Dia:** Compromissos e reuniões extraídos do Google Calendar.
2. **Tarefas & Lembretes Pendentes:** Itens da coleção `notes_reminders` agendados para a data de hoje.
3. **Jogos da FURIA Esports no Dia:**
   - Se o jogo ocorreu entre 00:00 e 08:00: informa o resultado/placar final já consolidado.
   - Se o jogo está agendado para após as 08:00: informa apenas o horário de início e o adversário.
4. **Animes com Episódio Novo Hoje:** Animes da watchlist pessoal do usuário que lançam novos episódios nas próximas 24 horas.

## 2. Arquitetura e Idempotência
- **Agendador:** Rotina assíncrona diária (`_rotina_briefing_diario`) acoplada ao lifespan do FastAPI em `main.py`, com suporte a trigger manual via Cloud Scheduler ou endpoint protegido `POST /api/briefing/morning`.
- **Mecanismo Anti-duplicação (Idempotência):** Registro no Firestore na coleção `briefing_logs` com documento chaveado pela data (ex: `2026-09-03`). Garante que mesmo com reinícios do container Cloud Run, o usuário receba apenas 1 briefing por dia.
- **Endpoint de Preview:** `GET /api/briefing/preview` permite inspecionar o briefing do dia sem persistir envio ou disparar mensagem no WhatsApp.

## 3. Formatação WhatsApp
```
🌅 *BOM DIA! SEU BRIEFING MATINAL* 📅 03/09/2026
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 *COMPROMISSOS DO DIA*
• Reunião de Arquitetura (10:00)
• Alinhamento Semanal (15:30)

📝 *TAREFAS & LEMBRETES DE HOJE*
• ⏰ Enviar relatório de sprint (11:00)

⚡ *FURIA ESPORTS HOJE*
• 🎮 FURIA vs NAVI às 16:00

📺 *LANÇAMENTOS DE ANIMES HOJE*
• ⏰ *Mushoku Tensei III* — Ep. 11 às 11:30

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Tenha um excelente e produtivo dia! 🚀
```
