import unittest
from services.tools.notes_tool import (
    _reset_mock_storage,
    criar_anotacao,
    criar_lembrete,
    buscar_anotacoes,
    listar_lembretes_pendentes,
    concluir_lembrete
)

class TestFase9Notes(unittest.TestCase):
    def setUp(self):
        _reset_mock_storage()

    def tearDown(self):
        _reset_mock_storage()

    def test_criar_anotacao_sucesso(self):
        resultado = criar_anotacao(
            titulo="Configurações do Servidor",
            conteudo="Porta 8080, banco Firestore, cache Redis.",
            tags=["devops", "infra"]
        )
        self.assertIn("salva com sucesso", resultado)
        self.assertIn("Configurações do Servidor", resultado)
        self.assertIn("#devops", resultado)

    def test_criar_lembrete_sucesso(self):
        resultado = criar_lembrete(
            titulo="Trocar óleo do Fiat Fastback",
            data_hora_lembrete="2026-09-10 14:00",
            tags=["carro", "manutencao"]
        )
        self.assertIn("Lembrete agendado com sucesso", resultado)
        self.assertIn("Trocar óleo do Fiat Fastback", resultado)
        self.assertIn("2026-09-10 14:00", resultado)
        self.assertIn("Pendente", resultado)

    def test_buscar_anotacoes_por_termo(self):
        criar_anotacao(
            titulo="Ideias para o DAM",
            conteudo="Adicionar integração com Google Calendar e Maps.",
            tags=["features"]
        )
        criar_anotacao(
            titulo="Receita de Bolo de Cenoura",
            conteudo="Cenouras, ovos, óleo, farinha e chocolate.",
            tags=["culinaria"]
        )

        resultado = buscar_anotacoes(termo="Maps")
        self.assertIn("Ideias para o DAM", resultado)
        self.assertNotIn("Receita de Bolo", resultado)

    def test_buscar_anotacoes_por_tag(self):
        criar_anotacao(
            titulo="Comprar suplementos",
            conteudo="Creatina e Whey Protein Isolado.",
            tags=["saude", "treino"]
        )
        criar_anotacao(
            titulo="Reunião Sprint",
            conteudo="Alinhar entregas da Fase 8 e Fase 9.",
            tags=["trabalho"]
        )

        resultado = buscar_anotacoes(tag="saude")
        self.assertIn("Comprar suplementos", resultado)
        self.assertNotIn("Reunião Sprint", resultado)

    def test_buscar_anotacoes_nao_encontradas(self):
        criar_anotacao(
            titulo="Nota A",
            conteudo="Conteúdo qualquer.",
            tags=["geral"]
        )
        resultado = buscar_anotacoes(termo="termo_inexistente_xyz")
        self.assertIn("Nenhuma anotação encontrada", resultado)

    def test_listar_lembretes_pendentes(self):
        # Nenhum lembrete inicialmente
        res_vazio = listar_lembretes_pendentes()
        self.assertIn("Nenhum lembrete pendente", res_vazio)

        # Cadastrar dois lembretes
        criar_lembrete("Consulta Médica", "2026-09-08 09:00", ["saude"])
        criar_lembrete("Pagar IPVA", "2026-09-05 10:00", ["financas"])

        resultado = listar_lembretes_pendentes(apenas_hoje=False)
        self.assertIn("Lembretes Pendentes (2)", resultado)
        self.assertIn("Pagar IPVA", resultado)
        self.assertIn("Consulta Médica", resultado)

    def test_concluir_lembrete_por_titulo(self):
        criar_lembrete("Comprar ração para o cachorro", "2026-09-06 18:00", ["pets"])
        
        # Concluir pelo título
        conclusao = concluir_lembrete("Comprar ração")
        self.assertIn("marcado como concluído com sucesso", conclusao)

        # Não deve mais aparecer como pendente
        pendentes = listar_lembretes_pendentes()
        self.assertIn("Nenhum lembrete pendente", pendentes)

    def test_concluir_lembrete_por_id(self):
        msg = criar_lembrete("Renovar CNH", "2026-09-12 11:00", ["documentos"])
        # Extrair ID gerado
        import re
        match = re.search(r"ID: ([a-f0-9]+)", msg)
        self.assertIsNotNone(match)
        id_prefix = match.group(1)

        conclusao = concluir_lembrete(id_prefix)
        self.assertIn("marcado como concluído com sucesso", conclusao)

    def test_concluir_lembrete_inexistente(self):
        conclusao = concluir_lembrete("Lembrete que nunca existiu")
        self.assertIn("Não encontrei nenhum lembrete pendente", conclusao)

if __name__ == "__main__":
    unittest.main()
