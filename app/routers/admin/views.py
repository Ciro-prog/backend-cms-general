from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...auth.dependencies import require_admin
from ...models.view import ViewConfig, ViewConfigCreate, ViewConfigUpdate
from ...models.responses import BaseResponse
from ...services.view_service import ViewService

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[List[ViewConfig]])
async def get_view_configs(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuraciones de vistas de un business"""
    view_service = ViewService()
    configs = await view_service.get_view_configs_by_business(business_id)
    return BaseResponse(data=configs)

@router.get("/{business_id}/{vista}", response_model=BaseResponse[ViewConfig])
async def get_view_config(
    business_id: str,
    vista: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuración específica de vista"""
    view_service = ViewService()
    config = await view_service.get_view_config(business_id, vista)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de vista no encontrada")
    
    return BaseResponse(data=config)

@router.post("/", response_model=BaseResponse[ViewConfig])
async def create_view_config(
    config_data: ViewConfigCreate,
    _: dict = Depends(require_admin)
):
    """Crear configuración de vista"""
    view_service = ViewService()
    config = await view_service.create_view_config(config_data)
    return BaseResponse(data=config, message="Configuración de vista creada exitosamente")

@router.put("/{business_id}/{vista}", response_model=BaseResponse[ViewConfig])
async def update_view_config(
    business_id: str,
    vista: str,
    config_update: ViewConfigUpdate,
    _: dict = Depends(require_admin)
):
    """Actualizar configuración de vista"""
    view_service = ViewService()
    config = await view_service.update_view_config(business_id, vista, config_update)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de vista no encontrada")
    
    return BaseResponse(data=config, message="Configuración actualizada exitosamente")

@router.delete("/{business_id}/{vista}", response_model=BaseResponse[dict])
async def delete_view_config(
    business_id: str,
    vista: str,
    _: dict = Depends(require_admin)
):
    """Eliminar configuración de vista"""
    view_service = ViewService()
    success = await view_service.delete_view_config(business_id, vista)
    
    if not success:
        raise HTTPException(status_code=404, detail="Configuración de vista no encontrada")
    
    return BaseResponse(data={"deleted": True}, message="Configuración eliminada exitosamente")
