# ================================
# app/models/responses.py - Modelos de Respuesta
# ================================

from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, List, Dict, Any
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """Respuesta base para todas las APIs"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada"""
    success: bool = True
    message: Optional[str] = None
    data: List[T] = []
    pagination: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PaginationInfo(BaseModel):
    """Información de paginación"""
    page: int = 1
    per_page: int = 10
    total_items: int = 0
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ================================
# RESPUESTAS ESPECÍFICAS PARA APIs
# ================================

class ApiTestResponse(BaseModel):
    """Respuesta del test de conexión API"""
    success: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    sample_data: Optional[Dict[str, Any]] = None
    detected_fields: Optional[List[str]] = None

class ApiConfigurationResponse(BaseModel):
    """Respuesta para configuración de API"""
    api_id: str
    business_id: str
    name: str
    status: str  # "active", "inactive", "error"
    last_test: Optional[ApiTestResponse] = None
    created_at: datetime
    updated_at: datetime

class ComponentPreviewResponse(BaseModel):
    """Respuesta para preview de componente"""
    component_type: str  # "table", "cards", "chart"
    sample_data: List[Dict[str, Any]]
    field_mapping: Dict[str, str]
    display_config: Dict[str, Any]

# ================================
# HELPER FUNCTIONS
# ================================

def create_success_response(data: T, message: str = None) -> BaseResponse[T]:
    """Crear respuesta exitosa"""
    return BaseResponse(
        success=True,
        message=message,
        data=data
    )

def create_error_response(error: str, detail: str = None, error_code: str = None) -> ErrorResponse:
    """Crear respuesta de error"""
    return ErrorResponse(
        success=False,
        error=error,
        detail=detail,
        error_code=error_code
    )

def create_paginated_response(
    data: List[T], 
    page: int, 
    per_page: int, 
    total_items: int,
    message: str = None
) -> PaginatedResponse[T]:
    """Crear respuesta paginada"""
    total_pages = (total_items + per_page - 1) // per_page
    
    pagination_info = PaginationInfo(
        page=page,
        per_page=per_page,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        pagination=pagination_info.dict()
    )