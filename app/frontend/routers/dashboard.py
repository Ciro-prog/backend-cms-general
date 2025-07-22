# ================================
# app/frontend/routers/dashboard.py - BÁSICO
# ================================

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..auth import require_auth

router = APIRouter()
templates = Jinja2Templates(directory="app/frontend/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: dict = Depends(require_auth)):
    """Dashboard básico"""
    
    # HTML básico inline por ahora
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard - CMS Dinámico</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100">
        <div class="container mx-auto p-8">
            <div class="bg-white rounded-lg shadow p-6">
                <h1 class="text-3xl font-bold text-gray-800 mb-4">🎉 ¡Bienvenido al CMS Dinámico!</h1>
                
                <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
                    <strong>✅ ¡Sistema funcionando correctamente!</strong>
                </div>
                
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div class="bg-blue-50 p-4 rounded">
                        <h3 class="font-bold text-blue-800">👤 Usuario Actual</h3>
                        <p><strong>Nombre:</strong> {current_user.get('name', 'N/A')}</p>
                        <p><strong>Usuario:</strong> {current_user.get('username', 'N/A')}</p>
                        <p><strong>Rol:</strong> {current_user.get('role', 'N/A')}</p>
                    </div>
                    
                    <div class="bg-yellow-50 p-4 rounded">
                        <h3 class="font-bold text-yellow-800">🚀 Sistema</h3>
                        <p><strong>Estado:</strong> ✅ Operativo</p>
                        <p><strong>Versión:</strong> 1.0.0</p>
                        <p><strong>Base de datos:</strong> ✅ Conectada</p>
                    </div>
                </div>
                
                <div class="mt-6 flex space-x-4">
                    <a href="/api/docs" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                        📚 API Docs
                    </a>
                    <form method="post" action="/logout" style="display: inline;">
                        <button type="submit" class="bg-red-500 text-white px-4 py-2 rounded hover:bg-red-600">
                            🚪 Cerrar Sesión
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html_content)
