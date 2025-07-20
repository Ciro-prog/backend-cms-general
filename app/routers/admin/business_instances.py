from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...auth.dependencies import require_admin
from ...models.business import BusinessInstance, BusinessInstanceCreate, BusinessInstanceUpdate
from ...models.responses import BaseResponse, PaginatedResponse
from ...services.business_service import BusinessService

router = APIRouter()

@router.get("/", response_model=BaseResponse[List[BusinessInstance]])
async def get_business_instances(
    tipo_base: Optional[str] = Query(None, description="Filtrar por tipo base"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
    _: dict = Depends(require_admin)
):
    """Obtener todas las instancias de negocio"""
    business_service = BusinessService()
    businesses = await business_service.get_all_business_instances(
        tipo_base=tipo_base,
        activo=activo
    )
    return BaseResponse(data=businesses)

@router.get("/{business_id}", response_model=BaseResponse[BusinessInstance])
async def get_business_instance(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Obtener una instancia de negocio específica"""
    business_service = BusinessService()
    business = await business_service.get_business_instance(business_id)
    
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    return BaseResponse(data=business)

@router.post("/", response_model=BaseResponse[BusinessInstance])
async def create_business_instance(
    business_data: BusinessInstanceCreate,
    _: dict = Depends(require_admin)
):
    """Crear una nueva instancia de negocio"""
    business_service = BusinessService()
    
    # Verificar que no exista
    existing = await business_service.get_business_instance(business_data.business_id)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un negocio con este ID"
        )
    
    # Verificar que el tipo base exista
    business_type = await business_service.get_business_type_by_tipo(business_data.tipo_base)
    if not business_type:
        raise HTTPException(
            status_code=400,
            detail="El tipo base especificado no existe"
        )
    
    business = await business_service.create_business_instance(business_data)
    return BaseResponse(
        data=business,
        message="Negocio creado exitosamente"
    )

@router.put("/{business_id}", response_model=BaseResponse[BusinessInstance])
async def update_business_instance(
    business_id: str,
    business_update: BusinessInstanceUpdate,
    _: dict = Depends(require_admin)
):
    """Actualizar una instancia de negocio"""
    business_service = BusinessService()
    business = await business_service.update_business_instance(business_id, business_update)
    
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    return BaseResponse(
        data=business,
        message="Negocio actualizado exitosamente"
    )

@router.delete("/{business_id}", response_model=BaseResponse[dict])
async def delete_business_instance(
    business_id: str,
    _: dict = Depends(require_admin)
):
    """Eliminar una instancia de negocio"""
    business_service = BusinessService()
    
    success = await business_service.delete_business_instance(business_id)
    if not success:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    
    return BaseResponse(
        data={"deleted": True},
        message="Negocio eliminado exitosamente"
    )