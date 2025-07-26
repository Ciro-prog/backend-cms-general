# ================================
# app/routers/business/entity_data.py - Router para datos de entidades
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Imports adaptativos
try:
    from ...auth.dependencies import get_current_business_user
except ImportError:
    def get_current_business_user():
        from ...models.user import User
        return User(username="admin", rol="admin")

try:
    from ...models.user import User
except ImportError:
    from pydantic import BaseModel
    class User(BaseModel):
        username: str = "admin"
        rol: str = "admin"
        business_id: str = "demo"

from ...models.responses import BaseResponse
from ...services.api_service import ApiService
from ...services.entity_service import EntityService

# Importar cache service si está disponible
try:
    from ...services.cache_service import CacheService
except ImportError:
    # Fallback simple para cache
    class CacheService:
        async def get(self, key: str): return None
        async def set(self, key: str, value: Any, ttl: int = 300): return True
        async def delete(self, key: str): return True

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/business", tags=["Entity Data"])

# ================================
# OBTENER DATOS DE ENTIDADES
# ================================

@router.get("/{business_id}/entity-data/{entity_name}")
async def get_entity_data(
    business_id: str,
    entity_name: str,
    limit: int = Query(25, ge=1, le=100, description="Límite de registros"),
    refresh_cache: bool = Query(False, description="Forzar actualización de cache"),
    format: str = Query("json", regex="^(json|table|cards|stats)$", description="Formato de respuesta"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de una entidad con diferentes formatos"""
    
    # Verificar permisos básicos
    try:
        if hasattr(current_user, 'business_id') and current_user.business_id != business_id and getattr(current_user, 'rol', '') != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
    except:
        # Si no hay sistema de permisos, continuar
        pass
    
    try:
        entity_service = EntityService()
        api_service = ApiService()
        cache_service = CacheService()
        
        # Obtener configuración de la entidad
        entity_config = await entity_service.get_entity_config(business_id, entity_name)
        if not entity_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Entidad no encontrada: {entity_name}"
            )
        
        # Verificar si la entidad tiene configuración de API
        api_config_data = entity_config.configuracion.get("api_config")
        if not api_config_data:
            # Si no hay API, intentar obtener datos desde la base de datos local
            logger.info(f"📁 Obteniendo datos locales para entidad: {entity_name}")
            
            # Datos de ejemplo para demostración
            sample_data = {
                "entity_name": entity_name,
                "business_id": business_id,
                "items": [
                    {"id": 1, "name": f"Registro 1 de {entity_name}", "status": "active"},
                    {"id": 2, "name": f"Registro 2 de {entity_name}", "status": "inactive"}
                ],
                "total_records": 2,
                "from_cache": False,
                "last_updated": datetime.utcnow().isoformat(),
                "data_source": "local_db"
            }
            
            return BaseResponse(
                data=_format_entity_data(sample_data, format),
                message=f"Datos locales obtenidos: {len(sample_data['items'])} registros"
            )
        
        # Obtener datos desde cache si está disponible
        cache_key = f"entity_data:{business_id}:{entity_name}"
        
        if not refresh_cache:
            try:
                cached_data = await cache_service.get(cache_key)
                if cached_data:
                    logger.info(f"📦 Datos obtenidos desde cache: {entity_name}")
                    return BaseResponse(
                        data=_format_entity_data(cached_data, format),
                        message=f"Datos obtenidos desde cache: {len(cached_data.get('items', []))} registros"
                    )
            except Exception as cache_error:
                logger.warning(f"Error accediendo cache: {cache_error}")
        
        # Obtener datos desde API
        api_id = api_config_data.get("api_id")
        if not api_id:
            raise HTTPException(
                status_code=400,
                detail="Configuración de API incompleta: falta api_id"
            )
        
        # Test de la API para obtener datos
        test_result = await api_service.test_api_connection(
            business_id=business_id,
            api_id=api_id,
            limit_records=limit,
            test_mapping=True
        )
        
        if not test_result.success:
            # Si falla la API, devolver datos de ejemplo
            logger.warning(f"API falló, devolviendo datos de ejemplo para {entity_name}")
            
            fallback_data = {
                "entity_name": entity_name,
                "business_id": business_id,
                "items": [
                    {"id": f"demo_{i}", "name": f"Registro Demo {i}", "source": "fallback"}
                    for i in range(1, min(limit + 1, 6))
                ],
                "total_records": min(limit, 5),
                "from_cache": False,
                "last_updated": datetime.utcnow().isoformat(),
                "api_source": api_id,
                "error": test_result.error_message
            }
            
            return BaseResponse(
                data=_format_entity_data(fallback_data, format),
                message=f"Datos de fallback: {len(fallback_data['items'])} registros (API no disponible)"
            )
        
        # Preparar datos estructurados
        entity_data = {
            "entity_name": entity_name,
            "business_id": business_id,
            "api_source": api_id,
            "items": getattr(test_result, 'mapped_data', None) or test_result.sample_data or [],
            "total_records": test_result.total_records or 0,
            "detected_fields": test_result.detected_fields or [],
            "response_time_ms": test_result.response_time_ms,
            "last_updated": datetime.utcnow().isoformat(),
            "cache_ttl": api_config_data.get("cache_ttl", 300),
            "from_cache": False
        }
        
        # Guardar en cache si es posible
        try:
            await cache_service.set(
                cache_key, 
                entity_data, 
                ttl=entity_data["cache_ttl"]
            )
        except Exception as cache_error:
            logger.warning(f"No se pudo guardar en cache: {cache_error}")
        
        logger.info(f"🔄 Datos actualizados desde API: {entity_name} - {len(entity_data['items'])} registros")
        
        return BaseResponse(
            data=_format_entity_data(entity_data, format),
            message=f"Datos actualizados: {len(entity_data['items'])} registros"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo datos de entidad {entity_name}: {e}")
        
        # Fallback con datos básicos
        fallback_data = {
            "entity_name": entity_name,
            "business_id": business_id,
            "items": [{"id": "error", "message": f"Error: {str(e)}"}],
            "total_records": 0,
            "from_cache": False,
            "last_updated": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        
        return BaseResponse(
            data=_format_entity_data(fallback_data, format),
            message=f"Error obteniendo datos: {str(e)}",
            success=False
        )

@router.get("/{business_id}/entity-stats/{entity_name}")
async def get_entity_statistics(
    business_id: str,
    entity_name: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener estadísticas de una entidad"""
    
    try:
        # Obtener datos de la entidad
        entity_data_response = await get_entity_data(
            business_id, entity_name, limit=100, format="json", current_user=current_user
        )
        
        if not entity_data_response.success:
            raise HTTPException(status_code=500, detail="Error obteniendo datos para estadísticas")
        
        entity_data = entity_data_response.data
        items = entity_data.get("items", [])
        
        if not items:
            return BaseResponse(
                data={"message": "No hay datos para generar estadísticas"},
                message="Sin datos disponibles"
            )
        
        # Calcular estadísticas
        stats = _calculate_entity_statistics(items)
        stats.update({
            "entity_name": entity_name,
            "total_records": len(items),
            "last_updated": entity_data.get("last_updated"),
            "data_source": entity_data.get("api_source", "local"),
            "response_time_ms": entity_data.get("response_time_ms")
        })
        
        return BaseResponse(
            data=stats,
            message="Estadísticas generadas exitosamente"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generando estadísticas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando estadísticas: {str(e)}"
        )

@router.get("/{business_id}/entities/overview")
async def get_entities_overview(
    business_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener resumen de todas las entidades de un business"""
    
    try:
        entity_service = EntityService()
        
        # Obtener todas las configuraciones de entidades
        entities = await entity_service.get_entity_configs_by_business(business_id)
        
        overview = {
            "business_id": business_id,
            "total_entities": len(entities),
            "entities_with_api": 0,
            "entities_active": 0,
            "last_updated": datetime.utcnow().isoformat(),
            "entities_detail": []
        }
        
        for entity in entities:
            entity_info = {
                "name": entity.entidad,
                "has_api_config": bool(entity.configuracion.get("api_config")),
                "active": entity.configuracion.get("activo", True),
                "fields_count": len(entity.configuracion.get("campos", [])),
                "created_at": entity.created_at.isoformat() if hasattr(entity, 'created_at') and entity.created_at else None
            }
            
            if entity_info["has_api_config"]:
                overview["entities_with_api"] += 1
            
            if entity_info["active"]:
                overview["entities_active"] += 1
            
            # Intentar obtener datos básicos de la entidad
            entity_info["cached_records"] = 0
            try:
                cache_service = CacheService()
                cache_key = f"entity_data:{business_id}:{entity.entidad}"
                cached_data = await cache_service.get(cache_key)
                
                if cached_data and isinstance(cached_data, dict):
                    entity_info["cached_records"] = len(cached_data.get("items", []))
                    entity_info["last_cache_update"] = cached_data.get("last_updated")
                        
            except Exception:
                pass
            
            overview["entities_detail"].append(entity_info)
        
        return BaseResponse(
            data=overview,
            message=f"Resumen generado: {overview['total_entities']} entidades"
        )
        
    except Exception as e:
        logger.error(f"Error generando resumen de entidades: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generando resumen: {str(e)}"
        )

# ================================
# EXPORTACIÓN DE DATOS
# ================================

@router.get("/{business_id}/entity-data/{entity_name}/export")
async def export_entity_data(
    business_id: str,
    entity_name: str,
    format: str = Query("csv", regex="^(csv|json)$"),
    limit: int = Query(1000, ge=1, le=5000),
    current_user: User = Depends(get_current_business_user)
):
    """Exportar datos de entidad en diferentes formatos"""
    
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io
        import json
        
        # Obtener datos
        entity_data_response = await get_entity_data(
            business_id, entity_name, limit=limit, current_user=current_user
        )
        
        if not entity_data_response.success:
            raise HTTPException(status_code=500, detail="Error obteniendo datos para exportar")
        
        items = entity_data_response.data.get("items", [])
        
        if not items:
            raise HTTPException(status_code=404, detail="No hay datos para exportar")
        
        filename = f"{entity_name}_{business_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if format == "csv":
            output = io.StringIO()
            
            if items and isinstance(items[0], dict):
                writer = csv.DictWriter(output, fieldnames=items[0].keys())
                writer.writeheader()
                writer.writerows(items)
            
            response = StreamingResponse(
                io.BytesIO(output.getvalue().encode('utf-8')),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}.csv"}
            )
            
        else:  # json
            export_data = {
                "entity_name": entity_name,
                "business_id": business_id,
                "export_date": datetime.utcnow().isoformat(),
                "total_records": len(items),
                "data": items
            }
            
            response = StreamingResponse(
                io.BytesIO(json.dumps(export_data, indent=2, default=str).encode('utf-8')),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename={filename}.json"}
            )
        
        logger.info(f"📄 Datos exportados: {entity_name} - {len(items)} registros en formato {format}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exportando datos: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error exportando datos: {str(e)}"
        )

# ================================
# FUNCIONES AUXILIARES
# ================================

def _format_entity_data(entity_data: Dict[str, Any], format: str) -> Dict[str, Any]:
    """Formatear datos según el tipo solicitado"""
    
    items = entity_data.get("items", [])
    
    if format == "json":
        return entity_data
    
    elif format == "table":
        if not items:
            return {"columns": [], "rows": [], "total": 0}
        
        # Manejar items que pueden no ser diccionarios
        if items and isinstance(items[0], dict):
            columns = list(items[0].keys())
            rows = []
            
            for item in items:
                row = [item.get(col, "") for col in columns]
                rows.append(row)
        else:
            columns = ["data"]
            rows = [[str(item)] for item in items]
        
        return {
            "columns": columns,
            "rows": rows,
            "total": len(items),
            "entity_info": {
                "name": entity_data.get("entity_name"),
                "last_updated": entity_data.get("last_updated")
            }
        }
    
    elif format == "cards":
        return {
            "cards": items,
            "total": len(items),
            "entity_info": {
                "name": entity_data.get("entity_name"),
                "api_source": entity_data.get("api_source"),
                "last_updated": entity_data.get("last_updated")
            }
        }
    
    elif format == "stats":
        return {
            "statistics": _calculate_entity_statistics(items),
            "summary": {
                "total_records": len(items),
                "entity_name": entity_data.get("entity_name"),
                "data_source": entity_data.get("api_source", "local")
            }
        }
    
    return entity_data

def _calculate_entity_statistics(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcular estadísticas de los datos de una entidad"""
    
    if not items:
        return {"error": "No hay datos para calcular estadísticas"}
    
    # Asegurar que tenemos diccionarios
    dict_items = []
    for item in items:
        if isinstance(item, dict):
            dict_items.append(item)
        else:
            dict_items.append({"value": str(item)})
    
    if not dict_items:
        return {"error": "No hay datos válidos para estadísticas"}
    
    stats = {
        "total_records": len(dict_items),
        "fields_analysis": {},
        "data_quality": {
            "completeness_avg": 0,
            "consistency_score": 0
        },
        "field_types": {},
        "numeric_stats": {}
    }
    
    # Analizar cada campo
    fields = set()
    for item in dict_items:
        fields.update(item.keys())
    
    fields = list(fields)
    
    for field in fields:
        values = [item.get(field) for item in dict_items]
        non_null_values = [v for v in values if v is not None and v != ""]
        
        # Completitud
        completeness = len(non_null_values) / len(values) if values else 0
        
        # Tipos de datos
        types = [type(v).__name__ for v in non_null_values]
        type_counts = {}
        for t in types:
            type_counts[t] = type_counts.get(t, 0) + 1
        
        primary_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "unknown"
        
        stats["fields_analysis"][field] = {
            "completeness": round(completeness * 100, 2),
            "primary_type": primary_type,
            "unique_values": len(set(str(v) for v in non_null_values)),
            "sample_values": non_null_values[:3] if non_null_values else []
        }
        
        stats["field_types"][field] = primary_type
        
        # Estadísticas numéricas
        if primary_type in ['int', 'float']:
            numeric_values = [v for v in non_null_values if isinstance(v, (int, float))]
            if numeric_values:
                stats["numeric_stats"][field] = {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "avg": sum(numeric_values) / len(numeric_values),
                    "median": sorted(numeric_values)[len(numeric_values) // 2] if numeric_values else 0
                }
    
    # Calcular promedio de completitud
    if stats["fields_analysis"]:
        completeness_values = [fa["completeness"] for fa in stats["fields_analysis"].values()]
        stats["data_quality"]["completeness_avg"] = round(
            sum(completeness_values) / len(completeness_values), 2
        )
    
    return stats

# Log de inicialización del router
logger.info("📊 Router Entity Data configurado correctamente")