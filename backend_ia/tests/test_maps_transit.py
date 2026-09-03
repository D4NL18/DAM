import unittest
import json
from unittest.mock import patch, MagicMock
from config.settings import settings
from services.tools.maps_tool import (
    resolver_apelido_endereco,
    obter_dados_rota,
    consultar_rota,
    calcular_horario_saida
)

class TestFase8Maps(unittest.TestCase):
    def setUp(self):
        self.original_maps_key = settings.GOOGLE_MAPS_API_KEY
        self.original_home = settings.USER_HOME_ADDRESS
        self.original_work = settings.USER_WORK_ADDRESS
        settings.GOOGLE_MAPS_API_KEY = ""
        settings.USER_HOME_ADDRESS = "Avenida Paulista, 1000 - Bela Vista, São Paulo - SP"
        settings.USER_WORK_ADDRESS = "Avenida Brigadeiro Faria Lima, 3500 - Itaim Bibi, São Paulo - SP"

    def tearDown(self):
        settings.GOOGLE_MAPS_API_KEY = self.original_maps_key
        settings.USER_HOME_ADDRESS = self.original_home
        settings.USER_WORK_ADDRESS = self.original_work

    def test_resolver_apelido_casa(self):
        self.assertEqual(resolver_apelido_endereco("casa"), settings.USER_HOME_ADDRESS)
        self.assertEqual(resolver_apelido_endereco("minha casa"), settings.USER_HOME_ADDRESS)
        self.assertEqual(resolver_apelido_endereco("home"), settings.USER_HOME_ADDRESS)

    def test_resolver_apelido_trabalho(self):
        self.assertEqual(resolver_apelido_endereco("trabalho"), settings.USER_WORK_ADDRESS)
        self.assertEqual(resolver_apelido_endereco("meu trabalho"), settings.USER_WORK_ADDRESS)
        self.assertEqual(resolver_apelido_endereco("escritório"), settings.USER_WORK_ADDRESS)

    def test_resolver_endereco_literal(self):
        end = "Rua Oscar Freire, 500, Jardins"
        self.assertEqual(resolver_apelido_endereco(end), end)

    def test_consultar_rota_modo_simulacao(self):
        resultado = consultar_rota("casa", "trabalho")
        self.assertIn("Rota e Trânsito", resultado)
        self.assertIn("Avenida Paulista", resultado)
        self.assertIn("Faria Lima", resultado)
        self.assertIn("Tempo estimado", resultado)
        self.assertIn("Vias principais", resultado)

    @patch("urllib.request.urlopen")
    def test_consultar_rota_com_google_maps_api(self, mock_urlopen):
        settings.GOOGLE_MAPS_API_KEY = "dummy_maps_key_123"
        
        mock_response_payload = {
            "status": "OK",
            "routes": [
                {
                    "summary": "Av. 23 de Maio",
                    "legs": [
                        {
                            "distance": {"text": "11.2 km", "value": 11200},
                            "duration": {"text": "30 mins", "value": 1800},
                            "duration_in_traffic": {"text": "38 mins", "value": 2280}
                        }
                    ]
                }
            ]
        }
        
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(mock_response_payload).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        resultado = consultar_rota("casa", "trabalho")
        self.assertIn("11.2 km", resultado)
        self.assertIn("38 mins", resultado)
        self.assertIn("Av. 23 de Maio", resultado)
        mock_urlopen.assert_called_once()

    def test_calcular_horario_saida_padrao(self):
        # Saída calculada para chegada às 10:00 com antecedência de 10 min
        resultado = calcular_horario_saida("casa", "trabalho", horario_chegada="10:00", antecedencia_minutos=10)
        self.assertIn("Planejamento de Saída", resultado)
        self.assertIn("Horário recomendado de saída", resultado)
        self.assertIn("Horário previsto de chegada:** 10:00", resultado)
        self.assertIn("Margem de antecedência:** 10 min", resultado)
        self.assertIn("09:26", resultado)

    def test_calcular_horario_saida_com_data_completa(self):
        chegada = "2026-09-04 15:30"
        resultado = calcular_horario_saida("Aeroporto de Congonhas", "Av. Paulista", horario_chegada=chegada, antecedencia_minutos=15)
        self.assertIn("Planejamento de Saída", resultado)
        self.assertIn("15:30", resultado)
        self.assertIn("15 min", resultado)

    def test_calcular_horario_saida_formato_invalido(self):
        resultado = calcular_horario_saida("casa", "trabalho", horario_chegada="amanhã cedo")
        self.assertIn("Não consegui identificar o horário", resultado)

if __name__ == "__main__":
    unittest.main()
