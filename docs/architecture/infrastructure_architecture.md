# Arquitetura de Infraestrutura & Nuvem (GCP & FinOps)

## 1. Topologia da Infraestrutura
O DAM foi concebido seguindo os princípios de **Serverless First** e **FinOps Rigoroso**, operando dentro dos limites da cota gratuita (Always Free Tier) do Google Cloud Platform (GCP).

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      GOOGLE CLOUD PLATFORM (GCP)                       │
 │                                                                        │
 │   ┌───────────────────────┐             ┌─────────────────────────┐    │
 │   │  Cloud Run (Core IA)  │             │   Compute Engine (e2)   │    │
 │   │   - FastAPI           │             │    - Evolution API      │    │
 │   │   - Gemini Flash      │             │    - PostgreSQL 15      │    │
 │   │   - RateLimiter       │             └────────────▲────────────┘    │
 │   └───────────▲───────────┘                          │                 │
 │               │                                      │                 │
 │               │ Webhook HTTPS                        │ WhatsApp Web    │
 │               │                                      ▼                 │
 │   ┌───────────▼───────────┐             ┌─────────────────────────┐    │
 │   │  Cloud Firestore      │             │   WhatsApp Servers      │    │
 │   │   - NoSQL Nativo      │             └─────────────────────────┘    │
 │   └───────────────────────┘                                            │
 │                                                                        │
 │   ┌───────────────────────┐             ┌─────────────────────────┐    │
 │   │   Firebase Hosting    │             │   Cloud Scheduler       │    │
 │   │   - Angular Dashboard │             │   - Morning Briefing 8h │    │
 │   └───────────────────────┘             └─────────────────────────┘    │
 └────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Componentes de Nuvem

### 2.1. Cloud Run (`backend_ia`)
- **Container Docker:** Imagem leve baseada em `python:3.12-slim`.
- **Dimensionamento Automático:** Escala de 0 a 1 instância sob demanda. Quando inativo, consome zero CPU/Memória.
- **Porta de Execução:** 8080.
- **HTTPS Nativo:** Certificado SSL/TLS gerenciado automaticamente pelo Google Cloud, prevenindo problemas de *mixed content* na comunicação com o frontend.

### 2.2. Compute Engine VM (`e2-micro` / Evolution API)
- Instância `e2-micro` (gratuita no Always Free tier na região `us-central1` ou `us-east1`).
- Orquestrada via `docker-compose.yml`:
  - `postgres:15-alpine`: Limitado a 64MB de shared buffers e 50 conexões máximas.
  - `evolution_api`: Servidor do WhatsApp com log em nível `ERROR` e cache em disco para preservação de memória RAM.

### 2.3. Firebase Hosting (`frontend_dashboard`)
- Hospedagem estática global via CDN do Google com domínios SSL:
  - `https://bot-dam-72ef2.web.app`
  - `https://bot-dam-72ef2.firebaseapp.com`
- Integração contínua (CI/CD) via GitHub Actions que compila o Angular (`npm run build`) e efetua o deploy automático no merge na branch `main`.

### 2.4. Cloud Scheduler
- Trigger cronológico (`0 8 * * *` em fuso horário `America/Sao_Paulo`) que dispara requisição HTTP autenticada `POST /api/briefing/morning` para o Cloud Run caso o container esteja suspenso em repouso.

---

## 3. Gestão de Segredos & Variáveis de Ambiente
- Variáveis locais mantidas no arquivo `.env` (ignorado no Git).
- Em ambiente de produção no Cloud Run, os segredos são injetados diretamente nas configurações do serviço ou integrados ao **Google Cloud Secret Manager**:
  - `GEMINI_API_KEY`
  - `WEBHOOK_TOKEN`
  - `ALLOWED_PHONE_NUMBER`
  - `VOICE_MONKEY_API_TOKEN`
  - `TMDB_API_KEY`
  - `GOOGLE_MAPS_API_KEY`
  - `ANILIST_ACCESS_TOKEN`
  - `VAULT_SECRET_KEY`

---

## 4. Práticas de FinOps (Otimização de Custos)
1. **Gemini 1.5/3.6 Flash:** Modelo ultra-eficiente de alta capacidade de raciocínio e custo por token ordens de magnitude menor que modelos Ultra/Pro.
2. **Compressão de Janela de Contexto:** Apenas as 10 mensagens mais recentes do usuário são enviadas no histórico de chat, prevenindo crescimento descontrolado de tokens.
3. **Escalonamento a Zero:** Containers suspendem execução após períodos ociosos, gerando faturas próximas a R$ 0,00 mensais no Cloud Run.
