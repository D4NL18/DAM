import unittest
from unittest.mock import MagicMock, patch
from services.tools.item_finder_tool import (
    registrar_localizacao_objeto,
    onde_guardei_objeto,
    listar_historico_movimentacoes,
    _reset_memory,
    _in_memory_items
)
from config import firebase

class TestFase12ItemFinder(unittest.TestCase):

    def setUp(self):
        _reset_memory()
        self.orig_db = firebase.db
        firebase.db = None  # Garante modo em memória por padrão nos testes base

    def tearDown(self):
        _reset_memory()
        firebase.db = self.orig_db

    def test_registrar_localizacao_objeto_sucesso_memoria(self):
        resultado = registrar_localizacao_objeto(
            objeto="Passaporte",
            local="Segunda gaveta da cômoda do quarto",
            categoria="Documentos",
            detalhes="Dentro da pasta azul com o visto americano"
        )
        self.assertIn("Passaporte", resultado)
        self.assertIn("registrada com sucesso", resultado)
        self.assertIn("Segunda gaveta", resultado)
        self.assertIn("Documentos", resultado)
        self.assertIn("pasta azul", resultado)

    def test_registrar_localizacao_validacao_campos_vazios(self):
        resp1 = registrar_localizacao_objeto(objeto="", local="Gaveta")
        self.assertIn("informe o nome do objeto", resp1)

        resp2 = registrar_localizacao_objeto(objeto="Chave", local="")
        self.assertIn("informe onde o objeto foi guardado", resp2)

    def test_onde_guardei_objeto_encontrado_e_nao_encontrado(self):
        registrar_localizacao_objeto("Óculos de Sol", "Porta-luvas do carro", categoria="Acessórios")
        
        # Busca exata
        resp_encontrado = onde_guardei_objeto("Óculos de Sol")
        self.assertIn("Óculos de Sol", resp_encontrado)
        self.assertIn("Porta-luvas do carro", resp_encontrado)
        self.assertIn("Acessórios", resp_encontrado)

        # Busca insensível a maiúsculas/minúsculas
        resp_case = onde_guardei_objeto("óculos de sol")
        self.assertIn("Porta-luvas do carro", resp_case)

        # Busca por palavra-chave parcial
        resp_parcial = onde_guardei_objeto("óculos")
        self.assertIn("Porta-luvas do carro", resp_parcial)

        # Objeto inexistente
        resp_inexistente = onde_guardei_objeto("Guarda-chuva invisível")
        self.assertIn("Não encontrei nenhum registro", resp_inexistente)

        # Termo vazio
        resp_vazio = onde_guardei_objeto("")
        self.assertIn("especifique o objeto", resp_vazio)

    def test_atualizacao_de_local_e_historico_movimentacoes(self):
        # 1º Registro
        registrar_localizacao_objeto("Chave Reserva Fiat", "Gabinete da sala", detalhes="Chaveiro vermelho")
        
        # Histórico inicial sem movimentações anteriores
        hist_inicial = listar_historico_movimentacoes("Chave Reserva Fiat")
        self.assertIn("Gabinete da sala", hist_inicial)
        self.assertIn("Não possui movimentações anteriores", hist_inicial)

        # 2º Registro (objeto movido)
        registrar_localizacao_objeto("Chave Reserva Fiat", "Gaveta da mesa do escritório", detalhes="Junto com os pen drives")
        
        # 3º Registro (objeto movido novamente)
        registrar_localizacao_objeto("Chave Reserva Fiat", "Chaveiro da entrada")

        # Verifica histórico completo
        hist_completo = listar_historico_movimentacoes("Chave Reserva Fiat")
        self.assertIn("Local Atual**: Chaveiro da entrada", hist_completo)
        self.assertIn("Gaveta da mesa do escritório", hist_completo)
        self.assertIn("Gabinete da sala", hist_completo)

    def test_listar_historico_objeto_inexistente_ou_vazio(self):
        resp = listar_historico_movimentacoes("Item Desconhecido 404")
        self.assertIn("Não encontrei nenhum registro", resp)

        resp_vazio = listar_historico_movimentacoes("")
        self.assertIn("especifique o objeto", resp_vazio)

    def test_integracao_firestore_mock(self):
        """Valida que quando firebase.db estiver ativo, as chamadas utilizam Firestore."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_snap = MagicMock()

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref
        
        # Cenário: Documento ainda não existe
        mock_snap.exists = False
        mock_doc_ref.get.return_value = mock_snap

        firebase.db = mock_db

        resultado = registrar_localizacao_objeto("Kindle", "Mochila de viagem", categoria="Eletrônicos")
        self.assertIn("registrada com sucesso", resultado)
        mock_collection.document.assert_called_with("kindle")
        mock_doc_ref.set.assert_called_once()
        
        saved_data = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(saved_data["objeto"], "Kindle")
        self.assertEqual(saved_data["local_atual"], "Mochila de viagem")
        self.assertEqual(saved_data["categoria"], "Eletrônicos")

        # Teste onde_guardei com documento existente no mock
        mock_snap.exists = True
        mock_snap.to_dict.return_value = {
            "objeto": "Kindle",
            "local_atual": "Mochila de viagem",
            "categoria": "Eletrônicos",
            "detalhes": "Capa preta",
            "atualizado_em": "2026-09-03T15:00:00+00:00"
        }
        resp_onde = onde_guardei_objeto("Kindle")
        self.assertIn("Mochila de viagem", resp_onde)
        self.assertIn("Capa preta", resp_onde)

if __name__ == "__main__":
    unittest.main()
