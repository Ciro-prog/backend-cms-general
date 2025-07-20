from fastapi import Depends, Request, HTTPException
from typing import Optional
from ..models.user import User
from ..database import get_database

async def get_current_user(request: Request) -> dict:
    """Obtener usuario actual desde el middleware"""
    if not hasattr(request.state, 'user'):
        raise HTTPException(status_code=401, detail="Usuario no autenticado")
    return request.state.user

async def get_current_business_user(
    request: Request,
    current_user: dict = Depends(get_current_user)
) -> User:
    """Obtener usuario con información del business"""
    db = get_database()
    
    user_doc = await db.users.find_one({
        "clerk_user_id": current_user["user_id"]
    })
    
    if not user_doc:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    return User(**user_doc)

async def require_super_admin(
    current_user: User = Depends(get_current_business_user)
):
    """Verificar que el usuario sea super admin"""
    if current_user.rol != "super_admin":
        raise HTTPException(
            status_code=403, 
            detail="Se requieren permisos de super administrador"
        )
    return current_user

async def require_admin(
    current_user: User = Depends(get_current_business_user)
):
    """Verificar que el usuario sea admin o super admin"""
    if current_user.rol not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403, 
            detail="Se requieren permisos de administrador"
        )
    return current_user
