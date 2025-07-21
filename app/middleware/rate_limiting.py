from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from collections import defaultdict, deque
import logging

from ..config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting por IP"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        # Obtener IP del cliente
        client_ip = self._get_client_ip(request)
        
        # Verificar rate limit
        if self._is_rate_limited(client_ip):
            logger.warning(f"Rate limit excedido para IP: {client_ip}")
            raise HTTPException(
                status_code=429, 
                detail="Demasiadas peticiones. Intenta más tarde."
            )
        
        # Registrar petición
        self._register_request(client_ip)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente considerando proxies"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _is_rate_limited(self, client_ip: str) -> bool:
        """Verificar si la IP está limitada"""
        now = time.time()
        minute_ago = now - 60
        
        # Limpiar peticiones antiguas
        while self.requests[client_ip] and self.requests[client_ip][0] < minute_ago:
            self.requests[client_ip].popleft()
        
        # Verificar límite
        return len(self.requests[client_ip]) >= self.requests_per_minute
    
    def _register_request(self, client_ip: str):
        """Registrar nueva petición"""
        self.requests[client_ip].append(time.time())