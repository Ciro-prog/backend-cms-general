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
            
            # Obtener datos de clientes (ejemplo)
            clientes_response = await client.get(f"{BACKEND_URL}/api/business/entities/{business_id}/clientes")
            clientes_data = clientes_response.json() if clientes_response.status_code == 200 else []
            
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
        "clientes": clientes_data[:10],  # Primeros 10 para preview
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