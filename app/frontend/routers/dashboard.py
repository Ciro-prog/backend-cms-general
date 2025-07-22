# ================================
# app/frontend/routers/dashboard.py
# ================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging
from datetime import datetime

from ..auth import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(require_auth)):
    """Dashboard principal"""
    
    # Obtener datos del backend
    health_data = await get_health_data()
    info_data = await get_info_data()
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "current_user": current_user,
        "health_data": health_data,
        "info_data": info_data,
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

async def get_health_data():
    """Obtener datos de salud del backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo health data: {e}")
    
    # Datos por defecto si no se puede conectar
    return {
        "status": "unknown",
        "services": {
            "mongodb": "❌ No disponible",
            "waha": "❌ No disponible", 
            "n8n": "❌ No disponible"
        }
    }

async def get_info_data():
    """Obtener información del sistema"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/info", timeout=5.0)
            if response.status_code == 200:
                return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo info data: {e}")
    
    # Datos por defecto
    return {
        "name": "CMS Dinámico",
        "version": "1.0.0",
        "environment": "development",
        "python_version": "3.13",
        "integrations": {
            "waha_url": "No disponible",
            "n8n_url": "No disponible",
            "mongodb_url": "No disponible"
        }
    }