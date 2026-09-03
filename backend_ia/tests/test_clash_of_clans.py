"""
Testes Unitarios -- Clash of Clans Tool (TDD)
Modulo: services/tools/clash_of_clans_tool.py
Cobre: P-001 ao P-010 das Regras de Negocio
"""
import pytest
from unittest.mock import patch, MagicMock

RAID_ONGOING_COM_ATAQUES = {
    "state": "ongoing",
    "members": [
        {"tag": "#ABC987", "attacks": 3, "attackLimit": 6, "bonusAttackLimit": 0},
        {"tag": "#OTHER1", "attacks": 6, "attackLimit": 6, "bonusAttackLimit": 0},
    ]
}
RAID_ONGOING_SEM_ATAQUES = {
    "state": "ongoing",
    "members": [{"tag": "#ABC987", "attacks": 6, "attackLimit": 6, "bonusAttackLimit": 0}]
}
RAID_ENDED = {"state": "ended", "members": []}
RAID_SEM_MEMBRO = {
    "state": "ongoing",
    "members": [{"tag": "#OTHER1", "attacks": 0, "attackLimit": 6, "bonusAttackLimit": 0}]
}
GUERRA_ATIVA_PENDENTE = {
    "state": "inWar",
    "attacksPerMember": 2,
    "clan": {"members": [{"tag": "#ABC987", "attacks": [{"stars": 3}]}]}
}
GUERRA_ATIVA_COMPLETA = {
    "state": "inWar",
    "attacksPerMember": 2,
    "clan": {"members": [{"tag": "#ABC987", "attacks": [{"stars": 3}, {"stars": 2}]}]}
}
GUERRA_NAO_ATIVA = {"state": "notInWar", "attacksPerMember": 2, "clan": {"members": []}}
GUERRA_PREP = {"state": "preparation", "attacksPerMember": 2, "clan": {"members": []}}


class TestTagEncoding:
    def test_encode_hash(self):
        from services.tools.clash_of_clans_tool import _encode_tag
        assert _encode_tag("#ABC987") == "%23ABC987"

    def test_encode_sem_hash(self):
        from services.tools.clash_of_clans_tool import _encode_tag
        assert _encode_tag("ABC987") == "ABC987"

    def test_encode_maiusculo(self):
        from services.tools.clash_of_clans_tool import _encode_tag
        assert _encode_tag("#abc987") == "%23ABC987"


class TestRaidSeasonAlert:
    def test_ataques_pendentes_retorna_alerta(self):
        from services.tools.clash_of_clans_tool import _verificar_raid_season
        r = _verificar_raid_season(RAID_ONGOING_COM_ATAQUES, "#ABC987")
        assert r is not None
        assert "ataque" in r.lower() or "3" in r

    def test_ataques_completos_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_raid_season
        assert _verificar_raid_season(RAID_ONGOING_SEM_ATAQUES, "#ABC987") is None

    def test_season_encerrada_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_raid_season
        assert _verificar_raid_season(RAID_ENDED, "#ABC987") is None

    def test_membro_ausente_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_raid_season
        assert _verificar_raid_season(RAID_SEM_MEMBRO, "#ABC987") is None


class TestClanWarAlert:
    def test_ataques_pendentes_retorna_alerta(self):
        from services.tools.clash_of_clans_tool import _verificar_clan_war
        r = _verificar_clan_war(GUERRA_ATIVA_PENDENTE, "#ABC987")
        assert r is not None
        assert "guerra" in r.lower() or "ataque" in r.lower()

    def test_ataques_completos_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_clan_war
        assert _verificar_clan_war(GUERRA_ATIVA_COMPLETA, "#ABC987") is None

    def test_fora_de_guerra_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_clan_war
        assert _verificar_clan_war(GUERRA_NAO_ATIVA, "#ABC987") is None

    def test_preparacao_retorna_none(self):
        from services.tools.clash_of_clans_tool import _verificar_clan_war
        assert _verificar_clan_war(GUERRA_PREP, "#ABC987") is None


class TestConsultarClashOfClans:
    @patch("services.tools.clash_of_clans_tool._fetch_coc_data")
    @patch("services.tools.clash_of_clans_tool.settings")
    def test_consulta_raid_retorna_string(self, mock_settings, mock_fetch):
        from services.tools.clash_of_clans_tool import consultar_clash_of_clans
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"
        mock_fetch.return_value = RAID_ONGOING_COM_ATAQUES
        r = consultar_clash_of_clans("raid")
        assert isinstance(r, str) and len(r) > 0

    @patch("services.tools.clash_of_clans_tool._fetch_coc_data")
    @patch("services.tools.clash_of_clans_tool.settings")
    def test_consulta_guerra_retorna_string(self, mock_settings, mock_fetch):
        from services.tools.clash_of_clans_tool import consultar_clash_of_clans
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"
        mock_fetch.return_value = GUERRA_ATIVA_PENDENTE
        r = consultar_clash_of_clans("guerra")
        assert isinstance(r, str) and len(r) > 0

    @patch("services.tools.clash_of_clans_tool._fetch_coc_data")
    @patch("services.tools.clash_of_clans_tool.settings")
    def test_api_falha_retorna_erro_amigavel(self, mock_settings, mock_fetch):
        from services.tools.clash_of_clans_tool import consultar_clash_of_clans
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"
        mock_fetch.side_effect = Exception("timeout")
        r = consultar_clash_of_clans("raid")
        assert isinstance(r, str)
        assert any(w in r.lower() for w in ["indisponível", "erro", "não foi possível", "falha"])

    @patch("services.tools.clash_of_clans_tool._fetch_coc_data")
    @patch("services.tools.clash_of_clans_tool.settings")
    def test_guerra_403_war_log_privado_orienta_usuario(self, mock_settings, mock_fetch):
        import httpx
        from services.tools.clash_of_clans_tool import consultar_clash_of_clans
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"

        req = httpx.Request("GET", "https://api.clashofclans.com/v1/clans/%23XYZ123/currentwar")
        resp = httpx.Response(403, request=req)

        def mock_side_effect(endpoint):
            if "currentwar" in endpoint:
                raise httpx.HTTPStatusError("Forbidden", request=req, response=resp)
            if endpoint == "clans/%23XYZ123":
                return {"name": "Os Imortais", "isWarLogPublic": False}
            return {}

        mock_fetch.side_effect = mock_side_effect
        r = consultar_clash_of_clans("guerra")
        assert "Registro Privado" in r
        assert "Tornar registro de guerra público" in r



class TestAlertasBriefingCoC:
    """Testes para _obter_alertas_coc no briefing matinal."""

    @patch("services.briefing_service._fetch_coc_data")
    @patch("services.briefing_service.settings")
    def test_sem_configuracao_retorna_vazio(self, mock_settings, mock_fetch):
        from services.briefing_service import _obter_alertas_coc
        mock_settings.COC_API_TOKEN = ""
        mock_settings.COC_CLAN_TAG = ""
        mock_settings.COC_PLAYER_TAG = ""
        resultado = _obter_alertas_coc()
        assert resultado == ""
        mock_fetch.assert_not_called()

    @patch("services.briefing_service._fetch_coc_data")
    @patch("services.briefing_service.settings")
    def test_com_ataques_pendentes_retorna_alertas(self, mock_settings, mock_fetch):
        from services.briefing_service import _obter_alertas_coc
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"

        def side_effect(endpoint):
            if "capitalraidseasons" in endpoint:
                return {"items": [{"state": "ongoing", "members": [
                    {"tag": "#ABC987", "attacks": 2, "attackLimit": 6, "bonusAttackLimit": 0}
                ]}]}
            elif "currentwarleaguegroup" in endpoint:
                raise Exception("not in league")
            else:
                return {"state": "notInWar", "attacksPerMember": 2, "clan": {"members": []}}

        mock_fetch.side_effect = side_effect
        resultado = _obter_alertas_coc()
        assert "Raid Weekend" in resultado

    @patch("services.briefing_service._fetch_coc_data")
    @patch("services.briefing_service.settings")
    def test_sem_pendencias_retorna_vazio(self, mock_settings, mock_fetch):
        from services.briefing_service import _obter_alertas_coc
        mock_settings.COC_API_TOKEN = "fake"
        mock_settings.COC_CLAN_TAG = "#XYZ123"
        mock_settings.COC_PLAYER_TAG = "#ABC987"

        def side_effect(endpoint):
            if "capitalraidseasons" in endpoint:
                return {"items": [{"state": "ended", "members": []}]}
            elif "currentwarleaguegroup" in endpoint:
                raise Exception("not in league")
            else:
                return {"state": "notInWar", "attacksPerMember": 2, "clan": {"members": []}}

        mock_fetch.side_effect = side_effect
        resultado = _obter_alertas_coc()
        assert resultado == ""
