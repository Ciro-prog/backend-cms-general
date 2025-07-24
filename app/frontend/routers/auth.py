# ================================
# ARCHIVO: app/frontend/routers/auth.py
# RUTA: app/frontend/routers/auth.py
# 🔧 CORREGIDO: Debe exportar 'router'
# ================================

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import logging

from ..auth import authenticate_user, login_user, logout_user, get_current_user

router = APIRouter()  # ← DEBE ESTAR PRESENTE Y SER LLAMADO 'router'
templates = Jinja2Templates(directory="app/frontend/templates")
logger = logging.getLogger(__name__)

@router.get("/", response_class=HTMLResponse)
async def root_redirect(request: Request):
    """Ruta raíz - redirigir según autenticación"""
    current_user = get_current_user(request)
    
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/login", status_code=302)

@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    """Mostrar formulario de login"""
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    error_message = None
    if hasattr(request, 'session') and "login_error" in request.session:
        error_message = request.session.pop("login_error")
    
    return templates.TemplateResponse("auth/login.html", {
        "request": request,
        "error": error_message
    })

@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Procesar login"""
    user = authenticate_user(username, password)
    
    if user:
        login_user(request, user)
        logger.info(f"Usuario {username} logueado exitosamente")
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        if not hasattr(request, 'session'):
            request.session = {}
        request.session["login_error"] = "Usuario o contraseña incorrectos"
        return RedirectResponse(url="/login", status_code=302)

@router.post("/logout")
async def logout(request: Request):
    """Cerrar sesión"""
    current_user = get_current_user(request)
    if current_user:
        logger.info(f"Usuario {current_user['username']} cerró sesión")
    
    logout_user(request)
    return RedirectResponse(url="/login", status_code=302)
