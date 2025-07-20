from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...auth.dependencies import require_admin
from ...models.entity import EntityConfig, EntityConfigCreate, EntityConfigUpdate
from ...models.responses import BaseResponse
from ...services.entity_service import EntityService

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[List[EntityConfig]])
async def get_entity_configs(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuraciones de entidades de un business"""
    entity_service = EntityService()
    configs = await entity_service.get_entity_configs_by_business(business_id)
    return BaseResponse(data=configs)

@router.get("/{business_id}/{entidad}", response_model=BaseResponse[EntityConfig])
async def get_entity_config(
    business_id: str,
    entidad: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuración específica de entidad"""
    entity_service = EntityService()
    config = await entity_service.get_entity_config(business_id, entidad)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return BaseResponse(data=config)

@router.post("/", response_model=BaseResponse[EntityConfig])
async def create_entity_config(
    config_data: EntityConfigCreate,
    _: dict = Depends(require_admin)
):
    """Crear configuración de entidad"""
    entity_service = EntityService()
    config = await entity_service.create_entity_config(config_data)
    return BaseResponse(data=config, message="Configuración creada exitosamente")

@router.put("/{business_id}/{entidad}", response_model=BaseResponse[EntityConfig])
async def update_entity_config(
    business_id: str,
    entidad: str,
    config_update: EntityConfigUpdate,
    _: dict = Depends(require_admin)
):
    """Actualizar configuración de entidad"""
    entity_service = EntityService()
    config = await entity_service.update_entity_config(business_id, entidad, config_update)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return BaseResponse(data=config, message="Configuración actualizada exitosamente")
