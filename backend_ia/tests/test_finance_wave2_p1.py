"""
Testes Automatizados TDD First — Onda 2 (P1 - Alto)
Cobertura:
1. Eliminação de Full-Scans no Firestore (Filtro obrigatório .where("userId", "==", effective_user))
2. Proteção contra IDOR em rotas de mutação financeira (PUT/DELETE /transactions, /categories, /cards)
3. Materialização de despesas fixas projetadas (proj_...) em edição e deleção
4. Correção contábil no dashboard (Receitas não somadas a total_spent)
5. Bloqueio de vazamento de transações sem data (_transacao_no_periodo)
6. Desduplicação do clear_cache e limite LRU no ConversationCacheService
7. Métricas dinâmicas reais no FinOps Scorecard GCP
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from main import app
from services.cache_service import ConversationCacheService, QueryVolatility, CacheEntry
from services.tools.gcp_billing_tool import calcular_finops_scorecard

client = TestClient(app)


class TestFinanceWave2P1:

    def _criar_mock_doc(self, doc_id, data):
        doc = MagicMock()
        doc.id = doc_id
        doc.to_dict.return_value = data
        doc.exists = True
        doc.get.return_value = doc
        doc.reference = MagicMock()
        return doc

    # =========================================================================
    # 1. Eliminação de Full-Scans no Firestore (.where("userId", "==", user))
    # =========================================================================
    def test_finance_dashboard_queries_with_user_id_where(self):
        """Dashboard financeiro deve usar .where('userId', '==', effective_user) para categorias e finances."""
        mock_db = MagicMock()
        mock_col_finances = MagicMock()
        mock_col_categories = MagicMock()

        # Mock collections
        def get_collection(name):
            if name == "finances":
                return mock_col_finances
            elif name == "finance_categories":
                return mock_col_categories
            return MagicMock()

        mock_db.collection.side_effect = get_collection
        mock_col_categories.where.return_value.stream.return_value = []
        mock_col_finances.where.return_value.stream.return_value = []

        with patch("config.firebase.db", mock_db):
            res = client.get("/api/v1/finance/dashboard?year=2026&month=11", headers={"X-User-Id": "mariana"})
            assert res.status_code == 200

            # Verifica se foi feito where com userId == mariana
            mock_col_finances.where.assert_called_with("userId", "==", "mariana")

    def test_finance_trends_queries_with_user_id_where(self):
        """Tendências financeiras devem consultar o Firestore filtrando por userId."""
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col
        mock_col.where.return_value.stream.return_value = []

        with patch("config.firebase.db", mock_db):
            res = client.get("/api/v1/finance/trends?period=last6months", headers={"X-User-Id": "mariana"})
            assert res.status_code == 200
            mock_col.where.assert_called_with("userId", "==", "mariana")

    def test_finance_tool_obter_documentos_com_user_id(self):
        """_obter_documentos_financas deve filtrar por userId quando fornecido."""
        from services.tools.finance_tool import _obter_documentos_financas
        mock_col = MagicMock()
        agora = datetime.now(timezone.utc)

        # Act
        _obter_documentos_financas(mock_col, agora, agora, dias_retroativos=None, user_id="daniel")

        # Assert: where com userId deve ter sido invocado
        mock_col.where.assert_any_call("userId", "==", "daniel")

    # =========================================================================
    # 2. Correção Contábil em routers/dashboard.py (Sem somar receitas a total_spent)
    # =========================================================================
    def test_dashboard_monthly_summary_ignores_income_and_isolates_user(self):
        """get_finance_monthly_summary não deve somar receitas (type='income') a total_spent e deve filtrar userId."""
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_db.collection.return_value = mock_col

        dt_str = "2026-11-05T12:00:00Z"
        doc_gasto = self._criar_mock_doc("tx1", {
            "userId": "daniel",
            "amount": 100.0,
            "type": "expense_variable",
            "category": "Mercado",
            "date": dt_str
        })
        doc_receita = self._criar_mock_doc("tx2", {
            "userId": "daniel",
            "amount": 5000.0,
            "type": "income",
            "category": "Receitas",
            "date": dt_str
        })
        doc_outro_user = self._criar_mock_doc("tx3", {
            "userId": "mariana",
            "amount": 300.0,
            "type": "expense_variable",
            "category": "Lazer",
            "date": dt_str
        })

        mock_col.where.return_value.stream.return_value = [doc_gasto, doc_receita]

        with patch("config.firebase.db", mock_db):
            res = client.get("/api/v1/finance/monthly-summary?year=2026&month=11", headers={"X-User-Id": "daniel"})
            assert res.status_code == 200
            data = res.json()
            # totalSpent deve ser exatamente 100.0, NUNCA 5100.0 ou 5400.0!
            assert data["totalSpent"] == 100.0

    # =========================================================================
    # 3. Proteção contra IDOR e Validação de Propriedade
    # =========================================================================
    def test_update_transaction_idor_protection(self):
        """PUT /transactions/{tx_id} deve barrar alteração de transação pertencente a outro usuário (HTTP 403 ou 404)."""
        mock_db = MagicMock()
        mock_doc = self._criar_mock_doc("tx-daniel-1", {
            "userId": "daniel",
            "description": "Jantar",
            "amount": 80.0
        })
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("config.firebase.db", mock_db):
            # Usuário 'mariana' tentando alterar transação do 'daniel'
            res = client.put(
                "/api/v1/finance/transactions/tx-daniel-1",
                json={"description": "Hackeado", "amount": 1.0},
                headers={"X-User-Id": "mariana"}
            )
            assert res.status_code in [403, 404]

    def test_delete_transaction_idor_protection(self):
        """DELETE /transactions/{tx_id} deve barrar deleção de transação pertencente a outro usuário."""
        mock_db = MagicMock()
        mock_doc = self._criar_mock_doc("tx-daniel-1", {
            "userId": "daniel",
            "description": "Almoço",
            "amount": 50.0
        })
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc

        with patch("config.firebase.db", mock_db):
            res = client.delete(
                "/api/v1/finance/transactions/tx-daniel-1",
                headers={"X-User-Id": "mariana"}
            )
            assert res.status_code in [403, 404]

    # =========================================================================
    # 4. Materialização de Despesas Fixas Projetadas (proj_...)
    # =========================================================================
    def test_update_projected_transaction_materializes_new_document(self):
        """Ao editar uma despesa projetada proj_orig_year_month, um novo documento materializado deve ser criado."""
        mock_db = MagicMock()
        mock_origin_doc = self._criar_mock_doc("orig123", {
            "userId": "daniel",
            "description": "Internet Fibra",
            "amount": 120.0,
            "category": "Casa",
            "type": "expense_fixed",
            "payment_method": "Cartão de Crédito Pessoal",
            "date": "2026-01-05T12:00:00Z"
        })

        mock_new_ref = MagicMock()
        mock_new_ref.id = "materialized-id-999"
        mock_db.collection.return_value.document.side_effect = lambda doc_id=None: (
            mock_origin_doc if doc_id == "orig123" else mock_new_ref
        )

        with patch("config.firebase.db", mock_db):
            payload = {
                "description": "Internet Fibra (Promoção)",
                "amount": 99.90,
                "category": "Casa"
            }
            res = client.put(
                "/api/v1/finance/transactions/proj_orig123_2026_11",
                json=payload,
                headers={"X-User-Id": "daniel"}
            )
            assert res.status_code in [200, 201]
            data = res.json()
            assert data["success"] is True

            # Verifica se foi gravado o novo documento materializado com originId
            mock_new_ref.set.assert_called_once()
            saved_call_data = mock_new_ref.set.call_args[0][0]
            assert saved_call_data["amount"] == 99.90
            assert saved_call_data["originId"] == "orig123"
            assert saved_call_data["isRecurring"] is False

    def test_delete_projected_transaction_excludes_for_target_month(self):
        """Ao deletar uma despesa projetada proj_orig_year_month, deve registrar exclusão/tombstone para aquele mês."""
        mock_db = MagicMock()
        mock_origin_doc = self._criar_mock_doc("orig123", {
            "userId": "daniel",
            "description": "Academia",
            "amount": 150.0,
            "category": "Saúde",
            "type": "expense_fixed"
        })
        mock_tombstone_ref = MagicMock()
        mock_tombstone_ref.id = "tombstone-999"
        mock_db.collection.return_value.document.side_effect = lambda doc_id=None: (
            mock_origin_doc if doc_id == "orig123" else mock_tombstone_ref
        )

        with patch("config.firebase.db", mock_db):
            res = client.delete(
                "/api/v1/finance/transactions/proj_orig123_2026_11",
                headers={"X-User-Id": "daniel"}
            )
            assert res.status_code == 200
            assert res.json()["success"] is True
            mock_tombstone_ref.set.assert_called_once()
            saved_tombstone = mock_tombstone_ref.set.call_args[0][0]
            assert saved_tombstone["originId"] == "orig123"
            assert saved_tombstone["amount"] == 0.0

    # =========================================================================
    # 5. Prevenção de Vazamento de Transações sem Data
    # =========================================================================
    def test_undated_transaction_does_not_leak_into_monthly_period(self):
        """Transação sem data (dt is None) NUNCA deve ser incluída no período filtrado."""
        from services.tools.finance_tool import _transacao_no_periodo
        agora = datetime.now(timezone.utc)
        assert _transacao_no_periodo(None, agora, 2026, 11, None) is False

    # =========================================================================
    # 6. ConversationCacheService: clear_cache desduplicado e limite LRU
    # =========================================================================
    def test_cache_service_clear_cache_with_domain_and_all(self):
        """clear_cache deve aceitar domain opcional ou limpar tudo sem conflito de assinatura."""
        ConversationCacheService.clear_cache()
        agora = datetime.now()
        ConversationCacheService._l1_cache["k1"] = CacheEntry("user1", "q1", "r1", QueryVolatility.REALTIME_VOLATILE, agora, agora, 60)
        ConversationCacheService._l1_cache["k2"] = CacheEntry("user1", "q2", "r2", QueryVolatility.STATIC_INFORMATIONAL, agora, agora, 60)

        # Limpar apenas REALTIME_VOLATILE
        ConversationCacheService.clear_cache(domain=QueryVolatility.REALTIME_VOLATILE)
        assert "k1" not in ConversationCacheService._l1_cache
        assert "k2" in ConversationCacheService._l1_cache

        # Limpar tudo
        ConversationCacheService.clear_cache()
        assert len(ConversationCacheService._l1_cache) == 0

    def test_cache_service_l1_eviction_lru(self):
        """_l1_cache deve respeitar o limite máximo de 500 entradas descartando a mais antiga."""
        ConversationCacheService.clear_cache()
        # Adicionar 505 entradas
        for i in range(505):
            ConversationCacheService.save_response("user1@s.whatsapp.net", f"pergunta_{i}", f"resposta_{i}", custom_ttl=3600)

        assert len(ConversationCacheService._l1_cache) <= 500

    # =========================================================================
    # 7. GCP Billing Tool: FinOps Scorecard Dinâmico
    # =========================================================================
    def test_finops_scorecard_dynamic_metrics(self):
        """calcular_finops_scorecard deve integrar métricas reais do cache."""
        ConversationCacheService.reset_metrics()
        ConversationCacheService._metrics["hits"] = 40
        ConversationCacheService._metrics["misses"] = 10
        ConversationCacheService._metrics["tokens_saved_estimated"] = 80000

        scorecard = calcular_finops_scorecard()
        assert "score_global" in scorecard
        assert scorecard["score_global"] >= 4.5
        assert "pilares" in scorecard
        gov_ia = scorecard["pilares"]["governanca_ia_tokens"]
        assert "80" in gov_ia["detalhes"] or "tokens" in gov_ia["detalhes"].lower()
