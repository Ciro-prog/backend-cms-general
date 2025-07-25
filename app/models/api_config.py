# ================================
# app/models/api_config.py - Modelos API Configuration
# ================================

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Dict, Any, Optional, List, Literal
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic v2 - Fixed for Python 3.13"""
    
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        try:
            from pydantic_core import core_schema
            return core_schema.no_info_plain_validator_function(
                cls.validate,
                serialization=core_schema.to_string_ser_schema()
            )
        except (ImportError, AttributeError):
            # Fallback para versiones diferentes
            try:
                from pydantic_core import core_schema
                return core_schema.str_schema()
            except ImportError:
                # Fallback final - usar string simple
                return {"type": "string"}

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return ObjectId(v)
            raise ValueError(f"Invalid ObjectId: {v}")
        if v is None:
            return None
        raise ValueError(f"ObjectId expected, got {type(v)}")

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema, model_type=None):
        field_schema.update(
            type="string",
            format="objectid",
            examples=["507f1f77bcf86cd799439011"]
        )
        return field_schema
    
    def __str__(self):
        return str(super())
    
    def __repr__(self):
        return f"PyObjectId('{self}')"

# ================================
# MODELOS DE AUTENTICACIÓN
# ================================

class AuthConfig(BaseModel):
    """Configuración de autenticación"""
    type: Literal["none", "api_key_header", "api_key_query", "bearer", "basic", "oauth2", "custom"] = "none"
    
    # Para API Key
    api_key: Optional[str] = None
    header_name: Optional[str] = "X-API-Key"  # Si type = api_key_header
    query_param: Optional[str] = "api_key"    # Si type = api_key_query
    
    # Para Bearer Token
    access_token: Optional[str] = None
    
    # Para Basic Auth
    username: Optional[str] = None
    password: Optional[str] = None
    
    # Para OAuth2
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    refresh_token: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    
    # Para Custom Headers
    custom_headers: Optional[Dict[str, str]] = {}

# ================================
# MODELOS DE CACHE Y CONFIGURACIÓN
# ================================

class CacheConfig(BaseModel):
    """Configuración de cache"""
    enabled: bool = True
    ttl_seconds: int = 300  # 5 minutos default
    max_size_mb: int = 5    # 5MB max por API
    strategy: Literal["time", "manual", "api_driven"] = "time"

class RateLimitConfig(BaseModel):
    """Configuración de rate limiting"""
    enabled: bool = True
    requests_per_minute: int = 60
    burst_limit: int = 10

class FieldMapping(BaseModel):
    """Mapeo de campo de API a campo de entidad"""
    api_field: str
    entity_field: str
    display_name: str
    field_type: Literal["string", "number", "boolean", "date", "email", "url"] = "string"
    visible: bool = True
    searchable: bool = False
    sortable: bool = False

# ================================
# MODELO PRINCIPAL DE CONFIGURACIÓN API
# ================================

class ApiConfiguration(BaseModel):
    """Configuración completa de API externa"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    api_id: str = Field(..., description="ID único de la API")
    business_id: str = Field(..., description="ID del business")
    name: str = Field(..., description="Nombre descriptivo de la API")
    description: Optional[str] = None
    
    # === CONFIGURACIÓN DE REQUEST ===
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    base_url: str = Field(..., description="URL base de la API")
    endpoint: str = Field(..., description="Endpoint específico")
    timeout_seconds: int = 30
    
    # === AUTENTICACIÓN ===
    auth: AuthConfig = Field(default_factory=AuthConfig)
    
    # === HEADERS Y PARÁMETROS ===
    default_headers: Dict[str, str] = Field(default_factory=dict)
    default_query_params: Dict[str, str] = Field(default_factory=dict)
    request_body_template: Optional[Dict[str, Any]] = None
    
    # === PROCESAMIENTO DE DATOS ===
    response_path: Optional[str] = None  # JSONPath para extraer datos
    field_mappings: List[FieldMapping] = Field(default_factory=list)
    
    # === CONFIGURACIONES ADICIONALES ===
    cache_config: CacheConfig = Field(default_factory=CacheConfig)
    rate_limit_config: RateLimitConfig = Field(default_factory=RateLimitConfig)
    
    # === ESTADO Y METADATA ===
    active: bool = True
    last_test_at: Optional[datetime] = None
    last_test_success: Optional[bool] = None
    last_error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url debe comenzar con http:// o https://')
        return v
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        if not v.startswith('/'):
            return '/' + v
        return v

# ================================
# MODELOS PARA CREAR/ACTUALIZAR
# ================================

class ApiConfigurationCreate(BaseModel):
    """Modelo para crear configuración de API"""
    api_id: str
    business_id: str
    name: str
    description: Optional[str] = None
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = "GET"
    base_url: str
    endpoint: str
    auth: Optional[AuthConfig] = None
    default_headers: Optional[Dict[str, str]] = None
    default_query_params: Optional[Dict[str, str]] = None
    field_mappings: Optional[List[FieldMapping]] = None
    cache_config: Optional[CacheConfig] = None
    
    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('base_url debe comenzar con http:// o https://')
        return v
    
    @field_validator('endpoint')
    @classmethod
    def validate_endpoint(cls, v):
        if not v.startswith('/'):
            return '/' + v
        return v

class ApiConfigurationUpdate(BaseModel):
    """Modelo para actualizar configuración de API"""
    name: Optional[str] = None
    description: Optional[str] = None
    method: Optional[Literal["GET", "POST", "PUT", "DELETE", "PATCH"]] = None
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    auth: Optional[AuthConfig] = None
    default_headers: Optional[Dict[str, str]] = None
    default_query_params: Optional[Dict[str, str]] = None
    field_mappings: Optional[List[FieldMapping]] = None
    cache_config: Optional[CacheConfig] = None
    active: Optional[bool] = None

# ================================
# MODELOS PARA TESTING DE API
# ================================

class ApiTestRequest(BaseModel):
    """Request para probar API"""
    limit_records: int = Field(5, ge=1, le=50, description="Límite de registros para test")
    custom_params: Optional[Dict[str, str]] = None

class ApiTestResult(BaseModel):
    """Resultado del test de API"""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    sample_data: Optional[List[Dict[str, Any]]] = None
    detected_fields: Optional[List[str]] = None
    total_records: Optional[int] = None
    
    # Sugerencias automáticas
    suggested_mappings: Optional[List[FieldMapping]] = None
    recommended_cache_ttl: Optional[int] = None

# ================================
# VALIDADORES PARA PYDANTIC V2
# ================================

# Los validadores se definen dentro de cada clase usando @field_validator