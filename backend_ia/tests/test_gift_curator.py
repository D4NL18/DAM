import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
from services.tools.gift_curator_tool import (
    salvar_ideia_presente,
    consultar_ideias_presente,
    alertar_datas_proximas,
    _reset_mock_gift_db,
    _MOCK_GIFT_IDEAS
)
from config import firebase

class TestFase10Gifts(unittest.TestCase):
    def setUp(self):
        _reset_mock_gift_db()
        self.original_db = firebase.db
        firebase.db = None

    def tearDown(self):
        _reset_mock_gift_db()
        firebase.db = self.original_db

    def test_salvar_ideia_presente_fallback_memoria(self):
        resultado = salvar_ideia_presente(
            pessoa="Mariana",
            relacao="namorada",
            ideia="Kindle Paperwhite",
            data_especial="2026-10-12",
            tags=["tecnologia", "leitura"]
        )
        self.assertIn("Mariana", resultado)
        self.assertIn("namorada", resultado)
        self.assertIn("Kindle Paperwhite", resultado)
        self.assertIn("2026-10-12", resultado)
        self.assertIn("tecnologia", resultado)
        self.assertEqual(len(_MOCK_GIFT_IDEAS), 1)
        self.assertEqual(_MOCK_GIFT_IDEAS[0]["pessoa"], "Mariana")

    def test_salvar_ideia_presente_validacao_campos_obrigatorios(self):
        res1 = salvar_ideia_presente(pessoa="", relacao="amigo", ideia="Camisa")
        self.assertIn("informe o nome da pessoa", res1)

        res2 = salvar_ideia_presente(pessoa="Carlos", relacao="amigo", ideia="")
        self.assertIn("descreva a ideia", res2)

    def test_salvar_ideia_presente_com_firestore_conectado(self):
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection
        firebase.db = mock_db

        resultado = salvar_ideia_presente(
            pessoa="Mãe",
            relacao="mãe",
            ideia="Bolsa de Couro",
            data_especial="10/05/2026",
            tags=["moda", "aniversário"]
        )
        self.assertIn("Bolsa de Couro", resultado)
        mock_db.collection.assert_called_with("gift_ideas")
        mock_collection.add.assert_called_once()
        saved_dict = mock_collection.add.call_args[0][0]
        self.assertEqual(saved_dict["pessoa"], "Mãe")
        self.assertEqual(saved_dict["ideia"], "Bolsa de Couro")

    def test_salvar_ideia_presente_firestore_exception_usa_fallback(self):
        mock_db = MagicMock()
        mock_db.collection.side_effect = Exception("Firestore offline timeout")
        firebase.db = mock_db

        resultado = salvar_ideia_presente(
            pessoa="Lucas",
            relacao="amigo",
            ideia="Jogo de Tabuleiro Catan"
        )
        self.assertIn("Jogo de Tabuleiro Catan", resultado)
        self.assertEqual(len(_MOCK_GIFT_IDEAS), 1)

    def test_consultar_ideias_sem_registros(self):
        resultado = consultar_ideias_presente()
        self.assertIn("Nenhuma ideia de presente encontrada", resultado)

    def test_consultar_ideias_com_filtros(self):
        salvar_ideia_presente("Mariana", "namorada", "Perfume Libre", "12/06")
        salvar_ideia_presente("Marcos", "irmão", "Teclado Mecânico", "05/08")
        salvar_ideia_presente("Mãe", "mãe", "Cafeteira Nespresso", "15/05")

        # Filtro por pessoa (case insensitive)
        res_pessoa = consultar_ideias_presente(pessoa="mariana")
        self.assertIn("Perfume Libre", res_pessoa)
        self.assertNotIn("Teclado Mecânico", res_pessoa)

        # Filtro por relação
        res_rel = consultar_ideias_presente(relacao="mãe")
        self.assertIn("Cafeteira Nespresso", res_rel)
        self.assertNotIn("Perfume Libre", res_rel)

        # Consulta geral
        res_todos = consultar_ideias_presente()
        self.assertIn("Mariana", res_todos)
        self.assertIn("Marcos", res_todos)
        self.assertIn("Mãe", res_todos)

    def test_alertar_datas_proximas_detecta_eventos(self):
        hoje = date.today()
        data_em_10_dias = (hoje + timedelta(days=10)).strftime("%d/%m/%Y")
        data_em_50_dias = (hoje + timedelta(days=50)).strftime("%d/%m/%Y")

        salvar_ideia_presente("Fernanda", "namorada", "Aliança de Prata", data_especial=data_em_10_dias)
        salvar_ideia_presente("Roberto", "pai", "Relógio Esportivo", data_especial=data_em_50_dias)

        # Busca padrão (30 dias) -> deve alertar Fernanda e não Roberto
        alerta_30 = alertar_datas_proximas(dias_antecedencia=30)
        self.assertIn("Fernanda", alerta_30)
        self.assertIn("Aliança de Prata", alerta_30)
        self.assertNotIn("Roberto", alerta_30)

        # Busca expandida (60 dias) -> deve alertar ambos
        alerta_60 = alertar_datas_proximas(dias_antecedencia=60)
        self.assertIn("Fernanda", alerta_60)
        self.assertIn("Roberto", alerta_60)

    def test_alertar_datas_sem_eventos_proximos(self):
        salvar_ideia_presente("Primo", "primo", "Livro Sci-Fi")  # sem data
        alerta = alertar_datas_proximas(dias_antecedencia=30)
        self.assertIn("Nenhuma data especial encontrada", alerta)

if __name__ == "__main__":
    unittest.main()
