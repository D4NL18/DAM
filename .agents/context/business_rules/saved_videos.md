# Regras de Negócio: Repositório de Vídeos Salvos (EL-07)

## 📋 Visão Geral
Define as regras de negócio para a funcionalidade de salvamento, catalogação e recuperação semântica de vídeos de redes sociais (TikTok, Instagram Reels/Posts e YouTube/Shorts), permitindo ao usuário resgatar recomendações e referências facilmente via linguagem natural no WhatsApp.

---

## 📌 Regras de Negócio (P-XXX)

### P-0701: Detecção Automática de Plataforma
O sistema DEVE identificar e normalizar a plataforma de origem do vídeo analisando o domínio e o formato da URL fornecida:
- `tiktok.com`, `vm.tiktok.com`, `vt.tiktok.com` -> `"TikTok"`
- `instagram.com` (incluindo `/reel/`, `/p/`, `/tv/`) -> `"Instagram"`
- `youtube.com`, `youtu.be`, `m.youtube.com` (incluindo Shorts e vídeos padrão) -> `"YouTube"`
- Qualquer outra URL válida -> `"Outro"`
Se a URL não contiver esquema ou domínio reconhecível, deve ser validada conforme a regra P-0706.

### P-0702: Captura Semântica e Contexto do Vídeo
Ao salvar um vídeo, o sistema DEVE registrar:
1. `url`: Link completo e sanitizado do vídeo.
2. `titulo`: Título atribuído ou inferido do conteúdo. Se não fornecido pelo usuário, deve ser inferido a partir do resumo do assunto ou nome padrão `"Vídeo do [Plataforma]"` acrescido da data/hora.
3. `descricao`: Texto livre detalhando sobre o que era o vídeo (ex: "receita de bolo de cenoura com cobertura crocante", "tutorial de corte no Premiere", "treino de pernas com foco em quadríceps").
4. `categoria`: Categoria temática opcional (ex: `"Culinária"`, `"Treino"`, `"Tecnologia"`, `"Humor"`, `"Finanças"`).
5. `tags`: Lista de palavras-chave normalizadas em minúsculas (ex: `["receita", "sobremesa", "bolo"]`).
6. `status`: Estado inicial obrigatório: `"pendente"`.

### P-0703: Busca Multicritério e Semântica por Assunto
A consulta de vídeos DEVE ser inteligente e tolerante a termos parciais:
1. O usuário pode buscar informando palavras sobre o que era o vídeo, título, plataforma ou categoria (ex: *"o que eu salvei sobre bolo?"*, *"qual era aquele vídeo do tiktok de mobilidade?"*, *"vídeos do youtube que salvei"*).
2. O motor de busca DEVE varrer campos `titulo`, `descricao`, `categoria`, `tags` e `plataforma` aplicando normalização de texto (remoção de acentos e case-insensitive).
3. Deve suportar parâmetros opcionais de filtro: `plataforma` ("TikTok", "Instagram", "YouTube") e `status` ("pendente", "assistido", "todos").
4. O resultado deve ser retornado em ordem decrescente de criação (mais recentes primeiro), limitado por padrão aos últimos 10 itens para não poluir o chat.

### P-0704: Ciclo de Vida e Estados
1. Todo vídeo salvo inicia com `status = "pendente"`.
2. O usuário pode solicitar a marcação de um vídeo como assistido através de `marcar_video_assistido(termo_ou_id)`.
3. O status só pode alternar entre `"pendente"` e `"assistido"`.
4. Em caso de múltiplos vídeos correspondentes ao termo informado pelo usuário para marcar como assistido ou remover, o sistema DEVE listar os candidatos encontrados e solicitar desambiguação amigável, impedindo alterações acidentais em itens indesejados.

### P-0705: Isolamento Inviolável Multi-Usuário (Multi-Tenant)
1. Todos os documentos de vídeos salvos na coleção `saved_videos` do Firestore DEVEM conter obrigatoriamente o atributo `userId` ou `user_id`.
2. Apenas o usuário autenticado na sessão (`UserContext.get_user_id()`) tem permissão de leitura, gravação, atualização e exclusão dos seus próprios vídeos.
3. Sob NENHUMA hipótese Daniel terá acesso aos vídeos salvos por Lari ou vice-versa.

### P-0706: Validação e Sanitização de URLs
1. O sistema DEVE validar rigorosamente que a URL enviada possui esquema `http://` ou `https://`.
2. Esquemas potencialmente maliciosos como `javascript:`, `data:`, `file:`, `vbscript:` DEVEM ser rejeitados sumariamente.
3. Caracteres de quebra de linha ou injeções em links devem ser sanitizados.
