from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}/sessions", response_model=BaseResponse[Dict[str, Any]])
async def get_whatsapp_sessions(
    business_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener sesiones de WhatsApp"""
    # TODO: Implementar WAHAService
    return BaseResponse(data={"sessions": []})

@router.post("/{business_id}/send-message", response_model=BaseResponse[Dict[str, Any]])
async def send_whatsapp_message(
    business_id: str,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_business_user)
):
    """Enviar mensaje de WhatsApp"""
    # TODO: Implementar
    return BaseResponse(data={"sent": True})
