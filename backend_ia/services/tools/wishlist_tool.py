import logging
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse
from repositories.wishlist_repository import WishlistRepository
from services.user_context import UserContext
from config.timezone import get_brasilia_now_str

logger = logging.getLogger(__name__)

_PROHIBITED_SCHEMES = {"javascript", "file", "data", "ftp", "gopher", "dict", "ldap"}


def _validar_e_normalizar_url(url: str) -> Tuple[bool, str]:
    """
    Valida e normaliza uma URL fornecida para o item da Wishlist.
    Retorna uma tupla (eh_valida, url_normalizada_ou_erro).
    """
    if not url:
        return True, ""

    url_limpa = url.strip()
    parsed = urlparse(url_limpa)
    if parsed.scheme.lower() in _PROHIBITED_SCHEMES:
        return (
            False,
            "Link com protocolo inválido ou não permitido. Por segurança, use apenas links web normais (https:// ou http://)."
        )

    if not parsed.scheme:
        url_limpa = f"https://{url_limpa}"
        parsed = urlparse(url_limpa)

    if parsed.scheme.lower() not in {"http", "https"}:
        return (
            False,
            "Link com protocolo inválido ou não permitido. Utilize apenas links que comecem com http ou https."
        )

    if not parsed.netloc:
        return (
            False,
            "Link inválido. Certifique-se de informar um endereço web correto (ex: mercadolivre.com.br)."
        )

    return True, url_limpa


def _normalizar_moeda(moeda: str, texto_auxiliar: str = "") -> str:
    """Normaliza o código da moeda para 'USD' ou 'BRL'."""
    m = (moeda or "").strip().upper()
    if m in {"USD", "US$", "DOLAR", "DOLARES", "DÓLAR", "DÓLARES", "$"}:
        return "USD"
    aux = (texto_auxiliar or "").lower()
    if any(k in aux for k in ["usd", "us$", "dolar", "dólar", "dolares", "dólares"]):
        return "USD"
    return "BRL"


def _formatar_preco(preco: Optional[float], moeda: str = "BRL") -> str:
    """Formata valor monetário em BRL (R$ 1.234,56) ou USD (US$ 1,234.56)."""
    if preco is None:
        return ""
    moeda_norm = _normalizar_moeda(moeda)
    try:
        val = float(preco)
        if moeda_norm == "USD":
            return f"US$ {val:,.2f}"
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        prefix = "US$" if moeda_norm == "USD" else "R$"
        return f"{prefix} {preco}"


def adicionar_item_wishlist(
    nome_produto: str,
    descricao: str = "",
    link: str = "",
    preco_estimado: Optional[float] = None,
    moeda: str = "BRL",
    categoria: str = ""
) -> str:
    """
    Add a product, PC component, or item to the user's personal Wishlist in the Firestore database.

    Args:
        nome_produto (str): Product or component name (e.g. 'Intel Core i7 14700K', 'Power Bank Baseus').
        descricao (str, optional): Specs, model, store, or details.
        link (str, optional): Store URL (e.g. Mercado Livre, Amazon, Micro Center, Kabum).
        preco_estimado (float, optional): Estimated numeric price (e.g. 339.99).
        moeda (str, optional): Currency code: 'BRL' (default, Reais) or 'USD' (Dollars).
        categoria (str, optional): Item category (e.g. 'Peças de Computador', 'Eletrônicos').
    """
    nome_limpo = (nome_produto or "").strip()
    if not nome_limpo:
        return "Por favor, informe o nome do produto que deseja adicionar à sua Wishlist."

    if len(nome_limpo) < 2:
        return "O nome do produto deve ter pelo menos 2 caracteres."

    url_valida, url_ou_erro = _validar_e_normalizar_url(link or "")
    if not url_valida:
        return f"⚠️ {url_ou_erro}"

    moeda_final = _normalizar_moeda(moeda, f"{nome_limpo} {descricao}")

    item_data: Dict[str, Any] = {
        "nome_produto": nome_limpo,
        "descricao": (descricao or "").strip(),
        "categoria": (categoria or "").strip(),
        "link": url_ou_erro,
        "preco_estimado": float(preco_estimado) if preco_estimado is not None else None,
        "moeda": moeda_final,
        "status": "desejado",
        "compradoEm": None
    }

    salvo = WishlistRepository.salvar(item_data)
    item_id = salvo.get("id", "")

    linhas = [
        "✨ *Produto adicionado e salvo com sucesso na sua Wishlist (Banco de Dados)!*",
        f"🛍️ *Item:* {nome_limpo}"
    ]

    if item_data["categoria"]:
        linhas.append(f"🏷️ *Categoria:* {item_data['categoria']}")

    if item_data["descricao"]:
        linhas.append(f"📝 *Detalhes:* {item_data['descricao']}")

    if item_data["preco_estimado"] is not None:
        linhas.append(f"💰 *Preço Estimado:* {_formatar_preco(item_data['preco_estimado'], moeda_final)}")

    if item_data["link"]:
        linhas.append(f"🔗 *Link:* {item_data['link']}")

    linhas.append(f"🆔 *ID:* `{item_id}`")

    return "\n".join(linhas)


def _formatar_lista_wishlist(itens: List[Dict[str, Any]], titulo_cabecalho: str) -> str:
    """Formata a lista de itens da Wishlist com somatório automático por moeda."""
    linhas = [f"{titulo_cabecalho}\n"]
    total_brl = 0.0
    total_usd = 0.0

    for idx, item in enumerate(itens, 1):
        icone = "✅" if item.get("status") == "comprado" else "🛍️"
        nome = item.get("nome_produto", "Sem nome")
        cat = f" [{item['categoria']}]" if item.get("categoria") else ""
        linhas.append(f"{idx}. {icone} *{nome}*{cat}")

        if item.get("descricao"):
            linhas.append(f"   📝 {item['descricao']}")

        preco = item.get("preco_estimado")
        moeda_item = _normalizar_moeda(item.get("moeda", "BRL"), str(item.get("descricao", "")))
        if preco is not None:
            try:
                val = float(preco)
                if moeda_item == "USD":
                    total_usd += val
                else:
                    total_brl += val
            except (ValueError, TypeError):
                pass
            linhas.append(f"   💰 {_formatar_preco(preco, moeda_item)}")

        if item.get("link"):
            linhas.append(f"   🔗 {item['link']}")

        if item.get("status") == "comprado" and item.get("compradoEm"):
            linhas.append(f"   🎉 Adquirido em: {str(item['compradoEm'])[:10]}")

        linhas.append(f"   🆔 `{item.get('id', '')}`")
        linhas.append("")

    totais_partes = []
    if total_usd > 0:
        totais_partes.append(_formatar_preco(total_usd, "USD"))
    if total_brl > 0:
        totais_partes.append(_formatar_preco(total_brl, "BRL"))
    if totais_partes:
        linhas.append(f"💵 *Total Acumulado:* {' + '.join(totais_partes)}")

    return "\n".join(linhas).strip()


def consultar_wishlist(
    termo_busca: str = "",
    status: str = "desejado"
) -> str:
    """
    Query items saved in the user's personal Wishlist in the Firestore database.

    Args:
        termo_busca (str, optional): Keyword to filter products (e.g. 'pc', 'peças de computador', 'power bank'). Leave empty to list all.
        status (str, optional): Item status: 'desejado' (default), 'comprado', or 'todos'.
    """
    status_filtro = (status or "desejado").strip().lower()
    itens = WishlistRepository.listar(status=status_filtro, busca=termo_busca)

    if not itens and termo_busca:
        # Fallback: se o termo filtrado não bateu diretamente mas existem itens na wishlist do usuário,
        # retorna todos os itens para que a IA tenha visibilidade completa e nunca diga que está vazia.
        todos_status = WishlistRepository.listar(status=status_filtro, busca="")
        if todos_status:
            cabecalho = (
                f"ℹ️ Nenhum item correspondeu exatamente ao filtro '{termo_busca}', "
                f"mas aqui está a sua Wishlist completa ({len(todos_status)} itens):"
            )
            return _formatar_lista_wishlist(todos_status, cabecalho)

    if not itens:
        if termo_busca:
            return f"ℹ️ Nenhum item encontrado na sua Wishlist para a busca: '{termo_busca}'."
        if status_filtro == "comprado":
            return "ℹ️ Você ainda não marcou nenhum item como comprado na sua Wishlist."
        return "🎁 Sua Wishlist está vazia no momento! O que gostaria de adicionar para comprar no futuro?"

    status_rotulo = {
        "desejado": "itens desejados",
        "comprado": "itens comprados / realizados",
        "todos": "todos os itens"
    }.get(status_filtro, "itens")

    cabecalho = f"🎁 *Sua Wishlist ({len(itens)} {status_rotulo}):*"
    return _formatar_lista_wishlist(itens, cabecalho)


def atualizar_item_wishlist(
    identificador: str,
    novo_nome: str = "",
    nova_descricao: str = "",
    novo_preco: Optional[float] = None,
    nova_moeda: str = "",
    novo_link: str = "",
    nova_categoria: str = ""
) -> str:
    """
    Update an existing item in the user's Wishlist by ID or product name.

    Args:
        identificador (str): Existing item ID or product name substring.
        novo_nome (str, optional): New product name if changing.
        nova_descricao (str, optional): Updated description/specs.
        novo_preco (float, optional): Updated estimated price.
        nova_moeda (str, optional): Updated currency ('BRL' or 'USD').
        novo_link (str, optional): Updated URL link.
        nova_categoria (str, optional): Updated category.
    """
    termo = (identificador or "").strip()
    if not termo:
        return "Por favor, informe o nome ou ID do item da Wishlist que deseja atualizar."

    user_id = UserContext.get_user_id()
    alvo = WishlistRepository.obter_por_id(termo, user_id=user_id)
    if not alvo:
        candidatos = WishlistRepository.listar(user_id=user_id, status="todos", busca=termo)
        if not candidatos:
            return f"Não encontrei nenhum item com '{termo}' na sua Wishlist."
        if len(candidatos) > 1:
            linhas = [f"Encontrei mais de um item compatível com '{termo}'. Qual deles deseja atualizar?"]
            for c in candidatos:
                linhas.append(f"• *{c.get('nome_produto')}* (ID: `{c.get('id')}`)")
            return "\n".join(linhas)
        alvo = candidatos[0]

    updates: Dict[str, Any] = {}
    if novo_nome and novo_nome.strip():
        updates["nome_produto"] = novo_nome.strip()
    if nova_descricao and nova_descricao.strip():
        updates["descricao"] = nova_descricao.strip()
    if nova_categoria and nova_categoria.strip():
        updates["categoria"] = nova_categoria.strip()
    if novo_preco is not None:
        updates["preco_estimado"] = float(novo_preco)
    if nova_moeda and nova_moeda.strip():
        updates["moeda"] = _normalizar_moeda(nova_moeda)
    if novo_link and novo_link.strip():
        ok, url_norm = _validar_e_normalizar_url(novo_link)
        if not ok:
            return f"⚠️ {url_norm}"
        updates["link"] = url_norm

    if not updates:
        return "Nenhuma alteração foi informada para atualizar o item."

    WishlistRepository.atualizar(alvo["id"], updates, user_id=user_id)
    nome_exibicao = updates.get("nome_produto") or alvo.get("nome_produto")
    return f"✅ Item *{nome_exibicao}* (`{alvo['id']}`) atualizado com sucesso na sua Wishlist!"


def marcar_item_wishlist_comprado(
    item_id: str = "",
    nome_produto: str = ""
) -> str:
    """
    Mark a Wishlist item as purchased/acquired in the database.

    Args:
        item_id (str, optional): Unique ID of the item.
        nome_produto (str, optional): Product name or substring.
    """
    id_clean = (item_id or "").strip()
    nome_clean = (nome_produto or "").strip()

    if not id_clean and not nome_clean:
        return "Por favor, informe o nome do produto ou o ID do item que você comprou."

    user_id = UserContext.get_user_id()

    if id_clean:
        item = WishlistRepository.obter_por_id(id_clean, user_id=user_id)
        if not item:
            return f"Não encontrei nenhum item com o ID `{id_clean}` na sua Wishlist."

        WishlistRepository.atualizar(id_clean, {
            "status": "comprado",
            "compradoEm": get_brasilia_now_str()
        }, user_id=user_id)
        return f"🎉 *Parabéns pela conquista!* O item *{item.get('nome_produto')}* foi marcado como comprado na sua Wishlist!"

    candidatos = WishlistRepository.listar(user_id=user_id, status="desejado", busca=nome_clean)

    if not candidatos:
        todos = WishlistRepository.listar(user_id=user_id, status="todos", busca=nome_clean)
        if todos and all(i.get("status") == "comprado" for i in todos):
            return f"ℹ️ O item *{todos[0].get('nome_produto')}* já está marcado como comprado na sua Wishlist!"
        return f"Não encontrei nenhum item desejado com o nome '{nome_clean}' na sua Wishlist."

    if len(candidatos) > 1:
        linhas = [f"Encontrei mais de um produto compatível com '{nome_clean}'. Qual deles você comprou?"]
        for c in candidatos:
            linhas.append(f"• *{c.get('nome_produto')}* (ID: `{c.get('id')}`)")
        linhas.append("\nPor favor, confirme informando o ID ou o nome exato.")
        return "\n".join(linhas)

    alvo = candidatos[0]
    alvo_id = alvo["id"]
    WishlistRepository.atualizar(alvo_id, {
        "status": "comprado",
        "compradoEm": get_brasilia_now_str()
    }, user_id=user_id)

    return f"🎉 *Parabéns pela conquista!* O item *{alvo.get('nome_produto')}* foi marcado como comprado na sua Wishlist!"


def remover_item_wishlist(
    item_id: str = "",
    nome_produto: str = ""
) -> str:
    """
    Permanently remove an item from the user's Wishlist in the database.

    Args:
        item_id (str, optional): Unique ID of the item.
        nome_produto (str, optional): Product name or substring to remove.
    """
    id_clean = (item_id or "").strip()
    nome_clean = (nome_produto or "").strip()

    if not id_clean and not nome_clean:
        return "Por favor, informe o nome do produto ou o ID do item que deseja remover."

    user_id = UserContext.get_user_id()

    if id_clean:
        item = WishlistRepository.obter_por_id(id_clean, user_id=user_id)
        if not item:
            return f"Não encontrei nenhum item com o ID `{id_clean}` na sua Wishlist."

        WishlistRepository.remover(id_clean, user_id=user_id)
        return f"🗑️ O item *{item.get('nome_produto')}* foi removido com sucesso da sua Wishlist!"

    candidatos = WishlistRepository.listar(user_id=user_id, status="todos", busca=nome_clean)

    if not candidatos:
        return f"Não encontrei nenhum item com o nome '{nome_clean}' na sua Wishlist."

    if len(candidatos) > 1:
        linhas = [f"Encontrei mais de um produto compatível com '{nome_clean}'. Qual deles deseja remover?"]
        for c in candidatos:
            linhas.append(f"• *{c.get('nome_produto')}* (ID: `{c.get('id')}`)")
        linhas.append("\nPor favor, informe o ID ou nome exato para remoção segura.")
        return "\n".join(linhas)

    alvo = candidatos[0]
    WishlistRepository.remover(alvo["id"], user_id=user_id)
    return f"🗑️ O item *{alvo.get('nome_produto')}* foi removido com sucesso da sua Wishlist!"
