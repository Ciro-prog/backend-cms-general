# ================================
# Middleware de autenticación simple
# ================================

async def simple_auth_middleware(request: Request, call_next):
    """Middleware de autenticación simple basado en sesiones"""
    
    # Rutas públicas (no requieren autenticación)
    public_paths = [
        "/", 
        "/login", 
        "/health", 
        "/docs", 
        "/openapi.json", 
        "/redoc",
        "/static"
    ]
    
    path = request.url.path
    
    # Permitir acceso a rutas públicas
    if any(path.startswith(public_path) for public_path in public_paths):
        return await call_next(request)
    
    # Verificar autenticación para rutas protegidas
    authenticated = False
    if hasattr(request, 'session'):
        authenticated = request.session.get("authenticated", False)
    
    # Si no está autenticado y trata de acceder a ruta protegida
    if not authenticated:
        # Si es una petición AJAX/API, devolver 401
        if path.startswith('/api/') or request.headers.get('content-type', '').startswith('application/json'):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"detail": "Autenticación requerida"}
            )
        else:
            # Si es petición HTML, redirigir a login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/login")
    
    # Usuario autenticado, continuar
    return await call_next(request)

# Agregar a main.py después de crear la app:
# app.middleware("http")(simple_auth_middleware)
