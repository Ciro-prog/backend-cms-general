from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from bson import ObjectId
from ._common import PyObjectId

class CampoConfig(BaseModel):
    """Configuración de un campo de entidad"""
    campo: str
    tipo: str  # "text", "number", "select", "date", "boolean", "phone", "email"
    obligatorio: bool = False
    visible_roles: List[str] = ["*"]
    editable_roles: List[str] = ["admin"]
    validacion: Optional[str] = None  # "min:10", "max:100", "email", etc.
    opciones: Optional[List[Dict[str, Any]]] = None  # Para selects estáticos
    opciones_api: Optional[str] = None  # "api_1:/endpoints" para selects dinámicos
    mapeo: Optional[Dict[str, str]] = None  # Para mapear respuesta API
    placeholder: Optional[str] = None
    descripcion: Optional[str] = None

class CacheConfig(BaseModel):
    """Configuración de cache para entidades"""
    tipo: str = "tiempo"  # "tiempo", "webhook", "manual"
    refresh_seconds: int = 300
    webhook_url: Optional[str] = None

class CrudOperation(BaseModel):
    """Configuración de operación CRUD"""
    habilitado: bool = True
    roles: List[str] = ["admin"]
    endpoint: Optional[str] = None
    campos_requeridos: Optional[List[str]] = None
    confirmacion: bool = False

class CrudConfig(BaseModel):
    """Configuración completa de CRUD"""
    crear: CrudOperation = Field(default_factory=CrudOperation)
    editar: CrudOperation = Field(default_factory=CrudOperation)
    eliminar: CrudOperation = Field(default_factory=CrudOperation)
    exportar: Optional[CrudOperation] = None

class ApiConfig(BaseModel):
    """Configuración de API externa para entidad"""
    fuente: str  # Referencia a api_configurations
    endpoint: str
    metodo: str = "GET"
    mapeo: Dict[str, str] = {}  # Mapeo campo_api -> campo_entidad
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    filtros_default: Optional[Dict[str, Any]] = None

class EntityConfig(BaseModel):
    """Configuración completa de una entidad"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    entidad: str
    configuracion: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str}

    
    )
class EntityConfigDetailed(BaseModel):
    """Configuración detallada de entidad con tipos específicos"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    entidad: str
    campos: List[CampoConfig] = []
    api_config: Optional[ApiConfig] = None
    crud_config: CrudConfig = Field(default_factory=CrudConfig)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name = True,
        arbitrary_types_allowed = True,
        json_encoders = {ObjectId: str}

    
    )
class EntityConfigCreate(BaseModel):
    """Modelo para crear configuración de entidad"""
    business_id: str
    entidad: str
    campos: List[CampoConfig] = []
    api_config: Optional[ApiConfig] = None
    crud_config: Optional[CrudConfig] = None

class EntityConfigUpdate(BaseModel):
    """Modelo para actualizar configuración de entidad"""
    campos: Optional[List[CampoConfig]] = None
    api_config: Optional[ApiConfig] = None
    crud_config: Optional[CrudConfig] = None

# ================================
# app/models/view.py
# ================================

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

class Posicion(BaseModel):
    """Posición de componente en grid"""
    x: int = 0
    y: int = 0
    w: int = 12  # ancho en columnas
    h: int = 4   # alto en filas

class ConfiguracionComponente(BaseModel):
    """Configuración específica de cada tipo de componente"""
    titulo: Optional[str] = None
    entidad: Optional[str] = None
    operacion: Optional[str] = None  # "count", "sum", "avg", "count_by_month"
    filtro: Optional[str] = None
    icono: Optional[str] = None
    color: Optional[str] = "primary"
    tipo_grafico: Optional[str] = None  # "line", "bar", "pie", "area"
    columnas_visibles: Optional[List[str]] = None
    ordenamiento: Optional[Dict[str, str]] = None
    paginacion: Optional[Dict[str, Any]] = None
    acciones: Optional[Dict[str, Dict[str, List[str]]]] = None
    filtros: Optional[List[Dict[str, Any]]] = None
