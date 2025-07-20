from fastapi import APIRouter, Depends
from typing import Dict, Any

from ...auth.dependencies import get_current_business_user
from ...models.user import User
from ...models.responses import BaseResponse

router = APIRouter()

@router.get("/{business_id}/workflows", response_model=BaseResponse[Dict[str, Any]])
async def get_workflows(
    business_id: str,
    current_user: User = Depends(get_current_business_user)
):
    """Obtener workflows de N8N"""
    # TODO: Implementar N8NService
    return BaseResponse(data={"workflows": []})
