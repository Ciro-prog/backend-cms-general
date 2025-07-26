# ================================
# app/models/view.py - MODELOS DE VISTA
# ================================

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId
from ._common import PyObjectId

# Configuración estándar para Pydantic v2
VIEW_CONFIG = ConfigDict(
    populate_by_name=True,
    arbitrary_types_allowed=True,
    json_encoders={ObjectId: str},
    str_strip_whitespace=True,
    validate_assignment=True
)

# ================================
# COMPONENTES DE VISTA
# ================================

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

class ComponenteVista(BaseModel):
    """Componente individual de una vista"""
    id: str
    tipo: str  # "stats_card", "chart", "data_table", "form", "custom"
    posicion: Posicion = Field(default_factory=Posicion)
    configuracion: ConfiguracionComponente = Field(default_factory=ConfiguracionComponente)
    permisos_rol: List[str] = ["*"]

class LayoutConfig(BaseModel):
    """Configuración del layout de la vista"""
    tipo: str = "grid"  # "grid", "flex", "absolute"
    columnas: int = 12
    gap: int = 4
    responsive: bool = True

class ItemNavegacion(BaseModel):
    """Item de navegación"""
    titulo: str
    ruta: str
    icono: Optional[str] = None
    permisos_rol: List[str] = ["*"]

class ConfiguracionVista(BaseModel):
    """Configuración completa de la vista"""
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    componentes: List[ComponenteVista] = []
    navegacion: List[ItemNavegacion] = []

# ================================
# MODELOS PRINCIPALES
# ================================

class ViewConfig(BaseModel):
    """Configuración de vista"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    vista: str
    configuracion: ConfiguracionVista = Field(default_factory=ConfiguracionVista)
    permisos_vista: List[str] = ["*"]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = VIEW_CONFIG

class ViewConfigCreate(BaseModel):
    """Modelo para crear configuración de vista"""
    business_id: str
    vista: str
    configuracion: ConfiguracionVista
    permisos_vista: List[str] = ["*"]

class ViewConfigUpdate(BaseModel):
    """Modelo para actualizar configuración de vista"""
    configuracion: Optional[ConfiguracionVista] = None
    permisos_vista: Optional[List[str]] = None
