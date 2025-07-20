from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import httpx
import logging
from ..config import settings

logger = logging.getLogger(__name__)

class ClerkAuthMiddleware(BaseHTTPMiddleware):
    """Middleware para autenticación con Clerk"""
    
    def __init__(self, app):
        super().__init__(app)
        self.excluded_paths = [
            "/",
            "/health",
            "/docs",
            "/openapi.json",
            "/api/auth/webhook"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Saltar autenticación para rutas excluidas
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Verificar token de autorización
        auth_header = request.headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Token de autorización requerido")
        
        token = auth_header.split(" ")[1]
        
        try:
            # Verificar token con Clerk
            user_data = await self.verify_clerk_token(token)
            request.state.user = user_data
            
        except Exception as e:
            logger.error(f"Error verificando token: {e}")
            raise HTTPException(status_code=401, detail="Token inválido")
        
        return await call_next(request)
    
    async def verify_clerk_token(self, token: str) -> dict:
        """Verificar token con la API de Clerk"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.clerk.dev/v1/sessions/verify",
                headers={
                    "Authorization": f"Bearer {settings.clerk_secret_key}",
                    "X-Session-Token": token
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Token inválido")
            
            return response.json()