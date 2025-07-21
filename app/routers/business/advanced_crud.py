# ================================
# app/routers/business/advanced_crud.py
# ================================

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import Dict, Any, Optional, List, Union
import json

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse
from ...core.dynamic_crud import DynamicCrudGenerator
from ...services.validation_service import ValidationService

router = APIRouter()

@router.get("/{business_id}/{entity_name}/advanced")
async def get_entity_data_advanced(
    business_id: str,
    entity_name: str,
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(25, ge=1, le=100, description="Items por página"),
    filters: Optional[str] = Query(None, description="Filtros en formato JSON o query string"),
    sort_by: Optional[str] = Query(None, description="Campo para ordenar"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    include_metadata: bool = Query(False, description="Incluir metadatos de la entidad"),
    format: str = Query("json", regex="^(json|csv|excel)$", description="Formato de respuesta"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de entidad con opciones avanzadas"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        
        # Procesar filtros avanzados
        processed_filters = None
        if filters:
            try:
                # Intentar parsear como JSON primero
                processed_filters = json.loads(filters)
            except json.JSONDecodeError:
                # Si falla, tratar como query string
                processed_filters = filters
        
        result = await crud_generator.list_entities(
            business_id=business_id,
            entity_name=entity_name,
            user=current_user,
            page=page,
            per_page=per_page,
            filters=processed_filters,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        response_data = result
        
        # Agregar metadatos si se solicita
        if include_metadata:
            entity_config = await crud_generator.get_entity_config(business_id, entity_name)
            response_data["metadata"] = {
                "entity_name": entity_name,
                "fields_config": entity_config.configuracion.get("campos", []),
                "api_config": entity_config.configuracion.get("api_config", {}),
                "crud_permissions": entity_config.configuracion.get("crud_config", {}),
                "total_fields": len(entity_config.configuracion.get("campos", [])),
                "data_source": "api" if entity_config.configuracion.get("api_config") else "database"
            }
        
        # Manejar diferentes formatos de respuesta
        if format == "csv":
            return await _export_to_csv(response_data["items"], entity_name)
        elif format == "excel":
            return await _export_to_excel(response_data["items"], entity_name)
        
        return BaseResponse(
            data=response_data,
            message=f"Datos de {entity_name} obtenidos exitosamente"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/{entity_name}/bulk")
async def bulk_create_entities(
    business_id: str,
    entity_name: str,
    items_data: List[Dict[str, Any]],
    validate_all: bool = Query(True, description="Validar todos los items antes de crear"),
    continue_on_error: bool = Query(False, description="Continuar si algún item falla"),
    current_user: User = Depends(get_current_business_user)
):
    """Crear múltiples entidades en una operación"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if len(items_data) > 100:
        raise HTTPException(status_code=400, detail="Máximo 100 items por operación bulk")
    
    try:
        crud_generator = DynamicCrudGenerator()
        validation_service = ValidationService()
        
        results = []
        errors = []
        
        # Validar todos primero si se solicita
        if validate_all:
            entity_config = await crud_generator.get_entity_config(business_id, entity_name)
            campos_config = entity_config.configuracion.get("campos", [])
            
            for i, item_data in enumerate(items_data):
                try:
                    for campo_config in campos_config:
                        field_name = campo_config["campo"]
                        if field_name in item_data:
                            await validation_service.validate_field(
                                item_data[field_name], campo_config
                            )
                except Exception as e:
                    errors.append({"index": i, "error": str(e), "data": item_data})
            
            if errors and not continue_on_error:
                return BaseResponse(
                    data={
                        "created": 0,
                        "errors": errors,
                        "validation_failed": True
                    },
                    message="Validación falló, no se crearon items"
                )
        
        # Crear items uno por uno
        for i, item_data in enumerate(items_data):
            try:
                result = await crud_generator.create_entity(
                    business_id=business_id,
                    entity_name=entity_name,
                    data=item_data,
                    user=current_user
                )
                results.append({"index": i, "success": True, "data": result})
                
            except Exception as e:
                error_info = {"index": i, "success": False, "error": str(e), "data": item_data}
                errors.append(error_info)
                
                if not continue_on_error:
                    break
        
        return BaseResponse(
            data={
                "created": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors,
                "total_processed": len(results) + len(errors)
            },
            message=f"Operación bulk completada: {len(results)} creados, {len(errors)} errores"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{business_id}/{entity_name}/bulk")
async def bulk_update_entities(
    business_id: str,
    entity_name: str,
    updates_data: List[Dict[str, Any]],
    current_user: User = Depends(get_current_business_user)
):
    """Actualizar múltiples entidades en una operación"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        
        results = []
        errors = []
        
        for i, update_data in enumerate(updates_data):
            if "id" not in update_data:
                errors.append({"index": i, "error": "Campo 'id' requerido", "data": update_data})
                continue
            
            entity_id = update_data.pop("id")
            
            try:
                result = await crud_generator.update_entity(
                    business_id=business_id,
                    entity_name=entity_name,
                    entity_id=str(entity_id),
                    data=update_data,
                    user=current_user
                )
                results.append({"index": i, "id": entity_id, "success": True, "data": result})
                
            except Exception as e:
                errors.append({
                    "index": i, 
                    "id": entity_id,
                    "success": False, 
                    "error": str(e), 
                    "data": update_data
                })
        
        return BaseResponse(
            data={
                "updated": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors
            },
            message=f"Actualización bulk: {len(results)} actualizados, {len(errors)} errores"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{business_id}/{entity_name}/bulk")
async def bulk_delete_entities(
    business_id: str,
    entity_name: str,
    entity_ids: List[str] = Body(..., description="Lista de IDs a eliminar"),
    force: bool = Query(False, description="Forzar eliminación sin confirmación"),
    current_user: User = Depends(get_current_business_user)
):
    """Eliminar múltiples entidades en una operación"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    if len(entity_ids) > 50:
        raise HTTPException(status_code=400, detail="Máximo 50 items para eliminación bulk")
    
    try:
        crud_generator = DynamicCrudGenerator()
        
        # Verificar permisos de eliminación
        entity_config = await crud_generator.get_entity_config(business_id, entity_name)
        crud_config = entity_config.configuracion.get("crud_config", {})
        delete_config = crud_config.get("eliminar", {})
        
        if delete_config.get("confirmacion", False) and not force:
            raise HTTPException(
                status_code=400, 
                detail="Esta entidad requiere confirmación. Use force=true"
            )
        
        results = []
        errors = []
        
        for entity_id in entity_ids:
            try:
                success = await crud_generator.delete_entity(
                    business_id=business_id,
                    entity_name=entity_name,
                    entity_id=entity_id,
                    user=current_user
                )
                
                if success:
                    results.append({"id": entity_id, "success": True})
                else:
                    errors.append({"id": entity_id, "success": False, "error": "No encontrado"})
                    
            except Exception as e:
                errors.append({"id": entity_id, "success": False, "error": str(e)})
        
        return BaseResponse(
            data={
                "deleted": len(results),
                "failed": len(errors),
                "results": results,
                "errors": errors
            },
            message=f"Eliminación bulk: {len(results)} eliminados, {len(errors)} errores"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/{entity_name}/search")
async def advanced_search_entities(
    business_id: str,
    entity_name: str,
    search_query: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Búsqueda avanzada en entidades"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        
        # Obtener configuración de la entidad
        entity_config = await crud_generator.get_entity_config(business_id, entity_name)
        campos = entity_config.configuracion.get("campos", [])
        
        # Construir query de búsqueda
        search_filters = {}
        
        # Búsqueda por texto en múltiples campos
        if "text" in search_query:
            text_query = search_query["text"]
            text_fields = [c["campo"] for c in campos if c["tipo"] in ["text", "textarea", "email"]]
            # TODO: Implementar búsqueda de texto completo
            # Por ahora, buscar en el primer campo de texto
            if text_fields:
                search_filters[text_fields[0]] = {"$regex": text_query, "$options": "i"}
        
        # Filtros por campo específico
        if "filters" in search_query:
            for field, value in search_query["filters"].items():
                search_filters[field] = value
        
        # Rango de fechas
        if "date_range" in search_query:
            date_range = search_query["date_range"]
            date_field = date_range.get("field", "created_at")
            if "start" in date_range:
                search_filters[date_field] = {"$gte": date_range["start"]}
            if "end" in date_range:
                if date_field in search_filters:
                    search_filters[date_field]["$lte"] = date_range["end"]
                else:
                    search_filters[date_field] = {"$lte": date_range["end"]}
        
        # Realizar búsqueda
        result = await crud_generator.list_entities(
            business_id=business_id,
            entity_name=entity_name,
            user=current_user,
            page=search_query.get("page", 1),
            per_page=search_query.get("per_page", 25),
            filters=search_filters,
            sort_by=search_query.get("sort_by"),
            sort_order=search_query.get("sort_order", "asc")
        )
        
        return BaseResponse(
            data={
                **result,
                "search_query": search_query,
                "filters_applied": search_filters
            },
            message=f"Búsqueda completada: {len(result.get('items', []))} resultados"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/{entity_name}/schema")
async def get_entity_schema(
    business_id: str,
    entity_name: str,
    include_validation: bool = Query(True, description="Incluir reglas de validación"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener esquema completo de la entidad"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        entity_config = await crud_generator.get_entity_config(business_id, entity_name)
        
        campos = entity_config.configuracion.get("campos", [])
        api_config = entity_config.configuracion.get("api_config")
        crud_config = entity_config.configuracion.get("crud_config", {})
        
        # Generar esquema de campos
        fields_schema = []
        for campo in campos:
            field_schema = {
                "name": campo["campo"],
                "type": campo["tipo"],
                "required": campo.get("obligatorio", False),
                "visible_roles": campo.get("visible_roles", ["*"]),
                "editable_roles": campo.get("editable_roles", ["admin"]),
                "description": campo.get("descripcion", "")
            }
            
            if include_validation and campo.get("validacion"):
                field_schema["validation"] = campo["validacion"]
            
            if campo.get("opciones"):
                field_schema["options"] = campo["opciones"]
            
            fields_schema.append(field_schema)
        
        # Información de la fuente de datos
        data_source = {
            "type": "api" if api_config else "database",
            "config": api_config if api_config else None
        }
        
        # Capacidades CRUD
        capabilities = {
            "create": crud_config.get("crear", {}).get("habilitado", False),
            "read": True,  # Siempre disponible
            "update": crud_config.get("editar", {}).get("habilitado", False),
            "delete": crud_config.get("eliminar", {}).get("habilitado", False)
        }
        
        schema = {
            "entity_name": entity_name,
            "business_id": business_id,
            "fields": fields_schema,
            "data_source": data_source,
            "capabilities": capabilities,
            "total_fields": len(fields_schema),
            "required_fields": len([f for f in fields_schema if f["required"]]),
            "last_updated": entity_config.updated_at.isoformat()
        }
        
        return BaseResponse(
            data=schema,
            message="Esquema de entidad obtenido"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/{entity_name}/validate")
async def validate_entity_data(
    business_id: str,
    entity_name: str,
    data_to_validate: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Validar datos contra el esquema de la entidad"""
    
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        crud_generator = DynamicCrudGenerator()
        validation_service = ValidationService()
        
        entity_config = await crud_generator.get_entity_config(business_id, entity_name)
        campos = entity_config.configuracion.get("campos", [])
        
        validation_results = []
        overall_valid = True
        
        for campo_config in campos:
            field_name = campo_config["campo"]
            field_value = data_to_validate.get(field_name)
            
            try:
                validated_value = await validation_service.validate_field(
                    field_value, campo_config
                )
                
                validation_results.append({
                    "field": field_name,
                    "valid": True,
                    "value": validated_value,
                    "message": "Válido"
                })
                
            except Exception as e:
                overall_valid = False
                validation_results.append({
                    "field": field_name,
                    "valid": False,
                    "value": field_value,
                    "message": str(e)
                })
        
        return BaseResponse(
            data={
                "overall_valid": overall_valid,
                "field_validations": validation_results,
                "valid_fields": len([r for r in validation_results if r["valid"]]),
                "invalid_fields": len([r for r in validation_results if not r["valid"]])
            },
            message="Validación completada"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ================================
# FUNCIONES AUXILIARES
# ================================

async def _export_to_csv(items: List[Dict[str, Any]], entity_name: str):
    """Exportar datos a CSV"""
    import csv
    import io
    from fastapi.responses import StreamingResponse
    
    if not items:
        raise HTTPException(status_code=400, detail="No hay datos para exportar")
    
    output = io.StringIO()
    
    # Usar las claves del primer item como headers
    fieldnames = list(items[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    
    writer.writeheader()
    for item in items:
        # Convertir valores complejos a string
        row = {}
        for key, value in item.items():
            if isinstance(value, (dict, list)):
                row[key] = json.dumps(value)
            else:
                row[key] = str(value) if value is not None else ""
        writer.writerow(row)
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_name}.csv"}
    )

async def _export_to_excel(items: List[Dict[str, Any]], entity_name: str):
    """Exportar datos a Excel"""
    # TODO: Implementar exportación a Excel usando openpyxl
    raise HTTPException(status_code=501, detail="Exportación a Excel no implementada aún")

