"""
Testes Unitários para Resiliência a Cota 429 do Firestore, Fallback de Chat e Cooldown do Briefing.
"""
import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from google.api_core.exceptions import ResourceExhausted

from config.firebase import (
    DEFAULT_FIRESTORE_TIMEOUT,
    ResilientFirestoreClient,
    is_circuit_breaker_open,
    reset_circuit_breaker,
)
from repositories.chat_repository import ChatRepository, _reset_memory_chat_cache
from services.briefing_service import (
    _disparar_briefing_se_horario_correto,
    _obter_todos_usuarios_briefing,
    _reset_briefing_memory,
    _reset_briefing_preferences,
    salvar_preferencias_briefing,
)
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def clean_resilience_state():
    reset_circuit_breaker()
    _reset_memory_chat_cache()
    _reset_briefing_memory()
    _reset_briefing_preferences()
    UserContext.set_user("daniel", "5571991269995")
    yield
    reset_circuit_breaker()
    _reset_memory_chat_cache()
    _reset_briefing_memory()
    _reset_briefing_preferences()
    UserContext.set_user("daniel", "5571991269995")


class TestFirestoreCircuitBreaker:
    def test_circuit_breaker_trips_on_429_and_fails_fast_without_hitting_raw_client(self):
        raw_client = MagicMock()
        raw_doc = raw_client.collection.return_value.document.return_value
        raw_doc.get.side_effect = ResourceExhausted("Quota exceeded.")

        client = ResilientFirestoreClient(raw_client)

        with pytest.raises(ResourceExhausted):
            client.collection("briefing_preferences").document("daniel").get()

        # Deve ter passado retry=None e timeout=4.0 para impedir retry gRPC de 60s
        _, kwargs = raw_doc.get.call_args
        assert kwargs.get("retry") is None
        assert kwargs.get("timeout") == DEFAULT_FIRESTORE_TIMEOUT
        assert is_circuit_breaker_open() is True

        # Chamadas subsequentes devem falhar imediatamente em 0ms sem chamar o cliente bruto
        raw_doc.get.reset_mock()
        raw_stream = raw_client.collection.return_value.stream
        t0 = time.monotonic()
        with pytest.raises(ResourceExhausted):
            client.collection("briefing_preferences").document("lari").get()
        with pytest.raises(ResourceExhausted):
            list(client.collection("chat_logs").stream())
        elapsed = time.monotonic() - t0

        assert elapsed < 0.1
        raw_doc.get.assert_not_called()
        raw_stream.assert_not_called()

    def test_stream_trips_circuit_breaker_when_iteration_raises_429(self):
        raw_client = MagicMock()

        def failing_stream(*args, **kwargs):
            raise ResourceExhausted("Quota exceeded.")
            yield  # pragma: no cover

        raw_client.collection.return_value.where.return_value.stream.side_effect = failing_stream
        client = ResilientFirestoreClient(raw_client)

        with pytest.raises(ResourceExhausted):
            list(client.collection("chat_logs").where("remoteJid", "==", "123").stream())

        assert is_circuit_breaker_open() is True

    def test_write_batch_unwraps_resilient_refs_and_uses_failfast_commit(self):
        raw_client = MagicMock()
        raw_doc = MagicMock()
        raw_client.collection.return_value.document.return_value = raw_doc
        raw_batch = raw_client.batch.return_value

        client = ResilientFirestoreClient(raw_client)
        doc_ref = client.collection("finance_categories").document()
        batch = client.batch()
        batch.set(doc_ref, {"name": "Lazer"})
        batch.commit()

        # Referência passada ao batch subjacente deve ser a bruta, não o wrapper
        raw_batch.set.assert_called_once_with(raw_doc, {"name": "Lazer"})
        _, commit_kwargs = raw_batch.commit.call_args
        assert commit_kwargs.get("retry") is None
        assert commit_kwargs.get("timeout") == DEFAULT_FIRESTORE_TIMEOUT


class TestChatRepositoryMemoryFallback:
    def test_chat_repository_falls_back_to_memory_cache_on_429(self):
        mock_db = MagicMock()
        mock_db.collection.return_value.add.side_effect = ResourceExhausted("Quota exceeded.")
        mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value.stream.side_effect = (
            ResourceExhausted("Quota exceeded.")
        )

        jid = "5571991269995@s.whatsapp.net"
        with patch("repositories.chat_repository.firebase.db", mock_db):
            ChatRepository.save_log(jid, False, "Oi DAM, tudo bem?")
            ChatRepository.save_log(jid, True, "Tudo ótimo! Como posso ajudar?")
            history = ChatRepository.get_recent_history(jid, limit=10)

        assert len(history) == 2
        assert history[0]["text"] == "Oi DAM, tudo bem?"
        assert history[0]["fromMe"] is False
        assert history[1]["text"] == "Tudo ótimo! Como posso ajudar?"
        assert history[1]["fromMe"] is True


class TestBriefingCooldownAndUserCache:
    @patch("services.briefing_service.montar_resumo_matinal", return_value="Resumo matinal")
    @patch("services.briefing_service.WhatsAppService.send_text", return_value=None)
    def test_briefing_applies_cooldown_after_whatsapp_send_failure(self, mock_send, _mock_resumo):
        salvar_preferencias_briefing(
            "daniel",
            {"userId": "daniel", "horario": "07:30", "ativo": True, "topicos": ["agenda"]},
        )

        with patch("services.briefing_service.firebase.db", None):
            # 1a tentativa no catch-up (08:00 > 07:30) falha porque Evolution API está fechada
            ok1 = _disparar_briefing_se_horario_correto("daniel", "08:00", force=False, permitir_catchup=True)
            assert ok1 is False
            assert mock_send.call_count == 1

            # 2a tentativa minutos depois NÃO deve chamar WhatsApp nem montar resumo novamente (cooldown ativo)
            ok2 = _disparar_briefing_se_horario_correto("daniel", "08:01", force=False, permitir_catchup=True)
            assert ok2 is False
            assert mock_send.call_count == 1

            # Disparo manual forçado ignora cooldown
            ok3 = _disparar_briefing_se_horario_correto("daniel", "07:30", force=True, permitir_catchup=False)
            assert ok3 is True
            assert mock_send.call_count == 2

    def test_obter_todos_usuarios_briefing_caches_result_in_memory(self):
        doc_extra = MagicMock()
        doc_extra.id = "convidado"
        mock_db = MagicMock()
        mock_db.collection.return_value.stream.return_value = [doc_extra]

        with patch("services.briefing_service.firebase.db", mock_db):
            users_first = _obter_todos_usuarios_briefing()
            users_second = _obter_todos_usuarios_briefing()

        assert users_first == ["daniel", "lari", "convidado"]
        assert users_second == ["daniel", "lari", "convidado"]
        mock_db.collection.return_value.stream.assert_called_once()
