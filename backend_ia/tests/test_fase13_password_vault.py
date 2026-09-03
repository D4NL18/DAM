import unittest
import string
import os
from unittest.mock import MagicMock, patch

from services.tools.password_vault_tool import (
    salvar_credencial,
    consultar_credencial,
    gerar_senha_forte,
    listar_servicos_cofre,
    _get_cipher,
    _mascarar_senha,
    _reset_memory,
    _in_memory_vault
)
from config import firebase

class TestFase13PasswordVault(unittest.TestCase):

    def setUp(self):
        _reset_memory()
        self.orig_db = firebase.db
        firebase.db = None  # Garante modo em memória nos testes unitários base

    def tearDown(self):
        _reset_memory()
        firebase.db = self.orig_db

    def test_gerar_senha_forte_tamanho_e_requisitos(self):
        # Senha padrão (16 caracteres com símbolos)
        senha1 = gerar_senha_forte()
        self.assertEqual(len(senha1), 16)
        self.assertTrue(any(c in string.ascii_uppercase for c in senha1), "Deve conter maiúsculas")
        self.assertTrue(any(c in string.ascii_lowercase for c in senha1), "Deve conter minúsculas")
        self.assertTrue(any(c in string.digits for c in senha1), "Deve conter dígitos")
        self.assertTrue(any(c in "!@#$%&*_-+=?~" for c in senha1), "Deve conter símbolos")

        # Senha com tamanho customizado
        senha_longa = gerar_senha_forte(tamanho=24)
        self.assertEqual(len(senha_longa), 24)

        # Senha sem símbolos
        senha_sem_simbolos = gerar_senha_forte(tamanho=12, incluir_simbolos=False)
        self.assertEqual(len(senha_sem_simbolos), 12)
        for s in "!@#$%&*_-+=?~":
            self.assertNotIn(s, senha_sem_simbolos)

        # Garantia de aleatoriedade criptográfica (senhas subsequentes diferentes)
        senha2 = gerar_senha_forte()
        self.assertNotEqual(senha1, senha2)

    def test_mascarar_senha(self):
        self.assertEqual(_mascarar_senha("1"), "*")
        self.assertEqual(_mascarar_senha("12"), "**")
        m_curta = _mascarar_senha("abcdef")
        self.assertTrue(m_curta.startswith("a") and m_curta.endswith("f"))
        self.assertIn("*", m_curta)

        m_longa = _mascarar_senha("SuperSenhaSecreta2026!")
        self.assertIn("****", m_longa)
        self.assertTrue(m_longa.startswith("Sup"))
        self.assertTrue(m_longa.endswith("6!"))

    def test_salvar_e_consultar_credencial_criptografada_memoria(self):
        senha_original = "MinhaChaveUltraSecreta#99"
        resultado_salvar = salvar_credencial(
            servico="GitHub",
            usuario="danilodev",
            senha=senha_original,
            notas="Chave de acesso com permissão de repo e workflow"
        )
        self.assertIn("GitHub", resultado_salvar)
        self.assertIn("criptografada e salva", resultado_salvar)
        self.assertIn("permissão de repo", resultado_salvar)

        # Certifica que a senha bruta NÃO está gravada no armazenamento interno
        item_armazenado = _in_memory_vault["github"]
        self.assertNotEqual(item_armazenado["senha_criptografada"], senha_original)
        self.assertNotIn(senha_original, item_armazenado["senha_criptografada"])

        # Consulta mascarada (padrão revelar_senha=False)
        consulta_mascarada = consultar_credencial("GitHub", revelar_senha=False)
        self.assertIn("GitHub", consulta_mascarada)
        self.assertIn("danilodev", consulta_mascarada)
        self.assertNotIn(senha_original, consulta_mascarada)
        self.assertIn("****", consulta_mascarada)
        self.assertIn("revelar_senha=True", consulta_mascarada)

        # Consulta revelada (revelar_senha=True)
        consulta_revelada = consultar_credencial("github", revelar_senha=True)
        self.assertIn(senha_original, consulta_revelada)
        self.assertIn("🔓", consulta_revelada)

    def test_salvar_validacoes_campos_obrigatorios(self):
        r1 = salvar_credencial("", "user", "pass")
        self.assertIn("informe o nome do serviço", r1)

        r2 = salvar_credencial("AWS", "", "pass")
        self.assertIn("informe o usuário", r2)

        r3 = salvar_credencial("AWS", "user", "")
        self.assertIn("informe a senha", r3)

    def test_consultar_servico_inexistente_ou_vazio(self):
        r_inexistente = consultar_credencial("ServicoFantasma")
        self.assertIn("Nenhuma credencial encontrada", r_inexistente)

        r_vazio = consultar_credencial("")
        self.assertIn("informe o nome do serviço", r_vazio)

    def test_listar_servicos_cofre_sem_vazar_senhas(self):
        # Cofre inicialmente vazio
        r_vazio = listar_servicos_cofre()
        self.assertIn("está vazio", r_vazio)

        # Adiciona 2 serviços
        salvar_credencial("AWS Console", "admin_root", "senhaAWS_SuperForte123!")
        salvar_credencial("Google Workspace", "contato@empresa.com", "senhaGoogle_Segura456!")

        lista = listar_servicos_cofre()
        self.assertIn("AWS Console", lista)
        self.assertIn("admin_root", lista)
        self.assertIn("Google Workspace", lista)
        self.assertIn("contato@empresa.com", lista)

        # Garante NENHUMA senha na listagem
        self.assertNotIn("senhaAWS_SuperForte123!", lista)
        self.assertNotIn("senhaGoogle_Segura456!", lista)

    def test_chave_derivacao_pbkdf2_e_chave_direta(self):
        # Teste derivação com segredo padrão
        cipher1 = _get_cipher()
        token = cipher1.encrypt(b"teste_segredo")
        self.assertEqual(cipher1.decrypt(token), b"teste_segredo")

        # Teste com chave Fernet direta
        from cryptography.fernet import Fernet
        nova_chave = Fernet.generate_key().decode()
        with patch.dict(os.environ, {"VAULT_ENCRYPTION_KEY": nova_chave}):
            cipher_custom = _get_cipher()
            token2 = cipher_custom.encrypt(b"dado_criptografado")
            self.assertEqual(cipher_custom.decrypt(token2), b"dado_criptografado")

    def test_integracao_firestore_mock(self):
        """Valida que quando firebase.db estiver ativo, as operações usam Firestore."""
        mock_db = MagicMock()
        mock_collection = MagicMock()
        mock_doc_ref = MagicMock()
        mock_snap = MagicMock()

        mock_db.collection.return_value = mock_collection
        mock_collection.document.return_value = mock_doc_ref

        firebase.db = mock_db

        salvar_credencial("Slack", "danilo@team.com", "slackPass2026!")
        mock_collection.document.assert_called_with("slack")
        mock_doc_ref.set.assert_called_once()

        saved_data = mock_doc_ref.set.call_args[0][0]
        self.assertEqual(saved_data["servico"], "Slack")
        self.assertEqual(saved_data["usuario"], "danilo@team.com")
        self.assertIn("senha_criptografada", saved_data)
        self.assertNotEqual(saved_data["senha_criptografada"], "slackPass2026!")

        # Simula consulta do Firestore
        mock_snap.exists = True
        mock_snap.to_dict.return_value = saved_data
        mock_doc_ref.get.return_value = mock_snap

        resp_cons = consultar_credencial("Slack", revelar_senha=True)
        self.assertIn("slackPass2026!", resp_cons)

if __name__ == "__main__":
    unittest.main()
