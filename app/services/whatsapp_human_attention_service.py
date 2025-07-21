# ================================
# app/services/whatsapp_human_attention_service.py
# ================================

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..database import get_database
from ..models.atencion_humana import (
    AtencionHumana, AtencionHumanaCreate, AtencionHumanaUpdate,
    ClienteExterno, ConversacionData, MensajeWhatsApp, TicketExterno
)
from ..models.user import User
from ..services.waha_service import WAHAService
from ..services.api_service import ApiService
from ..services.n8n_service import N8NService
from ..services.cache_service import CacheService

logger = logging.getLogger(__name__)

class WhatsAppHumanAttentionService:
    """Servicio completo para atención humana de WhatsApp"""
    
    def __init__(self):
        self.db = get_database()
        self.waha_service = WAHAService()
        self.api_service = ApiService()
        self.n8n_service = N8NService()
        self.cache_service = CacheService()
    
    async def process_incoming_message(
        self, 
        business_id: str, 
        mensaje_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Procesar mensaje entrante de WhatsApp"""
        
        try:
            whatsapp_numero = mensaje_data.get("from")
            mensaje_texto = mensaje_data.get("body", "")
            
            # 1. Buscar o crear cliente externo
            cliente_externo = await self._get_or_create_external_client(
                business_id, whatsapp_numero
            )
            
            # 2. Verificar si hay sesión de atención activa
            sesion_activa = await self._get_active_session(business_id, whatsapp_numero)
            
            # 3. Analizar el mensaje para determinar si requiere atención humana
            requiere_atencion = await self._analyze_message_for_human_attention(
                business_id, mensaje_texto, cliente_externo
            )
            
            # 4. Procesar según el caso
            if sesion_activa:
                # Actualizar sesión existente
                return await self._update_existing_session(
                    sesion_activa, mensaje_data, cliente_externo
                )
            elif requiere_atencion:
                # Crear nueva sesión de atención
                return await self._create_new_attention_session(
                    business_id, mensaje_data, cliente_externo
                )
            else:
                # Respuesta automática via N8N
                return await self._handle_automatic_response(
                    business_id, mensaje_data, cliente_externo
                )
                
        except Exception as e:
            logger.error(f"Error procesando mensaje WhatsApp: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "error"
            }
    
    async def _get_or_create_external_client(
        self, 
        business_id: str, 
        whatsapp_numero: str
    ) -> ClienteExterno:
        """Obtener o crear cliente desde API externa"""
        
        try:
            # Buscar en cache primero
            cache_key = f"client_{business_id}_{whatsapp_numero}"
            cached_client = await self.cache_service.get(cache_key)
            
            if cached_client:
                return ClienteExterno(**cached_client)
            
            # Obtener configuración de API del business
            api_configs = await self.db.api_configurations.find({
                "business_id": business_id,
                "activa": True
            }).to_list()
            
            cliente_datos = {"nombre": "Cliente", "telefono": whatsapp_numero}
            
            # Buscar cliente en APIs externas
            for api_config in api_configs:
                try:
                    # Buscar por teléfono en la API
                    response = await self.api_service.make_request(
                        business_id=business_id,
                        api_name=api_config["api_name"],
                        endpoint="/customers",
                        params={"phone": whatsapp_numero}
                    )
                    
                    if response and isinstance(response, list) and len(response) > 0:
                        customer = response[0]
                        cliente_datos = {
                            "nombre": customer.get("name", customer.get("customer_name", "Cliente")),
                            "telefono": whatsapp_numero,
                            "cliente_id": customer.get("id", customer.get("customer_id")),
                            "plan": customer.get("plan", customer.get("plan_name")),
                            "estado": customer.get("status", "activo"),
                            "api_origen": api_config["api_name"]
                        }
                        break
                        
                except Exception as e:
                    logger.warning(f"Error consultando API {api_config['api_name']}: {e}")
                    continue
            
            cliente_externo = ClienteExterno(
                api_origen=cliente_datos.get("api_origen", "unknown"),
                cliente_id=cliente_datos.get("cliente_id", whatsapp_numero),
                datos_cache=cliente_datos,
                ultimo_refresh=datetime.utcnow()
            )
            
            # Guardar en cache por 1 hora
            await self.cache_service.set(cache_key, cliente_externo.dict(), ttl=3600)
            
            return cliente_externo
            
        except Exception as e:
            logger.error(f"Error obteniendo cliente externo: {e}")
            # Retornar cliente básico
            return ClienteExterno(
                api_origen="unknown",
                cliente_id=whatsapp_numero,
                datos_cache={"nombre": "Cliente", "telefono": whatsapp_numero},
                ultimo_refresh=datetime.utcnow()
            )
    
    async def _analyze_message_for_human_attention(
        self, 
        business_id: str, 
        mensaje_texto: str, 
        cliente_externo: ClienteExterno
    ) -> bool:
        """Analizar si el mensaje requiere atención humana"""
        
        # Palabras clave que indican necesidad de atención humana
        keywords_atencion = [
            "urgente", "emergency", "problema", "error", "falla",
            "no funciona", "reclamo", "queja", "cancelar", "hablar con",
            "operador", "humano", "persona", "supervisor", "gerente",
            "ayuda", "soporte", "técnico", "configurar", "instalar"
        ]
        
        mensaje_lower = mensaje_texto.lower()
        
        # Verificar palabras clave
        for keyword in keywords_atencion:
            if keyword in mensaje_lower:
                logger.info(f"Keyword '{keyword}' detectada, requiere atención humana")
                return True
        
        # Verificar si es un cliente premium (requiere atención prioritaria)
        if cliente_externo.datos_cache.get("plan", "").lower() in ["premium", "enterprise", "vip"]:
            return True
        
        # Verificar horario de atención automática
        now = datetime.utcnow()
        if now.hour < 8 or now.hour > 20:  # Fuera de horario
            return True
        
        # Si el mensaje es muy largo (posible consulta compleja)
        if len(mensaje_texto) > 200:
            return True
        
        # Por defecto, no requiere atención humana (respuesta automática)
        return False
    
    async def _get_active_session(
        self, 
        business_id: str, 
        whatsapp_numero: str
    ) -> Optional[AtencionHumana]:
        """Obtener sesión de atención activa"""
        
        doc = await self.db.atencion_humana.find_one({
            "business_id": business_id,
            "whatsapp_numero": whatsapp_numero,
            "conversacion.estado": {"$in": ["pendiente", "atendiendo"]}
        })
        
        return AtencionHumana(**doc) if doc else None
    
    async def _create_new_attention_session(
        self, 
        business_id: str, 
        mensaje_data: Dict[str, Any], 
        cliente_externo: ClienteExterno
    ) -> Dict[str, Any]:
        """Crear nueva sesión de atención humana"""
        
        try:
            # Determinar área solicitada basada en el mensaje
            area = await self._determine_area_from_message(mensaje_data.get("body", ""))
            
            # Crear mensaje inicial
            mensaje_inicial = MensajeWhatsApp(
                timestamp=datetime.fromisoformat(mensaje_data.get("timestamp", datetime.utcnow().isoformat())),
                de=mensaje_data.get("from"),
                para=mensaje_data.get("to"),
                mensaje=mensaje_data.get("body", ""),
                tipo=mensaje_data.get("type", "texto"),
                metadata=mensaje_data.get("metadata", {})
            )
            
            # Crear conversación
            conversacion = ConversacionData(
                requiere_atencion=True,
                area_solicitada=area,
                estado="pendiente",
                mensajes_contexto=[mensaje_inicial],
                fecha_inicio=datetime.utcnow(),
                notas_atencion=f"Sesión iniciada automáticamente - Área: {area}"
            )
            
            # Crear sesión de atención
            atencion_data = AtencionHumanaCreate(
                business_id=business_id,
                whatsapp_numero=mensaje_data.get("from"),
                cliente_externo=cliente_externo,
                conversacion=conversacion
            )
            
            # Guardar en base de datos
            atencion = AtencionHumana(**atencion_data.dict())
            result = await self.db.atencion_humana.insert_one(atencion.dict(by_alias=True))
            
            # Notificar a usuarios del área correspondiente
            await self._notify_area_users(business_id, area, atencion)
            
            # Enviar mensaje de confirmación automática
            await self._send_automatic_confirmation(business_id, mensaje_data.get("from"))
            
            logger.info(f"Nueva sesión de atención creada: {result.inserted_id}")
            
            return {
                "success": True,
                "action": "human_attention_created",
                "session_id": str(result.inserted_id),
                "area": area,
                "message": "Sesión de atención humana creada"
            }
            
        except Exception as e:
            logger.error(f"Error creando sesión de atención: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "creation_failed"
            }
    
    async def _update_existing_session(
        self, 
        sesion: AtencionHumana, 
        mensaje_data: Dict[str, Any], 
        cliente_externo: ClienteExterno
    ) -> Dict[str, Any]:
        """Actualizar sesión existente con nuevo mensaje"""
        
        try:
            # Crear nuevo mensaje
            nuevo_mensaje = MensajeWhatsApp(
                timestamp=datetime.fromisoformat(mensaje_data.get("timestamp", datetime.utcnow().isoformat())),
                de=mensaje_data.get("from"),
                para=mensaje_data.get("to"),
                mensaje=mensaje_data.get("body", ""),
                tipo=mensaje_data.get("type", "texto"),
                metadata=mensaje_data.get("metadata", {})
            )
            
            # Actualizar conversación
            sesion.conversacion.mensajes_contexto.append(nuevo_mensaje)
            
            # Mantener solo los últimos 10 mensajes para contexto
            if len(sesion.conversacion.mensajes_contexto) > 10:
                sesion.conversacion.mensajes_contexto = sesion.conversacion.mensajes_contexto[-10:]
            
            # Actualizar cliente externo si es necesario
            sesion.cliente_externo = cliente_externo
            sesion.updated_at = datetime.utcnow()
            
            # Guardar cambios
            await self.db.atencion_humana.update_one(
                {"_id": sesion.id},
                {
                    "$set": {
                        "conversacion": sesion.conversacion.dict(),
                        "cliente_externo": cliente_externo.dict(),
                        "updated_at": sesion.updated_at
                    }
                }
            )
            
            # Notificar al usuario que está atendiendo (si hay alguno)
            if sesion.conversacion.usuario_atendiendo:
                await self._notify_attending_user(sesion, nuevo_mensaje)
            
            return {
                "success": True,
                "action": "session_updated",
                "session_id": str(sesion.id),
                "message": "Mensaje agregado a sesión existente"
            }
            
        except Exception as e:
            logger.error(f"Error actualizando sesión: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "update_failed"
            }
    
    async def _handle_automatic_response(
        self, 
        business_id: str, 
        mensaje_data: Dict[str, Any], 
        cliente_externo: ClienteExterno
    ) -> Dict[str, Any]:
        """Manejar respuesta automática via N8N"""
        
        try:
            # Triggear workflow de respuesta automática
            workflow_data = {
                "business_id": business_id,
                "message": mensaje_data,
                "client": cliente_externo.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Buscar workflow de respuesta automática
            workflows = await self.n8n_service.get_workflows(business_id)
            auto_response_workflow = None
            
            for workflow in workflows:
                if "auto_response" in workflow.get("tags", []) or "whatsapp_auto" in workflow.get("name", "").lower():
                    auto_response_workflow = workflow
                    break
            
            if auto_response_workflow:
                # Ejecutar workflow
                execution_result = await self.n8n_service.trigger_workflow(
                    auto_response_workflow["id"],
                    workflow_data
                )
                
                return {
                    "success": True,
                    "action": "automatic_response",
                    "workflow_executed": auto_response_workflow["name"],
                    "execution_id": execution_result.get("execution_id"),
                    "message": "Respuesta automática procesada"
                }
            else:
                # Respuesta por defecto si no hay workflow
                await self._send_default_auto_response(business_id, mensaje_data.get("from"))
                
                return {
                    "success": True,
                    "action": "default_response",
                    "message": "Respuesta automática por defecto enviada"
                }
                
        except Exception as e:
            logger.error(f"Error en respuesta automática: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "auto_response_failed"
            }
    
    async def take_conversation(
        self, 
        session_id: str, 
        user: User
    ) -> Dict[str, Any]:
        """Tomar una conversación para atender"""
        
        try:
            # Obtener sesión
            sesion_doc = await self.db.atencion_humana.find_one({"_id": session_id})
            if not sesion_doc:
                return {"success": False, "error": "Sesión no encontrada"}
            
            sesion = AtencionHumana(**sesion_doc)
            
            # Verificar permisos
            if not self._user_can_attend_area(user, sesion.conversacion.area_solicitada):
                return {"success": False, "error": "Sin permisos para esta área"}
            
            # Verificar que no esté siendo atendida
            if sesion.conversacion.estado == "atendiendo" and sesion.conversacion.usuario_atendiendo:
                return {"success": False, "error": "Conversación ya está siendo atendida"}
            
            # Tomar conversación
            await self.db.atencion_humana.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "conversacion.estado": "atendiendo",
                        "conversacion.usuario_atendiendo": str(user.id),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Enviar notificación al cliente
            await self._send_agent_joined_notification(
                sesion.business_id, 
                sesion.whatsapp_numero, 
                user.perfil.nombre
            )
            
            return {
                "success": True,
                "message": "Conversación tomada exitosamente",
                "session": {
                    "id": session_id,
                    "client": sesion.cliente_externo.datos_cache,
                    "messages": [msg.dict() for msg in sesion.conversacion.mensajes_contexto[-5:]]
                }
            }
            
        except Exception as e:
            logger.error(f"Error tomando conversación: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_message_to_client(
        self, 
        session_id: str, 
        mensaje: str, 
        user: User
    ) -> Dict[str, Any]:
        """Enviar mensaje a cliente desde agente humano"""
        
        try:
            # Obtener sesión
            sesion_doc = await self.db.atencion_humana.find_one({"_id": session_id})
            if not sesion_doc:
                return {"success": False, "error": "Sesión no encontrada"}
            
            sesion = AtencionHumana(**sesion_doc)
            
            # Verificar que el usuario esté atendiendo esta conversación
            if sesion.conversacion.usuario_atendiendo != str(user.id):
                return {"success": False, "error": "No estás atendiendo esta conversación"}
            
            # Enviar mensaje via WAHA
            waha_result = await self.waha_service.send_message(
                sesion.business_id,
                sesion.whatsapp_numero,
                mensaje
            )
            
            if not waha_result.get("success"):
                return {"success": False, "error": "Error enviando mensaje"}
            
            # Registrar mensaje en la conversación
            mensaje_enviado = MensajeWhatsApp(
                timestamp=datetime.utcnow(),
                de=sesion.whatsapp_numero,  # El número del business
                para=sesion.whatsapp_numero,  # El número del cliente
                mensaje=mensaje,
                tipo="texto",
                metadata={"sent_by_agent": user.perfil.nombre, "agent_id": str(user.id)}
            )
            
            # Actualizar sesión
            sesion.conversacion.mensajes_contexto.append(mensaje_enviado)
            if len(sesion.conversacion.mensajes_contexto) > 10:
                sesion.conversacion.mensajes_contexto = sesion.conversacion.mensajes_contexto[-10:]
            
            await self.db.atencion_humana.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "conversacion.mensajes_contexto": [msg.dict() for msg in sesion.conversacion.mensajes_contexto],
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return {
                "success": True,
                "message": "Mensaje enviado exitosamente",
                "waha_response": waha_result
            }
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            return {"success": False, "error": str(e)}
    
    async def close_conversation(
        self, 
        session_id: str, 
        user: User, 
        notas: Optional[str] = None,
        create_ticket: bool = False
    ) -> Dict[str, Any]:
        """Finalizar conversación"""
        
        try:
            # Obtener sesión
            sesion_doc = await self.db.atencion_humana.find_one({"_id": session_id})
            if not sesion_doc:
                return {"success": False, "error": "Sesión no encontrada"}
            
            sesion = AtencionHumana(**sesion_doc)
            
            # Crear ticket externo si se solicita
            ticket_externo = None
            if create_ticket:
                ticket_externo = await self._create_external_ticket(sesion, user, notas)
            
            # Finalizar conversación
            await self.db.atencion_humana.update_one(
                {"_id": session_id},
                {
                    "$set": {
                        "conversacion.estado": "finalizado",
                        "conversacion.fecha_finalizacion": datetime.utcnow(),
                        "conversacion.notas_atencion": notas or "",
                        "ticket_externo": ticket_externo.dict() if ticket_externo else None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Enviar mensaje de cierre al cliente
            await self._send_conversation_closed_notification(
                sesion.business_id,
                sesion.whatsapp_numero
            )
            
            return {
                "success": True,
                "message": "Conversación finalizada exitosamente",
                "ticket_created": ticket_externo is not None,
                "ticket_id": ticket_externo.ticket_id if ticket_externo else None
            }
            
        except Exception as e:
            logger.error(f"Error cerrando conversación: {e}")
            return {"success": False, "error": str(e)}
    
    # Métodos auxiliares
    async def _determine_area_from_message(self, mensaje: str) -> str:
        """Determinar área basada en el contenido del mensaje"""
        mensaje_lower = mensaje.lower()
        
        if any(word in mensaje_lower for word in ["técnico", "internet", "velocidad", "conexión", "router", "wifi"]):
            return "tecnica"
        elif any(word in mensaje_lower for word in ["factura", "pago", "precio", "plan", "costo", "dinero"]):
            return "admin"
        elif any(word in mensaje_lower for word in ["contratar", "nuevo", "servicio", "promoción", "oferta"]):
            return "ventas"
        else:
            return "soporte"
    
    def _user_can_attend_area(self, user: User, area: str) -> bool:
        """Verificar si el usuario puede atender un área específica"""
        if user.rol in ["super_admin", "admin"]:
            return True
        
        areas_usuario = user.permisos.areas_whatsapp
        return "*" in areas_usuario or area in areas_usuario
    
    async def _notify_area_users(self, business_id: str, area: str, atencion: AtencionHumana):
        """Notificar a usuarios del área sobre nueva conversación"""
        # TODO: Implementar sistema de notificaciones en tiempo real
        logger.info(f"Notificación: Nueva conversación en área {area} para business {business_id}")
    
    async def _send_automatic_confirmation(self, business_id: str, whatsapp_numero: str):
        """Enviar mensaje de confirmación automática"""
        mensaje = "¡Hola! Hemos recibido tu mensaje y pronto un agente te atenderá. Gracias por tu paciencia."
        await self.waha_service.send_message(business_id, whatsapp_numero, mensaje)