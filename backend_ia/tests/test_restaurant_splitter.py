import unittest
import re
from services.tools.restaurant_split_tool import dividir_conta_restaurante

class TestFase11Splitter(unittest.TestCase):

    def test_divisao_caso_padrao_prompt(self):
        consumo = [
            {
                "nome": "Você",
                "itens": [
                    {"nome": "Hambúrguer", "valor": 42.0},
                    {"nome": "1/2 Pizza", "valor": 20.0}
                ]
            },
            {
                "nome": "João",
                "itens": [
                    {"nome": "Cerveja", "valor": 36.0}
                ]
            }
        ]
        chave_pix = "11999998888"
        resultado = dividir_conta_restaurante(
            consumo_participantes=consumo,
            taxa_servico_percent=10.0,
            chave_pix=chave_pix
        )

        # Validações do Você
        self.assertIn("Você", resultado)
        self.assertIn("Hambúrguer", resultado)
        self.assertIn("R$ 42,00", resultado)
        self.assertIn("1/2 Pizza", resultado)
        self.assertIn("R$ 20,00", resultado)
        self.assertIn("Subtotal: R$ 62,00", resultado)
        self.assertIn("Serviço (10%): R$ 6,20", resultado)
        self.assertIn("Total a pagar: R$ 68,20", resultado)

        # Validações do João
        self.assertIn("João", resultado)
        self.assertIn("Cerveja", resultado)
        self.assertIn("Subtotal: R$ 36,00", resultado)
        self.assertIn("Serviço (10%): R$ 3,60", resultado)
        self.assertIn("Total a pagar: R$ 39,60", resultado)

        # Totais gerais
        self.assertIn("*Subtotal Geral:* R$ 98,00", resultado)
        self.assertIn("Taxa de Serviço (10%):* R$ 9,80", resultado)
        self.assertIn("*TOTAL DA CONTA:* R$ 107,80", resultado)

        # Pix
        self.assertIn(chave_pix, resultado)

    def test_ajuste_centavos_penny_balancing(self):
        # 3 pessoas com consumo de R$ 10.05 cada
        # Subtotal: 30.15. Taxa 10%: 3.015 -> 3.02. Total da conta: 33.17
        # Sem ajuste, cada uma pagaria 10.05 + 1.01 = 11.06 -> soma 33.18 (1 centavo a mais)
        consumo = [
            {"nome": "Ana", "itens": [{"nome": "Item A", "valor": 10.05}]},
            {"nome": "Beto", "itens": [{"nome": "Item B", "valor": 10.05}]},
            {"nome": "Caio", "itens": [{"nome": "Item C", "valor": 10.05}]}
        ]
        resultado = dividir_conta_restaurante(consumo, taxa_servico_percent=10.0)

        self.assertIn("*Subtotal Geral:* R$ 30,15", resultado)
        self.assertIn("Taxa de Serviço (10%):* R$ 3,02", resultado)
        self.assertIn("*TOTAL DA CONTA:* R$ 33,17", resultado)

        # Extrair totais individuais via regex e somar
        totais_individuais = [
            float(m.replace(".", "").replace(",", "."))
            for m in re.findall(r"Total a pagar:\s*R\$\s*([\d\.,]+)\*", resultado)
        ]
        self.assertEqual(len(totais_individuais), 3)
        self.assertAlmostEqual(sum(totais_individuais), 33.17, places=2)

    def test_divisao_sem_taxa_servico(self):
        consumo = [
            {"nome": "Lucas", "itens": [{"nome": "Prato Feito", "valor": 35.0}]},
            {"nome": "Julia", "itens": [{"nome": "Suco Natural", "valor": 12.5}]}
        ]
        resultado = dividir_conta_restaurante(consumo, taxa_servico_percent=0.0)
        self.assertIn("*TOTAL DA CONTA:* R$ 47,50", resultado)
        self.assertIn("Total a pagar: R$ 35,00*", resultado)
        self.assertIn("Total a pagar: R$ 12,50*", resultado)

    def test_sem_chave_pix(self):
        consumo = [{"nome": "Pedro", "itens": [{"nome": "Café", "valor": 8.0}]}]
        resultado = dividir_conta_restaurante(consumo, chave_pix=None)
        self.assertNotIn("Chave Pix", resultado)

    def test_consumo_vazio_ou_zerado(self):
        res_vazio = dividir_conta_restaurante([])
        self.assertIn("Nenhum consumo informado", res_vazio)

        res_zero = dividir_conta_restaurante([{"nome": "Tiago", "itens": []}])
        self.assertIn("R$ 0,00", res_zero)

    def test_suporte_json_string_e_valores_string(self):
        payload_json = (
            '[{"nome": "Carla", "itens": [{"nome": "Vinho", "valor": "R$ 85,50"}]},'
            ' {"nome": "Diego", "itens": [{"nome": "Massa", "valor": "45.00"}]}]'
        )
        resultado = dividir_conta_restaurante(payload_json, taxa_servico_percent=12.0)
        self.assertIn("Carla", resultado)
        self.assertIn("Diego", resultado)
        self.assertIn("*Subtotal Geral:* R$ 130,50", resultado)

if __name__ == "__main__":
    unittest.main()
