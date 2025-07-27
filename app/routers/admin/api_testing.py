# ================================
# app/routers/admin/api_testing.py
# Router mejorado con mapping manual y preview
# ================================

from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional, List
import httpx
import json
from ...auth.dependencies import require_admin
from ...models.user import User
from ...models.field_mapping import MappingConfiguration, MappedField, NestedFieldStructure
from ...services.field_mapper_service import FieldMapperService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/test-connection")
async def test_api_connection(
    business_id: str = Form(...),
    name: str = Form(...),
    base_url: str = Form(...),
    endpoint: str = Form(...),
    method: str = Form(default="GET"),
    headers: Optional[str] = Form(default="{}"),
    params: Optional[str] = Form(default="{}"),
    current_user: User = Depends(require_admin)
):
    """Test de conexión API con análisis de estructura"""
    
    try:
        # Construir URL completa
        full_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Parsear headers y params
        try:
            headers_dict = json.loads(headers) if headers else {}
            params_dict = json.loads(params) if params else {}
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Error en JSON: {str(e)}")
        
        # Realizar petición
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=full_url,
                headers=headers_dict,
                params=params_dict
            )
        
        # Parsear respuesta
        try:
            response_data = response.json()
        except:
            response_data = {"raw_response": response.text}
        
        # Analizar estructura si la respuesta es exitosa
        field_analysis = None
        if response.status_code == 200:
            mapper_service = FieldMapperService()
            structure = mapper_service.analyze_nested_structure(response_data)
            field_analysis = {
                "detected_structure": [s.dict() for s in structure],
                "available_paths": mapper_service.generate_field_paths(structure),
                "mapping_suggestions": [m.dict() for m in mapper_service.create_mapping_suggestions(structure)]
            }
        
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "response_data": response_data,
            "field_analysis": field_analysis,
            "message": f"Conexión {'exitosa' if response.status_code == 200 else 'fallida'}"
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Timeout en la conexión")
    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"Error de conexión: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado en test de conexión: {e}")
        raise HTTPException(status_code=500, detail=f"Error inesperado: {str(e)}")

@router.post("/analyze-fields")
async def analyze_api_fields(
    request_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Analizar campos de respuesta API para mapping manual"""
    
    try:
        api_response = request_data.get("api_response")
        if not api_response:
            raise HTTPException(status_code=400, detail="api_response es requerido")
        
        mapper_service = FieldMapperService()
        
        # Analizar estructura
        structure = mapper_service.analyze_nested_structure(api_response)
        available_paths = mapper_service.generate_field_paths(structure)
        suggestions = mapper_service.create_mapping_suggestions(structure)
        
        return {
            "success": True,
            "data": {
                "detected_structure": [s.dict() for s in structure],
                "available_paths": available_paths,
                "mapping_suggestions": [m.dict() for m in suggestions],
                "total_fields": len(available_paths)
            }
        }
        
    except Exception as e:
        logger.error(f"Error analizando campos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@router.post("/save-mapping")
async def save_field_mapping(
    mapping_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Guardar configuración de mapping manual"""
    
    try:
        # Validar datos requeridos
        required_fields = ["api_id", "mapped_fields"]
        for field in required_fields:
            if field not in mapping_data:
                raise HTTPException(status_code=400, detail=f"Campo requerido: {field}")
        
        # Validar configuración
        mapper_service = FieldMapperService()
        is_valid, errors = mapper_service.validate_mapping_configuration(mapping_data)
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Configuración inválida: {', '.join(errors)}")
        
        # Crear configuración de mapping
        mapping_config = MappingConfiguration(**mapping_data)
        
        # TODO: Guardar en base de datos
        # mapping_service = MappingConfigService()
        # saved_config = await mapping_service.save_mapping(mapping_config)
        
        return {
            "success": True,
            "mapping_id": f"mapping_{mapping_data['api_id']}",
            "message": "Configuración de mapping guardada exitosamente",
            "config": mapping_config.dict()
        }
        
    except Exception as e:
        logger.error(f"Error guardando mapping: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardando mapping: {str(e)}")

@router.get("/preview-data/{mapping_id}")
async def preview_mapped_data(
    mapping_id: str,
    limit: int = 10,
    current_user: User = Depends(require_admin)
):
    """Preview de datos usando configuración de mapping"""
    
    try:
        # TODO: Cargar configuración de mapping desde DB
        # mapping_service = MappingConfigService()
        # mapping_config = await mapping_service.get_mapping(mapping_id)
        
        # Simulación para desarrollo
        sample_preview = {
            "success": True,
            "data": {
                "total_records": 25,
                "preview_records": [
                    {
                        "ID": 1,
                        "Nombre": "Juan Pérez", 
                        "Correo": "juan@example.com",
                        "Teléfono": "+1234567890"
                    },
                    {
                        "ID": 2,
                        "Nombre": "María García",
                        "Correo": "maria@example.com", 
                        "Teléfono": "+0987654321"
                    }
                ],
                "field_config": [
                    {"path": "id", "display_name": "ID", "type": "number"},
                    {"path": "client.name", "display_name": "Nombre", "type": "text"},
                    {"path": "client.email", "display_name": "Correo", "type": "email"},
                    {"path": "client.phone", "display_name": "Teléfono", "type": "phone"}
                ]
            }
        }
        
        return sample_preview
        
    except Exception as e:
        logger.error(f"Error en preview: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando preview: {str(e)}")

@router.post("/auto-discovery")
async def auto_discovery_fields(
    discovery_data: Dict[str, Any],
    current_user: User = Depends(require_admin)
):
    """Auto-discovery mejorado de campos API"""
    
    try:
        business_id = discovery_data.get("business_id")
        api_id = discovery_data.get("api_id")
        
        if not business_id or not api_id:
            raise HTTPException(status_code=400, detail="business_id y api_id son requeridos")
        
        # Simulación mejorada para desarrollo
        discovery_result = {
            "success": True,
            "detected_fields": [
                "id", "client.name", "client.lastname", "client.email", 
                "client.phone", "client.address.street", "client.address.city",
                "orders", "orders.id", "orders.total", "orders.date", "created_at"
            ],
            "nested_structure": [
                {
                    "path": "id",
                    "type": "number",
                    "sample_value": 1,
                    "is_array": False
                },
                {
                    "path": "client",
                    "type": "json", 
                    "sample_value": "{object with 5 keys}",
                    "is_array": False,
                    "nested_fields": [
                        {"path": "client.name", "type": "text", "sample_value": "Juan"},
                        {"path": "client.lastname", "type": "text", "sample_value": "Pérez"},
                        {"path": "client.email", "type": "email", "sample_value": "juan@example.com"},
                        {"path": "client.phone", "type": "phone", "sample_value": "+1234567890"}
                    ]
                }
            ],
            "suggested_mappings": [
                {"api_path": "id", "display_name": "ID", "field_type": "number"},
                {"api_path": "client.name", "display_name": "Nombre", "field_type": "text"},
                {"api_path": "client.lastname", "display_name": "Apellido", "field_type": "text"},
                {"api_path": "client.email", "display_name": "Correo", "field_type": "email"},
                {"api_path": "client.phone", "display_name": "Teléfono", "field_type": "phone"}
            ],
            "sample_data": [
                {
                    "id": 1,
                    "client": {
                        "name": "Juan", 
                        "lastname": "Pérez",
                        "email": "juan@example.com",
                        "phone": "+1234567890"
                    }
                }
            ]
        }
        
        logger.info(f"🔍 Auto-discovery mejorado: {api_id}")
        
        return {
            "success": True,
            "data": discovery_result,
            "message": "Auto-discovery exitoso con análisis de estructura"
        }
        
    except Exception as e:
        logger.error(f"Error en auto-discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Error en auto-discovery: {str(e)}")

logger.info("🧪 Router API Testing mejorado configurado")
