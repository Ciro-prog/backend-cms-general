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
# ================================
# AGREGAR ESTOS MODELOS AL FINAL DE app/models/api_config.py
# ================================

# ================================
# MODELOS PARA AUTO-DISCOVERY
# ================================

class AutoDiscoveryResult(BaseModel):
    """Resultado del auto-discovery de campos"""
    success: bool
    detected_fields: List[str] = Field(default_factory=list)
    suggested_mappings: List[FieldMapping] = Field(default_factory=list)
    sample_data: Optional[List[Dict[str, Any]]] = None
    data_analysis: Optional[Dict[str, Any]] = None
    confidence_scores: Optional[Dict[str, float]] = None
    error_message: Optional[str] = None

class FieldSuggestion(BaseModel):
    """Sugerencia de mapeo de campo"""
    api_field: str
    entity_field: str
    display_name: str
    field_type: str
    confidence: float = Field(ge=0, le=1, description="Confianza del mapeo (0-1)")
    reasoning: Optional[str] = None

# ================================
# MODELOS EXTENDIDOS DE TESTING
# ================================

class ApiTestResultExtended(ApiTestResult):
    """Resultado extendido de test de API"""
    mapped_data: Optional[List[Dict[str, Any]]] = None
    raw_response_preview: Optional[str] = None
    suggested_mappings: Optional[List[FieldSuggestion]] = None
    recommended_cache_ttl: Optional[int] = None
    data_quality_score: Optional[float] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class ApiValidationResult(BaseModel):
    """Resultado de validación de configuración API"""
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)
    score: Optional[int] = Field(None, ge=0, le=100, description="Puntaje de calidad (0-100)")

# ================================
# MODELOS PARA LOGS Y MONITOREO
# ================================

class ApiLogEntry(BaseModel):
    """Entrada de log de API"""
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    business_id: str
    api_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    test_type: Literal["manual", "auto", "scheduled", "health_check"] = "manual"
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    total_records: Optional[int] = None
    detected_fields: Optional[List[str]] = None
    user_id: Optional[str] = None
    
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class ApiStatistics(BaseModel):
    """Estadísticas de API"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time_ms: Optional[float] = None
    last_request_at: Optional[datetime] = None
    success_rate: Optional[float] = None
    most_common_errors: Optional[List[str]] = None

# ================================
# MODELOS PARA BULK OPERATIONS
# ================================

class ApiBulkImportRequest(BaseModel):
    """Request para importación masiva de APIs"""
    configs: List[ApiConfigurationCreate]
    overwrite_existing: bool = False
    validate_before_import: bool = True

class ApiBulkImportResult(BaseModel):
    """Resultado de importación masiva"""
    imported: int = 0
    failed: int = 0
    skipped: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    imported_apis: List[str] = Field(default_factory=list)

# ================================
# MODELOS PARA ENTITY INTEGRATION
# ================================

class EntityApiIntegration(BaseModel):
    """Integración de entidad con API"""
    entity_name: str
    business_id: str
    api_config_id: str
    field_mappings: List[FieldMapping]
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = 30
    last_sync_at: Optional[datetime] = None
    sync_errors: Optional[List[str]] = None

class EntityDataRequest(BaseModel):
    """Request para obtener datos de entidad"""
    limit: int = Field(25, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    refresh_cache: bool = False
    format: Literal["json", "table", "cards", "stats"] = "json"
    filters: Optional[Dict[str, Any]] = None
    sort_by: Optional[str] = None
    sort_order: Literal["asc", "desc"] = "asc"

class EntityDataResponse(BaseModel):
    """Respuesta de datos de entidad"""
    entity_name: str
    business_id: str
    items: List[Dict[str, Any]]
    total_records: int
    from_cache: bool
    last_updated: Optional[datetime] = None
    api_source: Optional[str] = None
    response_time_ms: Optional[float] = None

# ================================
# MODELOS PARA WEBHOOKS Y EVENTOS
# ================================

class WebhookConfig(BaseModel):
    """Configuración de webhook"""
    enabled: bool = False
    url: str
    events: List[Literal["test_success", "test_failure", "data_sync", "config_change"]]
    auth_header: Optional[str] = None
    retry_attempts: int = 3
    timeout_seconds: int = 30

class ApiEvent(BaseModel):
    """Evento de API"""
    event_type: str
    api_id: str
    business_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

# ================================
# UTILIDADES Y HELPERS
# ================================

class ApiHealthCheck(BaseModel):
    """Estado de salud de API"""
    api_id: str
    status: Literal["healthy", "degraded", "down", "unknown"] = "unknown"
    last_check_at: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    error_count_24h: int = 0
    uptime_percentage: Optional[float] = None
    next_check_at: Optional[datetime] = None

class SmartMappingSuggestion(BaseModel):
    """Sugerencia inteligente de mapeo"""
    api_field: str
    suggested_entity_field: str
    confidence: float
    reasoning: str
    field_type_detected: str
    examples: List[Any] = Field(default_factory=list)
    
# ================================
# FUNCIÓN HELPER PARA COMPATIBILIDAD
# ================================

def ensure_api_config_compatibility(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Asegurar compatibilidad de configuración de API"""
    
    # Migrar campos antiguos si existen
    if "auth_type" in config_dict and "auth" not in config_dict:
        auth_type = config_dict.pop("auth_type", "none")
        auth_config = config_dict.pop("auth_config", {})
        
        config_dict["auth"] = {
            "type": auth_type,
            **auth_config
        }
    
    # Asegurar field_mappings es lista
    if "field_mappings" in config_dict and not isinstance(config_dict["field_mappings"], list):
        config_dict["field_mappings"] = []
    
    # Agregar configuraciones por defecto
    if "cache_config" not in config_dict:
        config_dict["cache_config"] = {"enabled": True, "ttl_seconds": 300}
    
    if "rate_limit_config" not in config_dict:
        config_dict["rate_limit_config"] = {"enabled": True, "requests_per_minute": 60}
    
    return config_dict