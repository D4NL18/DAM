import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta
from services.prompts.financial_rules import get_financial_prompt

class TestFinanceSummary(unittest.TestCase):

    def _criar_mock_doc(self, descricao, valor, categoria, metodo, dt):
        doc = MagicMock()
        doc.to_dict.return_value = {
            "description": descricao,
            "amount": valor,
            "category": categoria,
            "payment_method": metodo,
            "timestamp": dt,
            "date": dt.isoformat()
        }
        return doc

    @patch("services.tools.finance_tool.firebase.db")
    def test_resumo_gastos_com_dados_mensais(self, mock_db):
        from services.tools.finance_tool import consultar_resumo_gastos
        
        agora = datetime.now(timezone.utc)
        docs = [
            self._criar_mock_doc("Supermercado", 300.0, "Alimentação", "Cartão de Crédito Pessoal", agora),
            self._criar_mock_doc("Restaurante", 150.0, "Alimentação", "Cartão de Crédito Secundário", agora),
            self._criar_mock_doc("Uber", 50.0, "Transporte", "Cartão de Débito", agora),
            self._criar_mock_doc("Farmácia", 100.0, "Saúde", "Cartão de Crédito Pessoal", agora),
        ]
        
        mock_collection = MagicMock()
        mock_collection.where.return_value.where.return_value.stream.return_value = docs
        mock_db.collection.return_value = mock_collection

        resultado = consultar_resumo_gastos(mes=agora.month, ano=agora.year)

        # Validações
        self.assertIn("Resumo Financeiro", resultado)
        self.assertIn("Total Geral:", resultado)
        self.assertIn("600,00", resultado)  # 300 + 150 + 50 + 100 = 600
        self.assertIn("4 lançamentos", resultado)

        # Cartões
        self.assertIn("Cartão de Crédito Pessoal", resultado)
        self.assertIn("400,00", resultado)  # 300 + 100
        self.assertIn("Cartão de Crédito Secundário", resultado)
        self.assertIn("150,00", resultado)
        self.assertIn("Cartão de Débito", resultado)
        self.assertIn("50,00", resultado)

        # Categorias
        self.assertIn("Alimentação", resultado)
        self.assertIn("450,00", resultado)  # 300 + 150
        self.assertIn("Saúde", resultado)
        self.assertIn("Transporte", resultado)

        # Maiores compras
        self.assertIn("Supermercado", resultado)

    @patch("services.tools.finance_tool.firebase.db")
    def test_resumo_gastos_sem_dados(self, mock_db):
        from services.tools.finance_tool import consultar_resumo_gastos
        
        mock_collection = MagicMock()
        mock_collection.where.return_value.where.return_value.stream.return_value = []
        mock_db.collection.return_value = mock_collection

        resultado = consultar_resumo_gastos(mes=1, ano=2026)
        self.assertIn("Não encontrei registros de gastos", resultado)

    @patch("services.tools.finance_tool.firebase.db", None)
    def test_resumo_gastos_db_indisponivel(self):
        from services.tools.finance_tool import consultar_resumo_gastos
        
        resultado = consultar_resumo_gastos()
        self.assertIn("Erro: O banco de dados não está disponível", resultado)

    @patch("services.tools.finance_tool.firebase.db")
    def test_resumo_gastos_filtro_dias_retroativos(self, mock_db):
        from services.tools.finance_tool import consultar_resumo_gastos
        
        agora = datetime.now(timezone.utc)
        docs = [
            self._criar_mock_doc("Padaria", 25.0, "Alimentação", "Cartão de Débito", agora),
        ]
        
        mock_collection = MagicMock()
        mock_collection.where.return_value.stream.return_value = docs
        mock_db.collection.return_value = mock_collection

        resultado = consultar_resumo_gastos(dias_retroativos=7)
        self.assertIn("últimos 7 dias", resultado)
        self.assertIn("25,00", resultado)

    def test_prompt_financeiro_inclui_consultar_resumo_gastos(self):
        prompt = get_financial_prompt()
        self.assertIn("consultar_resumo_gastos", prompt)
        self.assertIn("resumo", prompt.lower())

if __name__ == "__main__":
    unittest.main()
