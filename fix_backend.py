#!/usr/bin/env python3
"""Solución simple - Reemplazar endpoint problemático"""

def fix_main_py():
    """Arreglar main.py reemplazando el endpoint problemático"""
    
    # Leer archivo
    with open("app/main.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Buscar y reemplazar el endpoint problemático
    old_endpoint = '''@app.get("/")
async def root():
    """Endpoint raíz - redirigir al frontend"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard", status_code=302)'''
    
    new_endpoint = '''# @app.get("/")  # COMENTADO - Manejado por frontend auth router
# async def root():
#     """Endpoint raíz - redirigir al frontend"""
#     from fastapi.responses import RedirectResponse
#     return RedirectResponse(url="/dashboard", status_code=302)'''
    
    # Reemplazar
    if old_endpoint in content:
        content = content.replace(old_endpoint, new_endpoint)
        
        # Escribir archivo
        with open("app/main.py", "w", encoding="utf-8") as f:
            f.write(content)
        
        print("✅ Endpoint / problemático comentado")
        return True
    else:
        print("⚠️ No se encontró el endpoint problemático")
        return False

def main():
    """Función principal"""
    print("🔧 Arreglando redirección raíz...")
    
    if fix_main_py():
        print("\n✅ ¡Problema solucionado!")
        print("\nAhora el flujo será:")
        print("  / → frontend auth router → /login (si no auth) o /dashboard (si auth)")
    else:
        print("\n⚠️ No se pudo arreglar automáticamente")
        print("Comenta manualmente el endpoint @app.get('/') en main.py")
    
    print("\n📝 Próximos pasos:")
    print("1. python run.py")
    print("2. Ve a: http://localhost:8000")
    print("3. ¡Deberías ver el login!")

if __name__ == "__main__":
    main()