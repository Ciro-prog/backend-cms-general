# ================================
# ARCHIVO: app/routers/admin/business_instances.py
# RUTA: app/routers/admin/business_instances.py  
# 🔧 CORREGIDO: Agregados imports faltantes
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from enum import Enum  # ← AGREGADO: Import faltante

from ...database import get_database
from ...services.business_service import BusinessService
from ...models.business import (
    BusinessInstance, BusinessInstanceCreate, BusinessInstanceUpdate,
    BusinessInstanceResponse, BusinessInstanceListResponse,
    BusinessStatus  # ← AGREGADO: Import de enum
)

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_business_service():
    db = get_database()
    return BusinessService(db)

@router.get("/", response_model=BusinessInstanceListResponse)
async def list_business_instances(
    business_type_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BusinessService = Depends(get_business_service)
):
    """Listar Business Instances"""
    try:
        instances = await service.list_business_instances(
            business_type_id=business_type_id, 
            skip=skip, 
            limit=limit
        )
        return BusinessInstanceListResponse(
            data=instances,
            total=len(instances),
            message=f"Se encontraron {len(instances)} business instances"
        )
    except Exception as e:
        logger.error(f"Error listando business instances: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@router.post("/", response_model=BusinessInstanceResponse)
async def create_business_instance(
    business_data: BusinessInstanceCreate,
    service: BusinessService = Depends(get_business_service)
):
    """Crear nueva Business Instance"""
    try:
        business = await service.create_business_instance(business_data, created_by="admin")
        return BusinessInstanceResponse(
            data=business,
            message="Business Instance creado exitosamente"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando business instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_id}", response_model=BusinessInstanceResponse)
async def get_business_instance(
    business_id: str,
    service: BusinessService = Depends(get_business_service)
):
    """Obtener Business Instance por ID"""
    business = await service.get_business_instance(business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business Instance no encontrado")
    
    return BusinessInstanceResponse(
        data=business,
        message="Business Instance encontrado"
    )

@router.put("/{business_id}", response_model=BusinessInstanceResponse) 
async def update_business_instance(
    business_id: str,
    update_data: BusinessInstanceUpdate,
    service: BusinessService = Depends(get_business_service)
):
    """Actualizar Business Instance"""
    try:
        business = await service.update_business_instance(business_id, update_data)
        if not business:
            raise HTTPException(status_code=404, detail="Business Instance no encontrado")
        
        return BusinessInstanceResponse(
            data=business,
            message="Business Instance actualizado exitosamente"
        )
    except Exception as e:
        logger.error(f"Error actualizando business instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{business_id}")
async def delete_business_instance(
    business_id: str,
    service: BusinessService = Depends(get_business_service)
):
    """Eliminar Business Instance"""
    try:
        deleted = await service.delete_business_instance(business_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Business Instance no encontrado")
        
        return {"success": True, "message": "Business Instance eliminado exitosamente"}
    except Exception as e:
        logger.error(f"Error eliminando business instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_id}/with-type")
async def get_business_with_type(
    business_id: str,
    service: BusinessService = Depends(get_business_service)
):
    """Obtener Business Instance con su Business Type"""
    result = await service.get_business_with_type(business_id)
    if not result:
        raise HTTPException(status_code=404, detail="Business Instance no encontrado")
    
    return {
        "success": True,
        "data": result,
        "message": "Business con tipo obtenido exitosamente"
    }