from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...auth.dependencies import require_admin
from ...models.view import ViewConfig, ViewConfigCreate, ViewConfigUpdate
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[List[ViewConfig]])
async def get_view_configs(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuraciones de vistas de un business"""
    # TODO: Implementar ViewService
    return BaseResponse(data=[])

@router.post("/", response_model=BaseResponse[ViewConfig])
async def create_view_config(
    config_data: ViewConfigCreate,
    _: dict = Depends(require_admin)
):
    """Crear configuración de vista"""
    # TODO: Implementar
    return BaseResponse(data=None)

# ================================
# app/routers/admin/api_configs.py
# ================================

from fastapi import APIRouter, Depends, HTTPException
from typing import List

from ...auth.dependencies import require_admin
from ...models.api_config import ApiConfiguration, ApiConfigurationCreate, ApiConfigurationUpdate
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[List[ApiConfiguration]])
async def get_api_configs(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener configuraciones de API de un business"""
    # TODO: Implementar ApiService
    return BaseResponse(data=[])

@router.post("/", response_model=BaseResponse[ApiConfiguration])
async def create_api_config(
    config_data: ApiConfigurationCreate,
    _: dict = Depends(require_admin)
):
    """Crear configuración de API"""
    # TODO: Implementar
    return BaseResponse(data=None)