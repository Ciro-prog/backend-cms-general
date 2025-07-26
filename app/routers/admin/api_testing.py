# ================================
# app/routers/admin/api_testing.py - BÁSICO
# ================================

from fastapi import APIRouter, Body, HTTPException
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["API Testing"])

@router.post("/api-test")
async def test_api_connection(test_request: Dict[str, Any] = Body(...)):
    """Probar conexión con API externa - versión básica"""
    
    try:
        required_fields = ["business_id", "api_id", "base_url", "endpoint"]
        missing_fields = [field for field in required_fields if not test_request.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Campos requeridos faltantes: {', '.join(missing_fields)}"
            )
        
        response_data = {
            "success": True,
            "status_code": 200,
            "response_time_ms": 150,
            "total_records": 3,
            "detected_fields": ["id", "name", "email"],
            "sample_data": [
                {"id": 1, "name": "Test User 1", "email": "test1@example.com"},
                {"id": 2, "name": "Test User 2", "email": "test2@example.com"},
                {"id": 3, "name": "Test User 3", "email": "test3@example.com"}
            ],
            "error_message": None
        }
        
        logger.info(f"✅ Test API simulado: {test_request['api_id']}")
        
        return {
            "success": True,
            "data": response_data,
            "message": "Test exitoso (simulado)"
        }
        
    except Exception as e:
        logger.error(f"Error en test de API: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno en test de API: {str(e)}")

@router.post("/api-discover")
async def auto_discover_api_fields(discover_request: Dict[str, Any] = Body(...)):
    """Auto-discovery de campos - versión básica"""
    
    try:
        business_id = discover_request.get("business_id")
        api_id = discover_request.get("api_id")
        
        if not business_id or not api_id:
            raise HTTPException(status_code=400, detail="business_id y api_id son requeridos")
        
        discovery_result = {
            "success": True,
            "detected_fields": ["id", "name", "email", "phone", "address"],
            "suggested_mappings": [
                {"api_field": "id", "entity_field": "usuario_id"},
                {"api_field": "name", "entity_field": "nombre_completo"},
                {"api_field": "email", "entity_field": "correo"},
                {"api_field": "phone", "entity_field": "telefono"}
            ],
            "sample_data": [{"id": 1, "name": "Test", "email": "test@example.com"}]
        }
        
        logger.info(f"🔍 Auto-discovery simulado: {api_id}")
        
        return {
            "success": True,
            "data": discovery_result,
            "message": "Auto-discovery exitoso (simulado)"
        }
        
    except Exception as e:
        logger.error(f"Error en auto-discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Error en auto-discovery: {str(e)}")

logger.info("🧪 Router API Testing básico configurado")
