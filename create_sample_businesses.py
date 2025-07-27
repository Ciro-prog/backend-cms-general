#!/usr/bin/env python3
"""
Script para crear empresas de ejemplo
"""

import asyncio
import sys
import os

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def create_sample_businesses():
    """Crear empresas de ejemplo"""
    
    try:
        # Importar después de configurar el path
        from app.services.business_service import BusinessService
        from app.models.business import BusinessTypeCreate, BusinessInstanceCreate
        
        business_service = BusinessService()
        
        print("🏢 Creando tipos de negocio...")
        
        # Crear tipos de negocio base
        business_types = [
            {
                "tipo": "retail",
                "nombre": "Comercio Minorista",
                "descripcion": "Tiendas, comercios, retail",
                "configuracion_base": {
                    "entidades_comunes": ["clientes", "productos", "ventas"],
                    "integraciones": ["pos", "ecommerce", "crm"]
                }
            },
            {
                "tipo": "services",
                "nombre": "Servicios Profesionales", 
                "descripcion": "Consultorías, agencias, servicios",
                "configuracion_base": {
                    "entidades_comunes": ["clientes", "proyectos", "facturas"],
                    "integraciones": ["crm", "accounting", "timetracking"]
                }
            },
            {
                "tipo": "tech",
                "nombre": "Tecnología",
                "descripcion": "Software, startups, tech",
                "configuracion_base": {
                    "entidades_comunes": ["usuarios", "productos", "analytics"],
                    "integraciones": ["api", "analytics", "monitoring"]
                }
            }
        ]
        
        for bt_data in business_types:
            try:
                existing = await business_service.get_business_type_by_tipo(bt_data["tipo"])
                if not existing:
                    bt_create = BusinessTypeCreate(**bt_data)
                    created = await business_service.create_business_type(bt_create)
                    print(f"✅ Tipo creado: {created.nombre}")
                else:
                    print(f"⏭️  Tipo ya existe: {existing.nombre}")
            except Exception as e:
                print(f"❌ Error creando tipo {bt_data['tipo']}: {e}")
        
        print("\n🏪 Creando instancias de negocio...")
        
        # Crear instancias de negocio
        business_instances = [
            {
                "business_id": "demo_retail_001",
                "nombre": "Tienda Demo",
                "tipo_base": "retail",
                "descripcion": "Tienda de demostración para testing",
                "configuracion": {
                    "timezone": "America/Argentina/Buenos_Aires",
                    "currency": "ARS",
                    "language": "es"
                },
                "contacto": {
                    "email": "demo@tienda.com",
                    "telefono": "+54 11 1234-5678"
                },
                "plan": "basic",
                "activo": True
            },
            {
                "business_id": "demo_services_001", 
                "nombre": "Consultora Demo",
                "tipo_base": "services",
                "descripcion": "Consultora de demostración",
                "configuracion": {
                    "timezone": "America/Argentina/Buenos_Aires",
                    "currency": "ARS", 
                    "language": "es"
                },
                "contacto": {
                    "email": "demo@consultora.com",
                    "telefono": "+54 11 9876-5432"
                },
                "plan": "professional",
                "activo": True
            },
            {
                "business_id": "demo_tech_001",
                "nombre": "Startup Demo",
                "tipo_base": "tech",
                "descripcion": "Startup tecnológica de demostración",
                "configuracion": {
                    "timezone": "America/Argentina/Buenos_Aires",
                    "currency": "USD",
                    "language": "es"
                },
                "contacto": {
                    "email": "demo@startup.com",
                    "telefono": "+54 11 5555-1234"
                },
                "plan": "enterprise",
                "activo": True
            }
        ]
        
        for bi_data in business_instances:
            try:
                existing = await business_service.get_business_instance(bi_data["business_id"])
                if not existing:
                    bi_create = BusinessInstanceCreate(**bi_data)
                    created = await business_service.create_business_instance(bi_create)
                    print(f"✅ Negocio creado: {created.nombre}")
                else:
                    print(f"⏭️  Negocio ya existe: {existing.nombre}")
            except Exception as e:
                print(f"❌ Error creando negocio {bi_data['business_id']}: {e}")
        
        print("\n📊 Verificando datos creados...")
        
        # Verificar resultados
        all_types = await business_service.get_all_business_types()
        all_instances = await business_service.get_all_business_instances()
        
        print(f"✅ Tipos de negocio: {len(all_types)}")
        for bt in all_types:
            print(f"   - {bt.tipo}: {bt.nombre}")
        
        print(f"✅ Instancias de negocio: {len(all_instances)}")
        for bi in all_instances:
            print(f"   - {bi.business_id}: {bi.nombre} ({bi.tipo_base})")
        
        return True
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🚀 Iniciando creación de datos de empresas...")
    
    success = await create_sample_businesses()
    
    if success:
        print("\n✅ ¡Datos de empresas creados exitosamente!")
        print("   Ahora puedes usar el wizard de APIs")
    else:
        print("\n❌ Hubo errores creando los datos")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\n⏹️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)
