from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..database import get_database
from ..models.user import User, UserCreate, UserUpdate

logger = logging.getLogger(__name__)

class UserService:
    """Servicio para gestión de usuarios"""
    
    def __init__(self):
        self.db = get_database()
    
    async def get_user_by_clerk_id(self, clerk_user_id: str) -> Optional[User]:
        """Obtener usuario por Clerk ID"""
        doc = await self.db.users.find_one({"clerk_user_id": clerk_user_id})
        return User(**doc) if doc else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Obtener usuario por ID interno"""
        from bson import ObjectId
        doc = await self.db.users.find_one({"_id": ObjectId(user_id)})
        return User(**doc) if doc else None
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Crear un nuevo usuario"""
        user = User(**user_data.dict())
        
        result = await self.db.users.insert_one(user.dict(by_alias=True))
        user.id = result.inserted_id
        
        logger.info(f"Usuario creado: {user.email}")
        return user
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Actualizar un usuario"""
        from bson import ObjectId
        
        update_data = user_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        result = await self.db.users.find_one_and_update(
            {"_id": ObjectId(user_id)},
            {"$set": update_data},
            return_document=True
        )
        
        if result:
            logger.info(f"Usuario actualizado: {user_id}")
            return User(**result)
        
        return None
    
    async def update_last_access(self, clerk_user_id: str):
        """Actualizar último acceso del usuario"""
        await self.db.users.update_one(
            {"clerk_user_id": clerk_user_id},
            {"$set": {"ultimo_acceso": datetime.utcnow()}}
        )
    
    async def get_users_by_business(self, business_id: str) -> List[User]:
        """Obtener usuarios de un business específico"""
        cursor = self.db.users.find({"business_id": business_id}).sort("perfil.nombre", 1)
        users = []
        
        async for doc in cursor:
            users.append(User(**doc))
        
        return users
    
    # === WEBHOOK HANDLERS ===
    
    async def handle_user_created(self, clerk_data: Dict[str, Any]):
        """Manejar creación de usuario desde Clerk"""
        try:
            # Extraer datos relevantes de Clerk
            clerk_user_id = clerk_data["id"]
            email = clerk_data["email_addresses"][0]["email_address"]
            first_name = clerk_data.get("first_name", "")
            last_name = clerk_data.get("last_name", "")
            
            # Verificar si ya existe
            existing_user = await self.get_user_by_clerk_id(clerk_user_id)
            if existing_user:
                logger.warning(f"Usuario ya existe: {clerk_user_id}")
                return
            
            # Crear usuario básico
            user_data = UserCreate(
                clerk_user_id=clerk_user_id,
                email=email,
                perfil={
                    "nombre": f"{first_name} {last_name}".strip() or email
                }
            )
            
            await self.create_user(user_data)
            logger.info(f"Usuario sincronizado desde Clerk: {email}")
            
        except Exception as e:
            logger.error(f"Error manejando creación de usuario: {e}")
    
    async def handle_user_updated(self, clerk_data: Dict[str, Any]):
        """Manejar actualización de usuario desde Clerk"""
        try:
            clerk_user_id = clerk_data["id"]
            
            user = await self.get_user_by_clerk_id(clerk_user_id)
            if not user:
                logger.warning(f"Usuario no encontrado para actualizar: {clerk_user_id}")
                return
            
            # Actualizar datos desde Clerk
            email = clerk_data["email_addresses"][0]["email_address"]
            first_name = clerk_data.get("first_name", "")
            last_name = clerk_data.get("last_name", "")
            
            update_data = UserUpdate(
                email=email,
                perfil={
                    **user.perfil.dict(),
                    "nombre": f"{first_name} {last_name}".strip() or email
                }
            )
            
            await self.update_user(str(user.id), update_data)
            logger.info(f"Usuario actualizado desde Clerk: {email}")
            
        except Exception as e:
            logger.error(f"Error manejando actualización de usuario: {e}")
    
    async def handle_user_deleted(self, clerk_data: Dict[str, Any]):
        """Manejar eliminación de usuario desde Clerk"""
        try:
            clerk_user_id = clerk_data["id"]
            
            result = await self.db.users.update_one(
                {"clerk_user_id": clerk_user_id},
                {"$set": {"activo": False, "updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Usuario desactivado desde Clerk: {clerk_user_id}")
            
        except Exception as e:
            logger.error(f"Error manejando eliminación de usuario: {e}")