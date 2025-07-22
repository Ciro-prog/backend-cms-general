# ================================
# app/frontend/routers/businesses.py
# ================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging

from ..auth import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/businesses", response_class=HTMLResponse)
async def list_businesses(request: Request, current_user: dict = Depends(require_admin)):
    """Listar Business Instances"""
    
    businesses = await get_businesses_from_api()
    business_types = await get_business_types_from_api()
    
    return templates.TemplateResponse("businesses/manager.html", {
        "request": request,
        "current_user": current_user,
        "businesses": businesses,
        "business_types": business_types,
        "messages": request.session.get("messages", [])
    })

# === FUNCIONES DE API ===

async def get_businesses_from_api():
    """Obtener Business Instances del backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/admin/businesses", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo businesses: {e}")
    
    return []

async def get_business_types_from_api():
    """Obtener Business Types para select"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/admin/business-types", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo business types: {e}")
    
    return []