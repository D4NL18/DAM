import unittest
from unittest.mock import patch, MagicMock
from services.tools.finance_tool import registrar_gasto, normalizar_metodo_pagamento

class TestFinanceCards(unittest.TestCase):

    def test_normalizar_cartao_secundario(self):
        self.assertEqual(normalizar_metodo_pagamento("cartao secundario"), "Cartão de Crédito Secundário")
        self.assertEqual(normalizar_metodo_pagamento("compartilhado"), "Cartão de Crédito Secundário")
        self.assertEqual(normalizar_metodo_pagamento("familiar"), "Cartão de Crédito Secundário")

    def test_normalizar_credito_pessoal(self):
        self.assertEqual(normalizar_metodo_pagamento("meu cartao de credito"), "Cartão de Crédito Pessoal")
        self.assertEqual(normalizar_metodo_pagamento("crédito pessoal"), "Cartão de Crédito Pessoal")

    def test_normalizar_debito_e_pix(self):
        self.assertEqual(normalizar_metodo_pagamento("meu cartao de debito"), "Cartão de Débito")
        self.assertEqual(normalizar_metodo_pagamento("débito"), "Cartão de Débito")
        self.assertEqual(normalizar_metodo_pagamento("pix"), "Cartão de Débito")
        self.assertEqual(normalizar_metodo_pagamento("PIX"), "Cartão de Débito")

    def test_normalizar_metodo_invalido(self):
        self.assertIsNone(normalizar_metodo_pagamento("em dinheiro vivo"))
        self.assertIsNone(normalizar_metodo_pagamento("cheque"))

    @patch("services.tools.finance_tool.firebase.db")
    def test_registrar_gasto_com_cartao_secundario(self, mock_db):
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection

        resultado = registrar_gasto(
            descricao="Almoço",
            valor=85.0,
            categoria="Alimentação",
            metodo_pagamento="cartao secundario"
        )
        self.assertIn("Sucesso!", resultado)
        self.assertIn("Cartão de Crédito Secundário", resultado)
        mock_collection.add.assert_called_once()
        salvo = mock_collection.add.call_args[0][0]
        self.assertEqual(salvo["payment_method"], "Cartão de Crédito Secundário")

    @patch("services.tools.finance_tool.firebase.db")
    def test_registrar_gasto_com_pix_grava_debito(self, mock_db):
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection

        resultado = registrar_gasto(
            descricao="Corte de cabelo",
            valor=60.0,
            categoria="Serviços",
            metodo_pagamento="Pix"
        )
        self.assertIn("Sucesso!", resultado)
        self.assertIn("Cartão de Débito", resultado)
        salvo = mock_collection.add.call_args[0][0]
        self.assertEqual(salvo["payment_method"], "Cartão de Débito")

    @patch("services.tools.finance_tool.firebase.db")
    def test_registrar_gasto_sem_metodo_valido(self, mock_db):
        resultado = registrar_gasto(
            descricao="Café",
            valor=12.0,
            categoria="Alimentação",
            metodo_pagamento="em moedas"
        )
        self.assertIn("Método de pagamento não identificado", resultado)
        self.assertIn("Cartão de crédito secundário", resultado)
        mock_db.collection.assert_not_called()

if __name__ == "__main__":
    unittest.main()
