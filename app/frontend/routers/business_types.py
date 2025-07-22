# ================================
# app/frontend/routers/business_types.py (PROTEGIDO)
# ================================

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging
from typing import Optional

from ..auth import require_super_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/business-types", response_class=HTMLResponse)
async def list_business_types(request: Request, current_user: dict = Depends(require_super_admin)):
    """Listar Business Types - SOLO SUPER ADMIN"""
    
    # Verificación adicional de rol
    if current_user["role"] != "super_admin":
        return templates.TemplateResponse("errors/403.html", {
            "request": request,
            "current_user": current_user,
            "error": "Solo los Super Administradores pueden gestionar Business Types"
        }, status_code=403)
    
    business_types = await get_business_types_from_api()
    
    return templates.TemplateResponse("business_types/configurator.html", {
        "request": request,
        "current_user": current_user,
        "business_types": business_types,
        "messages": request.session.get("messages", [])
    })

# === FUNCIONES DE API ===

async def get_business_types_from_api():
    """Obtener Business Types del backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/admin/business-types", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo business types: {e}")
    
    return []