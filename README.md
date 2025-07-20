# ================================
# README.md
# ================================

# CMS Dinámico - Backend

Sistema de CMS dinámico y configurable que permite crear dashboards y aplicaciones web completamente configurables desde un panel administrativo.

## 🚀 Inicio Rápido

### Prerrequisitos

- Python 3.11+
- MongoDB 7.0+
- Redis 7.2+
- Docker (opcional)

### Instalación

1. **Clonar el repositorio**
```bash
git clone <repo-url>
cd cms-dinamico/backend
```

2. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Inicializar base de datos**
```bash
python scripts/init_db.py
```

6. **Crear usuario administrador**
```bash
python scripts/create_admin.py
```

7. **Ejecutar servidor**
```bash
python run.py
# o
uvicorn app.main:app --reload
```

## 🐳 Docker

```bash
# Ejecutar con Docker Compose
docker-compose up -d

# Ver logs
docker-compose logs -f backend
```

## 📖 Documentación

- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🏗️ Estructura del Proyecto

```
backend/
├── app/
│   ├── auth/          # Autenticación y permisos
│   ├── models/        # Modelos Pydantic
│   ├── routers/       # Endpoints de la API
│   ├── services/      # Lógica de negocio
│   ├── utils/         # Utilidades
│   └── main.py        # Aplicación FastAPI
├── scripts/           # Scripts de utilidad
├── requirements.txt   # Dependencias
└── docker-compose.yml # Configuración Docker
```

## 🔧 Configuración

### Variables de Entorno

Ver `.env.example` para todas las variables necesarias.

### Clerk Authentication

1. Crear cuenta en [Clerk](https://clerk.dev)
2. Obtener las keys del dashboard
3. Configurar webhook para sincronización de usuarios

## 🧪 Testing

```bash
# Ejecutar tests
pytest

# Con coverage
pytest --cov=app tests/
```

## 📝 Desarrollo

### Agregar nuevo Business Type

1. Crear template en la base de datos
2. Configurar componentes base y opcionales
3. Definir entidades y sus campos
4. Configurar vistas y permisos

### Integrar nueva API Externa

1. Añadir configuración en `api_configurations`
2. Crear mapeo de campos
3. Configurar cache y rate limiting
4. Implementar en `ApiService`

## 🔒 Seguridad

- Autenticación via Clerk
- Permisos granulares por entidad
- Encriptación de API keys
- Rate limiting
- Validación de datos con Pydantic

## 📊 Monitoreo

- Logs estructurados
- Health checks
- Métricas de performance
- Alertas configurables

## 🤝 Contribución

1. Fork el proyecto
2. Crear feature branch
3. Commit cambios
4. Push al branch
5. Crear Pull Request

## 📜 Licencia

[MIT License](LICENSE)