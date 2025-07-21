# ================================
# app/middleware/business_context.py  
# ================================

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from ..database import get_database

logger = logging.getLogger(__name__)

class BusinessContextMiddleware(BaseHTTPMiddleware):
    """Middleware para validar contexto de business en rutas dinámicas"""
    
    async def dispatch(self, request: Request, call_next):
        # Solo aplicar a rutas de business
        if "/business/" in str(request.url.path):
            # Extraer business_id de la URL
            path_parts = request.url.path.split("/")
            
            if "business" in path_parts:
                business_index = path_parts.index("business")
                if len(path_parts) > business_index + 1:
                    business_id = path_parts[business_index + 1]
                    
                    # Validar que el business existe
                    if await self._validate_business_exists(business_id):
                        request.state.business_id = business_id
                    else:
                        return HTTPException(status_code=404, detail="Business no encontrado")
        
        return await call_next(request)
    
    async def _validate_business_exists(self, business_id: str) -> bool:
        """Validar que el business existe y está activo"""
        try:
            db = get_database()
            business = await db.business_instances.find_one({
                "business_id": business_id,
                "activo": True
            })
            return business is not None
        except Exception as e:
            logger.error(f"Error validando business {business_id}: {e}")
            return False