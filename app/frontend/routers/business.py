# ================================
# app/frontend/routers/businesses.py
# ================================

from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import httpx
import logging
from typing import Optional

from ..auth import require_admin

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/businesses", response_class=HTMLResponse)
async def list_businesses(request: Request, current_user: dict = Depends(require_admin)):
    """Listar Businesses"""
    
    businesses = await get_businesses_from_api()
    business_types = await get_business_types_from_api()
    
    return templates.TemplateResponse("businesses/list.html", {
        "request": request,
        "current_user": current_user,
        "businesses": businesses,
        "business_types": business_types,
        "messages": request.session.get("messages", [])
    })

@router.get("/businesses/create", response_class=HTMLResponse)
async def create_business_form(request: Request, current_user: dict = Depends(require_admin)):
    """Formulario para crear Business"""
    
    business_types = await get_business_types_from_api()
    
    return templates.TemplateResponse("businesses/create.html", {
        "request": request,
        "current_user": current_user,
        "business_types": business_types
    })

@router.post("/businesses/create")
async def create_business_submit(
    request: Request,
    current_user: dict = Depends(require_admin),
    business_id: str = Form(...),
    nombre: str = Form(...),
    tipo_base: str = Form(...),
    descripcion: Optional[str] = Form(None)
):
    """Crear Business"""
    
    # Preparar datos
    business_data = {
        "business_id": business_id,
        "nombre": nombre,
        "tipo_base": tipo_base
    }
    
    # Enviar al backend
    success = await create_business_in_api(business_data)
    
    if success:
        add_message(request, "success", f"Empresa '{nombre}' creada exitosamente")
        return RedirectResponse(url="/businesses", status_code=302)
    else:
        business_types = await get_business_types_from_api()
        add_message(request, "error", "Error creando empresa")
        return templates.TemplateResponse("businesses/create.html", {
            "request": request,
            "current_user": current_user,
            "business_types": business_types,
            "error": "Error creando empresa",
            "form_data": {
                "business_id": business_id, 
                "nombre": nombre, 
                "tipo_base": tipo_base,
                "descripcion": descripcion
            }
        })

@router.get("/businesses/{business_id}/edit", response_class=HTMLResponse)
async def edit_business_form(
    request: Request, 
    business_id: str,
    current_user: dict = Depends(require_admin)
):
    """Formulario para editar Business"""
    
    business = await get_business_from_api(business_id)
    business_types = await get_business_types_from_api()
    
    if not business:
        add_message(request, "error", f"Empresa '{business_id}' no encontrada")
        return RedirectResponse(url="/businesses", status_code=302)
    
    return templates.TemplateResponse("businesses/edit.html", {
        "request": request,
        "current_user": current_user,
        "business": business,
        "business_types": business_types
    })

@router.post("/businesses/{business_id}/edit")
async def edit_business_submit(
    request: Request,
    business_id: str,
    current_user: dict = Depends(require_admin),
    nombre: str = Form(...),
    activo: bool = Form(default=True)
):
    """Actualizar Business"""
    
    update_data = {
        "nombre": nombre,
        "activo": activo
    }
    
    success = await update_business_in_api(business_id, update_data)
    
    if success:
        add_message(request, "success", f"Empresa '{nombre}' actualizada exitosamente")
        return RedirectResponse(url="/businesses", status_code=302)
    else:
        add_message(request, "error", "Error actualizando empresa")
        return RedirectResponse(url=f"/businesses/{business_id}/edit", status_code=302)

@router.post("/businesses/{business_id}/delete")
async def delete_business(
    request: Request,
    business_id: str,
    current_user: dict = Depends(require_admin)
):
    """Eliminar Business"""
    
    success = await delete_business_in_api(business_id)
    
    if success:
        add_message(request, "success", f"Empresa '{business_id}' eliminada exitosamente")
    else:
        add_message(request, "error", "Error eliminando empresa")
    
    return RedirectResponse(url="/businesses", status_code=302)

# === FUNCIONES DE API ===

async def get_businesses_from_api():
    """Obtener Businesses del backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/admin/businesses", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
    except Exception as e:
        logger.error(f"Error obteniendo businesses: {e}")
    
    return []

async def get_business_from_api(business_id: str):
    """Obtener Business específico"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/admin/businesses/{business_id}", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data")
    except Exception as e:
        logger.error(f"Error obteniendo business {business_id}: {e}")
    
    return None

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

async def create_business_in_api(business_data: dict):
    """Crear Business en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/admin/businesses",
                json=business_data,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error creando business: {e}")
        return False

async def update_business_in_api(business_id: str, update_data: dict):
    """Actualizar Business en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://localhost:8000/api/admin/businesses/{business_id}",
                json=update_data,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error actualizando business: {e}")
        return False

async def delete_business_in_api(business_id: str):
    """Eliminar Business en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://localhost:8000/api/admin/businesses/{business_id}",
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error eliminando business: {e}")
        return False

def add_message(request: Request, type: str, text: str):
    """Agregar mensaje flash"""
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append({"type": type, "text": text})