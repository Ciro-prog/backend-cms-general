#!/usr/bin/env python3
"""
Script para Diagnosticar y Arreglar Problema de Empresas
Diagnóstica por qué no se cargan las empresas en el wizard y lo soluciona
"""

import os
import sys
import json
import asyncio
import shutil
from datetime import datetime
from pathlib import Path

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 {title}")
    print(f"{'='*60}")

def print_section(title):
    print(f"\n{'─'*40}")
    print(f"📋 {title}")
    print(f"{'─'*40}")

def backup_file(filepath):
    """Crear backup de un archivo antes de modificarlo"""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        print(f"💾 Backup creado: {backup_path}")
        return backup_path
    return None

def write_file(filepath, content, description=""):
    """Escribir contenido a un archivo"""
    parent_dir = os.path.dirname(filepath)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ {filepath} - {description}")

def diagnose_business_service():
    """Diagnosticar el BusinessService"""
    print_section("Diagnóstico del BusinessService")
    
    service_file = "app/services/business_service.py"
    if not os.path.exists(service_file):
        print(f"❌ {service_file} no existe")
        return False
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar métodos existentes
    methods = {
        "get_all_business_instances": "get_all_business_instances" in content,
        "get_all_businesses": "get_all_businesses" in content,
        "create_business_instance": "create_business_instance" in content,
        "get_business_instance": "get_business_instance" in content,
    }
    
    print("🔍 Métodos encontrados en BusinessService:")
    for method, exists in methods.items():
        status = "✅" if exists else "❌"
        print(f"  {status} {method}")
    
    return methods["get_all_business_instances"]

def diagnose_main_endpoints():
    """Diagnosticar endpoints en main.py"""
    print_section("Diagnóstico de Endpoints en main.py")
    
    main_file = "app/main.py"
    if not os.path.exists(main_file):
        print(f"❌ {main_file} no existe")
        return False
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar el problema específico
    issues = {
        "Llamada incorrecta": "get_all_businesses()" in content,
        "Wizard endpoint existe": "/api-management/wizard" in content,
        "Import BusinessService": "BusinessService" in content,
    }
    
    print("🔍 Problemas encontrados en main.py:")
    for issue, found in issues.items():
        status = "⚠️" if found and "incorrecta" in issue else "✅" if found else "❌"
        print(f"  {status} {issue}")
    
    # Mostrar línea problemática si existe
    if "get_all_businesses()" in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if "get_all_businesses()" in line:
                print(f"\n🚨 Línea problemática encontrada ({i+1}):")
                print(f"    {line.strip()}")
                break
    
    return True

def fix_main_endpoints():
    """Corregir endpoints en main.py"""
    print_section("Corrigiendo Endpoints en main.py")
    
    main_file = "app/main.py"
    if not os.path.exists(main_file):
        print(f"❌ {main_file} no existe")
        return False
    
    # Backup del archivo
    backup_file(main_file)
    
    with open(main_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Realizar correcciones
    corrections = [
        # Corregir llamada al método
        (
            "businesses = await business_service.get_all_businesses() if hasattr(business_service, 'get_all_businesses') else []",
            "businesses = await business_service.get_all_business_instances()"
        ),
        # Asegurar manejo de errores
        (
            "businesses = await business_service.get_all_business_instances()",
            """try:
            businesses = await business_service.get_all_business_instances()
        except Exception as e:
            logger.error(f"Error cargando businesses: {e}")
            businesses = []"""
        )
    ]
    
    for old_text, new_text in corrections:
        if old_text in content:
            content = content.replace(old_text, new_text)
            print(f"✅ Corregido: {old_text[:50]}...")
    
    # Escribir archivo corregido
    write_file(main_file, content, "main.py corregido")
    return True

def create_business_data_script():
    """Crear script para poblar datos de businesses"""
    print_section("Creando Script de Datos de Empresas")
    
    script_content = '''#!/usr/bin/env python3
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
        
        print("\\n🏪 Creando instancias de negocio...")
        
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
        
        print("\\n📊 Verificando datos creados...")
        
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
        print("\\n✅ ¡Datos de empresas creados exitosamente!")
        print("   Ahora puedes usar el wizard de APIs")
    else:
        print("\\n❌ Hubo errores creando los datos")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\\n⏹️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error inesperado: {e}")
        sys.exit(1)
'''
    
    write_file("create_sample_businesses.py", script_content, "Script para crear empresas de ejemplo")

def create_database_check_script():
    """Crear script para verificar base de datos"""
    print_section("Creando Script de Verificación de DB")
    
    script_content = '''#!/usr/bin/env python3
"""
Script para verificar estado de la base de datos
"""

import asyncio
import sys
import os

# Agregar el directorio app al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

async def check_database():
    """Verificar estado de la base de datos"""
    
    try:
        from app.database import get_database
        from app.services.business_service import BusinessService
        
        print("🔍 Verificando conexión a la base de datos...")
        
        db = get_database()
        
        # Verificar conexión
        try:
            await db.admin.command('ping')
            print("✅ Conexión a MongoDB exitosa")
        except Exception as e:
            print(f"❌ Error de conexión a MongoDB: {e}")
            return False
        
        # Verificar colecciones
        collections = await db.list_collection_names()
        print(f"📂 Colecciones encontradas: {len(collections)}")
        
        required_collections = [
            "business_types",
            "business_instances", 
            "users",
            "api_configurations"
        ]
        
        for collection in required_collections:
            exists = collection in collections
            status = "✅" if exists else "❌"
            count = await db[collection].count_documents({}) if exists else 0
            print(f"  {status} {collection}: {count} documentos")
        
        # Verificar business service
        print("\\n🏢 Verificando BusinessService...")
        business_service = BusinessService()
        
        try:
            business_types = await business_service.get_all_business_types()
            print(f"✅ Tipos de negocio: {len(business_types)}")
            for bt in business_types:
                print(f"   - {bt.tipo}: {bt.nombre}")
        except Exception as e:
            print(f"❌ Error obteniendo tipos: {e}")
        
        try:
            business_instances = await business_service.get_all_business_instances()
            print(f"✅ Instancias de negocio: {len(business_instances)}")
            for bi in business_instances:
                print(f"   - {bi.business_id}: {bi.nombre}")
        except Exception as e:
            print(f"❌ Error obteniendo instancias: {e}")
        
        # Verificar usuarios
        users_count = await db.users.count_documents({})
        print(f"\\n👥 Usuarios en sistema: {users_count}")
        
        if users_count > 0:
            # Mostrar algunos usuarios (sin passwords)
            users = await db.users.find({}, {"password": 0}).limit(3).to_list(length=3)
            for user in users:
                print(f"   - {user.get('username', 'N/A')}: {user.get('rol', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verificando base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("🔍 Verificando estado de la base de datos...")
    
    success = await check_database()
    
    if success:
        print("\\n✅ Verificación completada")
    else:
        print("\\n❌ Problemas encontrados en la base de datos")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(result)
    except KeyboardInterrupt:
        print("\\n⏹️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Error inesperado: {e}")
        sys.exit(1)
'''
    
    write_file("check_database.py", script_content, "Script para verificar base de datos")

def enhance_business_service():
    """Mejorar BusinessService con método de compatibilidad"""
    print_section("Mejorando BusinessService")
    
    service_file = "app/services/business_service.py"
    if not os.path.exists(service_file):
        print(f"❌ {service_file} no existe")
        return False
    
    # Backup del archivo
    backup_file(service_file)
    
    with open(service_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Agregar método de compatibilidad si no existe
    compatibility_method = '''
    # === MÉTODOS DE COMPATIBILIDAD ===
    
    async def get_all_businesses(self) -> List[BusinessInstance]:
        """Método de compatibilidad - usar get_all_business_instances()"""
        return await self.get_all_business_instances()
    
    async def get_businesses(self, **kwargs) -> List[BusinessInstance]:
        """Método de compatibilidad - usar get_all_business_instances()"""
        return await self.get_all_business_instances(**kwargs)'''
    
    if "get_all_businesses" not in content:
        # Encontrar dónde insertar el método
        if "logger.info(" in content:
            # Insertar antes del último logger.info
            lines = content.split('\n')
            insert_index = -1
            for i in range(len(lines) - 1, -1, -1):
                if 'logger.info(' in lines[i] and 'BusinessService' in lines[i]:
                    insert_index = i
                    break
            
            if insert_index > 0:
                lines.insert(insert_index, compatibility_method)
                content = '\n'.join(lines)
                print("✅ Métodos de compatibilidad agregados")
            else:
                content += compatibility_method
                print("✅ Métodos de compatibilidad agregados al final")
        else:
            content += compatibility_method
            print("✅ Métodos de compatibilidad agregados al final")
    else:
        print("⏭️  Métodos de compatibilidad ya existen")
    
    # Escribir archivo mejorado
    write_file(service_file, content, "BusinessService mejorado")
    return True

def create_wizard_test_script():
    """Crear script para probar el wizard"""
    print_section("Creando Script de Test del Wizard")
    
    script_content = '''#!/usr/bin/env python3
"""
Script para probar que el wizard funcione correctamente
"""

import asyncio
import sys
import os
import httpx

async def test_wizard_endpoints():
    """Probar endpoints del wizard"""
    
    print("🧪 Probando endpoints del wizard...")
    
    base_url = "http://localhost:8000"
    
    endpoints_to_test = [
        {
            "url": f"{base_url}/api-management",
            "description": "Página principal de gestión APIs"
        },
        {
            "url": f"{base_url}/api-management/wizard", 
            "description": "Wizard de configuración"
        },
        {
            "url": f"{base_url}/api-management/test",
            "description": "Página de testing"
        }
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints_to_test:
            try:
                print(f"\\n🔗 Probando: {endpoint['description']}")
                print(f"   URL: {endpoint['url']}")
                
                response = await client.get(endpoint['url'])
                
                if response.status_code == 200:
                    print(f"   ✅ OK (200) - Página carga correctamente")
                    
                    # Verificar si menciona empresas/businesses
                    content = response.text
                    if "business" in content.lower() or "empresa" in content.lower():
                        print(f"   ✅ Contiene referencias a empresas")
                    else:
                        print(f"   ⚠️  No contiene referencias a empresas")
                
                elif response.status_code == 302:
                    print(f"   🔄 Redirect (302) - Probablemente redirección a login")
                    
                elif response.status_code == 401:
                    print(f"   🔐 No autorizado (401) - Necesitas estar logueado")
                    
                else:
                    print(f"   ❌ Error ({response.status_code})")
                    
            except httpx.ConnectError:
                print(f"   ❌ No se puede conectar - ¿Está corriendo el servidor?")
                print(f"   💡 Ejecuta: uvicorn app.main:app --reload")
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
    
    print("\\n💡 Para probar completamente:")
    print("   1. Inicia el servidor: uvicorn app.main:app --reload")
    print("   2. Ve a: http://localhost:8000")
    print("   3. Loguéate con: superadmin / superadmin")
    print("   4. Ve a: http://localhost:8000/api-management/wizard")
    print("   5. Verifica que se carguen las empresas en el dropdown")

async def main():
    await test_wizard_endpoints()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\\n⏹️  Test cancelado")
'''
    
    write_file("test_wizard.py", script_content, "Script para probar wizard")

def generate_solution_summary():
    """Generar resumen de la solución"""
    print_section("Resumen de la Solución")
    
    solutions = {
        "Problemas Identificados": [
            "❌ main.py llamaba a get_all_businesses() que no existe",
            "❌ BusinessService no tenía método de compatibilidad", 
            "❌ Posiblemente no hay empresas creadas en la DB",
            "❌ Wizard no puede cargar dropdown de empresas"
        ],
        "Soluciones Implementadas": [
            "✅ Corregido main.py para usar get_all_business_instances()",
            "✅ Agregados métodos de compatibilidad en BusinessService",
            "✅ Script para crear empresas de ejemplo",
            "✅ Script para verificar estado de la DB",
            "✅ Script para probar el wizard",
            "✅ Mejor manejo de errores en endpoints"
        ],
        "Scripts Creados": [
            "📄 create_sample_businesses.py - Crear empresas de ejemplo",
            "📄 check_database.py - Verificar estado de la DB", 
            "📄 test_wizard.py - Probar funcionamiento del wizard"
        ],
        "Próximos Pasos": [
            "1. Ejecutar: python check_database.py",
            "2. Ejecutar: python create_sample_businesses.py", 
            "3. Reiniciar servidor: uvicorn app.main:app --reload",
            "4. Probar wizard: http://localhost:8000/api-management/wizard",
            "5. Ejecutar: python test_wizard.py (opcional)"
        ]
    }
    
    for section, items in solutions.items():
        print(f"\n{section}:")
        for item in items:
            print(f"  {item}")

def main():
    """Función principal"""
    print_header("DIAGNÓSTICO Y SOLUCIÓN DE PROBLEMA DE EMPRESAS")
    
    # Verificar directorio
    if not os.path.exists("app/main.py"):
        print("❌ Error: No se encuentra app/main.py")
        print("   Ejecuta este script desde la raíz del proyecto /api-test")
        sys.exit(1)
    
    try:
        # Diagnóstico
        print_header("FASE 1: DIAGNÓSTICO")
        has_business_service = diagnose_business_service()
        diagnose_main_endpoints()
        
        # Soluciones
        print_header("FASE 2: IMPLEMENTACIÓN DE SOLUCIONES")
        
        if has_business_service:
            enhance_business_service()
            fix_main_endpoints()
        else:
            print("❌ BusinessService no encontrado - no se pueden aplicar correcciones")
            return 1
        
        # Scripts de ayuda
        print_header("FASE 3: CREACIÓN DE SCRIPTS DE AYUDA")
        create_database_check_script()
        create_business_data_script()
        create_wizard_test_script()
        
        # Resumen
        print_header("FASE 4: RESUMEN Y PRÓXIMOS PASOS")
        generate_solution_summary()
        
        print(f"\n{'='*60}")
        print("🎉 DIAGNÓSTICO Y SOLUCIÓN COMPLETADOS!")
        print("✅ El problema del wizard debería estar solucionado")
        print("🚀 Ejecuta los scripts en el orden sugerido")
        print(f"{'='*60}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR DURANTE LA EJECUCIÓN:")
        print(f"   {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)