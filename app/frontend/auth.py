# ================================
# app/frontend/auth.py - CORREGIDO
# ================================

from fastapi import Request, HTTPException
from typing import Optional
import hashlib

# Usuarios hardcodeados
USERS = {
    "superadmin": {
        "password": "superadmin",
        "role": "super_admin",
        "name": "Super Administrador",
        "business_id": None
    },
    "admin": {
        "password": "admin", 
        "role": "admin",
        "name": "Administrador",
        "business_id": "isp_telconorte"
    },
    "usuario": {
        "password": "usuario",
        "role": "user", 
        "name": "Usuario",
        "business_id": "isp_telconorte"
    }
}

def hash_password(password: str) -> str:
    """Hash simple de password (solo para demo)"""
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(password: str, username: str) -> bool:
    """Verificar password contra usuarios hardcodeados"""
    if username in USERS:
        return password == USERS[username]["password"]
    return False

def authenticate_user(username: str, password: str) -> Optional[dict]:
    """Autenticar usuario"""
    if verify_password(password, username):
        user_data = USERS[username].copy()
        user_data["username"] = username
        return user_data
    return None

def get_current_user(request: Request) -> Optional[dict]:
    """Obtener usuario actual de la sesión"""
    if hasattr(request, 'session') and "user" in request.session:
        username = request.session["user"]["username"]
        if username in USERS:
            user_data = USERS[username].copy()
            user_data["username"] = username
            return user_data
    return None

def require_auth(request: Request):
    """Dependency para requerir autenticación"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return user

def require_admin(request: Request):
    """Dependency para requerir permisos de admin"""
    user = require_auth(request)
    if user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin required")
    return user

def require_super_admin(request: Request):
    """Dependency para requerir permisos de super admin"""
    user = require_auth(request)
    if user["role"] != "super_admin":
        raise HTTPException(status_code=403, detail="Super admin required")
    return user

def login_user(request: Request, user: dict):
    """Iniciar sesión de usuario"""
    request.session["user"] = user

def logout_user(request: Request):
    """Cerrar sesión de usuario"""
    if hasattr(request, 'session'):
        request.session.clear()

def is_authenticated(request: Request) -> bool:
    """Verificar si el usuario está autenticado"""
    return get_current_user(request) is not None