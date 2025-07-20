from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...auth.dependencies import require_super_admin
from ...models.business import BusinessType, BusinessTypeCreate, BusinessTypeUpdate
from ...models.responses import BaseResponse, PaginatedResponse
from ...services.business_service import BusinessService

router = APIRouter()

@router.get("/", response_model=BaseResponse[List[BusinessType]])
async def get_business_types(
    _: dict = Depends(require_super_admin)
):
    """Obtener todos los tipos de negocio"""
    business_service = BusinessService()
    business_types = await business_service.get_all_business_types()
    return BaseResponse(data=business_types)

@router.get("/{tipo}", response_model=BaseResponse[BusinessType])
async def get_business_type(
    tipo: str,
    _: dict = Depends(require_super_admin)
):
    """Obtener un tipo de negocio específico"""
    business_service = BusinessService()
    business_type = await business_service.get_business_type_by_tipo(tipo)
    
    if not business_type:
        raise HTTPException(status_code=404, detail="Tipo de negocio no encontrado")
    
    return BaseResponse(data=business_type)

@router.post("/", response_model=BaseResponse[BusinessType])
async def create_business_type(
    business_type_data: BusinessTypeCreate,
    _: dict = Depends(require_super_admin)
):
    """Crear un nuevo tipo de negocio"""
    business_service = BusinessService()
    
    # Verificar que no exista
    existing = await business_service.get_business_type_by_tipo(business_type_data.tipo)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Ya existe un tipo de negocio con este identificador"
        )
    
    business_type = await business_service.create_business_type(business_type_data)
    return BaseResponse(
        data=business_type,
        message="Tipo de negocio creado exitosamente"
    )

@router.put("/{tipo}", response_model=BaseResponse[BusinessType])
async def update_business_type(
    tipo: str,
    business_type_update: BusinessTypeUpdate,
    _: dict = Depends(require_super_admin)
):
    """Actualizar un tipo de negocio"""
    business_service = BusinessService()
    business_type = await business_service.update_business_type(tipo, business_type_update)
    
    if not business_type:
        raise HTTPException(status_code=404, detail="Tipo de negocio no encontrado")
    
    return BaseResponse(
        data=business_type,
        message="Tipo de negocio actualizado exitosamente"
    )

@router.delete("/{tipo}", response_model=BaseResponse[dict])
async def delete_business_type(
    tipo: str,
    _: dict = Depends(require_super_admin)
):
    """Eliminar un tipo de negocio"""
    business_service = BusinessService()
    
    # Verificar que no haya instances usando este tipo
    instances = await business_service.get_businesses_by_type(tipo)
    if instances:
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: existen negocios usando este tipo"
        )
    
    success = await business_service.delete_business_type(tipo)
    if not success:
        raise HTTPException(status_code=404, detail="Tipo de negocio no encontrado")
    
    return BaseResponse(
        data={"deleted": True},
        message="Tipo de negocio eliminado exitosamente"
    )