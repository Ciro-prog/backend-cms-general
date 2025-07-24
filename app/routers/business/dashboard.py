# ================================
# ARCHIVO: app/routers/business/dashboard.py
# RUTA: app/routers/business/dashboard.py
# 🔧 CORREGIDO: Agregados imports faltantes
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from enum import Enum  # ← AGREGADO: Import faltante

from ...database import get_database
from ...services.business_service import BusinessService
from ...services.api_service import APIService

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_business_service():
    db = get_database()
    return BusinessService(db)

async def get_api_service():
    db = get_database()
    return APIService(db)

@router.get("/{business_id}")
async def get_business_dashboard(
    business_id: str,
    business_service: BusinessService = Depends(get_business_service),
    api_service: APIService = Depends(get_api_service)
):
    """Obtener datos del dashboard para un business específico"""
    try:
        # Obtener información del business y su tipo
        business_info = await business_service.get_business_with_type(business_id)
        if not business_info:
            raise HTTPException(status_code=404, detail="Business no encontrado")
        
        business = business_info["business"]
        business_type = business_info["business_type"]
        
        # Obtener componentes dinámicos activos
        db = get_database()
        cursor = db.dynamic_components.find({
            "business_id": business_id,
            "is_active": True
        })
        
        active_components = []
        component_data = {}
        
        async for component_doc in cursor:
            component_id = component_doc["component_id"]
            active_components.append(component_doc)
            
            # Obtener datos para cada componente
            try:
                api_result = await api_service.call_api(
                    component_doc["api_id"], 
                    component_id=component_id,
                    user_id="dashboard"
                )
                component_data[component_id] = api_result
            except Exception as e:
                logger.error(f"Error obteniendo datos para componente {component_id}: {e}")
                component_data[component_id] = {
                    "success": False,
                    "error": str(e),
                    "data": []
                }
        
        # Generar estadísticas básicas
        stats = await _generate_dashboard_stats(business_id, component_data)
        
        return {
            "success": True,
            "data": {
                "business": business.dict(),
                "business_type": business_type.dict() if business_type else None,
                "active_components": active_components,
                "component_data": component_data,
                "stats": stats,
                "last_updated": str(datetime.utcnow())
            },
            "message": "Dashboard cargado exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error cargando dashboard para {business_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_id}/components")
async def get_business_components(
    business_id: str,
    component_type: Optional[str] = Query(None),
    layout_type: Optional[str] = Query(None)
):
    """Obtener componentes de un business con filtros opcionales"""
    try:
        db = get_database()
        
        # Construir filtro
        filter_dict = {"business_id": business_id, "is_active": True}
        if component_type:
            filter_dict["component_type"] = component_type
        if layout_type:
            filter_dict["layout_type"] = layout_type
        
        cursor = db.dynamic_components.find(filter_dict)
        components = []
        async for doc in cursor:
            components.append(doc)
        
        return {
            "success": True,
            "data": components,
            "total": len(components),
            "message": f"Se encontraron {len(components)} componentes"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo componentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{business_id}/component/{component_id}/data")
async def get_component_data(
    business_id: str,
    component_id: str,
    refresh: bool = Query(False, description="Forzar actualización de cache"),
    api_service: APIService = Depends(get_api_service)
):
    """Obtener datos específicos de un componente"""
    try:
        # Verificar que el componente pertenece al business
        db = get_database()
        component = await db.dynamic_components.find_one({
            "component_id": component_id,
            "business_id": business_id,
            "is_active": True
        })
        
        if not component:
            raise HTTPException(status_code=404, detail="Componente no encontrado")
        
        # Si refresh es True, limpiar cache primero
        if refresh:
            await db.api_cache.delete_many({"api_id": component["api_id"]})
        
        # Obtener datos del componente
        result = await api_service.call_api(
            component["api_id"],
            component_id=component_id,
            user_id="component_request"
        )
        
        return {
            "success": True,
            "data": result.get("data", []),
            "component_info": component,
            "cached": result.get("cached", False),
            "response_time_ms": result.get("response_time_ms"),
            "message": "Datos del componente obtenidos exitosamente"
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo datos del componente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# FUNCIONES AUXILIARES
# ================================

async def _generate_dashboard_stats(business_id: str, component_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generar estadísticas básicas del dashboard"""
    stats = {
        "total_components": len(component_data),
        "successful_components": 0,
        "failed_components": 0,
        "total_records": 0,
        "cached_components": 0
    }
    
    for component_id, data in component_data.items():
        if data.get("success", False):
            stats["successful_components"] += 1
            component_records = data.get("data", [])
            if isinstance(component_records, list):
                stats["total_records"] += len(component_records)
        else:
            stats["failed_components"] += 1
        
        if data.get("cached", False):
            stats["cached_components"] += 1
    
    return stats