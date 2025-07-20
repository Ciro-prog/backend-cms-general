from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging

from ..auth.dependencies import get_current_user, get_current_business_user
from ..models.user import User, UserCreate, UserUpdate
from ..models.responses import BaseResponse
from ..services.user_service import UserService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/me", response_model=BaseResponse[User])
async def get_current_user_info(
    current_user: User = Depends(get_current_business_user)
):
    """Obtener información del usuario actual"""
    return BaseResponse(data=current_user)

@router.put("/me", response_model=BaseResponse[User])
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_business_user)
):
    """Actualizar información del usuario actual"""
    user_service = UserService()
    updated_user = await user_service.update_user(
        str(current_user.id), 
        user_update
    )
    return BaseResponse(data=updated_user)

@router.post("/webhook")
async def clerk_webhook(request: Request):
    """Webhook de Clerk para sincronizar usuarios"""
    try:
        payload = await request.json()
        event_type = payload.get("type")
        
        user_service = UserService()
        
        if event_type == "user.created":
            await user_service.handle_user_created(payload["data"])
        elif event_type == "user.updated":
            await user_service.handle_user_updated(payload["data"])
        elif event_type == "user.deleted":
            await user_service.handle_user_deleted(payload["data"])
        
        return JSONResponse({"success": True})
        
    except Exception as e:
        logger.error(f"Error procesando webhook de Clerk: {e}")
        raise HTTPException(status_code=400, detail="Error procesando webhook")