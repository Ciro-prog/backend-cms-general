# ================================
# setup_mvp.py - SCRIPT PRINCIPAL PARA CONFIGURAR TODO
# ================================

#!/usr/bin/env python3
"""
Script para configurar MVP completo del CMS Dinámico
"""

import asyncio
import sys
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def setup_mvp():
    """Configurar MVP completo"""
    print("🚀 Configurando CMS Dinámico MVP...")
    
    # 1. Verificar dependencias
    print("\n📦 Verificando dependencias...")
    await check_dependencies()
    
    # 2. Configurar base de datos
    print("\n🗄️ Configurando base de datos...")
    await setup_database()
    
    # 3. Inicializar datos por defecto
    print("\n📊 Inicializando datos por defecto...")
    await initialize_default_data()
    
    # 4. Crear APIs de ejemplo
    print("\n🔌 Creando APIs de ejemplo...")
    await create_example_apis()
    
    # 5. Crear componentes de ejemplo
    print("\n🎨 Creando componentes de ejemplo...")
    await create_example_components()
    
    print("\n✅ ¡MVP configurado exitosamente!")
    print("\n📝 Próximos pasos:")
    print("1. Ejecutar: python run.py")
    print("2. Abrir: http://localhost:8000")
    print("3. Login admin: superadmin / superadmin")
    print("4. Ver API docs: http://localhost:8000/docs")

async def check_dependencies():
    """Verificar que las dependencias estén instaladas"""
    required_packages = ['fastapi', 'motor', 'aiohttp', 'pydantic']
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Ejecuta: pip install {package}")
            sys.exit(1)

async def setup_database():
    """Configurar base de datos"""
    try:
        # Importar después de verificar dependencias
        from app.database import connect_to_mongo
        await connect_to_mongo()
        print("✅ Base de datos configurada")
    except Exception as e:
        print(f"❌ Error configurando base de datos: {e}")
        sys.exit(1)

async def initialize_default_data():
    """Inicializar datos por defecto"""
    try:
        from app.database import get_database
        from app.services.business_service import BusinessService
        
        db = get_database()
        service = BusinessService(db)
        await service.initialize_default_data()
        print("✅ Datos por defecto inicializados")
    except Exception as e:
        print(f"❌ Error inicializando datos: {e}")
        sys.exit(1)

async def create_example_apis():
    """Crear APIs de ejemplo"""
    try:
        from app.database import get_database
        from app.services.api_service import APIService
        from app.models.api_integration import EXAMPLE_JSONPLACEHOLDER_API, APIConfiguration
        
        db = get_database()
        service = APIService(db)
        
        # Crear API de JSONPlaceholder
        api_config = APIConfiguration(
            api_id="jsonplaceholder_users",
            **EXAMPLE_JSONPLACEHOLDER_API.dict()
        )
        
        await service.create_api_config(api_config)
        print("✅ API de ejemplo creada (JSONPlaceholder)")
    except Exception as e:
        print(f"⚠️ Error creando APIs de ejemplo: {e}")

async def create_example_components():
    """Crear componentes de ejemplo"""
    try:
        from app.database import get_database
        from app.models.api_integration import EXAMPLE_USERS_TABLE_COMPONENT, DynamicComponent
        
        db = get_database()
        
        # Crear componente de tabla de usuarios
        component = DynamicComponent(
            component_id="users_table_component",
            **EXAMPLE_USERS_TABLE_COMPONENT.dict()
        )
        
        await db.dynamic_components.insert_one(component.dict())
        print("✅ Componente de ejemplo creado (Tabla Usuarios)")
    except Exception as e:
        print(f"⚠️ Error creando componentes de ejemplo: {e}")

if __name__ == "__main__":
    asyncio.run(setup_mvp())
