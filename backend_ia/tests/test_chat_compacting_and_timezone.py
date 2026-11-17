import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import zoneinfo
from repositories.chat_repository import ChatRepository
from config.timezone import TZ_BRASILIA, get_brasilia_now
from services.user_context import UserContext


@pytest.fixture(autouse=True)
def setup_user():
    UserContext.set_user("daniel", "5511999999999")


class TestChatCompactingAndTimezone:
    """Suíte de testes para corte às 00:00 BRT e compactação indexada do histórico de chat."""

    @patch("repositories.chat_repository.firebase.db")
    def test_cutoff_is_00_00_brasilia_time(self, mock_db):
        """
        O corte de mensagens ativas deve ser exatamente às 00:00 no horário de Brasília (UTC-3),
        não em UTC (que seria 21h BRT).
        """
        now_br = get_brasilia_now()
        today_00h_br = now_br.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Mensagem enviada ontem às 23:50 BRT
        yesterday_msg_time = today_00h_br - timedelta(minutes=10)
        # Mensagem enviada hoje às 00:10 BRT
        today_msg_time = today_00h_br + timedelta(minutes=10)

        doc_yesterday = MagicMock()
        doc_yesterday.to_dict.return_value = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "text": "Mensagem de ontem às 23h50",
            "timestamp": yesterday_msg_time
        }

        doc_today = MagicMock()
        doc_today.to_dict.return_value = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "text": "Mensagem de hoje às 00h10",
            "timestamp": today_msg_time
        }

        mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value.stream.return_value = [
            doc_today, doc_yesterday
        ]
        # Mock do histórico compactado retornando vazio para teste isolado
        mock_db.collection.return_value.where.return_value.order_by.return_value.limit.return_value.get.return_value = []

        history = ChatRepository.get_recent_history("5511999999999@s.whatsapp.net")

        # Apenas a mensagem de hoje deve estar nas mensagens ativas do dia
        texts = [m.get("text") for m in history]
        assert "Mensagem de hoje às 00h10" in texts
        assert "Mensagem de ontem às 23h50" not in texts

    @patch("repositories.chat_repository.firebase.db")
    def test_compact_and_archive_previous_history_excludes_daily_briefing(self, mock_db):
        """
        Ao compactar o histórico anterior, o ChatRepository deve excluir mensagens de resumo matinal/diário
        e salvar o histórico compactado indexado na coleção 'chat_history_compacted'.
        """
        now_br = get_brasilia_now()
        yesterday_date = (now_br - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_ts = now_br - timedelta(days=1)

        # Mensagens de ontem
        msg_user = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "text": "Lembrar de comprar ração do gato amanhã",
            "timestamp": yesterday_ts
        }
        msg_briefing = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": True,
            "text": "🌅 *DAM Briefing Matinal* - 06 de Novembro de 2026\n• Agenda: reuniões...\n• Animes: One Piece...",
            "timestamp": yesterday_ts
        }
        msg_bot = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": True,
            "text": "Anotado! Criei o lembrete para comprar ração do gato.",
            "timestamp": yesterday_ts
        }

        doc1 = MagicMock(); doc1.to_dict.return_value = msg_user
        doc2 = MagicMock(); doc2.to_dict.return_value = msg_briefing
        doc3 = MagicMock(); doc3.to_dict.return_value = msg_bot

        # Mock da busca de mensagens anteriores
        mock_db.collection.return_value.where.return_value.where.return_value.stream.return_value = [doc1, doc2, doc3]
        
        mock_doc_ref = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref

        res = ChatRepository.compact_and_archive_history(
            remote_jid="5511999999999@s.whatsapp.net",
            target_date=yesterday_date
        )

        assert res is not None
        assert res.get("status") == "success"
        assert res.get("message_count") == 2  # 2 mensagens (a do briefing diário foi excluída!)

        # Verifica se salvou na coleção 'chat_history_compacted'
        mock_db.collection.assert_any_call(ChatRepository.COMPACTED_COLLECTION)
        saved_payload = mock_doc_ref.set.call_args[0][0]
        assert saved_payload["remoteJid"] == "5511999999999@s.whatsapp.net"
        assert saved_payload["date"] == yesterday_date
        assert "Lembrar de comprar ração do gato" in saved_payload["compactedText"]
        assert "🌅 *DAM Briefing Matinal*" not in saved_payload["compactedText"]

    @patch("repositories.chat_repository.firebase.db")
    def test_get_recent_history_injects_compacted_summary_when_present(self, mock_db):
        """
        Quando houver histórico compactado recente no banco, get_recent_history deve injetá-lo
        como turno de contexto inicial para a IA manter a continuidade da memória.
        """
        now_br = get_brasilia_now()
        today_00h = now_br.replace(hour=0, minute=0, second=0, microsecond=0)

        # Mensagem ativa de hoje
        doc_today = MagicMock()
        doc_today.to_dict.return_value = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": False,
            "text": "E aí, o que temos para hoje?",
            "timestamp": today_00h + timedelta(hours=8)
        }

        # Mock da coleção chat_logs
        col_logs = MagicMock()
        col_logs.where.return_value.order_by.return_value.limit.return_value.stream.return_value = [doc_today]

        # Mock da coleção chat_history_compacted com resumo de ontem
        col_compacted = MagicMock()
        compacted_doc = MagicMock()
        compacted_doc.to_dict.return_value = {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "date": "2026-11-06",
            "compactedText": "[User]: Falamos sobre finanças e mercado ontem | [DAM]: Registrado R$ 120"
        }
        col_compacted.where.return_value.order_by.return_value.limit.return_value.stream.return_value = [compacted_doc]

        def collection_side_effect(name):
            if name == ChatRepository.COLLECTION:
                return col_logs
            if name == ChatRepository.COMPACTED_COLLECTION:
                return col_compacted
            return MagicMock()

        mock_db.collection.side_effect = collection_side_effect

        history = ChatRepository.get_recent_history("5511999999999@s.whatsapp.net")

        # Deve conter o contexto compactado e a mensagem de hoje
        assert len(history) >= 2
        primeiro_texto = history[0].get("text")
        assert "Histórico compactado dos dias anteriores" in primeiro_texto or "contexto anterior" in primeiro_texto.lower()
        assert "Falamos sobre finanças e mercado ontem" in primeiro_texto
        assert history[-1].get("text") == "E aí, o que temos para hoje?"

    @patch("repositories.chat_repository.firebase.db", None)
    def test_chat_repository_graceful_when_db_none(self):
        """Quando o Firebase estiver indisponível, métodos não lançam exceção."""
        assert ChatRepository.get_recent_history("5511999999999@s.whatsapp.net") == []
        ChatRepository.save_log("5511999999999@s.whatsapp.net", True, "Teste")
        res = ChatRepository.compact_and_archive_history("5511999999999@s.whatsapp.net")
        assert res.get("status") == "skipped"
