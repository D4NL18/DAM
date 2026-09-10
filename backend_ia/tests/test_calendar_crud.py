import unittest
from unittest.mock import patch, MagicMock
from services.user_context import UserContext

class TestCalendarCrud(unittest.TestCase):

    def setUp(self):
        UserContext.set_user("daniel", "5511999999999")

    def tearDown(self):
        UserContext.set_user("daniel", "5511999999999")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_excluir_evento_sucesso(self, mock_get_service):
        from services.tools.calendar_tool import excluir_evento

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()
        mock_delete = MagicMock()

        # Simula que encontrou 1 evento correspondente
        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "event_abc_123",
                    "summary": "Reunião de Alinhamento com Time",
                    "start": {"dateTime": "2026-09-10T15:00:00-03:00"},
                    "end": {"dateTime": "2026-09-10T16:00:00-03:00"}
                }
            ]
        }
        mock_delete.execute.return_value = {}

        mock_events.list.return_value = mock_list
        mock_events.delete.return_value = mock_delete
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        res = excluir_evento(termo_busca="Alinhamento", data_referencia="2026-09-10")

        self.assertIn("excluído com sucesso", res.lower())
        self.assertIn("Reunião de Alinhamento com Time", res)
        # Verifica que chamou delete com o eventId correto
        mock_events.delete.assert_called_once()
        _, kwargs = mock_events.delete.call_args
        self.assertEqual(kwargs.get("eventId"), "event_abc_123")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_excluir_evento_nao_encontrado(self, mock_get_service):
        from services.tools.calendar_tool import excluir_evento

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = {"items": []}

        mock_events.list.return_value = mock_list
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        res = excluir_evento(termo_busca="Dentista Inexistente")

        self.assertIn("não encontrei", res.lower())
        mock_events.delete.assert_not_called()

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_excluir_evento_multiplos_desambiguacao(self, mock_get_service):
        from services.tools.calendar_tool import excluir_evento

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()

        # Simula que encontrou 2 reuniões com o mesmo termo
        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "evt_1",
                    "summary": "1:1 com Mariana",
                    "start": {"dateTime": "2026-09-10T10:00:00-03:00"}
                },
                {
                    "id": "evt_2",
                    "summary": "1:1 com Mariana - Feedback",
                    "start": {"dateTime": "2026-09-10T16:00:00-03:00"}
                }
            ]
        }

        mock_events.list.return_value = mock_list
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        res = excluir_evento(termo_busca="1:1 com Mariana")

        self.assertIn("encontrei mais de um evento", res.lower())
        self.assertIn("10:00", res)
        self.assertIn("16:00", res)
        # Não deve deletar nada sem desambiguação!
        mock_events.delete.assert_not_called()

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_editar_evento_horario_sucesso(self, mock_get_service):
        from services.tools.calendar_tool import editar_evento

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()
        mock_patch = MagicMock()

        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "event_xyz_789",
                    "summary": "Sincronização Diária",
                    "start": {"dateTime": "2026-09-10T09:00:00-03:00"},
                    "end": {"dateTime": "2026-09-10T09:30:00-03:00"}
                }
            ]
        }
        mock_patch.execute.return_value = {
            "id": "event_xyz_789",
            "summary": "Sincronização Diária",
            "start": {"dateTime": "2026-09-10T11:00:00-03:00"},
            "end": {"dateTime": "2026-09-10T11:30:00-03:00"}
        }

        mock_events.list.return_value = mock_list
        mock_events.patch.return_value = mock_patch
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        res = editar_evento(
            termo_busca="Sincronização",
            novo_inicio_iso="2026-09-10T11:00:00-03:00",
            nova_duracao_minutos=30
        )

        self.assertIn("atualizado com sucesso", res.lower())
        mock_events.patch.assert_called_once()
        _, kwargs = mock_events.patch.call_args
        self.assertEqual(kwargs.get("eventId"), "event_xyz_789")
        patch_body = kwargs.get("body", {})
        self.assertEqual(patch_body["start"]["dateTime"], "2026-09-10T11:00:00-03:00")
        self.assertEqual(patch_body["end"]["dateTime"], "2026-09-10T11:30:00-03:00")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_editar_evento_titulo_e_localizacao(self, mock_get_service):
        from services.tools.calendar_tool import editar_evento

        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()
        mock_patch = MagicMock()

        mock_list.execute.return_value = {
            "items": [
                {
                    "id": "event_abc_456",
                    "summary": "Almoço",
                    "start": {"dateTime": "2026-09-10T12:30:00-03:00"},
                    "end": {"dateTime": "2026-09-10T14:00:00-03:00"}
                }
            ]
        }
        mock_patch.execute.return_value = {
            "id": "event_abc_456",
            "summary": "Almoço de Negócios",
            "location": "Restaurante Fasano"
        }

        mock_events.list.return_value = mock_list
        mock_events.patch.return_value = mock_patch
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        res = editar_evento(
            termo_busca="Almoço",
            novo_titulo="Almoço de Negócios",
            nova_localizacao="Restaurante Fasano"
        )

        self.assertIn("atualizado com sucesso", res.lower())
        mock_events.patch.assert_called_once()
        _, kwargs = mock_events.patch.call_args
        patch_body = kwargs.get("body", {})
        self.assertEqual(patch_body.get("summary"), "Almoço de Negócios")
        self.assertEqual(patch_body.get("location"), "Restaurante Fasano")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_lari_bloqueada_de_excluir_ou_editar_evento_daniel(self, mock_get_service):
        from services.tools.calendar_tool import excluir_evento, editar_evento

        # Simula chamada feita por Lari
        UserContext.set_user("lari", "5511888888888")

        mock_service = MagicMock()
        mock_get_service.return_value = mock_service

        res_del = excluir_evento(termo_busca="Reunião", usuario="daniel")
        self.assertIn("restrito", res_del.lower())
        mock_service.events.assert_not_called()

        res_edit = editar_evento(termo_busca="Reunião", novo_titulo="Hack", usuario="daniel")
        self.assertIn("restrito", res_edit.lower())
        mock_service.events.assert_not_called()
