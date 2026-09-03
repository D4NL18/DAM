# Estado Atual da Orquestração (STATE.md)

## Status Global
- **Arquitetura:** Microsserviços e Serverless (FastAPI + Evolution API + Angular 17 + Firestore)
- **Estruturação:** **100% Organizado por Domínios Funcionais** (sem divisão por fases)
- **Segurança & Defesa:** Guardrails contra Prompt Injection ativos, Rate Limiter Sliding Window, Headers HTTP defensivos, Mascaramento de dados sensíveis (LGPD) e autenticação Timing-Safe.
- **Suíte de Testes:** 214 testes unitários e de integração aprovados com 100% de taxa de sucesso.

---

## Domínios Funcionais do Sistema
1. **Gestão Pessoal & Rotina:** Agenda (Calendar), Lembretes/Notas, Memória Espacial, Morning Briefing 08h.
2. **Finanças & Gastos:** Classificação Multicartão, Divisão de Contas por Nome, Splitwise de Viagens, GCP Billing.
3. **Saúde & Bem-Estar:** Sono, Treinos, Webhook Apple Health.
4. **Entretenimento & Lazer:** Anime Tracker & AniList Bi-direcional, Streaming TMDB, FURIA CS2, Calculadora de Churrasco, Curador de Presentes.
5. **Utilitários & Segurança:** Cofre Criptografado AES-256, Tradutor de Cardápios, Conversor Universal, Banco de Horas Semanal, Trânsito Google Maps, Alexa Voice Monkey, Gestão Veicular.
6. **Plataforma & Core:** Motor IA Multimodal (Gemini Flash), GuardrailsService, RateLimiterMiddleware, SecurityHeadersMiddleware, Dashboard Web Angular.

---

## Últimas Ações Realizadas
- Implementação de `GuardrailsService` para interceptação ativa de ataques de Prompt Injection e jailbreaks.
- Modularização das instruções de sistema em `services/prompts/` com `PromptComposer`.
- Implementação de `RateLimiterMiddleware` e `SecurityHeadersMiddleware`.
- Mascaramento de números de telefone e JIDs nos logs (`mask_phone`).
- Erradicação de fallbacks de segredos em `settings.py`.
- Renomeação de 100% dos testes e arquivos de documentação para nomes estritamente funcionais.
- Elaboração completa da documentação técnica:
  - `docs/architecture/system_architecture.md`
  - `docs/architecture/database_architecture.md`
  - `docs/architecture/infrastructure_architecture.md`
  - `docs/architecture/security_architecture.md`
  - `docs/api-contracts/api_contracts.md`
  - `docs/business-rules/business_rules.md`
  - `docs/features/anime_tracker.md`
  - `docs/features/morning_briefing.md`
