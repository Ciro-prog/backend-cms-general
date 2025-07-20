from pydantic import BaseModel
from typing import List, Any, Optional, Generic, TypeVar

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """Respuesta base para APIs"""
    success: bool = True
    message: str = "OK"
    data: Optional[T] = None

class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada"""
    items: List[T]
    total: int
    page: int = 1
    per_page: int = 10
    pages: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    """Respuesta de error"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None