import unittest
from unittest.mock import MagicMock
from services.tools.work_hours_tool import (
    interpretar_horas,
    calcular_saldo_jornada,
    calcular_fechamento_semanal,
    registrar_ponto_dia,
    _limpar_dados_memoria
)
from config import firebase

class TestFase19WorkHours(unittest.TestCase):

    def setUp(self):
        _limpar_dados_memoria()
        self.orig_db = firebase.db
        firebase.db = None  # Garante fallback em memória

    def tearDown(self):
        firebase.db = self.orig_db
        _limpar_dados_memoria()

    def test_interpretar_horas_diversos_formatos(self):
        # Casos explícitos da especificação
        self.assertEqual(interpretar_horas("8h"), 8.0)
        self.assertEqual(interpretar_horas("7h30"), 7.5)
        self.assertEqual(interpretar_horas("9h15"), 9.25)
        self.assertEqual(interpretar_horas("8.5h"), 8.5)
        self.assertEqual(interpretar_horas("8,5h"), 8.5)
        self.assertEqual(interpretar_horas("8.5"), 8.5)
        self.assertEqual(interpretar_horas("8,5"), 8.5)
        self.assertEqual(interpretar_horas("7h30min"), 7.5)
        self.assertEqual(interpretar_horas("7:30"), 7.5)

        # Minutos isolados
        self.assertEqual(interpretar_horas("45m"), 0.75)
        self.assertEqual(interpretar_horas("30min"), 0.5)

        # Batidas de ponto como lista
        batidas_lista = ["09:00", "12:00", "13:00", "18:00"]
        self.assertEqual(interpretar_horas(batidas_lista), 8.0)

        # Batidas de ponto como string
        self.assertEqual(interpretar_horas("09:00, 12:00, 13:00, 18:00"), 8.0)
        self.assertEqual(interpretar_horas("09:00 - 12:00, 13:00 - 18:00"), 8.0)

    def test_interpretar_horas_formato_invalido(self):
        with self.assertRaises(ValueError):
            interpretar_horas("texto_qualquer")

    def test_calcular_saldo_jornada_credito(self):
        resultado = calcular_saldo_jornada("9h15", meta_diaria_horas=8.0)
        self.assertIn("Horas Trabalhadas: **9h15min**", resultado)
        self.assertIn("Meta Diária: **8h00**", resultado)
        self.assertIn("+1h15min", resultado)
        self.assertIn("Crédito", resultado)

    def test_calcular_saldo_jornada_debito(self):
        resultado = calcular_saldo_jornada("7h30", meta_diaria_horas=8.0)
        self.assertIn("Horas Trabalhadas: **7h30min**", resultado)
        self.assertIn("-0h30min", resultado)
        self.assertIn("Débito", resultado)

    def test_calcular_saldo_jornada_exata(self):
        resultado = calcular_saldo_jornada("8h", meta_diaria_horas=8.0)
        self.assertIn("Horas Trabalhadas: **8h00**", resultado)
        self.assertIn("0h00", resultado)
        self.assertIn("Meta cumprida exatamente", resultado)

    def test_calcular_saldo_jornada_batidas(self):
        resultado = calcular_saldo_jornada("08:00, 12:00, 13:00, 17:00", meta_diaria_horas=8.0)
        self.assertIn("Horas Trabalhadas: **8h00**", resultado)
        self.assertIn("0h00", resultado)

    def test_calcular_fechamento_semanal_positivo(self):
        dias = [
            {"dia": "Segunda-feira", "horas": "8h30"},
            {"dia": "Terça-feira", "horas": "8h"},
            {"dia": "Quarta-feira", "horas": "9h"},
            {"dia": "Quinta-feira", "horas": "7h30"},
            {"dia": "Sexta-feira", "horas": "8h"}
        ]
        # Total: 8.5 + 8.0 + 9.0 + 7.5 + 8.0 = 41.0h (+1h saldo sobre 40h)
        fechamento = calcular_fechamento_semanal(dias, meta_semanal_horas=40.0)
        self.assertIn("Fechamento Semanal de Banco de Horas", fechamento)
        self.assertIn("Total Acumulado:** **41h00**", fechamento)
        self.assertIn("Meta Semanal:** **40h00**", fechamento)
        self.assertIn("+1h00", fechamento)
        self.assertIn("Crédito positivo", fechamento)

    def test_calcular_fechamento_semanal_devedor(self):
        dias = [
            {"dia": "Segunda-feira", "horas": "7h30"},
            {"dia": "Terça-feira", "horas": "7h30"},
            {"dia": "Quarta-feira", "horas": "7h30"},
            {"dia": "Quinta-feira", "horas": "7h30"},
            {"dia": "Sexta-feira", "horas": "7h30"}
        ]
        # Total: 5 * 7.5 = 37.5h (-2h30min devedor sobre 40h)
        fechamento = calcular_fechamento_semanal(dias, meta_semanal_horas=40.0)
        self.assertIn("Total Acumulado:** **37h30min**", fechamento)
        self.assertIn("-2h30min", fechamento)
        self.assertIn("Saldo devedor negativo", fechamento)

    def test_calcular_fechamento_semanal_vazio(self):
        res = calcular_fechamento_semanal([])
        self.assertIn("Erro: Nenhum registro diário", res)

    def test_registrar_ponto_dia_memoria(self):
        resultado = registrar_ponto_dia("2026-09-03", "8h30", meta_diaria_horas=8.0, descricao="Home office")
        self.assertIn("Ponto Registrado com Sucesso", resultado)
        self.assertIn("2026-09-03", resultado)
        self.assertIn("8h30min", resultado)
        self.assertIn("+0h30min", resultado)
        self.assertIn("Home office", resultado)

    def test_registrar_ponto_dia_firestore_mock(self):
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        firebase.db = mock_db

        resultado = registrar_ponto_dia("2026-09-04", ["09:00", "12:00", "13:00", "18:00"], meta_diaria_horas=8.0)
        self.assertIn("Ponto Registrado com Sucesso", resultado)
        self.assertIn("2026-09-04", resultado)
        self.assertIn("8h00", resultado)
        mock_db.collection.assert_called_with("work_hours")
        mock_col.add.assert_called_once()

if __name__ == "__main__":
    unittest.main()
