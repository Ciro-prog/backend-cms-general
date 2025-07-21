from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse
from ...services.dashboard_service import DashboardService
from ...core.component_renderer import ComponentRenderer

router = APIRouter()

@router.get("/{business_id}")
async def get_dashboard_data(
    business_id: str,
    vista: str = Query("dashboard_principal", description="Nombre de la vista"),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos completos del dashboard"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        dashboard_service = DashboardService()
        dashboard_data = await dashboard_service.get_dashboard_data(
            business_id=business_id,
            vista=vista,
            user=current_user
        )
        
        return BaseResponse(data=dashboard_data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{business_id}/component/{component_id}")
async def get_component_data(
    business_id: str,
    component_id: str,
    context: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener datos de un componente específico"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        # TODO: Implementar obtención de configuración de componente específico
        # Por ahora retornamos datos mock
        component_data = {
            "component_id": component_id,
            "data": {},
            "timestamp": "2025-01-19T10:30:00Z"
        }
        
        return BaseResponse(data=component_data)
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{business_id}/refresh")
async def refresh_dashboard_cache(
    business_id: str,
    vista: str = Query("dashboard_principal"),
    current_user: User = Depends(get_current_business_user)
):
    """Refrescar cache del dashboard"""
    
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    try:
        # TODO: Implementar limpieza de cache específica
        from ...services.cache_service import CacheService
        
        cache_service = CacheService()
        pattern = f"dashboard_{business_id}_{vista}_*"
        cleared_keys = await cache_service.clear_pattern(pattern)
        
        return BaseResponse(
            data={"cleared_keys": cleared_keys},
            message="Cache del dashboard refrescado"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))