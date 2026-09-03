import unittest
from services.tools.bbq_planner_tool import calcular_churrasco

class TestFase15BBQ(unittest.TestCase):
    def test_zero_pessoas_retorna_aviso(self):
        res = calcular_churrasco(adultos_que_bebem=0, adultos_que_nao_bebem=0, criancas=0)
        self.assertIn("informe a quantidade de convidados", res)

    def test_churrasco_padrao_4_horas(self):
        # 10 adultos que bebem, 5 que não bebem (15 adultos), 4 crianças, 4 horas
        res = calcular_churrasco(
            adultos_que_bebem=10,
            adultos_que_nao_bebem=5,
            criancas=4,
            duracao_horas=4
        )
        
        # Validação do cabeçalho e contagem
        self.assertIn("LISTA DE COMPRAS PARA O CHURRASCO", res)
        self.assertIn("Adultos que bebem: *10*", res)
        self.assertIn("Adultos que não bebem: *5*", res)
        self.assertIn("Crianças: *4*", res)
        self.assertIn("Total de convidados: *19 pessoas*", res)
        self.assertIn("Duração estimada: *4 horas*", res)

        # Carnes per capita: 15 adultos * 450g + 4 crianças * 200g = 6750g + 800g = 7.55 kg
        self.assertIn("7.55 kg", res)
        self.assertIn("Carne Bovina", res)
        self.assertIn("Linguiça", res)
        self.assertIn("Frango", res)

        # Bebidas alcoólicas: 10 bebedores * 1.75L = 17.5L (~50 latas de 350ml)
        self.assertIn("BEBIDAS ALCOÓLICAS", res)
        self.assertIn("17.5 L", res)
        self.assertIn("latas", res)
        self.assertIn("fardo", res)

        # Não alcoólicos: 19 pessoas * 1L = 19L refri/suco; 19 * 0.5L = 9.5L água
        self.assertIn("Refrigerante / Suco: *19.0 L*", res)
        self.assertIn("Água Mineral: *9.5 L*", res)

        # Carvão e gelo
        self.assertIn("Carvão", res)
        self.assertIn("Gelo em Cubos", res)

        # Acompanhamentos
        self.assertIn("Pão de Alho", res)
        self.assertIn("Queijo Coalho", res)
        self.assertIn("Farofa Pronta", res)
        self.assertIn("Vinagrete", res)
        self.assertIn("Sal Grosso", res)

    def test_cortes_personalizados(self):
        cortes = ["Picanha Nobre", "Fraldinha", "Linguiça Campeira", "Coraçãozinho"]
        res = calcular_churrasco(
            adultos_que_bebem=6,
            adultos_que_nao_bebem=2,
            criancas=0,
            duracao_horas=4,
            tipos_carne=cortes
        )
        for corte in cortes:
            self.assertIn(corte, res)

    def test_churrasco_sem_bebidas_alcoolicas(self):
        res = calcular_churrasco(
            adultos_que_bebem=0,
            adultos_que_nao_bebem=8,
            criancas=4,
            duracao_horas=4
        )
        # Não deve haver seção de bebidas alcoólicas
        self.assertNotIn("BEBIDAS ALCOÓLICAS", res)
        self.assertNotIn("Cerveja:", res)
        self.assertIn("Refrigerante / Suco", res)
        self.assertIn("Água Mineral", res)

    def test_churrasco_longa_duracao_ajuste_proporcional(self):
        # 8 horas de festa deve resultar em mais carne e mais cerveja que 4 horas
        res_4h = calcular_churrasco(adultos_que_bebem=10, adultos_que_nao_bebem=0, criancas=0, duracao_horas=4)
        res_8h = calcular_churrasco(adultos_que_bebem=10, adultos_que_nao_bebem=0, criancas=0, duracao_horas=8)

        # Extrair pesos ou comparar strings
        self.assertIn("4.50 kg", res_4h) # 10 * 450g = 4.5kg
        # 8h: fator_tempo_adulto = 1.0 + (8-4)*0.08 = 1.32 -> 10 * 450 * 1.32 = 5.94 kg
        self.assertIn("5.94 kg", res_8h)
        # Cerveja em 8h deve ser 2x (35.0 L vs 17.5 L)
        self.assertIn("35.0 L", res_8h)

    def test_formatacao_whatsapp_e_dica(self):
        res = calcular_churrasco(adultos_que_bebem=4, adultos_que_nao_bebem=2, criancas=1, duracao_horas=3)
        self.assertIn("Dica do Mestre Churrasqueiro", res)
        self.assertTrue(res.startswith("🍖 *LISTA DE COMPRAS"))

if __name__ == "__main__":
    unittest.main()
