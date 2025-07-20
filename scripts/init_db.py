# ================================
# scripts/init_db.py
# ================================

#!/usr/bin/env python3
"""
Script para inicializar la base de datos con datos de ejemplo
"""

import asyncio
import sys
import os

# Agregar el directorio padre al path para importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import connect_to_mongo, get_database
from app.models.business import BusinessTypeCreate, BusinessInstanceCreate
from app.services.business_service import BusinessService
from datetime import datetime

async def init_database():
    """Inicializar base de datos con datos de ejemplo"""
    print("🚀 Inicializando base de datos...")
    
    # Conectar a MongoDB
    await connect_to_mongo()
    
    business_service = BusinessService()
    
    # Crear business type ISP
    print("📋 Creando business type ISP...")
    isp_type = BusinessTypeCreate(
        tipo="isp",
        nombre="ISP Template",
        descripcion="Template para proveedores de internet",
        componentes_base=[
            {
                "id": "whatsapp",
                "nombre": "WhatsApp Business",
                "tipo": "integration",
                "obligatorio": True,
                "configuracion_default": {
                    "waha_base_url": "",
                    "session_name": "",
                    "webhook_enabled": True
                }
            },
            {
                "id": "n8n",
                "nombre": "N8N Workflows",
                "tipo": "integration", 
                "obligatorio": True
            },
            {
                "id": "clientes",
                "nombre": "Gestión Clientes",
                "tipo": "entity",
                "obligatorio": True
            }
        ],
        componentes_opcionales=[
            {
                "id": "facturacion",
                "nombre": "Facturación",
                "tipo": "entity"
            }
        ]
    )
    
    await business_service.create_business_type(isp_type)
    
    # Crear business instance de ejemplo
    print("🏢 Creando business instance TelcoNorte...")
    telconorte = BusinessInstanceCreate(
        business_id="isp_telconorte",
        nombre="TelcoNorte ISP",
        tipo_base="isp",
        configuracion={
            "branding": {
                "logo_url": "/uploads/telconorte_logo.png",
                "colores": {
                    "primary": "#1e40af",
                    "secondary": "#059669",
                    "background": "#f8fafc",
                    "text": "#0f172a"
                }
            },
            "componentes_activos": ["whatsapp", "n8n", "clientes", "facturacion"],
            "roles_personalizados": [
                {
                    "rol": "admin",
                    "nombre": "Administrador",
                    "permisos": "*"
                },
                {
                    "rol": "tecnico",
                    "nombre": "Técnico",
                    "permisos": ["clientes:read", "tickets:*", "whatsapp:write"]
                }
            ]
        }
    )
    
    await business_service.create_business_instance(telconorte)
    
    print("✅ Base de datos inicializada correctamente!")
    print("\n📋 Datos creados:")
    print("  - Business Type: ISP")
    print("  - Business Instance: TelcoNorte (isp_telconorte)")
    print("\n🔗 Puedes acceder a la API en: http://localhost:8000/docs")

if __name__ == "__main__":
    asyncio.run(init_database())