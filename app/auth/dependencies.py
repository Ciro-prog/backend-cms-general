# ================================
# app/auth/dependencies.py - Auth Dependencies
# ================================

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

# ================================
# CONFIGURACIÓN DE SEGURIDAD
# ================================

security = HTTPBearer(auto_error=False)

# Usuarios hardcodeados para desarrollo
DEMO_USERS = {
    "superadmin": {
        "password": "superadmin", 
        "role": "super_admin",
        "business_id": None,
        "name": "Super Administrador",
        "email": "superadmin@cms.com"
    },
    "admin": {
        "password": "admin",
        "role": "admin", 
        "business_id": "isp_telconorte",
        "name": "Administrador ISP",
        "email": "admin@telconorte.com"
    },
    "tecnico": {
        "password": "tecnico",
        "role": "tecnico",
        "business_id": "isp_telconorte", 
        "name": "Técnico ISP",
        "email": "tecnico@telconorte.com"
    },
    "usuario": {
        "password": "usuario",
        "role": "user",
        "business_id": "isp_telconorte",
        "name": "Usuario Final",
        "email": "usuario@telconorte.com"
    }
}

# ================================
# FUNCIONES DE AUTENTICACIÓN
# ================================

def verify_demo_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """Verificar usuario demo"""
    user = DEMO_USERS.get(username)
    if user and user["password"] == password:
        return {
            "username": username,
            "role": user["role"],
            "business_id": user["business_id"],
            "name": user["name"],
            "email": user["email"]
        }
    return None

async def get_current_user_from_session(request: Request) -> Optional[Dict[str, Any]]:
    """Obtener usuario actual desde la sesión"""
    try:
        if hasattr(request, 'session') and 'user' in request.session:
            return request.session['user']
    except Exception as e:
        logger.error(f"Error obteniendo usuario de sesión: {e}")
    return None

async def get_current_user_from_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[Dict[str, Any]]:
    """Obtener usuario actual desde token (para APIs)"""
    if not credentials:
        return None
    
    # TODO: Implementar verificación de JWT token con Clerk
    # Por ahora, retornar usuario demo para testing
    return {
        "username": "api_user",
        "role": "admin",
        "business_id": "isp_telconorte",
        "name": "API User",
        "email": "api@test.com"
    }

# ================================
# DEPENDENCIAS DE AUTORIZACIÓN
# ================================

async def require_auth(request: Request) -> Dict[str, Any]:
    """Requerir autenticación (para frontend)"""
    user = await get_current_user_from_session(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticación requerida"
        )
    return user

async def require_api_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Requerir autenticación (para API)"""
    user = await get_current_user_from_token(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

async def require_super_admin(request: Request) -> Dict[str, Any]:
    """Requerir rol super_admin"""
    user = await require_auth(request)
    if user["role"] != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol super_admin"
        )
    return user

async def require_admin(request: Request) -> Dict[str, Any]:
    """Requerir rol admin o superior"""
    user = await require_auth(request)
    if user["role"] not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol admin o superior"
        )
    return user

async def require_admin_api(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Requerir rol admin o superior (para API)"""
    user = await require_api_auth(credentials)
    if user["role"] not in ["super_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: Se requiere rol admin o superior"
        )
    return user

async def get_current_business_user(request: Request, business_id: Optional[str] = None) -> Dict[str, Any]:
    """Obtener usuario verificando acceso al business"""
    user = await require_auth(request)
    
    # Super admin puede acceder a cualquier business
    if user["role"] == "super_admin":
        return user
    
    # Verificar que el usuario pertenece al business solicitado
    if business_id and user["business_id"] != business_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: No perteneces a este business"
        )
    
    return user

# ================================
# UTILIDADES DE PERMISOS
# ================================

def check_business_access(user: Dict[str, Any], business_id: str) -> bool:
    """Verificar si el usuario tiene acceso al business"""
    if user["role"] == "super_admin":
        return True
    return user["business_id"] == business_id

def check_role_permission(user: Dict[str, Any], required_roles: list) -> bool:
    """Verificar si el usuario tiene uno de los roles requeridos"""
    return user["role"] in required_roles

def get_user_permissions(user: Dict[str, Any]) -> Dict[str, bool]:
    """Obtener permisos del usuario"""
    role = user["role"]
    
    permissions = {
        "can_create_business_types": role == "super_admin",
        "can_manage_businesses": role in ["super_admin", "admin"],
        "can_configure_apis": role in ["super_admin", "admin"],
        "can_manage_users": role in ["super_admin", "admin"],
        "can_view_analytics": role in ["super_admin", "admin"],
        "can_edit_entities": role in ["super_admin", "admin"],
        "can_use_dashboard": True,  # Todos pueden usar dashboard
        "can_respond_whatsapp": role in ["super_admin", "admin", "tecnico"]
    }
    
    return permissions

# ================================
# MIDDLEWARE DE AUTENTICACIÓN
# ================================

async def auth_middleware(request: Request, call_next):
    """Middleware de autenticación para rutas protegidas"""
    path = request.url.path
    
    # Rutas públicas (no requieren autenticación)
    public_paths = ["/", "/login", "/health", "/docs", "/openapi.json", "/static"]
    
    if any(path.startswith(public_path) for public_path in public_paths):
        return await call_next(request)
    
    # Verificar autenticación para rutas protegidas
    try:
        user = await get_current_user_from_session(request)
        if not user:
            # Redirigir a login si no está autenticado
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login")
        
        # Agregar usuario al request para uso posterior
        request.state.user = user
        
    except Exception as e:
        logger.error(f"Error en middleware de auth: {e}")
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    
    return await call_next(request)