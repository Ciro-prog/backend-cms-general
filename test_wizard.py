#!/usr/bin/env python3
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
                print(f"\n🔗 Probando: {endpoint['description']}")
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
    
    print("\n💡 Para probar completamente:")
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
        print("\n⏹️  Test cancelado")
