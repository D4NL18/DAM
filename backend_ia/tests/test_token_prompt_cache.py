import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from services.cache_service import (
    ConversationCacheService,
    QueryVolatility,
    CacheEntry
)


class TestTokenPromptCache:
    """Suíte de testes para validação do Cache Inteligente de Conversas e Otimização de Tokens (PC-08)."""

    def setup_method(self):
        # Limpa o cache L1 em memória antes de cada teste
        ConversationCacheService.clear_cache()

    def test_normalize_query_and_cache_key(self):
        """RN-CACHE-002: Normalização semântica e geração de chaves seguras."""
        jid1 = "5511999998888@s.whatsapp.net"
        jid2 = "5511977776666@s.whatsapp.net"

        q1 = "Tenho guerra no Clash hoje?"
        q2 = "tenho guerra no clash hoje"
        q3 = "  TENHO GUERRA NO CLASH HOJE?!  "

        k1 = ConversationCacheService.generate_cache_key(jid1, q1)
        k2 = ConversationCacheService.generate_cache_key(jid1, q2)
        k3 = ConversationCacheService.generate_cache_key(jid1, q3)

        # Mesma query normalizada para o mesmo usuário gera a mesma chave
        assert k1 == k2
        assert k2 == k3

        # RN-CACHE-003: Usuários diferentes geram chaves estritamente diferentes
        k_other_user = ConversationCacheService.generate_cache_key(jid2, q1)
        assert k1 != k_other_user

    def test_classify_query_volatility(self):
        """RN-CACHE-001: Roteamento Semântico de Volatilidade."""
        # 1. Trânsito / Tempo Real -> REALTIME_VOLATILE
        assert ConversationCacheService.classify_query_volatility("Como tá o trânsito para o trabalho?") == QueryVolatility.REALTIME_VOLATILE
        assert ConversationCacheService.classify_query_volatility("qual o tempo de rota até a Paulista?") == QueryVolatility.REALTIME_VOLATILE
        assert ConversationCacheService.classify_query_volatility("melhor horário para sair agora?") == QueryVolatility.REALTIME_VOLATILE

        # 2. Ações de Escrita / Mutações -> STATE_CHANGING_ACTION
        assert ConversationCacheService.classify_query_volatility("Gastei R$ 45 no almoço no cartão de crédito") == QueryVolatility.STATE_CHANGING_ACTION
        assert ConversationCacheService.classify_query_volatility("cria um lembrete para pagar o condomínio amanhã") == QueryVolatility.STATE_CHANGING_ACTION
        assert ConversationCacheService.classify_query_volatility("tranca o carro por favor") == QueryVolatility.STATE_CHANGING_ACTION
        assert ConversationCacheService.classify_query_volatility("bater ponto 09:00 entrada") == QueryVolatility.STATE_CHANGING_ACTION

        # 3. Clash of Clans -> CLASH_OF_CLANS
        assert ConversationCacheService.classify_query_volatility("Tenho guerra no clash hoje?") == QueryVolatility.CLASH_OF_CLANS
        assert ConversationCacheService.classify_query_volatility("quantos ataques faltam na guerra do clash?") == QueryVolatility.CLASH_OF_CLANS
        assert ConversationCacheService.classify_query_volatility("como tá o raid da capital do clã?") == QueryVolatility.CLASH_OF_CLANS

        # 4. Counter-Strike 2 / Esports -> CS2_ESPORTS
        assert ConversationCacheService.classify_query_volatility("Quando a FURIA joga?") == QueryVolatility.CS2_ESPORTS
        assert ConversationCacheService.classify_query_volatility("tem jogo de cs hoje?") == QueryVolatility.CS2_ESPORTS
        assert ConversationCacheService.classify_query_volatility("qual o próximo jogo da furia no cs2?") == QueryVolatility.CS2_ESPORTS

        # 5. Informações Estáticas -> STATIC_INFORMATIONAL
        assert ConversationCacheService.classify_query_volatility("onde posso assistir Oppenheimer?") == QueryVolatility.STATIC_INFORMATIONAL
        assert ConversationCacheService.classify_query_volatility("posso trocar arroz por batata doce na dieta?") == QueryVolatility.STATIC_INFORMATIONAL
        assert ConversationCacheService.classify_query_volatility("quantos gramas tem 1 xícara de farinha?") == QueryVolatility.STATIC_INFORMATIONAL

    def test_clash_of_clans_cache_reuse(self):
        """Demanda Usuário: Perguntar sobre guerra no clash 2x não precisa pedir 2x, usa a mesma resposta."""
        jid = "5511999998888@s.whatsapp.net"
        pergunta = "Tenho guerra no clash hoje?"
        resposta = "⚔️ *Guerra de Clãs ativa!* Você ainda tem 1 ataque pendente contra o Clã Alpha."

        # Inicialmente não há cache
        cached = ConversationCacheService.get_cached_response(jid, pergunta)
        assert cached is None

        # Salva a resposta no cache
        saved = ConversationCacheService.save_response(
            remote_jid=jid,
            query=pergunta,
            response_text=resposta
        )
        assert saved is True

        # Segunda consulta retorna exatamente a resposta em cache
        cached_2x = ConversationCacheService.get_cached_response(jid, pergunta)
        assert cached_2x is not None
        assert cached_2x == resposta

    def test_traffic_never_cached(self):
        """Demanda Usuário: Respostas que podem variar devem ser checadas novamente, como trânsito."""
        jid = "5511999998888@s.whatsapp.net"
        pergunta = "Como está o trânsito para a Paulista agora?"
        resposta = "🚗 Trânsito moderado: 28 minutos via Avenida 23 de Maio."

        # Tenta salvar no cache
        saved = ConversationCacheService.save_response(
            remote_jid=jid,
            query=pergunta,
            response_text=resposta
        )
        # O serviço deve recusar salvar consultas de trânsito em cache (ou ter TTL 0)
        assert saved is False

        # Consulta subsequente deve ser miss
        cached = ConversationCacheService.get_cached_response(jid, pergunta)
        assert cached is None

    def test_cs2_dynamic_ttl_more_than_two_hours_away(self):
        """
        Demanda Usuário: No caso de jogo de CS, o cache pode ser até 2h antes do jogo
        porque depois pode mudar o horário.
        Cenário: Jogo daqui a 4 horas -> Cache expira em 2 horas (ou seja, 2h antes da partida).
        """
        now = datetime(2026, 9, 3, 14, 0, 0)
        game_time = datetime(2026, 9, 3, 18, 0, 0) # Jogo às 18:00 (daqui a 4h)

        ttl = ConversationCacheService.calculate_cs2_ttl(game_time=game_time, current_time=now)
        # 18:00 - 2h = 16:00. De 14:00 até 16:00 são 2 horas = 7200 segundos
        assert ttl == 7200

        jid = "5511999998888@s.whatsapp.net"
        pergunta = "Quando a FURIA joga?"
        resposta = "🔫 FURIA vs Vitality hoje às 18:00 (MD3)."

        with patch("services.cache_service.datetime") as mock_dt:
            mock_dt.now.return_value = now
            mock_dt.fromtimestamp = datetime.fromtimestamp

            ConversationCacheService.save_response(
                remote_jid=jid,
                query=pergunta,
                response_text=resposta,
                custom_ttl=ttl
            )

            # 1 hora depois (15:00): faltam 3h para o jogo, ainda está dentro do cache (antes das 16:00)
            mock_dt.now.return_value = now + timedelta(hours=1)
            cached_1h = ConversationCacheService.get_cached_response(jid, pergunta)
            assert cached_1h == resposta

            # 2 horas e 5 minutos depois (16:05): faltam menos de 2h para o jogo, cache expirou!
            mock_dt.now.return_value = now + timedelta(hours=2, minutes=5)
            cached_expired = ConversationCacheService.get_cached_response(jid, pergunta)
            assert cached_expired is None

    def test_cs2_dynamic_ttl_less_than_two_hours_away(self):
        """
        Cenário: Jogo daqui a 1 hora (menos de 2h para o jogo) ou ao vivo.
        O cache deve ser desabilitado (TTL = 0 ou não cachear).
        """
        now = datetime(2026, 9, 3, 17, 0, 0)
        game_time = datetime(2026, 9, 3, 18, 0, 0) # Jogo daqui a 1h

        ttl = ConversationCacheService.calculate_cs2_ttl(game_time=game_time, current_time=now)
        # Como falta menos de 2 horas para o jogo, TTL deve ser 0
        assert ttl == 0

        jid = "5511999998888@s.whatsapp.net"
        pergunta = "Quando a FURIA joga?"
        resposta = "🔫 FURIA vs Vitality às 18:00 (Aquecendo)."

        saved = ConversationCacheService.save_response(
            remote_jid=jid,
            query=pergunta,
            response_text=resposta,
            custom_ttl=ttl
        )
        assert saved is False

        cached = ConversationCacheService.get_cached_response(jid, pergunta)
        assert cached is None

    def test_mutations_never_cached(self):
        """RN-CACHE-001: Mutações de estado nunca são gravadas em cache."""
        jid = "5511999998888@s.whatsapp.net"
        queries = [
            "gastei 50 reais no cartão de crédito",
            "cria uma nota com a chave pix do joão",
            "agenda uma reunião amanhã às 14h",
            "tranca o carro agora"
        ]
        for q in queries:
            saved = ConversationCacheService.save_response(jid, q, "Ação confirmada com sucesso.")
            assert saved is False, f"Query mutativa não deveria ser cacheada: {q}"
            assert ConversationCacheService.get_cached_response(jid, q) is None

    def test_force_refresh_keywords(self):
        """RN-CACHE-004: Palavras de forçamento de atualização invalidam o cache."""
        jid = "5511999998888@s.whatsapp.net"
        pergunta = "Tenho guerra no clash hoje?"
        resposta = "⚔️ Guerra ativa."

        ConversationCacheService.save_response(jid, pergunta, resposta)
        assert ConversationCacheService.get_cached_response(jid, pergunta) == resposta

        # Pergunta com palavra de forçamento de atualização
        pergunta_refresh = "Tenho guerra no clash hoje? Atualizar"
        assert ConversationCacheService.get_cached_response(jid, pergunta_refresh) is None

    def test_multi_tenant_isolation(self):
        """RN-CACHE-003: Isolamento estrito por remote_jid."""
        user_a = "5511999998888@s.whatsapp.net"
        user_b = "5511977776666@s.whatsapp.net"
        pergunta = "Tenho guerra no clash hoje?"
        resposta_a = "⚔️ Clã do Usuário A em guerra."

        ConversationCacheService.save_response(user_a, pergunta, resposta_a)

        # Usuário A recebe a resposta
        assert ConversationCacheService.get_cached_response(user_a, pergunta) == resposta_a

        # Usuário B NÃO recebe a resposta do Usuário A
        assert ConversationCacheService.get_cached_response(user_b, pergunta) is None

    def test_cache_metrics(self):
        """RN-CACHE-006: Contabilização de métricas de hits, misses e economia de tokens."""
        ConversationCacheService.reset_metrics()
        jid = "5511999998888@s.whatsapp.net"

        # 1. Miss inicial
        res1 = ConversationCacheService.get_cached_response(jid, "tenho guerra no clash?")
        assert res1 is None

        ConversationCacheService.save_response(jid, "tenho guerra no clash?", "Sim, estamos em guerra ativa!")

        # 2. Hit subsequente
        res2 = ConversationCacheService.get_cached_response(jid, "tenho guerra no clash?")
        assert res2 is not None

        metrics = ConversationCacheService.get_metrics()
        assert metrics["hits"] == 1
        assert metrics["misses"] == 1
        assert metrics["tokens_saved_estimated"] > 0

    def test_cache_resilience_when_firestore_none(self):
        """RN-CACHE-005: Resiliência caso Firestore seja None."""
        jid = "5511999998888@s.whatsapp.net"
        with patch("config.firebase.db", None):
            saved = ConversationCacheService.save_response(jid, "onde assistir Interestelar?", "Disponível na Max.")
            assert saved is True
            res = ConversationCacheService.get_cached_response(jid, "onde assistir Interestelar?")
            assert res == "Disponível na Max."

    @patch("services.ai_service.genai.GenerativeModel")
    @patch("services.ai_service.ChatRepository.get_recent_history")
    def test_ai_service_integration_with_cache(self, mock_history, mock_genai_cls):
        """Integração completa: AIService utiliza o cache e poupa chamadas ao Gemini."""
        from services.ai_service import AIService

        mock_history.return_value = []
        mock_model = MagicMock()
        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "⚔️ *Resposta Gemini:* Você tem 1 ataque na guerra do Clash."
        mock_chat.send_message.return_value = mock_response
        mock_model.start_chat.return_value = mock_chat
        mock_genai_cls.return_value = mock_model

        jid = "5511999998888@s.whatsapp.net"
        pergunta_clash = "Tenho guerra no clash hoje?"

        # 1ª Chamada: Cache Miss -> Deve chamar o Gemini
        resp1 = AIService.process_message(jid, pergunta_clash)
        assert resp1 == "⚔️ *Resposta Gemini:* Você tem 1 ataque na guerra do Clash."
        assert mock_chat.send_message.call_count == 1

        # 2ª Chamada idêntica: Cache Hit -> NÃO deve chamar o Gemini novamente!
        resp2 = AIService.process_message(jid, pergunta_clash)
        assert resp2 == "⚔️ *Resposta Gemini:* Você tem 1 ataque na guerra do Clash."
        # A contagem de chamadas deve continuar 1 (Gemini poupado!)
        assert mock_chat.send_message.call_count == 1

        # Chamada de Trânsito: NÃO deve usar cache
        mock_response_transit = MagicMock()
        mock_response_transit.text = "🚗 Trânsito fluindo na Marginal: 22 minutos."
        mock_chat.send_message.return_value = mock_response_transit

        pergunta_transito = "Como tá o trânsito agora?"
        AIService.process_message(jid, pergunta_transito)
        assert mock_chat.send_message.call_count == 2

        # 2ª Chamada de Trânsito: Deve chamar o Gemini NOVAMENTE (volátil)
        AIService.process_message(jid, pergunta_transito)
        assert mock_chat.send_message.call_count == 3
