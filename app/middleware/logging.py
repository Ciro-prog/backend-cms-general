from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import json

logger = logging.getLogger("api_requests")

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging detallado de peticiones"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Información de la petición
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_ip": self._get_client_ip(request)
        }
        
        # Ejecutar petición
        response = await call_next(request)
        
        # Calcular tiempo de respuesta
        process_time = time.time() - start_time
        
        # Información de la respuesta
        response_info = {
            "status_code": response.status_code,
            "process_time": round(process_time * 1000, 2),  # ms
            "content_length": response.headers.get("content-length")
        }
        
        # Log estructurado
        log_data = {
            "timestamp": time.time(),
            "request": request_info,
            "response": response_info
        }
        
        # Determinar nivel de log según status code
        if response.status_code >= 500:
            logger.error(json.dumps(log_data))
        elif response.status_code >= 400:
            logger.warning(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Obtener IP del cliente"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"