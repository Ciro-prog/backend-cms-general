from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse, PaginatedResponse
from ...services.dynamic_crud_service import DynamicCrudService
from ...core.dynamic_crud import DynamicCrudGenerator

router = APIRouter()

@router.get("/{business_id}/{entidad}")
async def get_entity_data(
    business_id: str,
    entidad: str,
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=100, description="Items por página"),
    filters: Optional[str] = Query(None, description="Filtros en formato key=value&key2=value2"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenar"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Dirección del ordenamiento"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de una entidad con paginación y filtros"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        result = await crud_generator.list_entities(
            business_id=business_id,
            entity_name=entidad,
            user=current_user,
            page=page,
            per_page=per_page,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return BaseResponse(data=result)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/{entidad}/{item_id}")
async def get_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener un item específico de una entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.get_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            user=current_user
        )
        
        return BaseResponse(data=item)
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{business_id}/{entidad}")
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
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.create_entity(
            business_id=business_id,
            entity_name=entidad,
            data=item_data,
            user=current_user
        )
        
        return BaseResponse(data=item, message="Item creado exitosamente")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{business_id}/{entidad}/{item_id}")
async def update_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    item_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Actualizar item existente en entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        item = await crud_generator.update_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            data=item_data,
            user=current_user
        )
        
        return BaseResponse(data=item, message="Item actualizado exitosamente")
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{business_id}/{entidad}/{item_id}")
async def delete_entity_item(
    business_id: str,
    entidad: str,
    item_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Eliminar item de entidad"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        success = await crud_generator.delete_entity(
            business_id=business_id,
            entity_name=entidad,
            entity_id=item_id,
            user=current_user
        )
        
        if success:
            return BaseResponse(data={"deleted": True}, message="Item eliminado exitosamente")
        else:
            raise HTTPException(status_code=404, detail="Item no encontrado")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))