from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback

from ..utils.exceptions import CMSException

logger = logging.getLogger(__name__)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware para manejo centralizado de errores"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException:
            # Re-raise HTTPExceptions para que FastAPI las maneje
            raise
        except CMSException as e:
            logger.error(f"CMS Error: {e.message} - Code: {e.code}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "message": e.message,
                    "error_code": e.code
                }
            )
        except Exception as e:
            # Log del error completo
            logger.error(f"Error no manejado: {str(e)}\n{traceback.format_exc()}")
            
            # En producción, no exponer detalles del error
            if request.app.debug:
                error_detail = str(e)
            else:
                error_detail = "Error interno del servidor"
            
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "message": error_detail,
                    "error_code": "INTERNAL_ERROR"
                }
            )
