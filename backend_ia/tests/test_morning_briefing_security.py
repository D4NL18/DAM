"""
Testes de Segurança Ofensiva (SecOps / Red Team) para o Morning Briefing.
Valida OWASP Top 10: Injeções, Broken Access Control, IDOR, XSS e Vazamento Multi-Tenant.
"""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from config.settings import settings
from services.user_context import UserContext
from services.briefing_service import (
    montar_resumo_matinal,
    enviar_briefing_matinal,
    _obter_telefone_usuario,
    _reset_briefing_memory,
    _reset_briefing_preferences,
    TZ_BRASILIA
)
from services.tools.notes_tool import (
    criar_lembrete,
    _formatar_tags_exibicao as formatar_tags_notes,
    _reset_mock_storage
)

client = TestClient(app)

@pytest.fixture(autouse=True)
def clean_env():
    _reset_briefing_memory()
    _reset_briefing_preferences()
    _reset_mock_storage()
    UserContext.set_user("daniel", "5571991269995")
    yield
    _reset_briefing_memory()
    _reset_briefing_preferences()
    _reset_mock_storage()
    UserContext.set_user("daniel", "5571991269995")


class TestSecOpsMorningBriefing:

    # =========================================================================
    # 1. AUTENTICAÇÃO E CONTROLE DE ACESSO (BROKEN AUTHENTICATION & IDOR)
    # =========================================================================
    def test_red_team_endpoint_sem_autenticacao_bloqueado_401(self):
        """Ataque: Tentar disparar briefing sem credenciais."""
        res = client.post("/api/briefing/morning")
        assert res.status_code == 401
        assert "Não autorizado" in res.json()["detail"]

    def test_red_team_endpoint_token_falso_bloqueado_401(self):
        """Ataque: Injeção de credencial forjada ou inválida."""
        res = client.post("/api/briefing/morning", headers={"apikey": "token_hacker_invalido"})
        assert res.status_code == 401

        res2 = client.post("/api/briefing/morning", headers={"Authorization": "Bearer hacker_payload"})
        assert res2.status_code == 401

    def test_red_team_preview_sem_autenticacao_bloqueado_401(self):
        """Ataque: Pré-visualizar dados de usuários sem autenticação."""
        res = client.get("/api/briefing/preview?user_id=daniel")
        assert res.status_code == 401

    # =========================================================================
    # 2. INJEÇÃO DE PAYLOADS E PATH TRAVERSAL NO USER_ID
    # =========================================================================
    def test_red_team_path_traversal_user_id(self):
        """Ataque: Injeção de Path Traversal no parâmetro user_id."""
        auth_headers = {"apikey": settings.WEBHOOK_TOKEN}
        payloads = [
            "../../../../etc/passwd",
            "..\\..\\windows\\win.ini",
            "' OR '1'='1",
            "<script>alert('xss')</script>",
            "admin%00nullbyte"
        ]

        for payload in payloads:
            # Deve tratar com segurança sem vazar arquivos do sistema ou quebrar o servidor
            res = client.get(f"/api/briefing/preview?user_id={payload}", headers=auth_headers)
            assert res.status_code == 200
            data = res.json()
            assert "preview" in data
            assert "/etc/passwd" not in data["preview"]
            assert "<script>" not in data["preview"]

    # =========================================================================
    # 3. XSS E SANITIZAÇÃO DE TAGS E LEMBRETES
    # =========================================================================
    def test_red_team_xss_e_array_injection_nas_tags(self):
        """Ataque: Injeção de tags maliciosas com XSS, comandos e listas aninhadas."""
        malicious_tags = [
            "<script>alert('xss')</script>",
            "['financas', 'segredo']",
            "'; DROP TABLE users; --",
            "tag_normal",
            "<img src=x onerror=alert(1)>"
        ]

        resultado_fmt = formatar_tags_notes(malicious_tags)
        # O formatador de tags deve reter apenas caracteres [a-zA-Z0-9_\-]
        assert "<script>" not in resultado_fmt
        assert "<img" not in resultado_fmt
        assert "DROP TABLE" not in resultado_fmt
        assert "#tag_normal" in resultado_fmt
        assert "#financas" in resultado_fmt

    # =========================================================================
    # 4. ISOLAMENTO E PREVENÇÃO DE VAZAMENTO MULTI-TENANT (LGPD)
    # =========================================================================
    def test_red_team_multi_tenant_zero_leakage(self):
        """
        Auditoria Estrita LGPD:
        Garante que informações confidenciais do usuário A nunca apareçam para o usuário B.
        """
        # Cria dados sensíveis para Daniel
        UserContext.set_user("daniel", "5571991269995")
        criar_lembrete(
            titulo="Senha do Cofre Bancário: 987654",
            data_hora_lembrete="2026-09-08 09:00",
            tags=["confidencial", "financas"]
        )

        # Cria dados sensíveis para Lari
        UserContext.set_user("lari", "5571983278254")
        criar_lembrete(
            titulo="Exame Confidencial Ginecológico",
            data_hora_lembrete="2026-09-08 10:00",
            tags=["saude", "privado"]
        )

        hoje = datetime(2026, 9, 8, 8, 0, tzinfo=TZ_BRASILIA)

        # Gera o briefing da Lari
        resumo_lari = montar_resumo_matinal(data_alvo=hoje, user_id="lari")
        # NUNCA deve conter informações do Daniel
        assert "Senha do Cofre Bancário" not in resumo_lari
        assert "987654" not in resumo_lari
        assert "Daniel" not in resumo_lari
        assert "Exame Confidencial Ginecológico" in resumo_lari

        # Gera o briefing do Daniel
        resumo_daniel = montar_resumo_matinal(data_alvo=hoje, user_id="daniel")
        # NUNCA deve conter informações da Lari
        assert "Exame Confidencial Ginecológico" not in resumo_daniel
        assert "Senha do Cofre Bancário" in resumo_daniel

    def test_red_team_restauracao_de_contexto_em_caso_de_crash(self):
        """
        Segurança de Concorrência:
        Se a geração do briefing para Lari falhar por exceção interna,
        o contexto de thread/async local DEVE ser restaurado para o caller original,
        evitando contaminação cruzada para requisições subsequentes.
        """
        UserContext.set_user("daniel", "5571991269995")

        with patch("services.briefing_service.obter_preferencias_briefing", side_effect=RuntimeError("Falha simulada no Firestore")):
            with pytest.raises(RuntimeError):
                montar_resumo_matinal(user_id="lari")

        # Após o crash, o contexto deve ter voltado imediatamente para Daniel
        assert UserContext.get_user_id() == "daniel"
        assert UserContext.get_user_phone() == "5571991269995"
