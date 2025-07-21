# ================================
# app/services/n8n_service.py (ACTUALIZADO con API Key)
# ================================

import httpx
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import settings

logger = logging.getLogger(__name__)

class N8NService:
    """Servicio para integración con N8N"""
    
    def __init__(self):
        self.base_url = settings.default_n8n_url.rstrip('/')
        self.api_key = settings.default_n8n_api_key
        self.headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            self.headers["Authorization"] = f"Bearer {self.api_key}"
    
    async def get_workflows(self, business_id: str) -> List[Dict[str, Any]]:
        """Obtener workflows de N8N para un business"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/workflows",
                    headers=self.headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    workflows = response.json().get("data", [])
                    
                    # Filtrar workflows por tags del business (si los hay)
                    filtered_workflows = []
                    for workflow in workflows:
                        tags = workflow.get("tags", [])
                        # Si el workflow tiene el tag del business o es general
                        if business_id in tags or "general" in tags or not tags:
                            filtered_workflows.append({
                                "id": workflow.get("id"),
                                "name": workflow.get("name"),
                                "active": workflow.get("active", False),
                                "tags": tags,
                                "created_at": workflow.get("createdAt"),
                                "updated_at": workflow.get("updatedAt")
                            })
                    
                    return filtered_workflows
                else:
                    logger.error(f"Error obteniendo workflows N8N: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error conectando con N8N: {e}")
            return []
    
    async def trigger_workflow(
        self, 
        workflow_id: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecutar workflow de N8N"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows/{workflow_id}/execute",
                    headers=self.headers,
                    json=data,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Workflow N8N ejecutado: {workflow_id}")
                    return {
                        "success": True,
                        "execution_id": result.get("data", {}).get("executionId"),
                        "status": "running"
                    }
                else:
                    logger.error(f"Error ejecutando workflow N8N: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error ejecutando workflow N8N: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_workflow_executions(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Obtener ejecuciones de un workflow"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/executions",
                    headers=self.headers,
                    params={"workflowId": workflow_id, "limit": 10},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    executions = response.json().get("data", [])
                    return [
                        {
                            "id": exec.get("id"),
                            "status": exec.get("finished") and "success" or "running",
                            "started_at": exec.get("startedAt"),
                            "finished_at": exec.get("stoppedAt"),
                            "workflow_id": exec.get("workflowId")
                        }
                        for exec in executions
                    ]
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Error obteniendo ejecuciones N8N: {e}")
            return []
    
    async def create_webhook_workflow(
        self,
        business_id: str,
        workflow_name: str,
        webhook_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crear workflow con webhook para un business"""
        try:
            # Estructura básica de workflow con webhook
            workflow_data = {
                "name": workflow_name,
                "tags": [business_id, "webhook"],
                "nodes": [
                    {
                        "name": "Webhook",
                        "type": "n8n-nodes-base.webhook",
                        "typeVersion": 1,
                        "position": [250, 300],
                        "webhookId": f"{business_id}_{workflow_name.lower().replace(' ', '_')}",
                        "parameters": {
                            "httpMethod": "POST",
                            "path": f"/{business_id}/{workflow_name.lower().replace(' ', '_')}",
                            "responseMode": "onReceived"
                        }
                    }
                ],
                "connections": {},
                "active": True
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/v1/workflows",
                    headers=self.headers,
                    json=workflow_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Workflow creado: {workflow_name} para {business_id}")
                    return {
                        "success": True,
                        "workflow_id": result.get("data", {}).get("id"),
                        "webhook_url": f"{self.base_url}/webhook/{business_id}_{workflow_name.lower().replace(' ', '_')}"
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Error creando workflow N8N: {e}")
            return {"success": False, "error": str(e)}