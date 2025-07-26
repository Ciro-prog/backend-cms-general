# ================================
# app/models/business.py - ARREGLADO PARA PYDANTIC V2
# ================================

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 - FIXED"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        try:
            from pydantic_core import core_schema
            return core_schema.with_info_plain_validator_function(
                cls._validate,
                serialization=core_schema.to_string_ser_schema()
            )
        except ImportError:
            from pydantic_core import core_schema
            return core_schema.str_schema()

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, model_type=None):
        field_schema.update(
            type="string",
            format="objectid", 
            examples=["507f1f77bcf86cd799439011"],
            pattern="^[0-9a-fA-F]{24}$"
        )
        return field_schema
    
    @classmethod
    def _validate(cls, v, info=None):
        if v is None:
            return None
        if isinstance(v, ObjectId):
            return cls(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return cls(v)
            raise ValueError(f"Invalid ObjectId: {v}")
        raise ValueError(f"ObjectId expected, got {type(v)}")
    
    def __str__(self):
        return str(super())
    
    def __repr__(self):
        return f"PyObjectId('{self}')"


# Configuración estándar para Pydantic v2
STANDARD_CONFIG = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_encoders={ObjectId: str},
    str_strip_whitespace=True,
    validate_assignment=True
)

class ComponenteBase(BaseModel):
    """Componente base para templates"""
    id: str
    nombre: str
    tipo: str  # "integration", "entity", "view"
    obligatorio: bool = False
    configuracion_default: Optional[Dict[str, Any]] = {}

class ComponenteOpcional(BaseModel):
    """Componente opcional para templates"""
    id: str
    nombre: str
    tipo: str
    descripcion: Optional[str] = None

class BusinessType(BaseModel):
    """Template de tipo de negocio"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tipo: str = Field(..., description="Identificador único del tipo")
    nombre: str = Field(..., description="Nombre descriptivo del tipo")
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []
    componentes_opcionales: List[ComponenteOpcional] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = STANDARD_CONFIG  # ← PYDANTIC V2 ✅

class BusinessTypeCreate(BaseModel):
    """Modelo para crear un business type"""
    tipo: str
    nombre: str
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []
    componentes_opcionales: List[ComponenteOpcional] = []

class BrandingConfig(BaseModel):
    """Configuración de branding"""
    logo_url: Optional[str] = None
    colores: Dict[str, Any] = {
        "primary": "#1e40af",
        "secondary": "#059669",
        "background": "#f8fafc",
        "text": "#0f172a",
        "graficos": ["#3b82f6", "#10b981", "#f59e0b"]
    }

class RolPersonalizado(BaseModel):
    """Rol personalizado del business"""
    rol: str
    nombre: str
    permisos: Any  # Puede ser "*" o lista de permisos específicos

class ConfiguracionBusiness(BaseModel):
    """Configuración completa del business"""
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    componentes_activos: List[str] = []
    roles_personalizados: List[RolPersonalizado] = []

class Suscripcion(BaseModel):
    """Información de suscripción"""
    plan: str = "basic"
    activa: bool = True
    vence: Optional[datetime] = None

class BusinessInstance(BaseModel):
    """Instancia de negocio/cliente"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str = Field(..., description="Identificador único del business")
    nombre: str = Field(..., description="Nombre del negocio")
    tipo_base: str = Field(..., description="Tipo base desde business_types")
    configuracion: ConfiguracionBusiness = Field(default_factory=ConfiguracionBusiness)
    suscripcion: Suscripcion = Field(default_factory=Suscripcion)
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = STANDARD_CONFIG  # ← PYDANTIC V2 ✅

class BusinessInstanceCreate(BaseModel):
    """Modelo para crear una instancia de business"""
    business_id: str
    nombre: str
    tipo_base: str
    configuracion: Optional[ConfiguracionBusiness] = None