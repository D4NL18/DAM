import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from services.user_context import UserContext
from services.tools.calendar_tool import consultar_agenda, agendar_evento
from services.tools.finance_tool import registrar_gasto, consultar_resumo_gastos
from services.tools.notes_tool import criar_anotacao, _obter_todos_itens, _reset_mock_storage
from services.tools.password_vault_tool import salvar_credencial, consultar_credencial, _reset_memory as _reset_vault
from services.tools.item_finder_tool import registrar_localizacao_objeto, onde_guardei_objeto, _reset_memory as _reset_items


class TestMultiuserIsolation(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "TEST_KEY"
        settings.ALLOWED_PHONE_NUMBERS = ["5511999999999", "5511888888888"]
        settings.CALENDAR_ID_DANIEL = "admin_calendar@example.com"
        settings.CALENDAR_ID_LARI = "user_calendar@example.com"
        _reset_mock_storage()
        _reset_vault()
        _reset_items()
        UserContext.set_user("daniel", "5511999999999")

    def test_user_context_resolution(self):
        # 1. Daniel com e sem nono dígito
        u1 = UserContext.resolve_user_from_phone("5511999999999@s.whatsapp.net")
        self.assertIsNotNone(u1)
        self.assertEqual(u1["id"], "daniel")

        u1_sem9 = UserContext.resolve_user_from_phone("551199999999@s.whatsapp.net")
        self.assertIsNotNone(u1_sem9)
        self.assertEqual(u1_sem9["id"], "daniel")

        # 2. Lari com e sem nono dígito
        u2 = UserContext.resolve_user_from_phone("5511888888888@s.whatsapp.net")
        self.assertIsNotNone(u2)
        self.assertEqual(u2["id"], "lari")

        u2_sem9 = UserContext.resolve_user_from_phone("551188888888@s.whatsapp.net")
        self.assertIsNotNone(u2_sem9)
        self.assertEqual(u2_sem9["id"], "lari")

        # 3. Número desconhecido
        u3 = UserContext.resolve_user_from_phone("5511777777777@s.whatsapp.net")
        self.assertIsNone(u3)

    @patch("routers.webhook.process_and_reply")
    @patch("routers.webhook.ChatRepository.save_log")
    def test_webhook_accepts_both_daniel_and_lari(self, mock_save_log, mock_process):
        # Daniel
        payload_daniel = {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511999999999@s.whatsapp.net", "fromMe": False, "id": "1"},
                "message": {"conversation": "Oi bot, sou o Daniel"}
            }
        }
        res1 = self.client.post("/api/whatsapp/webhook", json=payload_daniel, headers={"apikey": "TEST_KEY"})
        self.assertEqual(res1.status_code, 200)
        self.assertEqual(res1.json().get("status"), "processing")

        # Lari
        payload_lari = {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511888888888@s.whatsapp.net", "fromMe": False, "id": "2"},
                "message": {"conversation": "Oi bot, sou a Lari"}
            }
        }
        res2 = self.client.post("/api/whatsapp/webhook", json=payload_lari, headers={"apikey": "TEST_KEY"})
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json().get("status"), "processing")

        # Desconhecido
        payload_estranho = {
            "event": "messages.upsert",
            "data": {
                "key": {"remoteJid": "5511999991111@s.whatsapp.net", "fromMe": False, "id": "3"},
                "message": {"conversation": "Mensagem invasora"}
            }
        }
        res3 = self.client.post("/api/whatsapp/webhook", json=payload_estranho, headers={"apikey": "TEST_KEY"})
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(res3.json().get("status"), "ignored")
        self.assertEqual(res3.json().get("reason"), "unauthorized_user")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_calendar_cross_access_rules(self, mock_get_service):
        mock_service = MagicMock()
        mock_get_service.return_value = mock_service
        mock_events = mock_service.events.return_value.list.return_value
        mock_events.execute.return_value = {"items": []}

        # 1. Daniel consulta sua agenda
        UserContext.set_user("daniel")
        resp1 = consultar_agenda(dias=1, usuario="auto")
        self.assertIn("Sua agenda está livre", resp1)
        mock_service.events().list.assert_called_with(
            calendarId="admin_calendar@example.com",
            maxResults=10,
            orderBy="startTime",
            singleEvents=True,
            timeMax=unittest.mock.ANY,
            timeMin=unittest.mock.ANY
        )

        # 2. Daniel consulta a agenda de Lari (PERMITIDO)
        resp2 = consultar_agenda(dias=1, usuario="lari")
        self.assertIn("está livre", resp2)
        mock_service.events().list.assert_called_with(
            calendarId="user_calendar@example.com",
            maxResults=10,
            orderBy="startTime",
            singleEvents=True,
            timeMax=unittest.mock.ANY,
            timeMin=unittest.mock.ANY
        )

        # 3. Lari tenta consultar a agenda de Daniel (BLOQUEADO)
        UserContext.set_user("lari")
        resp3 = consultar_agenda(dias=1, usuario="daniel")
        self.assertIn("Acesso restrito", resp3)

        # 4. Lari consulta a própria agenda (PERMITIDO)
        resp4 = consultar_agenda(dias=1, usuario="auto")
        self.assertIn("Sua agenda está livre", resp4)
        mock_service.events().list.assert_called_with(
            calendarId="user_calendar@example.com",
            maxResults=10,
            orderBy="startTime",
            singleEvents=True,
            timeMax=unittest.mock.ANY,
            timeMin=unittest.mock.ANY
        )

    def test_notes_isolation(self):
        # Daniel cria nota
        UserContext.set_user("daniel")
        criar_anotacao("Nota do Daniel", "Conteudo confidencial do Daniel")

        # Lari cria nota
        UserContext.set_user("lari")
        criar_anotacao("Nota da Lari", "Conteudo confidencial da Lari")

        # Lari lista notas: deve ver APENAS a dela
        notas_lari = _obter_todos_itens()
        self.assertEqual(len(notas_lari), 1)
        self.assertEqual(notas_lari[0]["titulo"], "Nota da Lari")

        # Daniel lista notas: deve ver APENAS a dele
        UserContext.set_user("daniel")
        notas_daniel = _obter_todos_itens()
        self.assertEqual(len(notas_daniel), 1)
        self.assertEqual(notas_daniel[0]["titulo"], "Nota do Daniel")

    def test_vault_isolation(self):
        # Daniel salva senha do GitHub
        UserContext.set_user("daniel")
        salvar_credencial("GitHub", "admin_user", "SenhaForte123!")

        # Lari tenta consultar a senha do GitHub
        UserContext.set_user("lari")
        resp_lari = consultar_credencial("GitHub", revelar_senha=True)
        self.assertIn("Nenhuma credencial encontrada", resp_lari)

        # Daniel consulta a senha do GitHub: permitido
        UserContext.set_user("daniel")
        resp_daniel = consultar_credencial("GitHub", revelar_senha=True)
        self.assertIn("SenhaForte123!", resp_daniel)

    def test_item_locations_isolation(self):
        # Daniel salva onde guardou a carteira
        UserContext.set_user("daniel")
        registrar_localizacao_objeto("Carteira", "No bolso da jaqueta preta")

        # Lari pergunta onde está a carteira dela
        UserContext.set_user("lari")
        resp_lari = onde_guardei_objeto("Carteira")
        self.assertIn("Não encontrei nenhum registro", resp_lari)

        # Lari registra a sua carteira
        registrar_localizacao_objeto("Carteira", "Na bolsa marrom")
        resp_lari_2 = onde_guardei_objeto("Carteira")
        self.assertIn("Na bolsa marrom", resp_lari_2)

        # Daniel pergunta da carteira dele: não sofreu interferência
        UserContext.set_user("daniel")
        resp_daniel = onde_guardei_objeto("Carteira")
        self.assertIn("No bolso da jaqueta preta", resp_daniel)


if __name__ == '__main__':
    unittest.main()
