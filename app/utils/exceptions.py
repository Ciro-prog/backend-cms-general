from fastapi import HTTPException

class CMSException(Exception):
    """Excepción base del CMS"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code
        super().__init__(self.message)

class BusinessNotFoundError(CMSException):
    """Error cuando no se encuentra un business"""
    def __init__(self, business_id: str):
        super().__init__(f"Business no encontrado: {business_id}", "BUSINESS_NOT_FOUND")

class EntityNotFoundError(CMSException):
    """Error cuando no se encuentra una entidad"""
    def __init__(self, entity_name: str):
        super().__init__(f"Entidad no encontrada: {entity_name}", "ENTITY_NOT_FOUND")

class PermissionDeniedError(CMSException):
    """Error de permisos insuficientes"""
    def __init__(self, action: str):
        super().__init__(f"Permisos insuficientes para: {action}", "PERMISSION_DENIED")

class ValidationError(CMSException):
    """Error de validación"""
    def __init__(self, field: str, message: str):
        super().__init__(f"Error de validación en {field}: {message}", "VALIDATION_ERROR")
