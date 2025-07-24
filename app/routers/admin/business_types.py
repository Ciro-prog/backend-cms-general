# ================================
# ARCHIVO: app/routers/admin/business_types.py  
# RUTA: app/routers/admin/business_types.py
# 🔧 CORREGIDO: Agregados imports faltantes
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from enum import Enum  # ← AGREGADO: Import faltante

from ...database import get_database
from ...services.business_service import BusinessService
from ...models.business import (
    BusinessType, BusinessTypeCreate, BusinessTypeUpdate,
    BusinessTypeResponse, BusinessTypeListResponse,
    BusinessTypeStatus, ComponentType  # ← AGREGADO: Imports de enums
)

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_business_service():
    """Dependency para obtener BusinessService"""
    db = get_database()
    return BusinessService(db)

@router.get("/", response_model=BusinessTypeListResponse)
async def list_business_types(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BusinessService = Depends(get_business_service)
):
    """Listar Business Types"""
    try:
        business_types = await service.list_business_types(skip=skip, limit=limit)
        return BusinessTypeListResponse(
            data=business_types,
            total=len(business_types),
            message=f"Se encontraron {len(business_types)} business types"
        )
    except Exception as e:
        logger.error(f"Error listando business types: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/", response_model=BusinessTypeResponse)
async def create_business_type(
    business_type_data: BusinessTypeCreate,
    service: BusinessService = Depends(get_business_service)
):
    """Crear nuevo Business Type"""
    try:
        business_type = await service.create_business_type(business_type_data, created_by="admin")
        return BusinessTypeResponse(
            data=business_type,
            message="Business Type creado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error creando business type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_type_id}", response_model=BusinessTypeResponse)
async def get_business_type(
    business_type_id: str,
    service: BusinessService = Depends(get_business_service)
):
    """Obtener Business Type por ID"""
    business_type = await service.get_business_type(business_type_id)
    if not business_type:
        raise HTTPException(status_code=404, detail="Business Type no encontrado")
    
    return BusinessTypeResponse(
        data=business_type,
        message="Business Type encontrado"
    )

@router.put("/{business_type_id}", response_model=BusinessTypeResponse)
async def update_business_type(
    business_type_id: str,
    update_data: BusinessTypeUpdate,
    service: BusinessService = Depends(get_business_service)
):
    """Actualizar Business Type"""
    try:
        business_type = await service.update_business_type(business_type_id, update_data)
        if not business_type:
            raise HTTPException(status_code=404, detail="Business Type no encontrado")
        
        return BusinessTypeResponse(
            data=business_type,
            message="Business Type actualizado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error actualizando business type: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{business_type_id}")
async def delete_business_type(
    business_type_id: str,
    service: BusinessService = Depends(get_business_service)
):
    """Eliminar Business Type"""
    try:
        deleted = await service.delete_business_type(business_type_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Business Type no encontrado")
        
        return {"success": True, "message": "Business Type eliminado exitosamente"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error eliminando business type: {e}")
        raise HTTPException(status_code=500, detail=str(e))