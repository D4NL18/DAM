import pytest
from unittest.mock import patch, MagicMock
from repositories.address_repository import AddressRepository, normalize_alias
from services.tools.address_tool import (
    salvar_endereco,
    consultar_enderecos_salvos,
    remover_endereco
)
from services.tools.maps_tool import resolver_apelido_endereco, consultar_rota
from config.settings import settings


class TestSavedAddressesUnit:
    def setup_method(self):
        # Limpa o cache L1 em memória antes de cada teste
        AddressRepository._cache.clear()

    def test_normalize_alias(self):
        assert normalize_alias("Casa") == "casa"
        assert normalize_alias("minha casa") == "casa"
        assert normalize_alias("Residência") == "casa"
        assert normalize_alias("Trabalho") == "trabalho"
        assert normalize_alias("Meu Escritório") == "trabalho"
        assert normalize_alias("Firma") == "trabalho"
        assert normalize_alias("Academia Smart Fit") == "academia smart fit"
        assert normalize_alias("  CASA DA MÃE  ") == "casa da mãe"
        assert normalize_alias("") == ""

    @patch("repositories.address_repository.db")
    def test_save_and_get_address_with_firestore(self, mock_db):
        mock_doc = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc
        mock_doc.get.return_value.exists = True
        mock_doc.get.return_value.to_dict.return_value = {
            "user_jid": "5511999999999@s.whatsapp.net",
            "alias": "casa",
            "address": "Rua das Flores, 123",
            "formatted_address": "Rua das Flores, 123 - São Paulo, SP",
            "latitude": -23.55,
            "longitude": -46.63,
            "details": "Apto 42",
            "updated_at": "2026-09-04T08:00:00Z"
        }

        user_jid = "5511999999999@s.whatsapp.net"
        saved = AddressRepository.save_address(
            user_jid=user_jid,
            alias="casa",
            address="Rua das Flores, 123",
            formatted_address="Rua das Flores, 123 - São Paulo, SP",
            latitude=-23.55,
            longitude=-46.63,
            details="Apto 42"
        )
        assert saved["alias"] == "casa"
        assert saved["latitude"] == -23.55

        # Busca pelo cache ou banco
        recuperado = AddressRepository.get_address(user_jid, "casa")
        assert recuperado is not None
        assert recuperado["address"] == "Rua das Flores, 123"
        assert recuperado["details"] == "Apto 42"

    def test_multitenant_isolation(self):
        user1 = "5511111111111@s.whatsapp.net"
        user2 = "5522222222222@s.whatsapp.net"

        AddressRepository._cache[(user1, "casa")] = {
            "alias": "casa",
            "address": "Rua do Usuário Um, 100",
            "formatted_address": "Rua do Usuário Um, 100",
            "latitude": -23.1,
            "longitude": -46.1
        }
        AddressRepository._cache[(user2, "casa")] = {
            "alias": "casa",
            "address": "Avenida do Usuário Dois, 200",
            "formatted_address": "Avenida do Usuário Dois, 200",
            "latitude": -23.2,
            "longitude": -46.2
        }

        addr1 = AddressRepository.get_address(user1, "casa")
        addr2 = AddressRepository.get_address(user2, "casa")

        assert addr1["address"] == "Rua do Usuário Um, 100"
        assert addr2["address"] == "Avenida do Usuário Dois, 200"

    @patch("repositories.address_repository.db")
    def test_delete_address(self, mock_db):
        mock_doc = MagicMock()
        mock_doc.get.return_value.exists = False
        mock_db.collection.return_value.document.return_value = mock_doc
        user_jid = "5511999999999@s.whatsapp.net"
        AddressRepository._cache[(user_jid, "academia")] = {"alias": "academia", "address": "Av Paulista 500"}

        assert AddressRepository.delete_address(user_jid, "academia") is True
        assert AddressRepository.get_address(user_jid, "academia") is None

    @patch("services.tools.address_tool.geocodificar_endereco")
    @patch("repositories.address_repository.AddressRepository.save_address")
    def test_tool_salvar_endereco(self, mock_save, mock_geocode):
        mock_geocode.return_value = {
            "formatted_address": "Rua Augusta, 1000 - Consolação, São Paulo - SP",
            "latitude": -23.553,
            "longitude": -46.656
        }
        mock_save.return_value = {
            "alias": "academia",
            "address": "Rua Augusta 1000",
            "formatted_address": "Rua Augusta, 1000 - Consolação, São Paulo - SP",
            "latitude": -23.553,
            "longitude": -46.656,
            "details": "Unidade Augusta"
        }

        res = salvar_endereco(
            apelido="Academia",
            endereco="Rua Augusta 1000",
            detalhes="Unidade Augusta"
        )
        assert "Endereço 'academia' salvo com sucesso" in res
        assert "Rua Augusta, 1000" in res

    def test_tool_consultar_enderecos_salvos_vazio(self):
        with patch("repositories.address_repository.AddressRepository.list_addresses", return_value=[]):
            res = consultar_enderecos_salvos()
            assert "Nenhum endereço salvo encontrado" in res

    def test_tool_consultar_enderecos_salvos_com_dados(self):
        mock_list = [
            {
                "alias": "casa",
                "address": "Rua Verde, 10",
                "formatted_address": "Rua Verde, 10 - SP",
                "details": "Casa de portão azul"
            },
            {
                "alias": "trabalho",
                "address": "Av Faria Lima, 1000",
                "formatted_address": "Av Faria Lima, 1000 - SP",
                "details": ""
            }
        ]
        with patch("repositories.address_repository.AddressRepository.list_addresses", return_value=mock_list):
            res = consultar_enderecos_salvos()
            assert "Endereços Salvos" in res
            assert "Casa" in res or "casa" in res.lower()
            assert "Trabalho" in res or "trabalho" in res.lower()

    def test_tool_remover_endereco(self):
        with patch("repositories.address_repository.AddressRepository.delete_address", return_value=True):
            res = remover_endereco("academia")
            assert "removido com sucesso" in res

    def test_resolver_apelido_endereco_com_firestore(self):
        user_jid = settings.ALLOWED_PHONE_NUMBER
        AddressRepository._cache[(user_jid, "casa")] = {
            "alias": "casa",
            "address": "Rua das Palmeiras, 999 - Bairro Nobre, Salvador - BA",
            "formatted_address": "Rua das Palmeiras, 999 - Bairro Nobre, Salvador - BA",
            "latitude": -12.97,
            "longitude": -38.51
        }
        # Resolve 'casa' priorizando o endereço salvo no banco
        resolvido = resolver_apelido_endereco("casa", user_jid=user_jid)
        assert resolvido == "Rua das Palmeiras, 999 - Bairro Nobre, Salvador - BA"

    def test_resolver_apelido_endereco_fallback_settings(self):
        # Quando não existe no banco, resolve via fallback configurado
        resolvido = resolver_apelido_endereco("trabalho", user_jid="novo_usuario")
        assert "Faria Lima" in resolvido or resolvido == settings.USER_WORK_ADDRESS

    @patch("services.tools.maps_tool.obter_dados_rota")
    def test_consultar_rota_usando_apelidos_salvos(self, mock_rota):
        mock_rota.return_value = {
            "origem": "Rua das Flores, 123",
            "destino": "Av Faria Lima, 3500",
            "modo": "de carro",
            "distancia_km": 10.5,
            "distancia_texto": "10.5 km",
            "duracao_minutos": 25,
            "duracao_texto": "25 mins",
            "vias_principais": "Av. Rebouças",
            "condicao_transito": "Trânsito fluido",
            "simulado": False
        }
        res = consultar_rota("casa", "trabalho")
        assert "Rota e Trânsito" in res or "25 mins" in res

