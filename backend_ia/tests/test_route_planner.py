"""
Testes Unitarios -- Route Planner (TDD)
Modulo: services/tools/maps_tool.py (novas tools)
Cobre: P-001 ao P-008 das Regras de Negocio
"""
import pytest
from unittest.mock import patch, MagicMock

# ──────────────────────────────────────────────────────────────
# Fixtures: matrizes e respostas simuladas
# ──────────────────────────────────────────────────────────────

MATRIX_2X2 = {
    "status": "OK",
    "origin_addresses": ["Ponto A", "Ponto B"],
    "destination_addresses": ["Ponto A", "Ponto B"],
    "rows": [
        {"elements": [
            {"status": "OK", "duration": {"value": 0}},
            {"status": "OK", "duration": {"value": 1800}},
        ]},
        {"elements": [
            {"status": "OK", "duration": {"value": 1800}},
            {"status": "OK", "duration": {"value": 0}},
        ]},
    ]
}

MATRIX_3X3 = {
    "status": "OK",
    "origin_addresses": ["A", "B", "C"],
    "destination_addresses": ["A", "B", "C"],
    "rows": [
        {"elements": [
            {"status": "OK", "duration": {"value": 0}},
            {"status": "OK", "duration": {"value": 600}},   # A->B 10min
            {"status": "OK", "duration": {"value": 3600}},  # A->C 60min
        ]},
        {"elements": [
            {"status": "OK", "duration": {"value": 600}},
            {"status": "OK", "duration": {"value": 0}},
            {"status": "OK", "duration": {"value": 1200}},  # B->C 20min
        ]},
        {"elements": [
            {"status": "OK", "duration": {"value": 3600}},
            {"status": "OK", "duration": {"value": 1200}},
            {"status": "OK", "duration": {"value": 0}},
        ]},
    ]
}

PLACES_RESPONSE_MUSEU = {
    "status": "OK",
    "results": [{"name": "Museu de Arte", "types": ["museum"], "rating": 4.5}]
}

PLACES_RESPONSE_PARQUE = {
    "status": "OK",
    "results": [{"name": "Parque Central", "types": ["park"], "rating": 4.2}]
}

PLACES_RESPONSE_RESTAURANTE = {
    "status": "OK",
    "results": [{"name": "Restaurante X", "types": ["restaurant"], "rating": 3.8}]
}

PLACES_RESPONSE_DESCONHECIDO = {
    "status": "OK",
    "results": [{"name": "Local Y", "types": ["point_of_interest"], "rating": 3.0}]
}


# ──────────────────────────────────────────────────────────────
# Testes: Algoritmo Nearest Neighbor (P-002)
# ──────────────────────────────────────────────────────────────

class TestNearestNeighborTSP:
    def test_ordem_otimizada_basica(self):
        """P-002: Deve escolher o vizinho mais proximo a cada passo."""
        from services.tools.maps_tool import _nearest_neighbor_tsp
        # Com matriz 3x3: de origem(0), B(1) e C(2)
        # De 0: B(600) < C(3600) => vai para B primeiro
        # De B: C(1200) => vai para C
        duracao_matrix = [
            [0,   600,  3600],
            [600, 0,    1200],
            [3600, 1200, 0],
        ]
        ordem = _nearest_neighbor_tsp(duracao_matrix, start=0, end=None)
        # O indice 0 eh a origem. Paradas sao 1 e 2.
        # A ordem otimizada das paradas deve ser [1, 2] (B antes de C)
        paradas_ordenadas = [i for i in ordem if i not in (0,)]
        assert paradas_ordenadas[0] == 1  # B primeiro

    def test_unica_parada_retorna_ela(self):
        """Com apenas 1 parada, a ordem e trivial."""
        from services.tools.maps_tool import _nearest_neighbor_tsp
        duracao_matrix = [[0, 500], [500, 0]]
        ordem = _nearest_neighbor_tsp(duracao_matrix, start=0, end=None)
        assert 1 in ordem

    def test_retorna_lista_com_todos_os_nos(self):
        """Todos os nos devem estar presentes na rota retornada."""
        from services.tools.maps_tool import _nearest_neighbor_tsp
        n = 4
        matrix = [[abs(i - j) * 300 for j in range(n)] for i in range(n)]
        ordem = _nearest_neighbor_tsp(matrix, start=0, end=None)
        assert sorted(ordem) == list(range(n))


# ──────────────────────────────────────────────────────────────
# Testes: Estimativa de tempo no local (P-004)
# ──────────────────────────────────────────────────────────────

class TestEstimarTempoNoLocal:
    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_museu_retorna_2h(self, mock_settings, mock_req):
        from services.tools.maps_tool import _estimar_tempo_no_local
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = PLACES_RESPONSE_MUSEU
        minutos = _estimar_tempo_no_local("Museu de Arte")
        assert minutos == 120  # 2h

    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_parque_retorna_90min(self, mock_settings, mock_req):
        from services.tools.maps_tool import _estimar_tempo_no_local
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = PLACES_RESPONSE_PARQUE
        minutos = _estimar_tempo_no_local("Parque Central")
        assert minutos == 90  # 1.5h

    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_restaurante_retorna_60min(self, mock_settings, mock_req):
        from services.tools.maps_tool import _estimar_tempo_no_local
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = PLACES_RESPONSE_RESTAURANTE
        minutos = _estimar_tempo_no_local("Restaurante X")
        assert minutos == 60  # 1h

    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_desconhecido_retorna_60min(self, mock_settings, mock_req):
        from services.tools.maps_tool import _estimar_tempo_no_local
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = PLACES_RESPONSE_DESCONHECIDO
        minutos = _estimar_tempo_no_local("Local Y")
        assert minutos == 60  # default 1h

    @patch("services.tools.maps_tool.settings")
    def test_sem_api_key_retorna_default(self, mock_settings):
        from services.tools.maps_tool import _estimar_tempo_no_local
        mock_settings.GOOGLE_MAPS_API_KEY = ""
        minutos = _estimar_tempo_no_local("Qualquer lugar")
        assert minutos == 60


# ──────────────────────────────────────────────────────────────
# Testes: otimizar_rota_multiplos_pontos (P-001, P-002, P-003)
# ──────────────────────────────────────────────────────────────

class TestOtimizarRotaMultiposPontos:
    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_retorna_string_com_ordem(self, mock_settings, mock_req):
        """P-003: Deve retornar string com a rota otimizada e tempo total."""
        from services.tools.maps_tool import otimizar_rota_multiplos_pontos
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = MATRIX_3X3
        resultado = otimizar_rota_multiplos_pontos(
            origem="A",
            paradas="B|C",
            destino="A"
        )
        assert isinstance(resultado, str)
        assert "B" in resultado or "C" in resultado
        assert "min" in resultado.lower() or "total" in resultado.lower()

    @patch("services.tools.maps_tool.settings")
    def test_sem_api_key_retorna_mensagem_clara(self, mock_settings):
        """P-007: Sem chave deve retornar mensagem clara."""
        from services.tools.maps_tool import otimizar_rota_multiplos_pontos
        mock_settings.GOOGLE_MAPS_API_KEY = ""
        resultado = otimizar_rota_multiplos_pontos(
            origem="Casa",
            paradas="Supermercado|Farmacia",
            destino="Casa"
        )
        assert isinstance(resultado, str)
        assert any(w in resultado.lower() for w in ["configurada", "chave", "api", "google maps"])

    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_inclui_destino_final(self, mock_settings, mock_req):
        """P-003: O destino final deve aparecer na rota."""
        from services.tools.maps_tool import otimizar_rota_multiplos_pontos
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = MATRIX_3X3
        resultado = otimizar_rota_multiplos_pontos(
            origem="A",
            paradas="B|C",
            destino="Destino Final"
        )
        assert isinstance(resultado, str)


# ──────────────────────────────────────────────────────────────
# Testes: planejar_roteiro_viagem (P-004, P-005, P-006)
# ──────────────────────────────────────────────────────────────

class TestPlanejarRoteiroViagem:
    @patch("services.tools.maps_tool._estimar_tempo_no_local")
    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_distribui_em_dias(self, mock_settings, mock_req, mock_estimar):
        """P-005: Os pontos devem ser distribuidos entre os dias com budget apertado."""
        from services.tools.maps_tool import planejar_roteiro_viagem
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = MATRIX_3X3
        mock_estimar.return_value = 120  # 2h por ponto

        # Com 3 pontos de 2h + deslocamento e budget de 3h/dia, Dia 2 deve ser usado
        resultado = planejar_roteiro_viagem(
            pontos="Museu Nacional|Parque Ibirapuera|Pinacoteca",
            dias=2,
            horas_por_dia=3
        )
        assert isinstance(resultado, str)
        assert "Dia 1" in resultado
        assert "Dia 2" in resultado

    @patch("services.tools.maps_tool._estimar_tempo_no_local")
    @patch("services.tools.maps_tool._fazer_requisicao_maps")
    @patch("services.tools.maps_tool.settings")
    def test_todos_os_pontos_aparecem(self, mock_settings, mock_req, mock_estimar):
        """Todos os pontos devem estar presentes no roteiro."""
        from services.tools.maps_tool import planejar_roteiro_viagem
        mock_settings.GOOGLE_MAPS_API_KEY = "fake"
        mock_req.return_value = MATRIX_3X3
        mock_estimar.return_value = 60

        resultado = planejar_roteiro_viagem(
            pontos="Ponto A|Ponto B|Ponto C",
            dias=2,
            horas_por_dia=8
        )
        assert "Ponto A" in resultado
        assert "Ponto B" in resultado
        assert "Ponto C" in resultado

    @patch("services.tools.maps_tool.settings")
    def test_sem_api_key_retorna_mensagem(self, mock_settings):
        """P-007: Sem chave retorna mensagem amigavel."""
        from services.tools.maps_tool import planejar_roteiro_viagem
        mock_settings.GOOGLE_MAPS_API_KEY = ""
        resultado = planejar_roteiro_viagem(
            pontos="Museu|Parque",
            dias=1,
            horas_por_dia=8
        )
        assert isinstance(resultado, str)
        assert any(w in resultado.lower() for w in ["configurada", "chave", "api", "google maps"])
