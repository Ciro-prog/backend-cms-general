# ================================
# app/services/mapping_config_service.py
# Servicio para gestión de configuraciones de mapping
# ================================

from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Dict, List, Any, Optional
from bson import ObjectId
from ..models.field_mapping import MappingConfiguration, MappedField
from ..database import get_database
import logging

logger = logging.getLogger(__name__)

class MappingConfigService:
    """Servicio para gestión de configuraciones de mapping"""
    
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.mapping_configurations
    
    async def save_mapping(self, mapping_config: MappingConfiguration) -> Dict[str, Any]:
        """Guardar configuración de mapping"""
        try:
            # Convertir a dict para MongoDB
            mapping_dict = mapping_config.dict(by_alias=True)
            mapping_dict["created_at"] = datetime.utcnow()
            mapping_dict["updated_at"] = datetime.utcnow()
            
            # Insertar en base de datos
            result = await self.collection.insert_one(mapping_dict)
            
            logger.info(f"Mapping configuration saved: {result.inserted_id}")
            
            return {
                "success": True,
                "mapping_id": str(result.inserted_id),
                "message": "Configuración guardada exitosamente"
            }
            
        except Exception as e:
            logger.error(f"Error saving mapping configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_mapping(self, mapping_id: str) -> Optional[MappingConfiguration]:
        """Obtener configuración de mapping por ID"""
        try:
            object_id = ObjectId(mapping_id)
            mapping_doc = await self.collection.find_one({"_id": object_id})
            
            if mapping_doc:
                # Convertir ObjectId a string
                mapping_doc["_id"] = str(mapping_doc["_id"])
                return MappingConfiguration(**mapping_doc)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting mapping configuration: {e}")
            return None
    
    async def get_mappings_by_business(self, business_id: str) -> List[MappingConfiguration]:
        """Obtener todas las configuraciones de mapping para un business"""
        try:
            cursor = self.collection.find({"business_id": business_id})
            mappings = []
            
            async for doc in cursor:
                doc["_id"] = str(doc["_id"])
                mappings.append(MappingConfiguration(**doc))
            
            return mappings
            
        except Exception as e:
            logger.error(f"Error getting mappings for business {business_id}: {e}")
            return []
    
    async def update_mapping(self, mapping_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar configuración de mapping"""
        try:
            object_id = ObjectId(mapping_id)
            updates["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                return {
                    "success": True,
                    "message": "Configuración actualizada exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "No se encontró la configuración o no hubo cambios"
                }
                
        except Exception as e:
            logger.error(f"Error updating mapping configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_mapping(self, mapping_id: str) -> Dict[str, Any]:
        """Eliminar configuración de mapping"""
        try:
            object_id = ObjectId(mapping_id)
            
            result = await self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                return {
                    "success": True,
                    "message": "Configuración eliminada exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "No se encontró la configuración"
                }
                
        except Exception as e:
            logger.error(f"Error deleting mapping configuration: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def apply_mapping_to_data(self, mapping_id: str, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aplicar configuración de mapping a datos raw"""
        try:
            mapping_config = await self.get_mapping(mapping_id)
            if not mapping_config:
                return {
                    "success": False,
                    "error": "Configuración de mapping no encontrada"
                }
            
            from .field_mapper_service import FieldMapperService
            mapper_service = FieldMapperService()
            
            mapped_data = []
            for raw_record in raw_data:
                mapped_record = {}
                
                for field in mapping_config.mapped_fields:
                    # Extraer valor usando el path de la API
                    value = mapper_service.extract_value_by_path(raw_record, field.api_path)
                    
                    # Usar el nombre amigable como key
                    mapped_record[field.display_name] = value
                
                mapped_data.append(mapped_record)
            
            return {
                "success": True,
                "data": mapped_data,
                "field_config": [f.dict() for f in mapping_config.mapped_fields],
                "total_records": len(mapped_data)
            }
            
        except Exception as e:
            logger.error(f"Error applying mapping to data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def validate_mapping_against_api(self, mapping_id: str, api_endpoint: str) -> Dict[str, Any]:
        """Validar que el mapping funcione con la API real"""
        try:
            mapping_config = await self.get_mapping(mapping_id)
            if not mapping_config:
                return {
                    "success": False,
                    "error": "Configuración de mapping no encontrada"
                }
            
            # Hacer petición a la API para obtener datos de muestra
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(api_endpoint)
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"API returned status {response.status_code}"
                    }
                
                api_data = response.json()
            
            # Aplicar mapping a los datos
            result = await self.apply_mapping_to_data(mapping_id, [api_data] if isinstance(api_data, dict) else api_data)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Mapping validado exitosamente contra API",
                    "sample_data": result["data"][:5],  # Mostrar solo 5 registros de muestra
                    "total_fields_mapped": len(mapping_config.mapped_fields)
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error validating mapping against API: {e}")
            return {
                "success": False,
                "error": str(e)
            }

logger.info("🗃️ Mapping Configuration Service creado")
