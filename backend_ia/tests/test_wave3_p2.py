"""
Testes Automatizados TDD First — Onda 3 (P2 - Médio)
Cobertura:
1. Validação de horário e tópicos no Briefing Matinal (Feature 05)
2. Fuso horário de Brasília e edição isolada de duração na Agenda Google (Feature 06)
3. Prevenção de crash em ano bissexto para lembretes anuais (Feature 07)
4. Busca de alimentos no Dietbox com word boundaries e formatação WhatsApp (Feature 09)
5. Tratamento de separador de milhar brasileiro no divisor de contas (Feature 19)
6. Suporte a números negativos e 'graus' no conversor de unidades (Feature 19)
7. Regex com word boundary no parser de dispositivos da Alexa (Feature 21)
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

from services.briefing_service import configurar_preferencias_briefing
from services.tools.calendar_tool import agendar_evento, editar_evento
from services.tools.notes_tool import calcular_proxima_ocorrencia
from services.tools.nutrition_dietbox_data import buscar_alimento_dietbox
from services.tools.nutrition_tool import consultar_lista_substituicao
from services.tools.restaurant_split_tool import dividir_conta_restaurante
from services.tools.unit_converter_tool import interpretar_e_converter, converter_unidade
from services.tools.alexa_tool import determinar_acao_e_device


class TestWave3P2:

    # =========================================================================
    # 1. Feature 05: Briefing Matinal
    # =========================================================================
    def test_briefing_horario_validation_and_normalization(self):
        """Horário no formato '8h' deve normalizar para '08:00', e horário inválido '25:00' deve ser rejeitado."""
        with patch("services.briefing_service.salvar_preferencias_briefing"):
            # Normalização de '8h' -> '08:00'
            res_ok = configurar_preferencias_briefing(horario="8h")
            assert "08:00" in res_ok

            # Rejeição de '25:00'
            res_err = configurar_preferencias_briefing(horario="25:00")
            assert "❌" in res_err or "inválido" in res_err.lower()

    # =========================================================================
    # 2. Feature 06: Agenda & Google Calendar
    # =========================================================================
    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_calendar_naive_datetime_tz_brasilia(self, mock_get_svc):
        """Data naive ISO sem timezone deve receber TZ_BRASILIA e timezone 'America/Sao_Paulo'."""
        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc
        mock_svc.events().insert().execute.return_value = {"htmlLink": "http://meet"}

        res = agendar_evento(
            titulo="Reunião Tech",
            inicio_iso="2026-11-10T15:00:00",
            duracao_minutos=60
        )
        assert "sucesso" in res.lower()
        call_body = mock_svc.events().insert.call_args[1]["body"]
        assert call_body["start"]["timeZone"] == "America/Sao_Paulo"
        assert "-03:00" in call_body["start"]["dateTime"]

    @patch("services.tools.calendar_tool._get_calendar_service")
    def test_calendar_edit_duration_without_new_start(self, mock_get_svc):
        """Editar apenas a duração (sem novo início) deve atualizar o horário de fim a partir do start original."""
        mock_svc = MagicMock()
        mock_get_svc.return_value = mock_svc
        evento_existente = {
            "id": "evt123",
            "summary": "Alinhamento",
            "start": {"dateTime": "2026-11-10T10:00:00-03:00"},
            "end": {"dateTime": "2026-11-10T10:30:00-03:00"}
        }
        mock_svc.events().list().execute.return_value = {"items": [evento_existente]}
        mock_svc.events().patch().execute.return_value = {
            "summary": "Alinhamento",
            "start": {"dateTime": "2026-11-10T10:00:00-03:00"},
            "end": {"dateTime": "2026-11-10T12:00:00-03:00"}
        }

        res = editar_evento(
            termo_busca="Alinhamento",
            nova_duracao_minutos=120
        )
        assert "sucesso" in res.lower()
        assert mock_svc.events().patch.call_count >= 1
        patch_body = mock_svc.events().patch.call_args[1]["body"]
        assert "end" in patch_body
        assert "12:00:00" in patch_body["end"]["dateTime"]

    # =========================================================================
    # 3. Feature 07: Lembretes Anuais em Ano Bissexto
    # =========================================================================
    def test_notes_leap_year_recurrence(self):
        """Lembrete anual cadastrado em 29/02 não deve estourar ValueError ao avançar para ano não-bissexto."""
        # 2024 é bissexto
        dt_leap = "2024-02-29 10:00"
        prox = calcular_proxima_ocorrencia(dt_leap, "anual")
        # Deve retornar 2025-02-28 10:00
        assert "-02-28" in prox or "-02-29" in prox

    # =========================================================================
    # 4. Feature 09: Nutrição Dietbox Word Boundaries & Formato WhatsApp
    # =========================================================================
    def test_nutrition_dietbox_word_boundaries(self):
        """'milho' não pode casar com 'Óleo Vegetal de Milho' nem 'mel' com 'Ameixa-vermelha'."""
        alimento_milho = buscar_alimento_dietbox("milho")
        assert alimento_milho is not None
        assert "óleo" not in alimento_milho["nome_oficial"].lower()

        alimento_mel = buscar_alimento_dietbox("mel")
        # Se 'mel' não estiver na dieta, não pode retornar 'Ameixa-vermelha'
        if alimento_mel is not None:
            assert "ameixa" not in alimento_mel["nome_oficial"].lower()

    def test_nutrition_substitution_whatsapp_format(self):
        """consultar_lista_substituicao deve usar bullet points nativos do WhatsApp sem tabelas Markdown."""
        res = consultar_lista_substituicao("carboidratos")
        assert "| :--- |" not in res
        assert "•" in res

    # =========================================================================
    # 5. Feature 19: Divisão de Conta e Conversor de Unidades
    # =========================================================================
    def test_restaurant_split_milhar_br(self):
        """Valor com separador de milhar brasileiro 'R$ 1.250,50' não deve ser zerado."""
        consumo = [
            {
                "nome": "Daniel",
                "itens": [{"nome": "Vinho Raro", "valor": "R$ 1.250,50"}]
            }
        ]
        res = dividir_conta_restaurante(consumo_participantes=consumo, taxa_servico=10.0)
        assert "1.250,50" in res or "1375" in res or "1.375,55" in res
        assert "R$ 0,00" not in res

    def test_unit_converter_negative_and_graus(self):
        """Conversor deve suportar temperaturas negativas (-10 C -> 14 F) e remover 'graus'."""
        # -10 °C = 14 °F
        res_neg = interpretar_e_converter("-10 c em f")
        assert "14" in res_neg

        res_graus = interpretar_e_converter("100 graus celsius em f")
        assert "212" in res_graus

    # =========================================================================
    # 6. Feature 21: Parser de Dispositivos Alexa
    # =========================================================================
    def test_alexa_word_boundary_armario_not_ar(self):
        """'ligar armário' não deve acionar o dispositivo 'ar'."""
        disp, estado = determinar_acao_e_device("ligar armário")
        assert disp != "ar"

        disp_ar, estado_ar = determinar_acao_e_device("ligar o ar")
        assert disp_ar == "ar"
        assert estado_ar == "open"
