import unittest
from unittest.mock import patch, MagicMock
from services.tools.calendar_tool import agendar_evento, consultar_agenda

class TestCalendarEnriched(unittest.TestCase):

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_agendar_evento_com_descricao_e_localizacao(self, mock_get_service):
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_insert = MagicMock()
        mock_insert.execute.return_value = {
            "htmlLink": "https://calendar.google.com/event?id=123",
            "summary": "Reunião de Alinhamento",
            "description": "Pauta: arquitetura e infraestrutura",
            "location": "Google Meet"
        }
        mock_events.insert.return_value = mock_insert
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        resultado = agendar_evento(
            titulo="Reunião de Alinhamento",
            inicio_iso="2026-09-10T14:00:00-03:00",
            duracao_minutos=45,
            descricao="Pauta: arquitetura e infraestrutura",
            localizacao="Google Meet"
        )

        self.assertIn("agendado com sucesso", resultado)
        # Valida que description e location foram incluídos no payload do evento
        mock_events.insert.assert_called_once()
        _, kwargs = mock_events.insert.call_args
        body = kwargs.get("body", {})
        self.assertEqual(body.get("summary"), "Reunião de Alinhamento")
        self.assertEqual(body.get("description"), "Pauta: arquitetura e infraestrutura")
        self.assertEqual(body.get("location"), "Google Meet")

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_consultar_agenda_exibe_localizacao_e_descricao(self, mock_get_service):
        mock_service = MagicMock()
        mock_events = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            "items": [
                {
                    "summary": "Consulta Médica",
                    "start": {"dateTime": "2026-09-10T09:00:00-03:00"},
                    "location": "Hospital Sírio-Libanês",
                    "description": "Levar exames de sangue"
                }
            ]
        }
        mock_events.list.return_value = mock_list
        mock_service.events.return_value = mock_events
        mock_get_service.return_value = mock_service

        resultado = consultar_agenda(dias_a_frente=7)
        self.assertIn("Consulta Médica", resultado)
        self.assertIn("Hospital Sírio-Libanês", resultado)
        self.assertIn("Levar exames de sangue", resultado)

if __name__ == "__main__":
    unittest.main()
