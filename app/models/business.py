# ================================
# app/models/business.py (MODELOS COMPLETOS)
# ================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from enum import Enum  # ← DEBE ESTAR PRESENTE

class BusinessStatus(str, Enum):  # ← DEBE ESTAR DEFINIDO
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class BusinessTypeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"

class ComponentType(str, Enum):
    TABLE = "table"
    CARDS = "cards" 
    CHART = "chart"
    METRIC = "metric"
    LIST = "list"
    DASHBOARD = "dashboard"

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

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
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class BusinessTypeCreate(BaseModel):
    """Modelo para crear un business type"""
    tipo: str
    nombre: str
    descripcion: Optional[str] = None
    componentes_base: List[ComponenteBase] = []
    componentes_opcionales: List[ComponenteOpcional] = []
 

class BusinessTypeComponent(BaseModel):
    """Componente disponible en un Business Type"""
    component_id: str = Field(..., description="ID único del componente")
    name: str = Field(..., description="Nombre del componente")
    type: ComponentType = Field(..., description="Tipo de componente")
    description: Optional[str] = Field(None, description="Descripción del componente")
    is_required: bool = Field(False, description="Si es obligatorio")
    default_config: Dict[str, Any] = Field(default_factory=dict, description="Configuración por defecto")

class BusinessType(BaseModel):
    """Template de tipo de negocio"""
    business_type_id: str = Field(..., description="ID único del tipo de negocio")
    name: str = Field(..., description="Nombre del tipo de negocio")
    description: Optional[str] = Field(None, description="Descripción")
    status: BusinessTypeStatus = Field(BusinessTypeStatus.ACTIVE, description="Estado")
    
    # Componentes disponibles
    available_components: List[BusinessTypeComponent] = Field(default_factory=list)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None, description="Usuario creador")

class BusinessTypeCreate(BaseModel):
    """Crear Business Type"""
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    available_components: List[BusinessTypeComponent] = Field(default_factory=list)

class BusinessTypeUpdate(BaseModel):
    """Actualizar Business Type"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    status: Optional[BusinessTypeStatus] = None
    available_components: Optional[List[BusinessTypeComponent]] = None


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

class BusinessStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class BusinessInstance(BaseModel):
    """Instancia específica de un negocio"""
    business_id: str = Field(..., description="ID único del negocio")
    name: str = Field(..., description="Nombre del negocio")
    business_type_id: str = Field(..., description="ID del tipo de negocio")
    status: BusinessStatus = Field(BusinessStatus.ACTIVE)
    
    # Configuración específica
    branding: Dict[str, Any] = Field(default_factory=dict, description="Configuración de marca")
    active_components: List[str] = Field(default_factory=list, description="Componentes activos")
    custom_config: Dict[str, Any] = Field(default_factory=dict, description="Configuración personalizada")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(None)

class BusinessInstanceCreate(BaseModel):
    """Crear Business Instance"""
    name: str = Field(..., min_length=2, max_length=100)
    business_type_id: str = Field(..., description="ID del tipo de negocio")
    branding: Dict[str, Any] = Field(default_factory=dict)
    active_components: List[str] = Field(default_factory=list)

class BusinessInstanceUpdate(BaseModel):
    """Actualizar Business Instance"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    status: Optional[BusinessStatus] = None
    branding: Optional[Dict[str, Any]] = None
    active_components: Optional[List[str]] = None
    custom_config: Optional[Dict[str, Any]] = None

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
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class BusinessInstanceCreate(BaseModel):
    """Modelo para crear una instancia de business"""
    business_id: str
    nombre: str
    tipo_base: str
    configuracion: Optional[ConfiguracionBusiness] = None

    # ================================
# RESPONSES
# ================================

class BusinessTypeResponse(BaseModel):
    """Respuesta de Business Type"""
    success: bool = True
    data: Optional[BusinessType] = None
    message: str = "OK"

class BusinessTypeListResponse(BaseModel):
    """Respuesta lista de Business Types"""
    success: bool = True
    data: List[BusinessType] = Field(default_factory=list)
    total: int = 0
    message: str = "OK"

class BusinessInstanceResponse(BaseModel):
    """Respuesta de Business Instance"""
    success: bool = True
    data: Optional[BusinessInstance] = None
    message: str = "OK"

class BusinessInstanceListResponse(BaseModel):
    """Respuesta lista de Business Instances"""
    success: bool = True
    data: List[BusinessInstance] = Field(default_factory=list)
    total: int = 0
    message: str = "OK"

# ================================
# DATOS DE EJEMPLO PARA TESTING
# ================================

# Business Type por defecto: ISP
DEFAULT_ISP_BUSINESS_TYPE = BusinessTypeCreate(
    name="ISP Provider",
    description="Template para proveedores de servicios de internet",
    available_components=[
        BusinessTypeComponent(
            component_id="clientes_table",
            name="Tabla de Clientes",
            type=ComponentType.TABLE,
            description="Tabla con lista de clientes",
            is_required=True,
            default_config={
                "columns": ["nombre", "email", "estado", "plan"],
                "pagination": True,
                "search": True
            }
        ),
        BusinessTypeComponent(
            component_id="stats_dashboard",
            name="Dashboard de Estadísticas",
            type=ComponentType.DASHBOARD,
            description="Métricas generales del ISP",
            is_required=True,
            default_config={
                "metrics": ["total_clientes", "ingresos_mes", "nuevos_clientes"],
                "refresh_interval": 300
            }
        ),
        BusinessTypeComponent(
            component_id="revenue_chart",
            name="Gráfico de Ingresos",
            type=ComponentType.CHART,
            description="Gráfico de ingresos mensuales",
            is_required=False,
            default_config={
                "chart_type": "line",
                "period": "monthly"
            }
        )
    ]
)

# Business Instance por defecto: TelcoNorte
DEFAULT_TELCONORTE_BUSINESS = BusinessInstanceCreate(
    name="TelcoNorte ISP",
    business_type_id="isp_provider",
    branding={
        "logo_url": "/static/images/telconorte-logo.png",
        "primary_color": "#2563eb",
        "secondary_color": "#059669"
    },
    active_components=["clientes_table", "stats_dashboard", "revenue_chart"]
)