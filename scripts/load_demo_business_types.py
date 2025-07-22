#!/usr/bin/env python3
"""
Script para cargar Business Types de ejemplo
"""

import asyncio
import httpx
import json

# Business Types de ejemplo
BUSINESS_TYPES = [
    {
        "tipo": "isp",
        "nombre": "ISP Template",
        "descripcion": "Template para proveedores de servicios de internet",
        "componentes_base": [
            {"id": "whatsapp", "nombre": "WhatsApp Business", "tipo": "integration", "obligatorio": True},
            {"id": "n8n", "nombre": "N8N Workflows", "tipo": "integration", "obligatorio": True},
            {"id": "clientes", "nombre": "Gestión de Clientes", "tipo": "entity", "obligatorio": True}
        ],
        "componentes_opcionales": [
            {"id": "facturacion", "nombre": "Sistema de Facturación", "tipo": "entity"},
            {"id": "tickets", "nombre": "Sistema de Tickets", "tipo": "entity"},
            {"id": "caja", "nombre": "Control de Caja", "tipo": "module"},
            {"id": "inventario", "nombre": "Inventario de Equipos", "tipo": "entity"}
        ]
    },
    {
        "tipo": "restaurante",
        "nombre": "Restaurant Template",
        "descripcion": "Template para restaurantes y locales gastronómicos",
        "componentes_base": [
            {"id": "whatsapp", "nombre": "WhatsApp Business", "tipo": "integration", "obligatorio": True},
            {"id": "n8n", "nombre": "N8N Workflows", "tipo": "integration", "obligatorio": True},
            {"id": "menu", "nombre": "Gestión de Menú", "tipo": "entity", "obligatorio": True},
            {"id": "pedidos", "nombre": "Sistema de Pedidos", "tipo": "entity", "obligatorio": True}
        ],
        "componentes_opcionales": [
            {"id": "clientes", "nombre": "Base de Clientes", "tipo": "entity"},
            {"id": "reservas", "nombre": "Sistema de Reservas", "tipo": "entity"},
            {"id": "delivery", "nombre": "Delivery Tracking", "tipo": "module"},
            {"id": "inventario", "nombre": "Inventario de Ingredientes", "tipo": "entity"},
            {"id": "caja", "nombre": "Control de Caja", "tipo": "module"}
        ]
    },
    {
        "tipo": "clinica",
        "nombre": "Clínica Template",
        "descripcion": "Template para clínicas y consultorios médicos",
        "componentes_base": [
            {"id": "whatsapp", "nombre": "WhatsApp Business", "tipo": "integration", "obligatorio": True},
            {"id": "pacientes", "nombre": "Gestión de Pacientes", "tipo": "entity", "obligatorio": True},
            {"id": "turnos", "nombre": "Sistema de Turnos", "tipo": "entity", "obligatorio": True},
            {"id": "profesionales", "nombre": "Gestión de Profesionales", "tipo": "entity", "obligatorio": True}
        ],
        "componentes_opcionales": [
            {"id": "n8n", "nombre": "N8N Workflows", "tipo": "integration"},
            {"id": "historias_clinicas", "nombre": "Historias Clínicas", "tipo": "entity"},
            {"id": "facturacion", "nombre": "Facturación Médica", "tipo": "entity"},
            {"id": "obra_social", "nombre": "Gestión Obra Social", "tipo": "module"},
            {"id": "caja", "nombre": "Control de Caja", "tipo": "module"}
        ]
    }
]

async def load_business_type(business_type):
    """Cargar un Business Type individual"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/admin/business-types",
                json=business_type,
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ Business Type '{business_type['tipo']}' creado exitosamente")
                return True
            elif response.status_code == 409:
                print(f"⚠️ Business Type '{business_type['tipo']}' ya existe")
                return True
            else:
                print(f"❌ Error creando '{business_type['tipo']}': {response.status_code}")
                print(f"   Respuesta: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Error de conexión para '{business_type['tipo']}': {e}")
        return False

async def main():
    """Función principal"""
    print("🚀 Cargando Business Types de ejemplo...\n")
    
    # Verificar que el backend esté corriendo
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=5.0)
            if response.status_code != 200:
                print("❌ Backend no está respondiendo correctamente")
                return
    except Exception as e:
        print(f"❌ No se puede conectar al backend: {e}")
        print("   Asegúrate de que esté corriendo en http://localhost:8000")
        return
    
    print("✅ Backend conectado\n")
    
    # Cargar cada Business Type
    success_count = 0
    for business_type in BUSINESS_TYPES:
        if await load_business_type(business_type):
            success_count += 1
    
    print(f"\n📊 Resultado: {success_count}/{len(BUSINESS_TYPES)} Business Types cargados")
    
    if success_count == len(BUSINESS_TYPES):
        print("🎉 ¡Todos los Business Types cargados exitosamente!")
    else:
        print("⚠️ Algunos Business Types no se pudieron cargar")

if __name__ == "__main__":
    asyncio.run(main())