import unittest
from unittest.mock import patch, MagicMock
from services.tools.vehicle_tool import consultar_status_veiculo, acionar_travas_veiculo
from services.tools.esports_tool import consultar_jogos_cs2

class TestFase4Tools(unittest.TestCase):

    def test_consultar_status_veiculo(self):
        status = consultar_status_veiculo()
        self.assertIn("Fiat Fastback", status)
        self.assertIn("Combustível", status)
        self.assertIn("Autonomia estimada", status)
        self.assertIn("Travas", status)

    def test_acionar_travas_veiculo_travar(self):
        resultado = acionar_travas_veiculo(acao="travar")
        self.assertIn("travadas com sucesso", resultado)

    def test_acionar_travas_veiculo_destravar(self):
        resultado = acionar_travas_veiculo(acao="destravar")
        self.assertIn("destravadas com sucesso", resultado)

    def test_acionar_travas_veiculo_acao_invalida(self):
        resultado = acionar_travas_veiculo(acao="voar")
        self.assertIn("Ação inválida", resultado)

    def test_consultar_jogos_cs2_geral(self):
        jogos = consultar_jogos_cs2()
        self.assertIn("Counter-Strike 2", jogos)
        self.assertTrue(len(jogos) > 20)

    def test_consultar_jogos_cs2_time_especifico(self):
        jogos = consultar_jogos_cs2(time="FURIA")
        self.assertIn("FURIA", jogos)

if __name__ == "__main__":
    unittest.main()
