import unittest
import logging
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from services.security_service import SecurityService, SensitiveDataFilter

class TestFase6Security(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.valid_token = "SuperSecretToken2026!"
        settings.WEBHOOK_TOKEN = self.valid_token
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"

    # =========================================================================
    # 1. Testes de Sanitização de Logs e Mascaramento de Dados Sensíveis
    # =========================================================================

    def test_mask_cpf_formatted_and_unformatted(self):
        """Deve mascarar CPFs formatados e não formatados preservando início e fim"""
        text_formatted = "O CPF do cliente é 123.456.789-01 para cadastro."
        masked_formatted = SecurityService.mask_cpf(text_formatted)
        self.assertIn("123.***.***-01", masked_formatted)
        self.assertNotIn("456.789", masked_formatted)

        text_unformatted = "Identificador CPF 98765432100 registrado."
        masked_unformatted = SecurityService.mask_cpf(text_unformatted)
        self.assertIn("987.***.***-00", masked_unformatted)
        self.assertNotIn("654321", masked_unformatted)

    def test_mask_bearer_token(self):
        """Deve mascarar tokens em cabeçalhos do tipo Bearer"""
        log_msg = "Request autorizado com Header: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.xyz"
        masked = SecurityService.mask_tokens_and_secrets(log_msg)
        self.assertIn("Bearer [REDACTED_TOKEN]", masked)
        self.assertNotIn("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9", masked)

    def test_mask_api_keys(self):
        """Deve mascarar chaves de provedores conhecidos (OpenAI, Google)"""
        openai_log = "Chamando OpenAI com key sk-abcdef1234567890abcdef1234567890"
        masked_openai = SecurityService.mask_tokens_and_secrets(openai_log)
        self.assertIn("[REDACTED_API_KEY]", masked_openai)
        self.assertNotIn("sk-abcdef123456", masked_openai)

        google_log = "Google Gemini key: AIzaSyD1234567890123456789012345678901"
        masked_google = SecurityService.mask_tokens_and_secrets(google_log)
        self.assertIn("[REDACTED_API_KEY]", masked_google)
        self.assertNotIn("AIzaSyD1234567890", masked_google)

    def test_mask_passwords_and_secrets_key_value(self):
        """Deve mascarar pares de chave-valor contendo senhas e segredos"""
        payload_str = '{"user": "admin", "password": "SuperSecretPassword123", "token": "tok_998877"}'
        sanitized = SecurityService.sanitize_log(payload_str)
        self.assertIn('"password": "[REDACTED_SECRET]"', sanitized)
        self.assertIn('"token": "[REDACTED_SECRET]"', sanitized)
        self.assertNotIn("SuperSecretPassword123", sanitized)
        self.assertNotIn("tok_998877", sanitized)

    def test_sanitize_dict_recursively(self):
        """Deve sanitizar dicionários aninhados removendo chaves confidenciais"""
        nested_data = {
            "cliente": "João Silva",
            "cpf": "123.456.789-01",
            "credenciais": {
                "senha": "minhaSenhaForte!",
                "api_key": "chave_secreta_privada",
                "detalhes": {
                    "token": "bearer_interno"
                }
            },
            "mensagens": ["Meu CPF é 12345678901 e minha senha é secreta"]
        }
        sanitized = SecurityService.sanitize_dict(nested_data)
        self.assertEqual(sanitized["cpf"], "[REDACTED_SENSITIVE]")
        self.assertEqual(sanitized["credenciais"]["senha"], "[REDACTED_SENSITIVE]")
        self.assertEqual(sanitized["credenciais"]["api_key"], "[REDACTED_SENSITIVE]")
        self.assertEqual(sanitized["credenciais"]["detalhes"]["token"], "[REDACTED_SENSITIVE]")
        self.assertNotIn("minhaSenhaForte!", str(sanitized))
        self.assertNotIn("chave_secreta_privada", str(sanitized))

    def test_logging_filter(self):
        """SensitiveDataFilter deve sanitizar LogRecords do Python Logging"""
        log_filter = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname=__file__,
            lineno=10,
            msg="Erro ao autenticar usuário com senha: SuperSenha123 e CPF 111.222.333-44",
            args=(),
            exc_info=None
        )
        passed = log_filter.filter(record)
        self.assertTrue(passed)
        self.assertNotIn("SuperSenha123", record.msg)
        self.assertNotIn("111.222.333-44", record.msg)
        self.assertIn("111.***.***-44", record.msg)

    # =========================================================================
    # 2. Testes de Validação Criptográfica de Tokens (Timing Attacks)
    # =========================================================================

    def test_validate_webhook_token_timing_safe(self):
        """Validação de token deve aceitar Bearer e token puro com secrets.compare_digest"""
        # Sucesso token puro
        self.assertTrue(SecurityService.validate_webhook_token("SuperSecretToken2026!", "SuperSecretToken2026!"))
        # Sucesso com prefixo Bearer
        self.assertTrue(SecurityService.validate_webhook_token("Bearer SuperSecretToken2026!", "SuperSecretToken2026!"))
        # Token incorreto
        self.assertFalse(SecurityService.validate_webhook_token("WrongToken", "SuperSecretToken2026!"))
        # Token ausente/None
        self.assertFalse(SecurityService.validate_webhook_token(None, "SuperSecretToken2026!"))
        # Expected token None (webhook aberto)
        self.assertTrue(SecurityService.validate_webhook_token(None, None))

    # =========================================================================
    # 3. Testes de Integração de Webhooks e Headers de Autorização
    # =========================================================================

    def test_whatsapp_webhook_authorization_header_bearer(self):
        """Webhook WhatsApp deve aceitar Authorization: Bearer <token>"""
        headers = {"Authorization": f"Bearer {self.valid_token}"}
        payload = {"event": "status.instance", "data": {}}
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_whatsapp_webhook_apikey_header(self):
        """Webhook WhatsApp deve aceitar apikey: <token>"""
        headers = {"apikey": self.valid_token}
        payload = {"event": "status.instance", "data": {}}
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_whatsapp_webhook_unauthorized(self):
        """Webhook WhatsApp deve rejeitar token ausente ou inválido com 401"""
        # Ausente
        res_no_auth = self.client.post("/api/whatsapp/webhook", json={})
        self.assertEqual(res_no_auth.status_code, 401)
        # Inválido
        res_invalid = self.client.post("/api/whatsapp/webhook", json={}, headers={"apikey": "token_errado"})
        self.assertEqual(res_invalid.status_code, 401)

    @patch("routers.health.firebase.db")
    def test_health_webhook_authorization_bearer_and_apikey(self, mock_db):
        """Webhook Health deve aceitar Authorization Bearer e apikey"""
        mock_collection = MagicMock()
        mock_db.collection.return_value = mock_collection

        payload = {"date": "2026-03-01", "metrics": {"steps": 8000}}

        # 1. Bearer Header
        res_bearer = self.client.post(
            "/api/health-webhook", 
            json=payload, 
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        self.assertEqual(res_bearer.status_code, 200)

        # 2. apikey Header
        res_apikey = self.client.post(
            "/api/health-webhook", 
            json=payload, 
            headers={"apikey": self.valid_token}
        )
        self.assertEqual(res_apikey.status_code, 200)

        # 3. Inválido -> 401
        res_unauth = self.client.post(
            "/api/health-webhook", 
            json=payload, 
            headers={"apikey": "token_errado"}
        )
        self.assertEqual(res_unauth.status_code, 401)

    @patch("routers.billing.WhatsAppService.send_text")
    def test_billing_alert_authorization_bearer_and_apikey(self, mock_send_text):
        """Webhook Billing Alert deve aceitar Bearer e apikey com validação uniforme"""
        import base64
        import json
        pubsub_payload = {
            "message": {
                "data": base64.b64encode(json.dumps({
                    "costAmount": 100.0,
                    "budgetAmount": 100.0,
                    "currencyCode": "BRL"
                }).encode("utf-8")).decode("utf-8")
            }
        }

        # 1. Bearer Header
        res_bearer = self.client.post(
            "/api/billing-alert",
            json=pubsub_payload,
            headers={"Authorization": f"Bearer {self.valid_token}"}
        )
        self.assertEqual(res_bearer.status_code, 200)

        # 2. apikey Header
        res_apikey = self.client.post(
            "/api/billing-alert",
            json=pubsub_payload,
            headers={"apikey": self.valid_token}
        )
        self.assertEqual(res_apikey.status_code, 200)

        # 3. Inválido -> 401
        res_unauth = self.client.post(
            "/api/billing-alert",
            json=pubsub_payload,
            headers={"Authorization": "Bearer token_falso"}
        )
        self.assertEqual(res_unauth.status_code, 401)

if __name__ == '__main__':
    unittest.main()
