# ================================
# ARCHIVO: app/models/common.py (NUEVO)
# RUTA: app/models/common.py  
# 🔧 CORREGIDO: PyObjectId compatible con Pydantic v2
# ================================

from bson import ObjectId
from pydantic import GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from typing import Any, Dict

class PyObjectId(ObjectId):
    """ObjectId compatible con Pydantic v2"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls, 
        source_type: Any, 
        handler
    ) -> core_schema.CoreSchema:
        """Schema para Pydantic v2"""
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ])
    
    @classmethod  
    def __get_pydantic_json_schema__(
        cls, 
        schema: core_schema.CoreSchema, 
        handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """JSON schema para Pydantic v2"""
        return {"type": "string", "format": "objectid"}
    
    @classmethod
    def validate(cls, v):
        """Validador para ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            try:
                return ObjectId(v)
            except Exception:
                raise ValueError("Invalid ObjectId")
        raise ValueError("Invalid ObjectId type")

    @classmethod
    def __modify_schema__(cls, field_schema: Dict[str, Any]) -> None:
        """Compatibilidad con Pydantic v1 (deprecated pero mantener)"""
        field_schema.update(type="string", format="objectid")

# ================================
# ARCHIVO: app/main.py (SECCIÓN DE RUTAS CORREGIDA)
# RUTA: app/main.py
# 🔧 CORREGIDO: Configuración de rutas principales
# ================================

# ... (resto del archivo igual hasta la configuración de rutas)

def setup_frontend():
    """Configurar el frontend después de que la app esté lista"""
    try:
        from .frontend.routers import frontend_router
        app.include_router(frontend_router, tags=["frontend"])
        logger.info("✅ Frontend configurado exitosamente")
    except Exception as e:
        logger.warning(f"⚠️ Frontend no disponible: {e}")

def setup_api_routers():
    """Configurar los routers de la API backend"""
    try:
        from .routers.admin import router as admin_router
        app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
        logger.info("✅ Router admin incluido")
    except Exception as e:
        logger.warning(f"⚠️ Router admin no disponible: {e}")

    try:
        from .routers.business import router as business_router
        app.include_router(business_router, prefix="/api/business", tags=["business"])
        logger.info("✅ Router business incluido")
    except Exception as e:
        logger.warning(f"⚠️ Router business no disponible: {e}")

    try:
        from .routers.auth import router as api_auth_router
        app.include_router(api_auth_router, prefix="/api/auth", tags=["auth"])
        logger.info("✅ Router auth incluido")
    except Exception as e:
        logger.warning(f"⚠️ Router auth no disponible: {e}")