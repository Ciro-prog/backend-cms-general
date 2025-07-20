from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}", response_model=BaseResponse[Dict[str, Any]])
async def get_dashboard_data(
    business_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos del dashboard"""
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # TODO: Implementar DashboardService
    dashboard_data = {
        "business_id": business_id,
        "stats": {},
        "charts": {},
        "notifications": []
    }
    
    return BaseResponse(data=dashboard_data)