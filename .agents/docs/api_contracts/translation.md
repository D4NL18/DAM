# Contrato de API: Tradutor Universal Multimodal (US-10)

## 1. Visão Geral
Define as interfaces RESTful e ferramentas de Function Calling (Gemini) para o serviço de tradução universal multimodal de textos, imagens e áudios, utilizando a Google Cloud Translation API v2 de forma gratuita (limite mensal de 500k caracteres) com resposta final sempre em formato textual.

---

## 2. Endpoints REST (FastAPI)

### 2.1. `POST /api/translate`
**Objetivo:** Traduz um texto de qualquer idioma para qualquer idioma com detecção automática opcional de origem.

**Requisição (Request):**
- **Autenticação:** Opcional para rotas internas / Bearer Token se configurado
- **Headers:** `Content-Type: application/json`
- **Payload/Body:**
```json
{
  "text": "Hello world, how are you today?",
  "target_language": "pt",
  "source_language": "en"
}
```
*(Nota: `source_language` é opcional. Se omitido ou vazio, o sistema detecta automaticamente).*

**Resposta de Sucesso (200 OK):**
```json
{
  "status": "success",
  "original_text": "Hello world, how are you today?",
  "translated_text": "Olá mundo, como você está hoje?",
  "source_language": "en",
  "target_language": "pt",
  "characters_count": 31,
  "provider": "google_cloud_translation_v2"
}
```

**Respostas de Erro Mapeadas:**
- **400 Bad Request:** Texto vazio ou código de idioma inválido.
- **429 Too Many Requests:** Limite de cota mensal atingido ou rate limit excedido.
- **500 Internal Server Error:** Falha de comunicação e fallback indisponível.

---

### 2.2. `GET /api/translate/usage`
**Objetivo:** Retorna a telemetria FinOps do consumo de caracteres no mês corrente para garantir a permanência no Free Tier (500k chars/mês).

**Requisição (Request):**
- **Headers:** `Content-Type: application/json`
- **Query Params:** N/A

**Resposta de Sucesso (200 OK):**
```json
{
  "month": "2026-09",
  "characters_used": 12450,
  "monthly_limit": 500000,
  "percentage_used": 2.49,
  "free_tier_active": true
}
```

---

## 3. Function Calling Tool (Gemini): `traduzir_conteudo`

**Nome:** `traduzir_conteudo`  
**Descrição:** Traduz qualquer texto, conteúdo transcrito de áudio ou texto extraído de imagem de qualquer idioma para qualquer idioma especificado, utilizando o motor Google Cloud Translation. Sempre retorna a tradução em texto.

**Parâmetros de Entrada:**
- `texto` (string, obrigatório): O conteúdo textual a ser traduzido (texto fornecido, texto extraído de imagem por OCR, ou transcrição de áudio).
- `idioma_destino` (string, opcional, default: `"pt"`): O código ISO ou nome do idioma para o qual o texto deve ser traduzido (ex: `'pt'`, `'en'`, `'es'`, `'fr'`, `'de'`, `'ja'`, etc.).
- `idioma_origem` (string, opcional, default: `None`): O código ISO do idioma de origem. Se omitido, a detecção é 100% automática.

**Retorno:**
Texto contendo o idioma identificado e a tradução formatada de forma clara e pronta para leitura no WhatsApp.

---

## 4. Tipagem (Typescript / Dashboard)
```typescript
export interface TranslationRequest {
  text: string;
  target_language?: string;
  source_language?: string;
}

export interface TranslationResponse {
  status: string;
  original_text: string;
  translated_text: string;
  source_language: string;
  target_language: string;
  characters_count: number;
  provider: string;
}

export interface TranslationUsageResponse {
  month: string;
  characters_used: number;
  monthly_limit: number;
  percentage_used: number;
  free_tier_active: boolean;
}
```
