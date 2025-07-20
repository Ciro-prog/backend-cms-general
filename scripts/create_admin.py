#!/usr/bin/env python3
"""
Script para crear un usuario administrador
"""

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import connect_to_mongo
from app.models.user import UserCreate
from app.services.user_service import UserService

async def create_admin():
    """Crear usuario administrador"""
    print("👤 Creando usuario administrador...")
    
    await connect_to_mongo()
    
    # Datos del admin
    email = input("Email del administrador: ")
    nombre = input("Nombre completo: ")
    clerk_user_id = input("Clerk User ID (opcional): ") or f"admin_{email}"
    
    user_service = UserService()
    
    admin_data = UserCreate(
        clerk_user_id=clerk_user_id,
        email=email,
        rol="super_admin",
        perfil={"nombre": nombre},
        permisos={
            "puede_editar_config": True,
            "puede_responder_whatsapp": True,
            "areas_whatsapp": ["*"],
            "entidades_acceso": ["*"],
            "vistas_acceso": ["*"]
        }
    )
    
    admin = await user_service.create_user(admin_data)
    
    print(f"✅ Usuario administrador creado: {admin.email}")
    print(f"🔑 ID: {admin.id}")
    print(f"👑 Rol: {admin.rol}")

if __name__ == "__main__":
    asyncio.run(create_admin())