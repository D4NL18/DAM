# Contrato de API / Function Calling: Repositório de Vídeos Salvos (EL-07)

## 1. Visão Geral
Este contrato define as interfaces de Function Calling do LLM (Gemini) e as assinaturas dos serviços do Backend IA (`backend_ia`) para gerenciar vídeos salvos das redes sociais (TikTok, Instagram, YouTube) no Firestore.

---

## 2. Ferramentas (Tools / Function Calling)

### 2.1. `salvar_video`
**Objetivo:** Salvar um vídeo de rede social para assistir mais tarde ou guardar como referência.

**Parâmetros de Entrada:**
- `url` (string, obrigatório): URL do vídeo (ex: `https://vm.tiktok.com/ZM...`, `https://www.instagram.com/reel/C...`, `https://youtu.be/...`).
- `titulo` (string, opcional): Título breve para identificar o vídeo. Se não informado, o sistema infere a partir do assunto ou da plataforma.
- `descricao` (string, opcional): Resumo sobre o que é o vídeo, assunto, dicas ou receita que ele ensina.
- `categoria` (string, opcional): Categoria do vídeo (ex: "Receitas", "Treino", "Humor", "Tecnologia").
- `tags` (string, opcional): Palavras-chave separadas por vírgula (ex: "strogonoff, culinaria, almoco").

**Retorno:**
String formatada para o WhatsApp confirmando o salvamento com plataforma detectada, título e ID gerado.

---

### 2.2. `consultar_videos_salvos`
**Objetivo:** Buscar vídeos salvos por palavras-chave (título, sobre o que era o vídeo, tags, criador), com filtros opcionais de plataforma e status.

**Parâmetros de Entrada:**
- `termo_busca` (string, opcional): Termo de busca livre para encontrar o vídeo (ex: "strogonoff", "mobilidade", "python"). Se vazio, lista os mais recentes.
- `plataforma` (string, opcional): Filtrar por plataforma: `"TikTok"`, `"Instagram"`, `"YouTube"` ou `""` para todas.
- `status` (string, opcional): Filtrar por status: `"pendente"`, `"assistido"` ou `"todos"`. Default: `"todos"`.
- `limite` (integer, opcional): Quantidade máxima de vídeos retornados (default: 10).

**Retorno:**
String formatada contendo os vídeos encontrados com detalhes essenciais.

---

### 2.3. `marcar_video_assistido`
**Objetivo:** Alterar o status de um vídeo salvo para `"assistido"`.

**Parâmetros de Entrada:**
- `termo_ou_id` (string, obrigatório): ID do vídeo ou trecho do título/descrição para localizar o vídeo.

**Retorno:**
Confirmação de alteração ou solicitação de desambiguação se mais de um vídeo for encontrado.

---

### 2.4. `remover_video_salvo`
**Objetivo:** Excluir permanentemente um vídeo da lista de salvos.

**Parâmetros de Entrada:**
- `termo_ou_id` (string, obrigatório): ID ou termo para localizar o vídeo a ser excluído.

**Retorno:**
Confirmação de exclusão ou mensagem de desambiguação/não encontrado.
