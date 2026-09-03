# Fase 14: Guia de Streaming Direto ("Onde Assistir?")

Este documento centraliza as especificações, regras de negócio e planejamento de execução para a Fase 14, responsável por consultar onde filmes e séries estão disponíveis para streaming no Brasil, poupando buscas manuais na web.

---

## 1. Especificação (Analista)

### Regras de Negócio e Escopo

- **P-1401 (Consulta em Linguagem Natural):** O usuário pode perguntar de maneira direta no WhatsApp onde assistir a determinado filme, série, anime ou documentário (ex.: *"Onde passa o filme Interestelar?"*, *"Em qual streaming encontro The Office?"*, *"Tem Oppenheimer no Prime Video?"*).
- **P-1402 (Precisão Regional - Brasil / BR):** O catálogo deve ser consultado especificamente para o mercado brasileiro (`region=BR`), evitando informar plataformas ou planos indisponíveis no Brasil.
- **P-1403 (Discriminação de Modalidades de Acesso):**
  - **Incluso na Assinatura (Flatrate):** Destacar com prioridade onde o título está disponível por catálogo padrão (ex: Netflix, Max, Disney+, Prime Video, Apple TV+, Globoplay).
  - **Aluguel ou Compra (Rent/Buy):** Se não estiver em nenhuma assinatura, informar as plataformas de aluguel/compra digital (ex: Google Play Filmes, Apple TV, Amazon Store) e seus respectivos formatos.
  - **Gratuito com Anúncios (Free/Ad-supported):** Identificar plataformas abertas (ex: Pluto TV, Mercado Play).
- **P-1404 (Formatação Resumida e Elegante):**
  - A resposta deve incluir o título nacional, título original, ano de lançamento, nota média (se disponível) e a lista clara das plataformas disponíveis.

---

## 2. Planejamento das Tarefas (Arquitetura)

### Tarefas da Fase 14

#### [ ] Task 14.1: Integração com TMDB / JustWatch API
- [ ] **Etapa 14.1.1:** Obter e configurar a API Key do The Movie Database (TMDB) em `config/settings.py` (`TMDB_API_KEY`).
- [ ] **Etapa 14.1.2:** Implementar cliente HTTP para busca de títulos (`/search/multi` ou `/search/movie` e `/search/tv`).
- [ ] **Etapa 14.1.3:** Implementar chamada ao endpoint de provedores (`/movie/{id}/watch/providers` e `/tv/{id}/watch/providers`) filtrando para o país `BR`.

#### [ ] Task 14.2: Tool LLM `streaming_tool.py`
- [ ] **Etapa 14.2.1:** Criar `backend_ia/services/tools/streaming_tool.py` contendo a função:
  - `consultar_onde_assistir(titulo: str, tipo: Optional[str] = None)`
- [ ] **Etapa 14.2.2:** Formatar o resultado priorizando assinaturas antes de locação/compra.
- [ ] **Etapa 14.2.3:** Registrar o schema no `backend_ia/services/ai_service.py` para detecção autônoma via Function Calling do Gemini.

#### [ ] Task 14.3: Cache de Consultas
- [ ] **Etapa 14.3.1:** Implementar cache com TTL (Time-to-Live) de 24 horas no Firestore ou em memória para evitar requisições redundantes de títulos idênticos.

---

## 3. Critérios de Aceite e Validação (QA)
- [ ] **Cenário 1 (Filme em Assinatura):** O usuário pergunta "Onde passa o filme Interestelar?". O bot responde informando que está disponível na Max e no Prime Video (ou provedores vigentes no Brasil).
- [ ] **Cenário 2 (Título Exclusivo de Compra/Aluguel):** O usuário pergunta sobre um filme recém-saído do cinema. O bot informa que atualmente não está em catálogo de assinatura, mas pode ser alugado na Apple TV e Google Play Filmes.
- [ ] **Cenário 3 (Série de TV):** O usuário pergunta "Onde assistir Breaking Bad?". O bot identifica como série e retorna que está disponível na Netflix.
- [ ] **Cenário 4 (Título Não Encontrado):** O usuário busca um título inexistente ou com grafia ambígua. O bot solicita confirmação educadamente sem travar.
