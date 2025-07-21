# ================================
# app/middleware/request_context.py
# ================================

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid
import logging

logger = logging.getLogger(__name__)

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware para agregar contexto a las peticiones"""
    
    async def dispatch(self, request: Request, call_next):
        # Generar ID único para la petición
        request_id = str(uuid.uuid4())[:8]
        
        # Agregar al state de la petición
        request.state.request_id = request_id
        request.state.start_time = time.time()
        
        # Agregar headers de contexto
        response = await call_next(request)
        
        # Calcular tiempo de procesamiento
        process_time = time.time() - request.state.start_time
        
        # Agregar headers de respuesta
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
        
        return response