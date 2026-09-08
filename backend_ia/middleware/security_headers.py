from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injeta cabeçalhos HTTP de segurança obrigatórios em todas as respostas da API
    para prevenir MIME sniffing, Clickjacking, XSS e vazamento de referrer.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Previne MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Previne clickjacking e renderização em iframes não autorizados
        response.headers["X-Frame-Options"] = "DENY"
        
        # Ativa filtro XSS legado de navegadores
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Restringe informações enviadas no cabeçalho Referer
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # HSTS (HTTP Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response
