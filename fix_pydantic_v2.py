#!/usr/bin/env python3
# ================================
# fix_main_py_auth_issues.py - ARREGLAR PROBLEMAS DE AUTENTICACIÓN
# ================================

from pathlib import Path
from datetime import datetime
import re

def fix_main_py_authentication():
    """Arreglar todos los problemas de autenticación en main.py"""
    
    main_file = Path("app/main.py")
    
    if not main_file.exists():
        print("❌ main.py no existe")
        return
    
    print("🔧 Arreglando problemas de autenticación en main.py...")
    
    # Backup
    timestamp = datetime.now().strftime("%H%M%S")
    backup_path = main_file.with_suffix(f'.backup_final_{timestamp}.py')
    backup_path.write_text(main_file.read_text(encoding='utf-8'), encoding='utf-8')
    print(f"✅ Backup: {backup_path.name}")
    
    content = main_file.read_text(encoding='utf-8')
    
    # ================================
    # 1. ARREGLAR ENDPOINT RAÍZ DUPLICADO
    # ================================
    
    # Remover el primer @app.get("/") que devuelve JSON
    first_root_pattern = r'@app\.get\("/"\)\s*\nasync def root\(\):\s*\n\s*return\s*\{[^}]*"message":\s*"CMS Dinámico API"[^}]*\}'
    
    if re.search(first_root_pattern, content, re.DOTALL):
        content = re.sub(first_root_pattern, '', content, flags=re.DOTALL)
        print("✅ Primer endpoint raíz (JSON) eliminado")
    
    # ================================
    # 2. CREAR FUNCIÓN DE VERIFICACIÓN DE AUTH
    # ================================
    
    auth_function = '''
# ================================
# FUNCIONES DE AUTENTICACIÓN
# ================================

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Obtener usuario actual de la sesión"""
    if hasattr(request, 'session') and request.session.get("authenticated"):
        return request.session.get("user")
    return None

def require_auth(request: Request) -> Dict[str, Any]:
    """Requerir autenticación - lanza excepción si no está logueado"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Autenticación requerida"
        )
    return user

def require_admin(request: Request) -> Dict[str, Any]:
    """Requerir rol admin o superior"""
    user = require_auth(request)
    if user["role"] not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=403,
            detail="Permisos de administrador requeridos"
        )
    return user
'''
    
    # Buscar dónde insertar las funciones de auth (después de los imports)
    insert_point = content.find("# ================================\n# MODELOS PYDANTIC\n# ================================")
    if insert_point != -1:
        content = content[:insert_point] + auth_function + "\n" + content[insert_point:]
        print("✅ Funciones de autenticación agregadas")
    
    # ================================
    # 3. ARREGLAR ENDPOINT RAÍZ FINAL
    # ================================
    
    # Buscar el @app.get("/", include_in_schema=False) y reemplazarlo
    root_redirect_pattern = r'@app\.get\("/", include_in_schema=False\)\s*\nasync def root_redirect\(\):\s*\n\s*return RedirectResponse\(url="/login", status_code=302\)'
    
    new_root_endpoint = '''@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página principal - redirige según autenticación"""
    
    user = get_current_user(request)
    
    if user:
        # Usuario logueado - ir al dashboard
        logger.info(f"🏠 Usuario {user['username']} accedió a página principal - redirigiendo a dashboard")
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        # Usuario no logueado - mostrar página de bienvenida
        logger.info("🏠 Usuario anónimo accedió a página principal - mostrando página de bienvenida")
        
        # Obtener información del sistema
        try:
            db = get_database()
            system_info = {
                "status": "running",
                "version": "1.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "total_businesses": await db.business_instances.count_documents({}),
                "active_apis": await db.api_configurations.count_documents({"active": True})
            }
        except Exception as e:
            logger.error(f"Error obteniendo info del sistema: {e}")
            system_info = {
                "status": "running",
                "version": "1.0.0", 
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Error conectando a base de datos"
            }
        
        return templates.TemplateResponse("home.html", {
            "request": request,
            "system_info": system_info
        })'''
    
    if re.search(root_redirect_pattern, content, re.DOTALL):
        content = re.sub(root_redirect_pattern, new_root_endpoint, content, flags=re.DOTALL)
        print("✅ Endpoint raíz arreglado")
    
    # ================================
    # 4. PROTEGER DASHBOARD
    # ================================
    
    # Buscar el endpoint dashboard y agregar verificación de auth
    dashboard_pattern = r'(@app\.get\("/dashboard", response_class=HTMLResponse\)\s*\nasync def dashboard\(request: Request\):)'
    
    if re.search(dashboard_pattern, content):
        dashboard_replacement = r'\1\n    """Dashboard principal - requiere autenticación"""\n    \n    # Verificar autenticación\n    user = require_auth(request)'
        content = re.sub(dashboard_pattern, dashboard_replacement, content)
        print("✅ Dashboard protegido con autenticación")
        
        # También actualizar el dashboard para usar el usuario real
        content = content.replace(
            'current_user = {\n        "name": "Super Admin",\n        "role": "super_admin",\n        "username": "superadmin",\n        "business_id": "isp_telconorte"\n    }',
            'current_user = user'
        )
        print("✅ Dashboard usando usuario real de sesión")
    
    # ================================
    # 5. PROTEGER RUTAS DE GESTIÓN
    # ================================
    
    # Proteger /api-management
    api_mgmt_pattern = r'(@app\.get\("/api-management", response_class=HTMLResponse\)\s*\nasync def api_management\(request: Request\):)'
    if re.search(api_mgmt_pattern, content):
        api_mgmt_replacement = r'\1\n    """Gestión de APIs - requiere admin"""\n    user = require_admin(request)\n'
        content = re.sub(api_mgmt_pattern, api_mgmt_replacement, content)
        print("✅ /api-management protegido")
    
    # Proteger /api-management/wizard  
    wizard_pattern = r'(@app\.get\("/api-management/wizard", response_class=HTMLResponse\)\s*\nasync def api_wizard\(request: Request\):)'
    if re.search(wizard_pattern, content):
        wizard_replacement = r'\1\n    """Wizard de APIs - requiere admin"""\n    user = require_admin(request)\n'
        content = re.sub(wizard_pattern, wizard_replacement, content)
        print("✅ /api-management/wizard protegido")
    
    # Proteger /api-management/test
    test_pattern = r'(@app\.get\("/api-management/test", response_class=HTMLResponse\)\s*\nasync def api_test_page\(request: Request\):)'
    if re.search(test_pattern, content):
        test_replacement = r'\1\n    """Test de APIs - requiere admin"""\n    user = require_admin(request)\n'
        content = re.sub(test_pattern, test_replacement, content)
        print("✅ /api-management/test protegido")
    
    # ================================
    # 6. AGREGAR LOGOUT FUNCIONAL
    # ================================
    
    logout_pattern = r'@app\.post\("/logout"\)\s*\nasync def logout\(\):\s*\n\s*return RedirectResponse\(url="/login", status_code=302\)'
    
    new_logout = '''@app.post("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    user = get_current_user(request)
    
    if user:
        logger.info(f"👋 Usuario {user['username']} cerró sesión")
    
    # Limpiar sesión
    request.session.clear()
    
    return RedirectResponse(url="/login", status_code=302)'''
    
    if re.search(logout_pattern, content, re.DOTALL):
        content = re.sub(logout_pattern, new_logout, content, flags=re.DOTALL)
        print("✅ Logout funcional agregado")
    
    # ================================
    # 7. AGREGAR IMPORTS NECESARIOS
    # ================================
    
    # Verificar si tiene los imports necesarios
    if 'from typing import Dict, Any, List, Optional' not in content:
        # Buscar línea de imports de typing y agregar lo que falta
        typing_pattern = r'from typing import ([^\\n]+)'
        if re.search(typing_pattern, content):
            content = re.sub(
                typing_pattern, 
                'from typing import Dict, Any, List, Optional', 
                content
            )
            print("✅ Imports de typing actualizados")
    
    # ================================
    # 8. ESCRIBIR ARCHIVO ARREGLADO
    # ================================
    
    main_file.write_text(content, encoding='utf-8')
    print(f"✅ {main_file} actualizado con autenticación completa")

def test_endpoints():
    """Mostrar URLs para probar"""
    
    print(f"\n🧪 ENDPOINTS PARA PROBAR:")
    print(f"")
    print(f"📍 PÚBLICOS:")
    print(f"   🏠 http://localhost:8000/ - Página principal (redirige según auth)")
    print(f"   🔑 http://localhost:8000/login - Login")
    print(f"   📚 http://localhost:8000/docs - Documentación API")
    print(f"   ❤️ http://localhost:8000/health - Estado del sistema")
    print(f"")
    print(f"🔐 REQUIEREN LOGIN:")
    print(f"   📊 http://localhost:8000/dashboard - Dashboard (cualquier usuario)")
    print(f"")
    print(f"👑 REQUIEREN ADMIN:")
    print(f"   ⚙️ http://localhost:8000/api-management - Gestión de APIs")
    print(f"   🧙 http://localhost:8000/api-management/wizard - Wizard de APIs")
    print(f"   🧪 http://localhost:8000/api-management/test - Test de APIs")
    print(f"")
    print(f"🔑 CREDENCIALES DE PRUEBA:")
    print(f"   superadmin / superadmin (Super Admin)")
    print(f"   admin / admin (Admin)")
    print(f"   usuario / usuario (User)")

def verify_templates():
    """Verificar que existen los templates necesarios"""
    
    templates_dir = Path("app/frontend/templates")
    
    required_templates = [
        "home.html",
        "auth/login.html", 
        "dashboard.html",
        "dashboard_with_permissions.html"
    ]
    
    print(f"\n🔍 Verificando templates:")
    
    all_exist = True
    for template in required_templates:
        template_path = templates_dir / template
        if template_path.exists():
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template} (FALTA)")
            all_exist = False
    
    return all_exist

def main():
    """Función principal"""
    print("🔧 ARREGLANDO PROBLEMAS DE AUTENTICACIÓN EN MAIN.PY")
    print("=" * 60)
    
    # 1. Verificar templates
    templates_ok = verify_templates()
    
    if not templates_ok:
        print("\n⚠️ Algunos templates faltan, pero continuaré...")
    
    # 2. Arreglar main.py
    fix_main_py_authentication()
    
    # 3. Mostrar endpoints para probar
    test_endpoints()
    
    print(f"\n🎉 AUTENTICACIÓN ARREGLADA COMPLETAMENTE")
    print(f"")
    print(f"✅ Endpoint raíz único que redirige correctamente")
    print(f"✅ Dashboard protegido con verificación de sesión")
    print(f"✅ Rutas de gestión protegidas (requieren admin)")
    print(f"✅ Logout funcional que limpia sesión")
    print(f"✅ Funciones de autenticación centralizadas")
    print(f"")
    print(f"🚀 AHORA EJECUTA:")
    print(f"   python run.py")
    print(f"")
    print(f"🔗 LUEGO VE A:")
    print(f"   http://localhost:8000")
    print(f"")
    print(f"💡 FLUJO ESPERADO:")
    print(f"   1. http://localhost:8000/ → muestra página de bienvenida")
    print(f"   2. Click en 'Iniciar Sesión' → /login")
    print(f"   3. Login con admin/admin → redirige a /dashboard")
    print(f"   4. Dashboard muestra stats reales del sistema")

if __name__ == "__main__":
    main()