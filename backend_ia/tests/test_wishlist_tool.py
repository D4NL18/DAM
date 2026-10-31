import pytest
from unittest.mock import MagicMock, patch
from services.user_context import UserContext
from repositories.wishlist_repository import WishlistRepository, _reset_mock_storage
from services.tools.wishlist_tool import (
    adicionar_item_wishlist,
    consultar_wishlist,
    atualizar_item_wishlist,
    marcar_item_wishlist_comprado,
    remover_item_wishlist,
    _validar_e_normalizar_url
)


@pytest.fixture(autouse=True)
def setup_teardown():
    _reset_mock_storage()
    UserContext.set_user("daniel")
    with patch("config.firebase.db", None):
        yield
    _reset_mock_storage()
    UserContext.set_user("daniel")


class TestURLValidation:
    def test_validar_url_http_https(self):
        valida, url = _validar_e_normalizar_url("https://amazon.com.br/item")
        assert valida is True
        assert url == "https://amazon.com.br/item"

        valida, url = _validar_e_normalizar_url("http://mercadolivre.com.br/produto")
        assert valida is True
        assert url == "http://mercadolivre.com.br/produto"

    def test_auto_completar_https_sem_esquema(self):
        valida, url = _validar_e_normalizar_url("kabum.com.br/produto/123")
        assert valida is True
        assert url == "https://kabum.com.br/produto/123"

    def test_rejeitar_esquemas_inseguros(self):
        for esquema in [
            "javascript:alert(1)",
            "file:///etc/passwd",
            "data:text/html;base64,PHNjcmlwdD4=",
            "ftp://servidor"
        ]:
            valida, msg = _validar_e_normalizar_url(esquema)
            assert valida is False
            assert "inválido ou não permitido" in msg.lower() or "inseguro" in msg.lower()

    def test_url_vazia(self):
        valida, url = _validar_e_normalizar_url("")
        assert valida is True
        assert url == ""


class TestAdicionarItemWishlist:
    def test_adicionar_item_minimo(self):
        resposta = adicionar_item_wishlist("Kindle Paperwhite")
        assert "adicionado" in resposta.lower()
        assert "Kindle Paperwhite" in resposta

        itens = WishlistRepository.listar(user_id="daniel", status="desejado")
        assert len(itens) == 1
        assert itens[0]["nome_produto"] == "Kindle Paperwhite"
        assert itens[0]["status"] == "desejado"
        assert itens[0]["userId"] == "daniel"

    def test_adicionar_item_completo_brl_e_usd(self):
        resp_brl = adicionar_item_wishlist(
            nome_produto="Fonte Corsair CX750 750W 80Plus",
            descricao="Fonte ATX 750W Bronze",
            preco_estimado=399.99,
            moeda="BRL",
            categoria="Peças de Computador"
        )
        assert "Fonte Corsair CX750 750W 80Plus" in resp_brl
        assert "R$ 399,99" in resp_brl

        resp_usd = adicionar_item_wishlist(
            nome_produto="Intel Core i7 14700K",
            descricao="Processador LGA 1700",
            preco_estimado=339.99,
            moeda="USD",
            categoria="Peças de Computador"
        )
        assert "Intel Core i7 14700K" in resp_usd
        assert "US$ 339.99" in resp_usd or "US$ 339,99" in resp_usd

        itens = WishlistRepository.listar(user_id="daniel")
        assert len(itens) == 2

    def test_persistencia_direta_no_firestore(self):
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_doc = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_col.document.return_value = mock_doc

        with patch("config.firebase.db", mock_db):
            adicionar_item_wishlist(
                nome_produto="Zotac RTX 5060 Ti 8GB",
                preco_estimado=379.99,
                moeda="USD",
                categoria="Peças de Computador"
            )
            mock_db.collection.assert_called_with("wishlist")
            assert mock_doc.set.called
            saved_payload = mock_doc.set.call_args[0][0]
            assert saved_payload["nome_produto"] == "Zotac RTX 5060 Ti 8GB"
            assert saved_payload["preco_estimado"] == 379.99
            assert saved_payload["moeda"] == "USD"
            assert saved_payload["userId"] == "daniel"

    def test_rejeitar_nome_invalido(self):
        resposta_vazio = adicionar_item_wishlist("   ")
        assert "informe o nome" in resposta_vazio.lower()

        resposta_curto = adicionar_item_wishlist("A")
        assert "pelo menos 2 caracteres" in resposta_curto.lower()

    def test_rejeitar_link_inseguro_na_adicao(self):
        resposta = adicionar_item_wishlist("Item Teste", link="javascript:void(0)")
        assert "link" in resposta.lower() and "inválido" in resposta.lower()
        itens = WishlistRepository.listar(user_id="daniel")
        assert len(itens) == 0


class TestConsultarWishlist:
    def test_consultar_wishlist_vazia(self):
        resposta = consultar_wishlist()
        assert "vazia" in resposta.lower() or "nenhum item" in resposta.lower()

    def test_consultar_wishlist_com_itens_e_totais(self):
        adicionar_item_wishlist("Intel Core i7 14700K", preco_estimado=339.99, moeda="USD")
        adicionar_item_wishlist("Zotac RTX 5060 Ti 8GB", preco_estimado=379.99, moeda="USD")
        adicionar_item_wishlist("Fonte Corsair CX750", preco_estimado=399.99, moeda="BRL")

        resposta = consultar_wishlist()
        assert "Intel Core i7 14700K" in resposta
        assert "Zotac RTX 5060 Ti 8GB" in resposta
        assert "Fonte Corsair CX750" in resposta
        assert "719" in resposta  # Total USD 719.98
        assert "399,99" in resposta  # Total BRL

    def test_filtrar_por_sinonimo_pecas_de_computador(self):
        adicionar_item_wishlist("Intel Core i7 14700K", preco_estimado=339.99, moeda="USD")
        adicionar_item_wishlist("Zotac RTX 5060 Ti 8GB", preco_estimado=379.99, moeda="USD")
        adicionar_item_wishlist("Power Bank Baseus", link="https://mercadolivre.com.br/p/MLB123")

        resposta = consultar_wishlist(termo_busca="peças de computador")
        assert "Intel Core i7 14700K" in resposta
        assert "Zotac RTX 5060 Ti 8GB" in resposta

    def test_fallback_exibe_todos_itens_se_termo_especifico_nao_bater(self):
        adicionar_item_wishlist("Intel Core i7 14700K", preco_estimado=339.99, moeda="USD")
        resposta = consultar_wishlist(termo_busca="termo_inexistente_xyz")
        assert "Intel Core i7 14700K" in resposta

    def test_filtrar_por_status(self):
        adicionar_item_wishlist("Produto 1")
        adicionar_item_wishlist("Produto 2")
        marcar_item_wishlist_comprado(nome_produto="Produto 1")

        res_desejados = consultar_wishlist(status="desejado")
        assert "Produto 2" in res_desejados
        assert "Produto 1" not in res_desejados

        res_comprados = consultar_wishlist(status="comprado")
        assert "Produto 1" in res_comprados
        assert "Produto 2" not in res_comprados


class TestAtualizarMarcarERemoverWishlist:
    def test_atualizar_item_wishlist(self):
        adicionar_item_wishlist("RTX 5060 Ti", preco_estimado=400.0, moeda="USD")
        resp = atualizar_item_wishlist("RTX 5060", novo_preco=379.99, nova_moeda="USD", nova_descricao="Zotac 8GB")
        assert "atualizado" in resp.lower()

        itens = WishlistRepository.listar(user_id="daniel")
        assert itens[0]["preco_estimado"] == 379.99
        assert itens[0]["descricao"] == "Zotac 8GB"

    def test_marcar_como_comprado_por_nome(self):
        adicionar_item_wishlist("AirPods Pro")
        resposta = marcar_item_wishlist_comprado(nome_produto="AirPods Pro")
        assert "comprado" in resposta.lower()

        itens = WishlistRepository.listar(user_id="daniel", status="comprado")
        assert len(itens) == 1
        assert itens[0]["status"] == "comprado"

    def test_remover_item_por_nome(self):
        adicionar_item_wishlist("Mouse Logitech MX Master")
        resposta = remover_item_wishlist(nome_produto="Mouse Logitech")
        assert "removido" in resposta.lower()
        assert len(WishlistRepository.listar(user_id="daniel")) == 0


class TestIsolamentoMultiUsuario:
    def test_isolamento_entre_daniel_e_lari(self):
        UserContext.set_user("daniel")
        adicionar_item_wishlist("Item Exclusivo Daniel")

        UserContext.set_user("lari")
        res_lari = consultar_wishlist()
        assert "Item Exclusivo Daniel" not in res_lari

        adicionar_item_wishlist("Item Exclusivo Lari")
        assert "Item Exclusivo Lari" in consultar_wishlist()

        UserContext.set_user("daniel")
        res_daniel = consultar_wishlist()
        assert "Item Exclusivo Daniel" in res_daniel
        assert "Item Exclusivo Lari" not in res_daniel
