import time
import logging
from typing import Dict, Tuple
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger(__name__)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware de Rate Limiting por IP utilizando Sliding Window.
    Protege endpoints de ataques de força bruta, scraping e DoS.
    """
    def __init__(
        self,
        app,
        max_requests_per_minute: int = 100,
        webhook_max_requests_per_minute: int = 200
    ):
        super().__init__(app)
        self.max_requests = max_requests_per_minute
        self.webhook_max_requests = webhook_max_requests_per_minute
        # Armazena IP -> lista de timestamps das requisições
        self._clients: Dict[str, list] = {}

    def _cleanup_old_requests(self, client_ip: str, window_seconds: float = 60.0):
        agora = time.time()
        if client_ip in self._clients:
            self._clients[client_ip] = [
                ts for ts in self._clients[client_ip] if agora - ts < window_seconds
            ]
            if not self._clients[client_ip]:
                del self._clients[client_ip]

    def _sweep_clients_if_needed(self, window_seconds: float = 60.0):
        # Previne crescimento desenfreado de memória (DoS via IP rotativo)
        if len(self._clients) > 500:
            agora = time.time()
            stale = [ip for ip, reqs in self._clients.items() if not reqs or (agora - reqs[-1] > window_seconds)]
            for ip in stale:
                self._clients.pop(ip, None)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Identifica se é TestClient legítimo da suíte de testes (apenas se request.client.host == 'testclient')
        conn_host = request.client.host if request.client else "unknown"
        is_test_client = (conn_host == "testclient")
        if is_test_client and "x-test-rate-limit" not in request.headers:
            return await call_next(request)

        # Extrai IP do cliente (respeitando headers de proxy se presentes)
        forwarded = request.headers.get("x-forwarded-for", "")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = conn_host

        agora = time.time()
        is_webhook = "/api/whatsapp/webhook" in request.url.path
        limite_atual = self.webhook_max_requests if is_webhook else self.max_requests

        self._cleanup_old_requests(client_ip)
        self._sweep_clients_if_needed()

        requests_cliente = self._clients.setdefault(client_ip, [])
        if len(requests_cliente) >= limite_atual:
            logger.warning(f"Rate limit excedido para IP: {client_ip} na rota {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "detail": "Taxa de requisições excedida (Rate Limit Exceeded). Tente novamente em alguns instantes."
                },
                headers={"Retry-After": "60"}
            )

        requests_cliente.append(agora)
        return await call_next(request)
