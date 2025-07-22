# ================================
# app/routers/auth.py - SIMPLIFICADO
# ================================

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Importar funciones de autenticación del frontend
try:
    from ..frontend.auth import get_current_user
except ImportError:
    # Fallback si no está disponible
    def get_current_user(request: Request):
        if hasattr(request, 'session') and "user" in request.session:
            return request.session["user"]
        raise HTTPException(status_code=401, detail="No autenticado")

@router.get("/me")
async def get_current_user_info(request: Request):
    """Obtener información del usuario actual"""
    try:
        user = get_current_user(request)
        return {
            "success": True,
            "data": user,
            "message": "Usuario actual obtenido"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error obteniendo usuario actual: {e}")
        raise HTTPException(status_code=500, detail="Error interno")

@router.post("/logout")
async def api_logout(request: Request):
    """Cerrar sesión via API"""
    try:
        if hasattr(request, 'session'):
            request.session.clear()
        
        return {
            "success": True,
            "message": "Sesión cerrada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error en logout: {e}")
        raise HTTPException(status_code=500, detail="Error cerrando sesión")

@router.get("/status")
async def auth_status(request: Request):
    """Verificar estado de autenticación"""
    try:
        user = get_current_user(request)
        return {
            "authenticated": True,
            "user": user
        }
    except:
        return {
            "authenticated": False,
            "user": None
        }

@router.post("/webhook")
async def dummy_webhook(request: Request):
    """Webhook dummy para compatibilidad"""
    return JSONResponse({"success": True, "message": "Webhook no implementado"})
