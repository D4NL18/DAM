import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from main import app
from config.settings import settings

class TestWebhookSecurity(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        settings.WEBHOOK_TOKEN = "DamBot2026SecureKey!"
        settings.ALLOWED_PHONE_NUMBER = "5511987654321"

    def test_secops_blocks_sql_injection_in_apikey(self):
        """Injeção SQL no header de autenticação deve ser bloqueada com 401"""
        malicious_headers = {"apikey": "' OR '1'='1"}
        response = self.client.post("/api/whatsapp/webhook", json={"test": "hack"}, headers=malicious_headers)
        self.assertEqual(response.status_code, 401)

    def test_secops_blocks_invalid_token(self):
        """Tentativa de acesso com token aleatório deve retornar 401"""
        headers = {"apikey": "invalid_token_attempt"}
        response = self.client.post("/api/whatsapp/webhook", json={"test": "data"}, headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_secops_blocks_spoofed_jid_domain(self):
        """JID com número do usuário embutido em domínio falso deve ser rejeitado"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        # Tentativa de spoofing colocando o número alvo como domínio ou canal
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "attacker@5511987654321.com",
                    "fromMe": False,
                    "id": "HACK_001"
                },
                "message": {"conversation": "exploit"}
            }
        }
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

    def test_secops_blocks_group_spoofing(self):
        """Mesmo com número no ID do grupo, deve ser rejeitado"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        payload = {
            "event": "messages.upsert",
            "data": {
                "key": {
                    "remoteJid": "5511987654321-1600000000@g.us",
                    "fromMe": False,
                    "id": "HACK_002"
                },
                "message": {"conversation": "hack no grupo"}
            }
        }
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

    def test_secops_survives_malformed_nested_json(self):
        """Payload truncado ou aninhado maliciosamente não deve estourar 500"""
        headers = {"apikey": "DamBot2026SecureKey!"}
        payload = {"event": "messages.upsert", "data": "invalid_type_string_instead_of_dict"}
        response = self.client.post("/api/whatsapp/webhook", json=payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "ignored")

if __name__ == '__main__':
    unittest.main()
