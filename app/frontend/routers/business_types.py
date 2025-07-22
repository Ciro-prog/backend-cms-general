# ================================
# app/frontend/routers/business_types.py
# ================================

from fastapi import APIRouter, Request, Depends, Form
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
    """Listar Business Types"""
    
    business_types = await get_business_types_from_api()
    
    return templates.TemplateResponse("business_types/list.html", {
        "request": request,
        "current_user": current_user,
        "business_types": business_types,
        "messages": request.session.get("messages", [])
    })

@router.get("/business-types/create", response_class=HTMLResponse)
async def create_business_type_form(request: Request, current_user: dict = Depends(require_super_admin)):
    """Formulario para crear Business Type"""
    
    return templates.TemplateResponse("business_types/create.html", {
        "request": request,
        "current_user": current_user
    })

@router.post("/business-types/create")
async def create_business_type_submit(
    request: Request,
    current_user: dict = Depends(require_super_admin),
    tipo: str = Form(...),
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None)
):
    """Crear Business Type"""
    
    # Preparar datos
    business_type_data = {
        "tipo": tipo,
        "nombre": nombre,
        "descripcion": descripcion or "",
        "componentes_base": [
            {
                "id": "whatsapp",
                "nombre": "WhatsApp Business",
                "tipo": "integration",
                "obligatorio": True
            }
        ],
        "componentes_opcionales": []
    }
    
    # Enviar al backend
    success = await create_business_type_in_api(business_type_data)
    
    if success:
        add_message(request, "success", f"Business Type '{nombre}' creado exitosamente")
        return RedirectResponse(url="/business-types", status_code=302)
    else:
        add_message(request, "error", "Error creando Business Type")
        return templates.TemplateResponse("business_types/create.html", {
            "request": request,
            "current_user": current_user,
            "error": "Error creando Business Type",
            "form_data": {"tipo": tipo, "nombre": nombre, "descripcion": descripcion}
        })

@router.get("/business-types/{tipo}/edit", response_class=HTMLResponse)
async def edit_business_type_form(
    request: Request, 
    tipo: str,
    current_user: dict = Depends(require_super_admin)
):
    """Formulario para editar Business Type"""
    
    business_type = await get_business_type_from_api(tipo)
    
    if not business_type:
        add_message(request, "error", f"Business Type '{tipo}' no encontrado")
        return RedirectResponse(url="/business-types", status_code=302)
    
    return templates.TemplateResponse("business_types/edit.html", {
        "request": request,
        "current_user": current_user,
        "business_type": business_type
    })

@router.post("/business-types/{tipo}/edit")
async def edit_business_type_submit(
    request: Request,
    tipo: str,
    current_user: dict = Depends(require_super_admin),
    nombre: str = Form(...),
    descripcion: Optional[str] = Form(None)
):
    """Actualizar Business Type"""
    
    update_data = {
        "nombre": nombre,
        "descripcion": descripcion or ""
    }
    
    success = await update_business_type_in_api(tipo, update_data)
    
    if success:
        add_message(request, "success", f"Business Type '{nombre}' actualizado exitosamente")
        return RedirectResponse(url="/business-types", status_code=302)
    else:
        add_message(request, "error", "Error actualizando Business Type")
        return RedirectResponse(url=f"/business-types/{tipo}/edit", status_code=302)

@router.post("/business-types/{tipo}/delete")
async def delete_business_type(
    request: Request,
    tipo: str,
    current_user: dict = Depends(require_super_admin)
):
    """Eliminar Business Type"""
    
    success = await delete_business_type_in_api(tipo)
    
    if success:
        add_message(request, "success", f"Business Type '{tipo}' eliminado exitosamente")
    else:
        add_message(request, "error", "Error eliminando Business Type")
    
    return RedirectResponse(url="/business-types", status_code=302)

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

async def get_business_type_from_api(tipo: str):
    """Obtener Business Type específico"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://localhost:8000/api/admin/business-types/{tipo}", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                return data.get("data")
    except Exception as e:
        logger.error(f"Error obteniendo business type {tipo}: {e}")
    
    return None

async def create_business_type_in_api(business_type_data: dict):
    """Crear Business Type en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/admin/business-types",
                json=business_type_data,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error creando business type: {e}")
        return False

async def update_business_type_in_api(tipo: str, update_data: dict):
    """Actualizar Business Type en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"http://localhost:8000/api/admin/business-types/{tipo}",
                json=update_data,
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error actualizando business type: {e}")
        return False

async def delete_business_type_in_api(tipo: str):
    """Eliminar Business Type en el backend"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"http://localhost:8000/api/admin/business-types/{tipo}",
                timeout=10.0
            )
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error eliminando business type: {e}")
        return False

def add_message(request: Request, type: str, text: str):
    """Agregar mensaje flash"""
    if "messages" not in request.session:
        request.session["messages"] = []
    request.session["messages"].append({"type": type, "text": text})