import unittest
from unittest.mock import patch, MagicMock
from services.tools.trip_ledger_tool import (
    criar_grupo_viagem,
    adicionar_despesa_viagem,
    calcular_fechamento_viagem,
    _limpar_dados_memoria
)
from config import firebase

class TestFase18TripLedger(unittest.TestCase):

    def setUp(self):
        _limpar_dados_memoria()
        self.orig_db = firebase.db
        firebase.db = None  # Garante modo fallback em memória por padrão

    def tearDown(self):
        firebase.db = self.orig_db
        _limpar_dados_memoria()

    def test_criar_grupo_viagem_sucesso(self):
        resultado = criar_grupo_viagem("Floripa 2026", ["Alice", "Bob", "Carlos"])
        self.assertIn("Grupo de Viagem Criado com Sucesso", resultado)
        self.assertIn("Floripa 2026", resultado)
        self.assertIn("Alice", resultado)
        self.assertIn("Bob", resultado)
        self.assertIn("Carlos", resultado)

    def test_criar_grupo_viagem_validacoes(self):
        # Nome vazio
        res_vazio = criar_grupo_viagem("", ["Alice", "Bob"])
        self.assertIn("Erro: O nome da viagem não pode ser vazio", res_vazio)

        # Menos de 2 participantes
        res_um = criar_grupo_viagem("Praia", ["Alice"])
        self.assertIn("Erro: O grupo deve conter pelo menos 2 participantes", res_um)

    def test_adicionar_despesa_grupo_inexistente(self):
        resultado = adicionar_despesa_viagem("Viagem Fantasma", "Gasolina", 150.0, "Alice")
        self.assertIn("não foi encontrado", resultado)

    def test_adicionar_despesa_valor_invalido(self):
        criar_grupo_viagem("Campos do Jordão", ["Alice", "Bob"])
        res_zero = adicionar_despesa_viagem("Campos do Jordão", "Lanche", 0, "Alice")
        self.assertIn("Erro: O valor da despesa deve ser maior que zero", res_zero)

        res_neg = adicionar_despesa_viagem("Campos do Jordão", "Lanche", -10.5, "Alice")
        self.assertIn("Erro: O valor da despesa deve ser maior que zero", res_neg)

    def test_adicionar_despesa_divisao_automatica_todos(self):
        criar_grupo_viagem("Rio 2026", ["Alice", "Bob", "Carlos"])
        res = adicionar_despesa_viagem("Rio 2026", "Airbnb", 300.0, "Alice")
        self.assertIn("Despesa Registrada", res)
        self.assertIn("R$ 300.00", res)
        self.assertIn("Dividido entre (3)", res)
        self.assertIn("100.00 cada", res)

    def test_adicionar_despesa_divisao_parcial(self):
        criar_grupo_viagem("Rio 2026", ["Alice", "Bob", "Carlos"])
        res = adicionar_despesa_viagem("Rio 2026", "Uber", 40.0, "Bob", ["Bob", "Carlos"])
        self.assertIn("Despesa Registrada", res)
        self.assertIn("R$ 40.00", res)
        self.assertIn("Dividido entre (2)", res)
        self.assertIn("20.00 cada", res)

    def test_calcular_fechamento_viagem_sem_despesas(self):
        criar_grupo_viagem("Ubatuba", ["Alice", "Bob"])
        res = calcular_fechamento_viagem("Ubatuba")
        self.assertIn("Nenhuma despesa encontrada", res)

    def test_calcular_fechamento_viagem_debt_minimization(self):
        """
        Cenário:
        Alice paga 90.00 para [Alice, Bob, Carlos] (30 cada).
        Bob paga 60.00 para [Bob, Carlos] (30 cada).
        Saldos líquidos:
        Alice: +60.00
        Bob: 0.00
        Carlos: -60.00
        Debt minimization: Carlos paga R$ 60.00 para Alice. Bob não faz transações!
        """
        criar_grupo_viagem("Serra Gaúcha", ["Alice", "Bob", "Carlos"])
        adicionar_despesa_viagem("Serra Gaúcha", "Jantar", 90.0, "Alice", ["Alice", "Bob", "Carlos"])
        adicionar_despesa_viagem("Serra Gaúcha", "Translado", 60.0, "Bob", ["Bob", "Carlos"])

        fechamento = calcular_fechamento_viagem("Serra Gaúcha", chave_pix="alice@pix.com")

        self.assertIn("150.00", fechamento)
        self.assertIn("Carlos", fechamento)
        self.assertIn("Alice", fechamento)
        self.assertIn("-R$ 60.00", fechamento)
        self.assertIn("+R$ 60.00", fechamento)
        # Menor número de transferências: exatamente 1 liquidação
        self.assertIn("Carlos** deve pagar **R$ 60.00** para **Alice", fechamento)
        self.assertNotIn("Bob** deve pagar", fechamento)
        # Chave Pix
        self.assertIn("alice@pix.com", fechamento)

    def test_calcular_fechamento_viagem_contas_quitadas(self):
        criar_grupo_viagem("Recife", ["Alice", "Bob"])
        adicionar_despesa_viagem("Recife", "Café Alice", 50.0, "Alice", ["Bob"])
        adicionar_despesa_viagem("Recife", "Café Bob", 50.0, "Bob", ["Alice"])

        fechamento = calcular_fechamento_viagem("Recife")
        self.assertIn("perfeitamente quitadas", fechamento)

    def test_com_firestore_mock(self):
        mock_db = MagicMock()
        firebase.db = mock_db

        # Mock collection trip_groups
        mock_groups_col = MagicMock()
        mock_expenses_col = MagicMock()
        def mock_collection(name):
            if name == "trip_groups":
                return mock_groups_col
            return mock_expenses_col
        mock_db.collection.side_effect = mock_collection

        # Criar grupo
        res_grupo = criar_grupo_viagem("Gramado", ["Alice", "Bob"])
        self.assertIn("Gramado", res_grupo)
        mock_groups_col.document.assert_called_with("gramado")

        # Adicionar despesa
        res_despesa = adicionar_despesa_viagem("Gramado", "Chocolate", 80.0, "Alice")
        self.assertIn("Despesa Registrada", res_despesa)
        mock_expenses_col.add.assert_called_once()

if __name__ == "__main__":
    unittest.main()
