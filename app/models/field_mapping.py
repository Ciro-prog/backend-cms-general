# ================================
# app/models/field_mapping.py  
# Nuevos modelos para mapping manual de campos anidados
# ================================

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from enum import Enum

class FieldType(str, Enum):
    """Tipos de campos soportados"""
    TEXT = "text"
    NUMBER = "number" 
    BOOLEAN = "boolean"
    DATE = "date"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    JSON = "json"
    ARRAY = "array"
    SELECT = "select"

class FieldValidation(BaseModel):
    """Validaciones para un campo"""
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None
    custom_validation: Optional[str] = None

class MappedField(BaseModel):
    """Campo mapeado con toda su configuración"""
    api_path: str = Field(..., description="Ruta del campo en API (ej: client.name)")
    display_name: str = Field(..., description="Nombre amigable para mostrar")
    field_type: FieldType = Field(default=FieldType.TEXT)
    validation: Optional[FieldValidation] = None
    visible_roles: List[str] = Field(default=["*"])
    editable_roles: List[str] = Field(default=["admin"])
    description: Optional[str] = None
    default_value: Optional[Any] = None
    
    # Para campos tipo select
    options: Optional[List[Dict[str, Any]]] = None
    options_api_path: Optional[str] = None
    
    # Configuración de visualización
    show_in_table: bool = True
    show_in_card: bool = True
    show_in_form: bool = True
    column_width: Optional[str] = None
    order: int = 0

class NestedFieldStructure(BaseModel):
    """Estructura de campo anidado detectada"""
    path: str = Field(..., description="Ruta completa del campo")
    type: str = Field(..., description="Tipo detectado")
    sample_value: Any = Field(default=None)
    is_array: bool = False
    nested_fields: Optional[List['NestedFieldStructure']] = None

class MappingConfiguration(BaseModel):
    """Configuración completa de mapping"""
    api_id: str
    mapping_type: str = Field(default="manual", description="manual | automatic")
    mapped_fields: List[MappedField] = Field(default=[])
    auto_detected_structure: Optional[List[NestedFieldStructure]] = None
    
    # Configuración de visualización
    default_view: str = Field(default="table", description="table | cards | chart")
    items_per_page: int = Field(default=20)
    enable_search: bool = True
    enable_filters: bool = True
    refresh_interval: Optional[int] = None  # segundos
    
    # Configuración de exports
    enable_export: bool = True
    export_formats: List[str] = Field(default=["json", "csv"])

# Fix para referencias circulares
NestedFieldStructure.model_rebuild()
