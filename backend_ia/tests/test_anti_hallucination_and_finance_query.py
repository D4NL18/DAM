import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from services.prompts.system_base import get_system_base_prompt
from services.prompts.financial_rules import get_financial_prompt
from services.tools_dispatcher import ToolsDispatcher

class TestAntiHallucinationAndFinanceQuery(unittest.TestCase):

    def _criar_mock_doc(self, descricao, valor, categoria, metodo, dt_str, tx_type="expense_variable", user_id="daniel"):
        doc = MagicMock()
        doc.to_dict.return_value = {
            "description": descricao,
            "amount": valor,
            "category": categoria,
            "payment_method": metodo,
            "date": dt_str,
            "type": tx_type,
            "userId": user_id,
            "user_id": user_id
        }
        return doc

    def test_system_base_prompt_anti_hallucination(self):
        """P-0801: Valida que o prompt base possui salvaguarda mandatória anti-alucinação."""
        prompt = get_system_base_prompt("2026-10-15 10:00")
        prompt_lower = prompt.lower()
        self.assertIn("never invent", prompt_lower)
        self.assertTrue(
            "fictional" in prompt_lower or "hallucinat" in prompt_lower or "inventar" in prompt_lower or "simulate" in prompt_lower
        )
        self.assertIn("database", prompt_lower)

    def test_financial_prompt_anti_hallucination_and_category_guidance(self):
        """P-0801: Valida regras financeiras com orientação de factualidade e filtro por categoria."""
        prompt = get_financial_prompt()
        prompt_lower = prompt.lower()
        self.assertIn("consultar_resumo_gastos", prompt)
        self.assertTrue("never invent" in prompt_lower or "strictly" in prompt_lower or "nunca invente" in prompt_lower)
        self.assertIn("categoria", prompt_lower)

    def test_tools_dispatcher_finance_intent_coverage(self):
        """P-0802: Valida que o ToolsDispatcher reconhece variações naturais de consultas financeiras."""
        exemplos = [
            "Faça um resumo dos valores de gastos por categoria em setembro",
            "Quais gastos entraram como moradia?",
            "Quanto gastei em alimentação em setembro de 2026?",
            "Resumo dos gastos do mês",
            "Quais foram meus gastos com lazer?",
            "O que gastei esse mês no cartão?",
            "Faça um resumo de gastos por categoria",
            "Quais despesas tive com mercado?"
        ]
        for frase in exemplos:
            dominios = ToolsDispatcher.detect_domains(frase)
            self.assertIn(
                "finance",
                dominios,
                f"Falha ao detectar domínio finance para a frase: '{frase}'"
            )

    @patch("services.tools.finance_tool.firebase.db")
    def test_consultar_resumo_gastos_com_categoria_especifica(self, mock_db):
        """P-0803: Valida consulta com detalhamento por categoria (ex: Moradia/Casa)."""
        from services.tools.finance_tool import consultar_resumo_gastos
        from services.user_context import UserContext

        UserContext.set_user("daniel")

        docs = [
            self._criar_mock_doc("Aluguel", 1200.0, "Casa", "Cartão de Débito", "2026-09-05T10:00:00Z"),
            self._criar_mock_doc("Conta de Luz", 180.0, "Moradia", "Cartão de Débito", "2026-09-10T10:00:00Z"),
            self._criar_mock_doc("Supermercado", 500.0, "Alimentação", "Cartão de Crédito Pessoal", "2026-09-12T10:00:00Z"),
        ]

        mock_db.collection.return_value.stream.return_value = docs

        # Consulta especificando categoria 'moradia'
        resultado = consultar_resumo_gastos(mes=9, ano=2026, categoria="moradia")

        self.assertIn("1.380,00", resultado)  # 1200 + 180 = 1380
        self.assertIn("Aluguel", resultado)
        self.assertIn("Conta de Luz", resultado)
        self.assertNotIn("Supermercado", resultado)  # Categoria diferente não pode aparecer
        self.assertIn("Setembro/2026", resultado)

    @patch("services.tools.finance_tool.firebase.db")
    def test_consultar_resumo_gastos_categoria_vazia_sem_alucinacao(self, mock_db):
        """P-0801 e P-0803: Valida que categoria sem gastos retorna mensagem factual sem inventar dados."""
        from services.tools.finance_tool import consultar_resumo_gastos
        from services.user_context import UserContext

        UserContext.set_user("daniel")

        docs = [
            self._criar_mock_doc("Supermercado", 500.0, "Alimentação", "Cartão de Crédito Pessoal", "2026-09-12T10:00:00Z"),
        ]

        mock_db.collection.return_value.stream.return_value = docs

        resultado = consultar_resumo_gastos(mes=9, ano=2026, categoria="Saúde")
        self.assertIn("Não encontrei registros de gastos", resultado)
        self.assertIn("Saúde", resultado)
        self.assertIn("Setembro/2026", resultado)
        self.assertNotIn("R$", resultado)  # Não deve inventar valores numéricos

    @patch("services.tools.finance_tool.firebase.db")
    def test_consultar_resumo_gastos_macro_dashboard(self, mock_db):
        """P-0803: Valida resumo macro agrupado por categorias e cartões idêntico ao dashboard."""
        from services.tools.finance_tool import consultar_resumo_gastos
        from services.user_context import UserContext

        UserContext.set_user("daniel")

        docs = [
            self._criar_mock_doc("Supermercado", 600.0, "Mercado", "Cartão de Crédito Pessoal", "2026-09-02T10:00:00Z"),
            self._criar_mock_doc("Combustível", 200.0, "Carro", "Cartão de Débito", "2026-09-15T10:00:00Z"),
            self._criar_mock_doc("Salário", 10000.0, "Receitas", "Cartão de Débito", "2026-09-05T10:00:00Z", tx_type="income"),
        ]

        mock_db.collection.return_value.stream.return_value = docs

        resultado = consultar_resumo_gastos(mes=9, ano=2026)

        # Total deve ser 800 (600 + 200) e NÃO incluir os 10.000 de receita
        self.assertIn("800,00", resultado)
        self.assertNotIn("10.800,00", resultado)
        self.assertIn("Mercado", resultado)
        self.assertIn("Carro", resultado)
        self.assertIn("Por Categoria:", resultado)
        self.assertIn("Por Cartão / Forma de Pagamento:", resultado)

    @patch("services.tools.finance_tool.firebase.db")
    def test_consultar_resumo_gastos_periodo_vazio(self, mock_db):
        """P-0801: Valida período sem gastos nenhum no banco de dados."""
        from services.tools.finance_tool import consultar_resumo_gastos
        from services.user_context import UserContext

        UserContext.set_user("daniel")

        mock_db.collection.return_value.stream.return_value = []

        resultado = consultar_resumo_gastos(mes=9, ano=2026)
        self.assertIn("Não encontrei registros de gastos", resultado)
        self.assertIn("Setembro/2026", resultado)
        self.assertNotIn("R$", resultado)

    @patch("services.tools.finance_tool.firebase.db")
    def test_consultar_resumo_gastos_isolamento_usuario(self, mock_db):
        """P-0803: Valida que gastos de outros usuários são estritamente isolados."""
        from services.tools.finance_tool import consultar_resumo_gastos
        from services.user_context import UserContext

        UserContext.set_user("daniel")

        docs = [
            self._criar_mock_doc("Gasto Daniel", 150.0, "Lazer", "Cartão de Crédito Pessoal", "2026-09-02T10:00:00Z", user_id="daniel"),
            self._criar_mock_doc("Gasto Outro Usuário", 999.0, "Lazer", "Cartão de Crédito Pessoal", "2026-09-02T10:00:00Z", user_id="outro_user"),
        ]

        mock_db.collection.return_value.stream.return_value = docs

        resultado = consultar_resumo_gastos(mes=9, ano=2026)
        self.assertIn("150,00", resultado)
        self.assertNotIn("999,00", resultado)
        self.assertNotIn("1.149,00", resultado)

if __name__ == "__main__":
    unittest.main()
