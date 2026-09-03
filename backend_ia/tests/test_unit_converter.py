import unittest
from services.tools.unit_converter_tool import (
    converter_unidade,
    interpretar_e_converter
)


class TestFase17UnitConverter(unittest.TestCase):
    # 1. Testes de Distância
    def test_distancia_milhas_para_km(self):
        resultado = converter_unidade(1.0, "mi", "km")
        self.assertIn("1,6093", resultado)
        self.assertIn("quilômetros", resultado)

    def test_distancia_km_para_milhas(self):
        resultado = converter_unidade(10.0, "km", "mi")
        # 10 / 1.609344 = 6.2137
        self.assertIn("6,2137", resultado)
        self.assertIn("milhas", resultado)

    def test_distancia_pes_para_cm_e_metros(self):
        res_cm = converter_unidade(1.0, "ft", "cm")
        self.assertIn("30,48", res_cm)

        res_m = converter_unidade(10.0, "ft", "m")
        self.assertIn("3,048", res_m)

    def test_distancia_polegadas_para_cm(self):
        resultado = converter_unidade(10.0, "in", "cm")
        self.assertIn("25,4", resultado)

    def test_distancia_jardas_para_metros(self):
        resultado = converter_unidade(10.0, "yd", "m")
        self.assertIn("9,144", resultado)

    # 2. Testes de Temperatura
    def test_temperatura_fahrenheit_para_celsius(self):
        resultado = converter_unidade(32.0, "F", "C")
        self.assertIn("0 °C", resultado)

        res_ebulicao = converter_unidade(212.0, "F", "C")
        self.assertIn("100 °C", res_ebulicao)

    def test_temperatura_celsius_para_fahrenheit(self):
        resultado = converter_unidade(100.0, "C", "F")
        self.assertIn("212 °F", resultado)

    def test_temperatura_kelvin_para_celsius(self):
        resultado = converter_unidade(273.15, "K", "C")
        self.assertIn("0 °C", resultado)

        res_amb = converter_unidade(300.0, "K", "C")
        self.assertIn("26,85", res_amb)

    def test_temperatura_destaque_forno_culinario_350F(self):
        resultado = converter_unidade(350.0, "F", "C")
        # ~176.67 C ou ~177 C
        self.assertIn("176,6667", resultado)
        self.assertIn("Destaque Culinário", resultado)
        self.assertIn("Forno médio", resultado)
        self.assertIn("bolos", resultado.lower())

    def test_temperatura_destaque_forno_culinario_pizza_450F(self):
        resultado = converter_unidade(450.0, "F", "C")
        self.assertIn("Destaque Culinário", resultado)
        self.assertIn("Forno muito quente", resultado)

    # 3. Testes de Peso / Massa
    def test_peso_libras_para_kg(self):
        resultado = converter_unidade(150.0, "lb", "kg")
        # 150 * 0.45359237 = 68.0388...
        self.assertIn("68,0389", resultado)
        self.assertIn("quilogramas", resultado)

    def test_peso_kg_para_libras(self):
        resultado = converter_unidade(1.0, "kg", "lb")
        # 1 / 0.45359237 = 2.20462
        self.assertIn("2,2046", resultado)

    def test_peso_oncas_para_gramas(self):
        resultado = converter_unidade(1.0, "oz", "g")
        self.assertIn("28,3495", resultado)

    def test_peso_gramas_para_oncas(self):
        resultado = converter_unidade(100.0, "g", "oz")
        self.assertIn("3,5274", resultado)

    # 4. Testes de Volume / Culinária
    def test_volume_galao_para_litros(self):
        resultado = converter_unidade(1.0, "gal", "L")
        self.assertIn("3,7854", resultado)

    def test_volume_fl_oz_para_ml(self):
        resultado = converter_unidade(8.0, "fl oz", "ml")
        # 8 * 29.5735... = 236.588
        self.assertIn("236,5882", resultado)

    def test_volume_xicara_para_ml(self):
        resultado = converter_unidade(2.0, "xícara", "ml")
        self.assertIn("480 mililitros", resultado)

    def test_volume_colher_sopa_para_ml(self):
        resultado = converter_unidade(3.0, "colher de sopa", "ml")
        self.assertIn("45 mililitros", resultado)

    def test_volume_colher_cha_para_ml(self):
        resultado = converter_unidade(2.0, "colher de chá", "ml")
        self.assertIn("10 mililitros", resultado)

    # 5. Tratamento de Erros e Dimensões Incompatíveis
    def test_incompatibilidade_de_dimensoes(self):
        resultado = converter_unidade(10.0, "km", "kg")
        self.assertIn("Incompatibilidade de dimensões", resultado)

    def test_unidade_desconhecida(self):
        resultado = converter_unidade(10.0, "batatas", "km")
        self.assertIn("não reconhecida", resultado)

    def test_unidades_identicas(self):
        resultado = converter_unidade(5.0, "km", "km")
        self.assertIn("são iguais", resultado)

    # 6. Parser Helper `interpretar_e_converter`
    def test_interpretar_frase_milhas_em_km(self):
        resultado = interpretar_e_converter("35 milhas em km")
        self.assertIn("56,327", resultado)
        self.assertIn("quilômetros", resultado)

    def test_interpretar_frase_fahrenheit_para_celsius(self):
        resultado = interpretar_e_converter("180 fahrenheit para celsius")
        self.assertIn("82,2222", resultado)
        self.assertIn("°C", resultado)

    def test_interpretar_frase_libras_em_kg(self):
        resultado = interpretar_e_converter("150 libras em kg")
        self.assertIn("68,0389", resultado)
        self.assertIn("quilogramas", resultado)

    def test_interpretar_frase_350f_para_c(self):
        resultado = interpretar_e_converter("350 F para C")
        self.assertIn("176,6667", resultado)
        self.assertIn("Destaque Culinário", resultado)

    def test_interpretar_frase_xicaras_em_ml(self):
        resultado = interpretar_e_converter("2 xícaras em ml")
        self.assertIn("480 mililitros", resultado)

    def test_interpretar_frase_colher_sopa_em_ml(self):
        resultado = interpretar_e_converter("3 colheres de sopa em ml")
        self.assertIn("45 mililitros", resultado)

    def test_interpretar_frase_com_virgula_e_unidade_grudada(self):
        resultado = interpretar_e_converter("500g em oz")
        self.assertIn("17,637", resultado)

    def test_interpretar_frase_pergunta(self):
        resultado = interpretar_e_converter("quanto é 10 pés em metros")
        self.assertIn("3,048", resultado)

    def test_interpretar_texto_invalido(self):
        resultado = interpretar_e_converter("bom dia assistente")
        self.assertIn("Não consegui identificar", resultado)

    def test_interpretar_texto_vazio(self):
        resultado = interpretar_e_converter("")
        self.assertIn("Por favor, forneça uma frase", resultado)


if __name__ == "__main__":
    unittest.main()
