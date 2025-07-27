#!/usr/bin/env python3
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
        print("\n🏢 Verificando BusinessService...")
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
        print(f"\n👥 Usuarios en sistema: {users_count}")
        
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
        print("\n✅ Verificación completada")
    else:
        print("\n❌ Problemas encontrados en la base de datos")
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
