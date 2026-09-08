import os
import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from config.settings import settings

class TestHealthWebhook(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Mock para evitar que a inicialização do firebase falhe durante o teste
        self.patcher_firebase = patch('routers.health.firebase.db')
        self.mock_db = self.patcher_firebase.start()
        
        # Seta o token esperado para testes
        settings.WEBHOOK_TOKEN = "TEST_TOKEN"

    def tearDown(self):
        self.patcher_firebase.stop()

    def test_health_webhook_unauthorized(self):
        response = self.client.post("/api/health-webhook", json={"test": "data"})
        self.assertEqual(response.status_code, 401)

    def test_health_webhook_success(self):
        payload = {
            "date": "2024-03-01",
            "metrics": {
                "steps": 10000,
                "activeEnergy": 500,
                "heartRate": 72
            }
        }
        headers = {"Authorization": "Bearer TEST_TOKEN"}
        response = self.client.post("/api/health-webhook", json=payload, headers=headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "success", "message": "Health data received"})
        self.mock_db.collection.assert_called_with("health_metrics")
        self.mock_db.collection().add.assert_called_once()

if __name__ == '__main__':
    unittest.main()
