import logging
import re
from urllib.parse import urlparse
from typing import Tuple, List, Optional
from services.user_context import UserContext
from repositories.saved_videos_repository import SavedVideosRepository, remover_acentos

logger = logging.getLogger(__name__)

PLATAFORMA_ICONES = {
    "TikTok": "🎵",
    "Instagram": "📸",
    "YouTube": "🔴",
    "Outro": "🔗"
}


def _detectar_plataforma(url: str) -> str:
    """Detecta automaticamente a rede social ou plataforma a partir da URL."""
    if not url:
        return "Outro"

    url_lower = url.lower()
    if any(d in url_lower for d in ["tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]):
        return "TikTok"
    if "instagram.com" in url_lower:
        return "Instagram"
    if any(d in url_lower for d in ["youtube.com", "youtu.be", "m.youtube.com"]):
        return "YouTube"

    return "Outro"


def _validar_e_sanitizar_url(url: str) -> Tuple[str, bool]:
    """
    Valida e sanitiza a URL fornecida.
    Aceita estritamente esquemas http e https. Rejeita esquemas perigosos (javascript:, data:, etc.).
    """
    if not url or not isinstance(url, str):
        return "", False

    url_limpa = url.strip()

    # Rejeita esquemas maliciosos explicitamente
    esquemas_bloqueados = ["javascript:", "data:", "file:", "vbscript:", "about:"]
    if any(url_limpa.lower().startswith(bad) for bad in esquemas_bloqueados):
        return "", False

    # Auto-completa protocolo se o usuário colou link direto iniciando com www. ou domínio conhecido
    if not url_limpa.startswith("http://") and not url_limpa.startswith("https://"):
        if url_limpa.startswith("www.") or any(d in url_limpa for d in ["tiktok.com", "instagram.com", "youtube.com", "youtu.be"]):
            url_limpa = f"https://{url_limpa}"
        else:
            return "", False

    parsed = urlparse(url_limpa)
    if parsed.scheme not in ["http", "https"]:
        return "", False

    if not parsed.netloc:
        return "", False

    return url_limpa, True


def salvar_video(
    url: str,
    titulo: str = "",
    descricao: str = "",
    categoria: str = "",
    tags: str = ""
) -> str:
    """
    Salva um vídeo de rede social (TikTok, Instagram, YouTube) para assistir mais tarde ou guardar como referência.

    :param url: Link completo do vídeo.
    :param titulo: Título ou nome breve do vídeo (opcional).
    :param descricao: Resumo detalhado sobre o que é o vídeo, receita, treino, dicas ou assunto (opcional).
    :param categoria: Categoria do conteúdo (ex: 'Culinária', 'Treino', 'Tecnologia', 'Humor').
    :param tags: Palavras-chave separadas por vírgula para facilitar a busca (ex: 'strogonoff, fit, almoco').
    :return: Confirmação formatada para o WhatsApp.
    """
    url_sanitizada, valida = _validar_e_sanitizar_url(url)
    if not valida:
        return (
            "❌ Link inválido! Por favor, envie uma URL válida iniciando com http:// ou https:// "
            "(ex: links do TikTok, Instagram ou YouTube)."
        )

    plataforma = _detectar_plataforma(url_sanitizada)
    icone = PLATAFORMA_ICONES.get(plataforma, "🔗")

    # Inferência de título se não fornecido
    titulo_final = (titulo or "").strip()
    if not titulo_final:
        if descricao and len(descricao.strip()) > 0:
            desc_limpa = descricao.strip()
            titulo_final = desc_limpa[:50] + ("..." if len(desc_limpa) > 50 else "")
        else:
            titulo_final = f"Vídeo do {plataforma}"

    # Normalização de tags
    tags_list: List[str] = []
    if tags:
        tags_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

    user_id = UserContext.get_user_id()
    repo = SavedVideosRepository.get_instance()

    item = {
        "userId": user_id,
        "user_id": user_id,
        "url": url_sanitizada,
        "plataforma": plataforma,
        "titulo": titulo_final,
        "descricao": (descricao or "").strip(),
        "categoria": (categoria or "").strip(),
        "tags": tags_list,
        "status": "pendente"
    }

    item_salvo = repo.salvar(item)

    resposta = [
        "✅ Vídeo salvo com sucesso!",
        f"{icone} Plataforma: {plataforma}",
        f"📌 Título: {titulo_final}"
    ]

    if item["descricao"]:
        resposta.append(f"📝 Sobre: {item['descricao']}")
    if item["categoria"]:
        resposta.append(f"🏷️ Categoria: {item['categoria']}")
    if item["tags"]:
        resposta.append(f"🔖 Tags: {', '.join(item['tags'])}")

    resposta.append(f"⏳ Status: Pendente")
    resposta.append(f"🔗 Link: {url_sanitizada}")

    return "\n".join(resposta)


def consultar_videos_salvos(
    termo_busca: str = "",
    plataforma: str = "",
    status: str = "",
    limite: int = 10
) -> str:
    """
    Busca vídeos salvos por assunto/descrição, título, categoria ou tags,
    com filtros opcionais de plataforma e status.

    :param termo_busca: Palavra-chave livre sobre o que era o vídeo, título, etc.
    :param plataforma: 'TikTok', 'Instagram', 'YouTube' ou vazio para todas.
    :param status: 'pendente', 'assistido' ou 'todos'.
    :param limite: Quantidade máxima de resultados (padrão: 10).
    :return: Lista formatada com os vídeos salvos.
    """
    user_id = UserContext.get_user_id()
    repo = SavedVideosRepository.get_instance()

    videos = repo.buscar_por_termo(
        user_id=user_id,
        termo=termo_busca,
        plataforma=plataforma if plataforma else None,
        status=status if status else None
    )

    if not videos:
        filtro_txt = []
        if termo_busca:
            filtro_txt.append(f"com o termo '{termo_busca}'")
        if plataforma:
            filtro_txt.append(f"na plataforma {plataforma}")
        if status and status != "todos":
            filtro_txt.append(f"com status '{status}'")

        detalhe = " " + " e ".join(filtro_txt) if filtro_txt else ""
        return f"🎬 Nenhum vídeo encontrado{detalhe}. Envie um link para salvar novos vídeos a qualquer momento!"

    videos_exibidos = videos[:limite]
    linhas = [f"🎬 Encontrei {len(videos)} vídeo(s) salvo(s):"]

    for i, v in enumerate(videos_exibidos, 1):
        plat = v.get("plataforma", "Outro")
        icone = PLATAFORMA_ICONES.get(plat, "🔗")
        tit = v.get("titulo", "Sem título")
        url = v.get("url", "")
        desc = v.get("descricao", "")
        cat = v.get("categoria", "")
        stat = v.get("status", "pendente")
        stat_icon = "⏳ Pendente" if stat == "pendente" else "✅ Assistido"

        bloco = [f"\n{i}. {icone} *{tit}* ({plat})"]
        if desc:
            bloco.append(f"   📝 Sobre: {desc}")
        meta = [f"   Status: {stat_icon}"]
        if cat:
            meta.append(f"🏷️ {cat}")
        bloco.append(" | ".join(meta))
        if url:
            bloco.append(f"   🔗 {url}")

        linhas.append("\n".join(bloco))

    if len(videos) > limite:
        linhas.append(f"\n_... e mais {len(videos) - limite} vídeo(s) guardados._")

    return "\n".join(linhas)


def marcar_video_assistido(termo_ou_id: str) -> str:
    """
    Marca um vídeo salvo como assistido.

    :param termo_ou_id: ID do vídeo ou trecho do título/descrição para localizar o vídeo.
    :return: Confirmação ou solicitação de desambiguação.
    """
    if not termo_ou_id or not termo_ou_id.strip():
        return "⚠️ Por favor, informe o título, assunto ou ID do vídeo que você assistiu."

    user_id = UserContext.get_user_id()
    repo = SavedVideosRepository.get_instance()
    termo = termo_ou_id.strip()

    # Tenta obter diretamente por ID exato
    video_exato = repo.obter_por_id(user_id=user_id, video_id=termo)
    if video_exato:
        repo.atualizar_status(user_id=user_id, video_id=video_exato["id"], novo_status="assistido")
        icone = PLATAFORMA_ICONES.get(video_exato.get("plataforma", ""), "🔗")
        return f"✅ Vídeo marcado como assistido:\n{icone} *{video_exato.get('titulo', 'Vídeo')}*"

    # Busca por termo
    candidatos = repo.buscar_por_termo(user_id=user_id, termo=termo)
    if not candidatos:
        return f"🎬 Nenhum vídeo encontrado para o termo '{termo}'."

    if len(candidatos) == 1:
        v = candidatos[0]
        repo.atualizar_status(user_id=user_id, video_id=v["id"], novo_status="assistido")
        icone = PLATAFORMA_ICONES.get(v.get("plataforma", ""), "🔗")
        return f"✅ Vídeo marcado como assistido:\n{icone} *{v.get('titulo', 'Vídeo')}*"

    # Múltiplos candidatos: solicita desambiguação amigável
    linhas = [f"⚠️ Encontrei mais de um vídeo correspondente a '{termo}':"]
    for i, c in enumerate(candidatos[:5], 1):
        icone = PLATAFORMA_ICONES.get(c.get("plataforma", ""), "🔗")
        linhas.append(f"{i}. {icone} {c.get('titulo', 'Sem título')} (ID: `{c.get('id', '')[:8]}`) - {c.get('plataforma')}")
    linhas.append("\nPor favor, informe o ID ou o título exato do vídeo que deseja marcar como assistido.")

    return "\n".join(linhas)


def remover_video_salvo(termo_ou_id: str) -> str:
    """
    Remove permanentemente um vídeo da lista de salvos.

    :param termo_ou_id: ID do vídeo ou trecho do título/descrição para localizar o vídeo.
    :return: Confirmação de exclusão ou mensagem amigável.
    """
    if not termo_ou_id or not termo_ou_id.strip():
        return "⚠️ Por favor, informe o título, assunto ou ID do vídeo que deseja remover."

    user_id = UserContext.get_user_id()
    repo = SavedVideosRepository.get_instance()
    termo = termo_ou_id.strip()

    # Tenta obter diretamente por ID exato
    video_exato = repo.obter_por_id(user_id=user_id, video_id=termo)
    if video_exato:
        repo.excluir(user_id=user_id, video_id=video_exato["id"])
        icone = PLATAFORMA_ICONES.get(video_exato.get("plataforma", ""), "🔗")
        return f"🗑️ Vídeo removido com sucesso:\n{icone} *{video_exato.get('titulo', 'Vídeo')}*"

    candidatos = repo.buscar_por_termo(user_id=user_id, termo=termo)
    if not candidatos:
        return f"🎬 Nenhum vídeo encontrado para o termo '{termo}'."

    if len(candidatos) == 1:
        v = candidatos[0]
        repo.excluir(user_id=user_id, video_id=v["id"])
        icone = PLATAFORMA_ICONES.get(v.get("plataforma", ""), "🔗")
        return f"🗑️ Vídeo removido com sucesso:\n{icone} *{v.get('titulo', 'Vídeo')}*"

    # Múltiplos candidatos: solicita desambiguação
    linhas = [f"⚠️ Encontrei mais de um vídeo correspondente a '{termo}':"]
    for i, c in enumerate(candidatos[:5], 1):
        icone = PLATAFORMA_ICONES.get(c.get("plataforma", ""), "🔗")
        linhas.append(f"{i}. {icone} {c.get('titulo', 'Sem título')} (ID: `{c.get('id', '')[:8]}`) - {c.get('plataforma')}")
    linhas.append("\nPor favor, informe o ID ou o título exato do vídeo que deseja remover.")

    return "\n".join(linhas)
