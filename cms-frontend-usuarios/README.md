# 🎯 CMS Dinámico - Dashboard Usuario Final

Frontend Python con FastAPI + Jinja2 para el dashboard de usuarios finales del CMS Dinámico.

## 🚀 Características

- ✅ **Login simple** con usuarios hardcodeados para demo
- ✅ **Dashboard personalizado** según business_id del usuario  
- ✅ **Componentes dinámicos** para ISP TelcoNorte (clientes, WhatsApp, stats)
- ✅ **Diseño responsive** con Tailwind CSS
- ✅ **Comunicación con backend** vía HTTP/REST
- ✅ **Sesiones de usuario** con middleware de FastAPI

## 📋 Prerrequisitos

- **Python 3.11+**
- **Backend CMS** corriendo en `localhost:8000`
- **MongoDB** y **Redis** (para el backend)

## 🛠️ Instalación

### 1. Clonar e instalar dependencias

```bash
# Crear directorio del proyecto
mkdir cms-frontend-usuarios
cd cms-frontend-usuarios

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o 
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Crear estructura de directorios

```bash
mkdir templates static
```

### 3. Copiar archivos de template

Copia todos los archivos `.html` al directorio `templates/`:

- `templates/base.html`
- `templates/login.html`
- `templates/business_dashboard.html`
- `templates/admin_dashboard.html`
- `templates/no_business.html`

### 4. Ejecutar el frontend

```bash
python run.py
```

## 🌐 URLs Disponibles

### Frontend (Puerto 3001)
- **Dashboard:** http://localhost:3001
- **Login:** http://localhost:3001/login
- **Health:** http://localhost:3001/health

### Backend (Puerto 8000)
- **API:** http://localhost:8000
- **Docs:** http://localhost:8000/docs
- **Admin:** http://localhost:8000 (panel admin)

## 👥 Usuarios Demo

| Usuario | Contraseña | Rol | Business |
|---------|------------|-----|----------|
| `admin` | `admin` | Admin | TelcoNorte ISP |
| `tecnico` | `tecnico` | Técnico | TelcoNorte ISP |
| `usuario` | `usuario` | Usuario | TelcoNorte ISP |
| `superadmin` | `superadmin` | Super Admin | (Sin asignar) |

## 📊 Funcionalidades del Dashboard

### Dashboard Business (TelcoNorte ISP)
- **Stats Cards:** Total clientes, activos, nuevos del mes
- **Tabla Clientes:** Lista con filtros y acciones según rol
- **Panel WhatsApp:** Estado de conexión y mensajes
- **Panel N8N:** Workflows activos y estadísticas
- **Gráfico Crecimiento:** Chart.js con datos de ejemplo

### Dashboard Admin (Super Admin)
- **Estadísticas generales** del sistema
- **Lista de businesses** registrados
- **Acciones rápidas** para configuración
- **Estado del sistema** (backend, DB, integraciones)

## 🔧 Configuración

### Variables de Entorno (.env)

```env
# Backend API
BACKEND_URL=http://localhost:8000

# Frontend
SECRET_KEY=your-secret-key-for-sessions
PORT=3001

# Logging
LOG_LEVEL=INFO
```

### Personalización de Usuarios Demo

Edita el diccionario `DEMO_USERS` en `main.py`:

```python
DEMO_USERS = {
    "tu_usuario": {
        "password": "tu_password",
        "role": "admin",
        "business_id": "tu_business_id",
        "name": "Tu Nombre"
    }
}
```

## 🏗️ Estructura del Proyecto

```
cms-frontend-usuarios/
├── main.py                 # Aplicación FastAPI principal
├── run.py                  # Ejecutor del servidor
├── requirements.txt        # Dependencias Python
├── README.md              # Documentación
├── templates/             # Templates Jinja2
│   ├── base.html         # Template base
│   ├── login.html        # Página de login
│   ├── business_dashboard.html
│   ├── admin_dashboard.html
│   └── no_business.html
└── static/               # Archivos estáticos (CSS, JS, imágenes)
```

## 🔌 Integración con Backend

El frontend se comunica con el backend mediante:

### APIs Consumidas
- `GET /api/business/dashboard/{business_id}` - Datos del dashboard
- `GET /api/business/entities/{business_id}/clientes` - Lista de clientes
- `GET /api/admin/businesses` - Lista de businesses (admin)
- `GET /api/admin/stats` - Estadísticas generales (admin)

### Autenticación
- **Sesiones locales** con middleware de FastAPI
- **No integra con Clerk** (usa login hardcodeado para demo)
- **Roles soportados:** super_admin, admin, tecnico, user

## 🎨 Personalización

### Cambiar Branding
Edita los colores en `templates/base.html`:

```html
<style>
:root {
  --primary-color: #1e40af;
  --secondary-color: #059669;
}
</style>
```

### Agregar Componentes
1. Crear template en `templates/`
2. Agregar ruta en `main.py`
3. Consumir API del backend si es necesario

### Modificar Dashboard Business
Edita `templates/business_dashboard.html` para:
- Cambiar layout de componentes
- Agregar nuevas cards de estadísticas
- Modificar tabla de clientes
- Integrar nuevas APIs

## 🐛 Solución de Problemas

### Error: Templates no encontrados
```bash
# Verificar estructura
ls templates/
# Debe mostrar: base.html, login.html, business_dashboard.html, etc.
```

### Error: Backend no responde
```bash
# Verificar backend
curl http://localhost:8000/health
# Debe retornar status 200
```

### Error: Puerto 3001 ocupado
```bash
# Cambiar puerto en run.py
uvicorn.run("main:app", port=3002)  # Usar 3002
```

## 📝 Desarrollo

### Agregar Nueva Página

1. **Crear template:**
```html
<!-- templates/nueva_pagina.html -->
{% extends "base.html" %}
{% block content %}
<!-- Tu contenido -->
{% endblock %}
```

2. **Agregar ruta:**
```python
# main.py
@app.get("/nueva-pagina", response_class=HTMLResponse)
async def nueva_pagina(request: Request, user: dict = Depends(require_auth)):
    return templates.TemplateResponse("nueva_pagina.html", {
        "request": request,
        "user": user
    })
```

### Consumir Nueva API

```python
async def get_new_data(business_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BACKEND_URL}/api/nueva-endpoint/{business_id}")
            return response.json()
    except Exception as e:
        logger.error(f"Error: {e}")
        return {}
```

## 🔐 Seguridad

- ✅ **Validación de sesiones** en todas las rutas protegidas
- ✅ **CORS configurado** para desarrollo
- ✅ **Sanitización** de datos de entrada
- ⚠️ **Usuarios hardcodeados** solo para demo
- ⚠️ **Secret key** debe cambiarse en producción

## 📈 Performance

- ✅ **Conexiones HTTP async** con httpx
- ✅ **Templates cacheados** por Jinja2
- ✅ **Archivos estáticos** servidos por FastAPI
- ✅ **Lazy loading** de datos pesados

## 🚀 Producción

Para production:

1. **Cambiar secret key**
2. **Integrar con Clerk** (remover usuarios hardcodeados)
3. **Configurar HTTPS**
4. **Usar Gunicorn** en lugar de Uvicorn
5. **Proxy reverso** con Nginx

---

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch: `git checkout -b feature/nueva-funcionalidad`
3. Commit cambios: `git commit -m 'Add nueva funcionalidad'`
4. Push al branch: `git push origin feature/nueva-funcionalidad`
5. Crear Pull Request

## 📄 Licencia

MIT License - ver archivo LICENSE para detalles.