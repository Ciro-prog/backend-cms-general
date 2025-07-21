from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...auth.dependencies import require_admin
from ...models.api_config import ApiConfiguration, ApiConfigurationCreate, ApiConfigurationUpdate
from ...models.responses import BaseResponse
from ...services.api_config_service import ApiConfigService

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[List[ApiConfiguration]])
async def get_api_configs(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuraciones de API de un business"""
    api_service = ApiConfigService()
    configs = await api_service.get_api_configs_by_business(business_id)
    return BaseResponse(data=configs)

@router.get("/{business_id}/{api_name}", response_model=BaseResponse[ApiConfiguration])
async def get_api_config(
    business_id: str,
    api_name: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuración específica de API"""
    api_service = ApiConfigService()
    config = await api_service.get_api_config(business_id, api_name)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de API no encontrada")
    
    return BaseResponse(data=config)

@router.post("/", response_model=BaseResponse[ApiConfiguration])
async def create_api_config(
    config_data: ApiConfigurationCreate,
    _: dict = Depends(require_admin)
):
    """Crear configuración de API"""
    api_service = ApiConfigService()
    config = await api_service.create_api_config(config_data)
    return BaseResponse(data=config, message="Configuración de API creada exitosamente")

@router.put("/{business_id}/{api_name}", response_model=BaseResponse[ApiConfiguration])
async def update_api_config(
    business_id: str,
    api_name: str,
    config_update: ApiConfigurationUpdate,
    _: dict = Depends(require_admin)
):
    """Actualizar configuración de API"""
    api_service = ApiConfigService()
    config = await api_service.update_api_config(business_id, api_name, config_update)
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de API no encontrada")
    
    return BaseResponse(data=config, message="Configuración actualizada exitosamente")

@router.post("/{business_id}/{api_name}/test", response_model=BaseResponse[dict])
async def test_api_connection(
    business_id: str,
    api_name: str,
    _: dict = Depends(require_admin)
):
    """Probar conexión con API externa"""
    from ...services.api_service import ApiService
    
    api_service = ApiService()
    result = await api_service.test_connection(business_id, api_name)
    
    return BaseResponse(data=result, message="Test de conexión completado")