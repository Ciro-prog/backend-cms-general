# ================================
# ARCHIVO: app/routers/admin/api_configs.py
# RUTA: app/routers/admin/api_configs.py
# 🔧 CORREGIDO: Agregados imports faltantes
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import logging
from enum import Enum  # ← AGREGADO: Import faltante

from ...database import get_database
from ...services.api_service import APIService
from ...models.api_integration import (
    APIConfiguration, APIConfigurationCreate,
    DynamicComponent, DynamicComponentCreate,
    AuthType, HTTPMethod, ComponentType, ComponentLayoutType  # ← AGREGADO: Imports de enums
)

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_api_service():
    db = get_database()
    return APIService(db)

# ================================
# API CONFIGURATIONS
# ================================

@router.post("/configurations", response_model=dict)
async def create_api_configuration(
    api_data: APIConfigurationCreate,
    service: APIService = Depends(get_api_service)
):
    """Crear nueva configuración de API"""
    try:
        # Generar ID único
        import time
        api_id = f"{api_data.name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Crear configuración completa
        api_config = APIConfiguration(
            api_id=api_id,
            **api_data.dict()
        )
        
        created_config = await service.create_api_config(api_config)
        return {
            "success": True,
            "data": created_config.dict(),
            "message": "Configuración de API creada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error creando API config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/configurations/{api_id}")
async def get_api_configuration(
    api_id: str,
    service: APIService = Depends(get_api_service)
):
    """Obtener configuración de API"""
    config = await service.get_api_config(api_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración de API no encontrada")
    
    return {
        "success": True,
        "data": config.dict(),
        "message": "Configuración encontrada"
    }

@router.post("/configurations/{api_id}/test")
async def test_api_configuration(
    api_id: str,
    service: APIService = Depends(get_api_service)
):
    """Probar configuración de API"""
    try:
        result = await service.call_api(api_id, component_id="test", user_id="admin")
        return {
            "success": result["success"],
            "data": result.get("data", [])[:5] if result.get("data") else None,  # Solo primeros 5 para test
            "message": "Prueba completada",
            "test_result": result
        }
    except Exception as e:
        logger.error(f"Error probando API: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Error en la prueba de API"
        }

# ================================
# DYNAMIC COMPONENTS
# ================================

@router.post("/components", response_model=dict)
async def create_dynamic_component(
    component_data: DynamicComponentCreate,
    service: APIService = Depends(get_api_service)
):
    """Crear nuevo componente dinámico"""
    try:
        # Generar ID único
        import time
        component_id = f"{component_data.name.lower().replace(' ', '_')}_{int(time.time())}"
        
        # Crear componente completo
        component = DynamicComponent(
            component_id=component_id,
            **component_data.dict()
        )
        
        # Guardar en base de datos
        db = get_database()
        await db.dynamic_components.insert_one(component.dict())
        
        return {
            "success": True,
            "data": component.dict(),
            "message": "Componente dinámico creado exitosamente"
        }
    except Exception as e:
        logger.error(f"Error creando componente: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/components/business/{business_id}")
async def list_business_components(
    business_id: str,
    service: APIService = Depends(get_api_service)
):
    """Listar componentes de un business"""
    try:
        db = get_database()
        cursor = db.dynamic_components.find({"business_id": business_id})
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
        logger.error(f"Error listando componentes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# ESTADÍSTICAS Y LOGS
# ================================

@router.get("/stats")
async def get_admin_stats():
    """Obtener estadísticas generales del sistema"""
    try:
        from ...services.business_service import BusinessService
        
        db = get_database()
        business_service = BusinessService(db)
        business_stats = await business_service.get_business_stats()
        
        # Estadísticas adicionales
        total_apis = await db.api_configurations.count_documents({})
        total_components = await db.dynamic_components.count_documents({})
        total_logs = await db.api_logs.count_documents({})
        
        return {
            "success": True,
            "data": {
                **business_stats,
                "total_api_configurations": total_apis,
                "total_dynamic_components": total_components,
                "total_api_calls": total_logs
            },
            "message": "Estadísticas obtenidas exitosamente"
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = Query(50, ge=1, le=500)
):
    """Obtener logs recientes del sistema"""
    try:
        db = get_database()
        cursor = db.api_logs.find({}).sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            # Remover _id para serialización
            doc.pop("_id", None)
            logs.append(doc)
        
        return {
            "success": True,
            "data": logs,
            "total": len(logs),
            "message": f"Se obtuvieron {len(logs)} logs recientes"
        }
    except Exception as e:
        logger.error(f"Error obteniendo logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ================================
# INICIALIZACIÓN
# ================================

@router.post("/initialize")
async def initialize_system():
    """Inicializar sistema con datos por defecto"""
    try:
        from ...services.business_service import BusinessService
        
        db = get_database()
        service = BusinessService(db)
        await service.initialize_default_data()
        return {
            "success": True,
            "message": "Sistema inicializado con datos por defecto"
        }
    except Exception as e:
        logger.error(f"Error inicializando sistema: {e}")
        raise HTTPException(status_code=500, detail=str(e))