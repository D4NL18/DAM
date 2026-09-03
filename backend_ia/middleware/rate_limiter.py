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

    async def dispatch(self, request: Request, call_next) -> Response:
        # Extrai IP do cliente (respeitando headers de proxy Cloud Run se presentes)
        client_ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not client_ip:
            client_ip = request.client.host if request.client else "unknown"

        # Evita envenenamento de rate limit entre testes com TestClient compartilhado
        if client_ip == "testclient" and "x-test-rate-limit" not in request.headers:
            return await call_next(request)

        agora = time.time()
        is_webhook = "/api/whatsapp/webhook" in request.url.path
        limite_atual = self.webhook_max_requests if is_webhook else self.max_requests

        self._cleanup_old_requests(client_ip)

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
