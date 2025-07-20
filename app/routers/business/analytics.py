from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
from datetime import datetime

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}/stats", response_model=BaseResponse[Dict[str, Any]])
async def get_business_stats(
    business_id: str,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_business_user)
):
    """Obtener estadísticas del business"""
    # Verificar permisos
    if not current_user.business_id == business_id and current_user.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Acceso denegado")
    
    # TODO: Implementar AnalyticsService
    stats = {
        "business_id": business_id,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "metrics": {}
    }
    
    return BaseResponse(data=stats)

# ================================
# app/routers/integrations/__init__.py
# ================================

from fastapi import APIRouter
from . import waha, n8n, webhooks

router = APIRouter()

router.include_router(waha.router, prefix="/waha", tags=["waha"])
router.include_router(n8n.router, prefix="/n8n", tags=["n8n"])
router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
