import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from services.briefing_service import (
    montar_resumo_matinal,
    enviar_briefing_matinal,
    _formatar_jogos_furia_dia,
    _MEMORY_BRIEFING_LOGS,
    _reset_briefing_memory
)

class TestFase21MorningBriefing:
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        _reset_briefing_memory()
        yield
        _reset_briefing_memory()

    def test_formatar_jogos_furia_jogo_madrugada_resultado(self):
        # Jogo ocorrido entre 00:00 e 08:00
        jogos_simulados = [
            {
                "time_a": "FURIA",
                "time_b": "MOUZ",
                "campeonato": "IEM Chengdu",
                "horario": "04:30",
                "hora_int": 4,
                "status": "FINALIZADO",
                "placar": "2 x 1",
                "vencedor": "FURIA"
            }
        ]
        res = _formatar_jogos_furia_dia(jogos_simulados)
        assert "FURIA" in res
        assert "MOUZ" in res
        assert "Resultado:" in res
        assert "2 x 1" in res

    def test_formatar_jogos_furia_jogo_tarde_apenas_hora_e_adversario(self):
        # Jogo agendado para depois das 08:00 (ex: 15:30)
        jogos_simulados = [
            {
                "time_a": "FURIA",
                "time_b": "FaZe Clan",
                "campeonato": "ESL Pro League",
                "horario": "15:30",
                "hora_int": 15,
                "status": "AGENDADO",
                "placar": None,
                "vencedor": None
            }
        ]
        res = _formatar_jogos_furia_dia(jogos_simulados)
        assert "FaZe Clan" in res
        assert "15:30" in res
        # Não deve conter resultado
        assert "Resultado:" not in res
        assert "Placar:" not in res

    def test_formatar_jogos_furia_sem_jogos_hoje(self):
        res = _formatar_jogos_furia_dia([])
        assert "Nenhum jogo da FURIA programado para hoje" in res

    @patch("services.briefing_service.consultar_agenda")
    @patch("services.briefing_service.listar_lembretes_pendentes")
    @patch("services.briefing_service._obter_jogos_furia_hoje")
    @patch("services.briefing_service._obter_animes_lancando_hoje")
    def test_montar_resumo_matinal_completo(
        self, mock_animes, mock_furia, mock_lembretes, mock_agenda
    ):
        mock_agenda.return_value = "• 10:00 - Reunião de Planejamento\n• 14:30 - Consulta Médica"
        mock_lembretes.return_value = "• [ ] Pagar conta de luz (Hoje às 12:00)\n• [ ] Comprar ração"
        mock_furia.return_value = [
            {
                "time_a": "FURIA",
                "time_b": "Complexity",
                "campeonato": "Blast Premier",
                "horario": "16:00",
                "hora_int": 16,
                "status": "AGENDADO"
            }
        ]
        mock_animes.return_value = [
            {
                "titulo": "Solo Leveling",
                "episodio": 9,
                "horario": "13:30"
            }
        ]

        resumo = montar_resumo_matinal()
        assert "Bom dia!" in resumo
        assert "Compromissos de Hoje" in resumo
        assert "Reunião de Planejamento" in resumo
        assert "Tarefas & Lembretes" in resumo
        assert "Pagar conta de luz" in resumo
        assert "Jogos da FURIA (CS2)" in resumo
        assert "Complexity" in resumo
        assert "Animes de Hoje" in resumo
        assert "Solo Leveling" in resumo
        assert "Ep. 9" in resumo

    @patch("services.briefing_service.montar_resumo_matinal")
    @patch("services.briefing_service.WhatsAppService.send_text")
    def test_enviar_briefing_matinal_idempotencia(self, mock_send, mock_resumo):
        mock_resumo.return_value = "Texto do Briefing Matinal"
        mock_send.return_value = True

        # Primeiro envio: sucesso
        res1 = enviar_briefing_matinal(force=False)
        assert "Briefing matinal enviado com sucesso" in res1
        assert mock_send.call_count == 1

        # Segundo envio no mesmo dia sem force: bloqueado por idempotência
        res2 = enviar_briefing_matinal(force=False)
        assert "já foi enviado" in res2
        assert mock_send.call_count == 1

        # Terceiro envio com force=True: enviado novamente
        res3 = enviar_briefing_matinal(force=True)
        assert "Briefing matinal enviado com sucesso" in res3
        assert mock_send.call_count == 2

    def test_router_trigger_briefing_unauthorized(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)

        res = client.post("/api/briefing/morning", headers={"apikey": "token_errado"})
        assert res.status_code == 401

    @patch("routers.briefing.enviar_briefing_matinal")
    def test_router_trigger_briefing_authorized(self, mock_enviar):
        from fastapi.testclient import TestClient
        from main import app
        from config.settings import settings
        client = TestClient(app)

        mock_enviar.return_value = "Briefing enviado"
        res = client.post(
            "/api/briefing/morning", 
            headers={"Authorization": f"Bearer {settings.WEBHOOK_TOKEN}"}
        )
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    @patch("services.briefing_service.consultar_agenda")
    @patch("services.briefing_service.listar_lembretes_pendentes")
    def test_consultar_briefing_matinal_pilares_estritos(self, mock_notes, mock_agenda):
        from services.briefing_service import consultar_briefing_matinal
        mock_agenda.return_value = "• 10:00 - Reunião de Planejamento"
        mock_notes.return_value = "• Enviar relatório financeiro"

        res = consultar_briefing_matinal()
        # 4 pilares obrigatórios
        assert "Compromissos de Hoje" in res
        assert "Tarefas & Lembretes" in res
        assert "Jogos da FURIA" in res
        assert "Animes de Hoje" in res

        # Exclusões obrigatórias solicitadas pelo usuário
        assert "Fastback" not in res
        assert "veículo" not in res.lower()
        assert "banco de horas" not in res.lower()
        assert "amanhã" not in res.lower()

    @patch("routers.briefing.montar_resumo_matinal")
    def test_router_preview_briefing_authorized(self, mock_montar):
        from fastapi.testclient import TestClient
        from main import app
        from config.settings import settings
        client = TestClient(app)

        mock_montar.return_value = "Preview Resumo"
        res = client.get(
            "/api/briefing/preview", 
            headers={"apikey": settings.WEBHOOK_TOKEN}
        )
        assert res.status_code == 200
        assert res.json()["preview"] == "Preview Resumo"

