from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/waha")
async def waha_webhook(request: Request):
    """Webhook para mensajes de WhatsApp desde WAHA"""
    try:
        payload = await request.json()
        # TODO: Procesar mensaje de WhatsApp
        logger.info(f"Webhook WAHA recibido: {payload}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error procesando webhook WAHA: {e}")
        return JSONResponse({"success": False}, status_code=400)

@router.post("/n8n")
async def n8n_webhook(request: Request):
    """Webhook para N8N"""
    try:
        payload = await request.json()
        # TODO: Procesar evento de N8N
        logger.info(f"Webhook N8N recibido: {payload}")
        return JSONResponse({"success": True})
    except Exception as e:
        logger.error(f"Error procesando webhook N8N: {e}")
        return JSONResponse({"success": False}, status_code=400)