from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging

from ..auth import require_super_admin, require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

# === RUTAS SOLO SUPER ADMIN ===

@router.get("/business-types", response_class=HTMLResponse)
async def list_business_types(request: Request, user: dict = Depends(require_super_admin)):
    """Gestión de Business Types - SOLO SUPER ADMIN"""

    # Opcional: traer datos si querés render server-side
    # business_types = await get_business_types_from_api()

    return templates.TemplateResponse("business_types/list.html", {
        "request": request,
        "user": user,
        "messages": request.session.get("messages", [])
        # "business_types": business_types
    })

@router.get("/businesses", response_class=HTMLResponse)
async def list_businesses(request: Request, user: dict = Depends(require_super_admin)):
    """Gestión de Business Instances - SOLO SUPER ADMIN"""

    return templates.TemplateResponse("business_types/businesses.html", {
        "request": request,
        "user": user,
        "messages": request.session.get("messages", [])
    })

@router.get("/api-configs", response_class=HTMLResponse)
async def list_api_configs(request: Request, user: dict = Depends(require_super_admin)):
    """Gestión de API Configurations - SOLO SUPER ADMIN"""

    return templates.TemplateResponse("api_configs/list.html", {
        "request": request,
        "user": user,
        "messages": request.session.get("messages", [])
    })

@router.get("/logs", response_class=HTMLResponse)
async def view_logs(request: Request, user: dict = Depends(require_super_admin)):
    """Ver logs del sistema - SOLO SUPER ADMIN"""

    return templates.TemplateResponse("logs/list.html", {
        "request": request,
        "user": user,
        "messages": request.session.get("messages", [])
    })

# === COMPONENTES - Acceso más amplio ===

@router.get("/components", response_class=HTMLResponse)
async def list_components(request: Request, user: dict = Depends(require_auth)):
    """Gestión de Dynamic Components"""

    return templates.TemplateResponse("components/list.html", {
        "request": request,
        "user": user,
        "messages": request.session.get("messages", [])
    })

# === FUNCIONES AUXILIARES OPCIONALES ===

async def get_business_types_from_api():
    """Obtener Business Types desde backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/admin/business-types", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo business types: {e}")

    return []
