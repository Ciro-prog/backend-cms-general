#!/usr/bin/env python3
"""
CMS Dinámico - Frontend para Usuarios Finales
Puerto: 3001
Backend API: localhost:8000
"""

import os
import httpx
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, Form, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Agregar estos imports al inicio del archivo
from fastapi import FastAPI, Request, Form, HTTPException, Depends, status, Query
from typing import Optional, Dict, Any, List

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración
BACKEND_URL = "http://localhost:8000"
SECRET_KEY = "your-secret-key-for-sessions-change-in-production"

# Crear aplicación FastAPI
app = FastAPI(
    title="CMS Dinámico - Dashboard Usuario Final",
    description="Dashboard personalizado para usuarios finales",
    version="1.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Configurar templates y archivos estáticos
templates = Jinja2Templates(directory="templates")

# Crear directorio static si no existe
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Cliente HTTP para comunicarse con el backend
async def get_backend_client():
    return httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0)

# ================================
# UTILIDADES DE AUTENTICACIÓN
# ================================

# Usuarios demo hardcodeados
DEMO_USERS = {
    "admin": {
        "password": "admin",
        "role": "admin", 
        "business_id": "isp_telconorte",
        "name": "Admin Usuario"
    },
    "tecnico": {
        "password": "tecnico",
        "role": "tecnico",
        "business_id": "isp_telconorte", 
        "name": "Técnico Soporte"
    },
    "usuario": {
        "password": "usuario",
        "role": "user",
        "business_id": "isp_telconorte",
        "name": "Usuario Final"
    },
    "superadmin": {
        "password": "superadmin",
        "role": "super_admin",
        "business_id": None,
        "name": "Super Administrador"
    }
}

def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Obtiene el usuario actual de la sesión"""
    return request.session.get("user")

def require_auth(request: Request):
    """Dependency que requiere autenticación"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no autenticado"
        )
    return user

# ================================
# RUTAS DE AUTENTICACIÓN
# ================================

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Página de inicio - redirige al dashboard o login"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/login", status_code=302)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Página de login"""
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "demo_users": DEMO_USERS
    })

@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Procesar login"""
    # Verificar credenciales
    if username in DEMO_USERS and DEMO_USERS[username]["password"] == password:
        user_data = DEMO_USERS[username].copy()
        user_data["username"] = username
        user_data["logged_in_at"] = datetime.now().isoformat()
        
        # Guardar en sesión
        request.session["user"] = user_data
        
        logger.info(f"✅ Login exitoso: {username} ({user_data['role']})")
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        logger.warning(f"❌ Login fallido: {username}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Usuario o contraseña incorrectos",
            "demo_users": DEMO_USERS
        })

@app.get("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    username = request.session.get("user", {}).get("username", "unknown")
    request.session.clear()
    logger.info(f"👋 Logout: {username}")
    return RedirectResponse(url="/login", status_code=302)

# ================================
# DASHBOARD PRINCIPAL  
# ================================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user: dict = Depends(require_auth)):
    """Dashboard principal del usuario"""
    
    # Si es super_admin sin business_id, mostrar vista de admin general
    if user["role"] == "super_admin" and not user["business_id"]:
        return await admin_dashboard(request, user)
    
    # Para usuarios con business_id, mostrar dashboard personalizado
    if user["business_id"]:
        return await business_dashboard(request, user, user["business_id"])
    
    # Fallback - sin business asignado
    return templates.TemplateResponse("no_business.html", {
        "request": request,
        "user": user
    })

async def admin_dashboard(request: Request, user: dict):
    """Dashboard para super admin"""
    try:
        async with httpx.AsyncClient() as client:
            # Obtener estadísticas generales
            stats_response = await client.get(f"{BACKEND_URL}/api/admin/stats")
            stats = stats_response.json() if stats_response.status_code == 200 else {}
            
            # Obtener lista de businesses
            businesses_response = await client.get(f"{BACKEND_URL}/api/admin/businesses")
            businesses = businesses_response.json() if businesses_response.status_code == 200 else []
            
    except Exception as e:
        logger.error(f"Error obteniendo datos admin: {e}")
        stats = {}
        businesses = []
    
    return templates.TemplateResponse("admin_dashboard.html", {
        "request": request,
        "user": user,
        "stats": stats,
        "businesses": businesses
    })
def safe_get_list_data(response_data, max_items=10):
    """Helper para extraer datos de lista de diferentes estructuras de respuesta"""
    if not response_data:
        return []
    
    # Si ya es una lista
    if isinstance(response_data, list):
        return response_data[:max_items]
    
    # Si es un dict, intentar extraer la lista
    if isinstance(response_data, dict):
        # Estructura: {"data": {"items": [...]}}
        if "data" in response_data and isinstance(response_data["data"], dict):
            if "items" in response_data["data"] and isinstance(response_data["data"]["items"], list):
                return response_data["data"]["items"][:max_items]
        
        # Estructura: {"data": [...]}
        if "data" in response_data and isinstance(response_data["data"], list):
            return response_data["data"][:max_items]
        
        # Estructura: {"success": true, "items": [...]}
        if "items" in response_data and isinstance(response_data["items"], list):
            return response_data["items"][:max_items]
    
    return []

async def business_dashboard(request: Request, user: dict, business_id: str):
    """Dashboard personalizado para business específico"""
    try:
        async with httpx.AsyncClient() as client:
            # Obtener datos del business
            business_response = await client.get(f"{BACKEND_URL}/api/admin/businesses/{business_id}")
            business_data = business_response.json() if business_response.status_code == 200 else {}
            
            # Obtener datos del dashboard
            dashboard_response = await client.get(f"{BACKEND_URL}/api/business/dashboard/{business_id}")
            dashboard_data = dashboard_response.json() if dashboard_response.status_code == 200 else {}
            
            # Obtener datos de clientes (ejemplo) - FIX AQUÍ
            clientes_response = await client.get(f"{BACKEND_URL}/api/business/entities/{business_id}/clientes")
            
            # FIX: Manejar correctamente la estructura de datos
            clientes_data = []
            if clientes_response.status_code == 200:
                response_json = clientes_response.json()
                logger.info(f"🔍 Estructura de clientes_data: {type(response_json)}")
                logger.info(f"🔍 Contenido: {response_json}")
                
                # Extraer items según la estructura de la respuesta
                if isinstance(response_json, dict):
                    if "data" in response_json and isinstance(response_json["data"], dict):
                        if "items" in response_json["data"]:
                            clientes_data = response_json["data"]["items"]
                        else:
                            clientes_data = list(response_json["data"].values())
                    elif "data" in response_json and isinstance(response_json["data"], list):
                        clientes_data = response_json["data"]
                    elif isinstance(response_json, list):
                        clientes_data = response_json
                elif isinstance(response_json, list):
                    clientes_data = response_json
            
            # Asegurar que clientes_data es una lista
            if not isinstance(clientes_data, list):
                logger.warning(f"⚠️ clientes_data no es lista: {type(clientes_data)}")
                clientes_data = []
            
    except Exception as e:
        logger.error(f"Error obteniendo datos business {business_id}: {e}")
        business_data = {"nombre": "Business no encontrado"}
        dashboard_data = {}
        clientes_data = []
    
    return templates.TemplateResponse("business_dashboard.html", {
        "request": request,
        "user": user,
        "business": business_data,
        "dashboard_data": dashboard_data,
        "clientes": clientes_data[:10] if clientes_data else [],  # FIX: Solo slice si hay datos
        "business_id": business_id
    })

# ================================
# RUTAS DE DATOS Y API
# ================================

@app.get("/api/business/{business_id}/clientes")
async def get_clientes(business_id: str, user: dict = Depends(require_auth)):
    """Obtener lista de clientes"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/business/entities/{business_id}/clientes")
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo clientes: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo datos")

@app.get("/api/business/{business_id}/stats")
async def get_business_stats(business_id: str, user: dict = Depends(require_auth)):
    """Obtener estadísticas del business"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/business/dashboard/{business_id}")
            return response.json()
    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo estadísticas")
    

# ================================
# HEALTH CHECK
# ================================

@app.get("/health")
async def health_check():
    """Health check del frontend"""
    try:
        async with httpx.AsyncClient() as client:
            backend_response = await client.get(f"{BACKEND_URL}/health")
            backend_status = "✅ Conectado" if backend_response.status_code == 200 else "❌ Error"
    except:
        backend_status = "❌ No disponible"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "services": {
            "frontend": "✅ Funcionando",
            "backend": backend_status,
            "port": 3001
        }
    }
# ================================
# CRUD DINÁMICO
# ================================

# ACTUALIZAR la ruta en cms-frontend-usuarios/main.py

@app.get("/crud", response_class=HTMLResponse)
async def crud_dinamico(
    request: Request, 
    user: dict = Depends(require_auth),
    entity: Optional[str] = None,
    view: Optional[str] = None
):
    """CRUD Dinámico para gestión de entidades"""
    return templates.TemplateResponse("crud_dinamico.html", {
        "request": request,
        "user": user,
        "business_id": user.get("business_id"),
        "preselected_entity": entity,
        "view_mode": view
    })

# ================================
# SERVIDOR
# ================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando CMS Dashboard Usuario Final...")
    logger.info("📍 URL: http://localhost:3001")
    logger.info("🔗 Backend: http://localhost:8000")
    logger.info("👥 Users demo: admin/admin, tecnico/tecnico, usuario/usuario")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3001,
        reload=True,
        log_level="info"
    )
    # ================================
# AGREGAR AL FINAL DE cms-frontend-usuarios/main.py
# ================================

# ================================
# CRUD DINÁMICO - API ENDPOINTS
# ================================

@app.get("/api/crud/{business_id}/entities")
async def get_entities_config(
    business_id: str, 
    user: dict = Depends(require_auth)
):
    """Obtener configuración de entidades disponibles"""
    logger.info(f"🔍 [FRONTEND] Solicitando entidades para {business_id}")
    
    try:
        async with httpx.AsyncClient() as client:
            # Verificar backend
            try:
                health_response = await client.get(f"{BACKEND_URL}/health", timeout=5.0)
                logger.info(f"✅ Backend disponible: {health_response.status_code}")
            except Exception as e:
                logger.error(f"❌ Backend no disponible: {e}")
                return {"success": False, "error": "Backend no disponible en puerto 8000"}
            
            # Obtener configuraciones del backend
            entities_url = f"{BACKEND_URL}/api/admin/entities/{business_id}"
            logger.info(f"📡 Llamando a: {entities_url}")
            
            response = await client.get(entities_url, timeout=10.0)
            logger.info(f"📥 Response: {response.status_code}")
            
            if response.status_code == 200:
                entities_data = response.json()
                logger.info(f"📄 Raw data: {entities_data}")
                
                # MANEJAR DIFERENTES FORMATOS DE RESPUESTA
                entities_list = []
                
                if isinstance(entities_data, list):
                    # Backend devuelve lista directa: [{"entidad": "clientes"}, ...]
                    entities_list = entities_data
                    logger.info(f"📋 Formato: Lista directa con {len(entities_list)} entidades")
                    
                elif isinstance(entities_data, dict):
                    if not entities_data.get("success", True):
                        logger.warning(f"⚠️ Backend error: {entities_data.get('error')}")
                        return {"success": False, "error": entities_data.get("error", "Error del backend")}
                    
                    # Backend devuelve objeto: {"success": true, "data": [...]}
                    entities_list = entities_data.get("data", [])
                    logger.info(f"📋 Formato: Objeto con {len(entities_list)} entidades")
                
                else:
                    logger.error(f"❌ Formato inesperado: {type(entities_data)}")
                    return {"success": False, "error": f"Formato inesperado del backend: {type(entities_data)}"}
                
                # Transformar datos
                entities_config = {}
                
                for entity in entities_list:
                    entity_name = entity.get("entidad")
                    if not entity_name:
                        continue
                    
                    campos = entity.get("configuracion", {}).get("campos", [])
                    
                    config = {
                        "titulo": f"Gestión de {entity_name.title()}",
                        "titulo_singular": entity_name.rstrip('s').title(),
                        "descripcion": entity.get("descripcion", f"Administra {entity_name}"),
                        "permisos": {
                            "crear": True,
                            "editar": True,
                            "eliminar": user.get("role") == "admin",
                            "exportar": True
                        },
                        "campos_tabla": [
                            {
                                "campo": campo["campo"],
                                "nombre": campo.get("nombre", campo["campo"].title()),
                                "tipo": campo.get("tipo", "text")
                            }
                            for campo in campos if campo.get("mostrar_en_tabla", True)
                        ],
                        "campos_form": [
                            {
                                "campo": campo["campo"],
                                "nombre": campo.get("nombre", campo["campo"].title()),
                                "tipo": campo.get("tipo", "text"),
                                "obligatorio": campo.get("obligatorio", False),
                                "placeholder": campo.get("placeholder", ""),
                                "opciones": campo.get("opciones", [])
                            }
                            for campo in campos
                        ],
                        "campos_filtros": [
                            {
                                "campo": campo["campo"],
                                "nombre": campo.get("nombre", campo["campo"].title()),
                                "opciones": campo.get("opciones", [])
                            }
                            for campo in campos if campo.get("tipo") == "select" and campo.get("opciones")
                        ]
                    }
                    
                    entities_config[entity_name] = config
                
                logger.info(f"✅ Entidades procesadas: {list(entities_config.keys())}")
                return {"success": True, "data": entities_config}
                
            else:
                error_text = response.text
                logger.error(f"❌ Backend error {response.status_code}: {error_text}")
                return {"success": False, "error": f"Error del backend: HTTP {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": f"Error de conexión: {str(e)}"}

@app.get("/api/crud/{business_id}/{entity_name}")
async def get_entity_data(
    business_id: str,
    entity_name: str,
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    filters: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    sort_order: str = Query("asc"),
    user: dict = Depends(require_auth)
):
    """Obtener datos de una entidad con paginación"""
    logger.info(f"🔍 [FRONTEND] Datos: {entity_name} para {business_id}")
    
    try:
        if user["business_id"] != business_id and user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        async with httpx.AsyncClient() as client:
            params = {
                "page": page,
                "per_page": per_page,
                "sort_order": sort_order
            }
            
            if filters:
                params["filters"] = filters
            if sort_by:
                params["sort_by"] = sort_by
            
            url = f"{BACKEND_URL}/api/business/entities/{business_id}/{entity_name}"
            logger.info(f"📡 Backend URL: {url}")
            
            response = await client.get(url, params=params, timeout=10.0)
            logger.info(f"📥 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Datos: {len(data.get('data', {}).get('items', []))} items")
                return data
            else:
                logger.warning(f"❌ Error {response.status_code}: {response.text}")
                return {"success": False, "error": f"Error: HTTP {response.status_code}"}
                
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/crud/{business_id}/{entity_name}")
async def create_entity_item(
    business_id: str,
    entity_name: str,
    item_data: Dict[str, Any],
    user: dict = Depends(require_auth)
):
    """Crear nuevo item"""
    try:
        if user["business_id"] != business_id and user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/api/business/entities/{business_id}/{entity_name}",
                json=item_data,
                timeout=10.0
            )
            
            return response.json() if response.status_code == 200 else {"success": False, "error": "Error creando"}
            
    except Exception as e:
        logger.error(f"❌ Error create: {e}")
        return {"success": False, "error": str(e)}

@app.put("/api/crud/{business_id}/{entity_name}/{item_id}")
async def update_entity_item(
    business_id: str,
    entity_name: str,
    item_id: str,
    item_data: Dict[str, Any],
    user: dict = Depends(require_auth)
):
    """Actualizar item"""
    try:
        if user["business_id"] != business_id and user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BACKEND_URL}/api/business/entities/{business_id}/{entity_name}/{item_id}",
                json=item_data,
                timeout=10.0
            )
            
            return response.json() if response.status_code == 200 else {"success": False, "error": "Error actualizando"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/crud/{business_id}/{entity_name}/{item_id}")
async def delete_entity_item(
    business_id: str,
    entity_name: str,
    item_id: str,
    user: dict = Depends(require_auth)
):
    """Eliminar item"""
    try:
        if user["business_id"] != business_id and user["role"] != "super_admin":
            raise HTTPException(status_code=403, detail="Acceso denegado")
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{BACKEND_URL}/api/business/entities/{business_id}/{entity_name}/{item_id}",
                timeout=10.0
            )
            
            return response.json() if response.status_code == 200 else {"success": False, "error": "Error eliminando"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

# ================================
# HELPER FUNCTIONS
# ================================

def _check_permission(user: dict, entity: dict, action: str) -> bool:
    """Verificar permisos según rol del usuario"""
    user_role = user.get("role", "user")
    
    # Super admin puede todo
    if user_role == "super_admin":
        return True
    
    # Configuración de permisos por defecto según roles
    permissions = {
        "admin": {"crear": True, "editar": True, "eliminar": True},
        "tecnico": {"crear": True, "editar": True, "eliminar": False},
        "user": {"crear": False, "editar": False, "eliminar": False}
    }
    
    return permissions.get(user_role, {}).get(action, False)

def _extract_table_fields(entity: dict) -> List[Dict]:
    """Extraer campos para tabla desde configuración de entidad"""
    campos = entity.get("configuracion", {}).get("campos", [])
    
    table_fields = []
    for campo in campos:
        if campo.get("mostrar_en_tabla", True):  # Por defecto mostrar
            table_fields.append({
                "campo": campo["campo"],
                "nombre": campo.get("nombre", campo["campo"].title()),
                "tipo": campo.get("tipo", "text")
            })
    
    return table_fields

def _extract_form_fields(entity: dict) -> List[Dict]:
    """Extraer campos para formulario"""
    campos = entity.get("configuracion", {}).get("campos", [])
    
    form_fields = []
    for campo in campos:
        field = {
            "campo": campo["campo"],
            "nombre": campo.get("nombre", campo["campo"].title()),
            "tipo": campo.get("tipo", "text"),
            "obligatorio": campo.get("obligatorio", False),
            "placeholder": campo.get("placeholder", ""),
            "descripcion": campo.get("descripcion", "")
        }
        
        # Agregar opciones si es select
        if campo.get("opciones"):
            field["opciones"] = campo["opciones"]
        
        form_fields.append(field)
    
    return form_fields

def _extract_filter_fields(entity: dict) -> List[Dict]:
    """Extraer campos para filtros"""
    campos = entity.get("configuracion", {}).get("campos", [])
    
    filter_fields = []
    for campo in campos:
        if campo.get("tipo") == "select" and campo.get("opciones"):
            filter_fields.append({
                "campo": campo["campo"],
                "nombre": campo.get("nombre", campo["campo"].title()),
                "opciones": campo["opciones"]
            })
    
    return filter_fields