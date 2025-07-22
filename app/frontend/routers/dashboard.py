# ================================
# app/frontend/routers/dashboard.py (ACTUALIZADO CON PERMISOS)
# ================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging

from ..auth import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(require_auth)):
    """Dashboard principal con permisos"""
    
    # Obtener información del sistema
    system_info = await get_system_health()
    
    # Obtener estadísticas según rol
    stats = {}
    if current_user["role"] in ["admin", "super_admin"]:
        stats = await get_admin_stats()
    
    # Template con datos del usuario y sistema
    return templates.TemplateResponse("dashboard_with_permissions.html", {
        "request": request,
        "current_user": current_user,
        "system_info": system_info,
        "stats": stats
    })

@router.get("/business-dashboard/{business_id}", response_class=HTMLResponse)
async def business_dashboard(
    request: Request, 
    business_id: str,
    current_user: dict = Depends(require_auth)
):
    """Dashboard específico del business"""
    
    # Verificar permisos de acceso al business
    if current_user["role"] != "super_admin" and current_user.get("business_id") != business_id:
        return templates.TemplateResponse("errors/403.html", {
            "request": request,
            "error": "No tienes permisos para acceder a este dashboard"
        }, status_code=403)
    
    # Cargar datos del business
    business_data = await get_business_data(business_id)
    
    return templates.TemplateResponse("business_dashboard.html", {
        "request": request,
        "current_user": current_user,
        "business_id": business_id,
        "business_data": business_data
    })

# === FUNCIONES AUXILIARES ===

async def get_system_health():
    """Obtener estado del sistema"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo health: {e}")
    
    return {
        "status": "unknown",
        "services": {
            "mongodb": "❌ Error",
            "waha": "❌ Error", 
            "n8n": "❌ Error"
        },
        "version": "1.0.0"
    }

async def get_admin_stats():
    """Obtener estadísticas para admins"""
    stats = {
        "businessTypes": 0,
        "totalBusinesses": 0,
        "activeBusinesses": 0
    }
    
    try:
        async with httpx.AsyncClient() as client:
            # Business Types
            bt_response = await client.get("http://localhost:8000/api/admin/business-types", timeout=10.0)
            if bt_response.status_code == 200:
                bt_data = bt_response.json()
                business_types = bt_data.get("data", []) if isinstance(bt_data, dict) else bt_data
                stats["businessTypes"] = len(business_types)
            
            # Businesses
            b_response = await client.get("http://localhost:8000/api/admin/businesses", timeout=10.0)
            if b_response.status_code == 200:
                b_data = b_response.json()
                businesses = b_data.get("data", []) if isinstance(b_data, dict) else b_data
                stats["totalBusinesses"] = len(businesses)
                stats["activeBusinesses"] = len([b for b in businesses if b.get("activo", False)])
                
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
    
    return stats

async def get_business_data(business_id: str):
    """Obtener datos específicos del business"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/business/dashboard/{business_id}", timeout=10.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo datos del business {business_id}: {e}")
    
    return {
        "error": "No se pudieron cargar los datos del business"
    }