from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse, PaginatedResponse
from ...services.dynamic_crud_service import DynamicCrudService

router = APIRouter()

@router.get("/{business_id}/{entidad}", response_model=BaseResponse[List[Dict[str, Any]]])
async def get_entity_data(
    business_id: str,
    entidad: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    filters: Optional[str] = Query(None),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de una entidad"""
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    crud_service = DynamicCrudService()
    data = await crud_service.get_entity_data(
        business_id, 
        entidad, 
        page, 
        per_page, 
        filters,
        current_user
    )
    return BaseResponse(data=data)

@router.post("/{business_id}/{entidad}", response_model=BaseResponse[Dict[str, Any]])
async def create_entity_item(
    business_id: str,
    entidad: str,
    item_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Crear nuevo item en entidad"""
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    crud_service = DynamicCrudService()
    item = await crud_service.create_entity_item(
        business_id, 
        entidad, 
        item_data,
        current_user
    )
    return BaseResponse(data=item, message="Item creado exitosamente")