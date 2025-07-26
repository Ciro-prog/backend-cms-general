"""
Módulo común para tipos de datos compartidos entre modelos
Compatible con Pydantic v2 y Python 3.13+
"""

from bson import ObjectId
from typing import Any, Dict

class PyObjectId(ObjectId):
    """
    Custom ObjectId type para Pydantic v2
    Compatible con Python 3.13+ y Pydantic v2.5+
    """
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Dict[str, Any]:
        """Schema para Pydantic v2"""
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_plain_validator_function(
                cls._validate,
                serialization=core_schema.to_string_ser_schema()
            )
        except (ImportError, AttributeError):
            # Fallback para diferentes versiones
            try:
                from pydantic_core import core_schema
                return core_schema.with_info_plain_validator_function(
                    cls._validate_with_info,
                    serialization=core_schema.to_string_ser_schema()
                )
            except ImportError:
                # Fallback final
                return {"type": "string", "format": "objectid"}

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema: Dict[str, Any], model_type: Any = None) -> Dict[str, Any]:
        """JSON Schema para documentación API"""
        field_schema.update(
            type="string",
            format="objectid",
            examples=["507f1f77bcf86cd799439011"],
            pattern="^[0-9a-fA-F]{24}$",
            description="MongoDB ObjectId as string"
        )
        return field_schema
    
    @classmethod
    def _validate(cls, v: Any) -> "PyObjectId":
        """Validador sin info para Pydantic v2"""
        if v is None:
            return None
        if isinstance(v, ObjectId):
            return cls(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return cls(v)
            raise ValueError(f"Invalid ObjectId string: {v}")
        raise ValueError(f"ObjectId expected, got {type(v).__name__}: {v}")
    
    @classmethod 
    def _validate_with_info(cls, v: Any, info: Any = None) -> "PyObjectId":
        """Validador con info para fallback"""
        return cls._validate(v)
    
    def __str__(self) -> str:
        return str(super())
    
    def __repr__(self) -> str:
        return f"PyObjectId('{self}')"

    @classmethod
    def is_valid(cls, oid: Any) -> bool:
        """Verificar si un valor es un ObjectId válido"""
        return ObjectId.is_valid(oid)
