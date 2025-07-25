# ================================
# app/models/business.py - ARREGLADO PARA PYDANTIC V2
# ================================

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from ._common import PyObjectId

# Configuracion estandar para Pydantic v2
STANDARD_CONFIG = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_encoders={ObjectId: str},
    str_strip_whitespace=True,
    validate_assignment=True
)

# ================================
# COMPONENTES BASE
# ================================

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

# ================================
# CONFIGURACION DE BUSINESS
# ================================

class BrandingConfig(BaseModel):
    """Configuracion de branding"""
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
    permisos: Any  # Puede ser "*" o lista de permisos especificos

class ConfiguracionBusiness(BaseModel):
    """Configuracion completa del business"""
    branding: BrandingConfig = Field(default_factory=BrandingConfig)
    componentes_activos: List[str] = []
    roles_personalizados: List[RolPersonalizado] = []

class Suscripcion(BaseModel):
    """Informacion de suscripcion"""
    plan: str = "basic"
    activa: bool = True
    vence: Optional[datetime] = None

# ================================
# BUSINESS TYPES
# ================================

class BusinessType(BaseModel):
    """Template de tipo de negocio"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    tipo: str = Field(..., description="Identificador unico del tipo")
    nombre: str = Field(..., description="Nombre descriptivo del tipo")
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []
    componentes_opcionales: List[ComponenteOpcional] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = STANDARD_CONFIG

class BusinessTypeCreate(BaseModel):
    """Modelo para crear un business type"""
    tipo: str
    nombre: str
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []
    componentes_opcionales: List[ComponenteOpcional] = []

class BusinessTypeUpdate(BaseModel):
    """Modelo para actualizar business type - AGREGADO"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    componentes_base: Optional[List[ComponenteBase]] = None
    componentes_opcionales: Optional[List[ComponenteOpcional]] = None

# ================================
# BUSINESS INSTANCES
# ================================

class BusinessInstance(BaseModel):
    """Instancia de negocio/cliente"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str = Field(..., description="Identificador unico del business")
    nombre: str = Field(..., description="Nombre del negocio")
    tipo_base: str = Field(..., description="Tipo base desde business_types")
    configuracion: ConfiguracionBusiness = Field(default_factory=ConfiguracionBusiness)
    suscripcion: Suscripcion = Field(default_factory=Suscripcion)
    activo: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = STANDARD_CONFIG

class BusinessInstanceCreate(BaseModel):
    """Modelo para crear una instancia de business"""
    business_id: str
    nombre: str
    tipo_base: str
    configuracion: Optional[ConfiguracionBusiness] = None

class BusinessInstanceUpdate(BaseModel):
    """Modelo para actualizar business instance - AGREGADO"""
    nombre: Optional[str] = None
    tipo_base: Optional[str] = None
    configuracion: Optional[ConfiguracionBusiness] = None
    suscripcion: Optional[Suscripcion] = None
    activo: Optional[bool] = None
