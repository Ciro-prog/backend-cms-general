@echo off
REM ================================
REM CMS Dinámico - Frontend Usuario Final
REM Script de Instalación para Windows
REM ================================

echo 🚀 CMS Dinámico - Instalación Frontend Usuario Final
echo ==================================================

REM Verificar que estamos en el directorio correcto
if not exist "main.py" (
    echo ❌ No se encontró main.py. Ejecuta este script desde el directorio del frontend.
    pause
    exit /b 1
)

REM 1. Verificar Python
echo ℹ️  Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python no encontrado. Instala Python 3.11+ antes de continuar.
    echo 💡 Descarga desde: https://www.python.org/downloads/
    pause
    exit /b 1
) else (
    echo ✅ Python encontrado
)

REM 2. Crear entorno virtual si no existe
if not exist "venv" (
    echo ℹ️  Creando entorno virtual...
    python -m venv venv
    echo ✅ Entorno virtual creado
) else (
    echo ✅ Entorno virtual ya existe
)

REM 3. Activar entorno virtual
echo ℹ️  Activando entorno virtual...
call venv\Scripts\activate.bat
echo ✅ Entorno virtual activado

REM 4. Instalar dependencias
echo ℹ️  Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt
echo ✅ Dependencias instaladas

REM 5. Crear directorios necesarios
echo ℹ️  Creando directorios...
if not exist "templates" mkdir templates
if not exist "static" mkdir static
echo ✅ Directorios creados

REM 6. Verificar que existen los templates
echo ℹ️  Verificando templates...
set MISSING_TEMPLATES=0

if not exist "templates\base.html" (
    echo ⚠️  Falta: templates\base.html
    set /a MISSING_TEMPLATES+=1
)

if not exist "templates\login.html" (
    echo ⚠️  Falta: templates\login.html
    set /a MISSING_TEMPLATES+=1
)

if not exist "templates\business_dashboard.html" (
    echo ⚠️  Falta: templates\business_dashboard.html
    set /a MISSING_TEMPLATES+=1
)

if not exist "templates\admin_dashboard.html" (
    echo ⚠️  Falta: templates\admin_dashboard.html
    set /a MISSING_TEMPLATES+=1
)

if not exist "templates\no_business.html" (
    echo ⚠️  Falta: templates\no_business.html
    set /a MISSING_TEMPLATES+=1
)

if %MISSING_TEMPLATES%==0 (
    echo ✅ Todos los templates están presentes
) else (
    echo ⚠️  %MISSING_TEMPLATES% templates faltantes. Cópialos antes de ejecutar.
)

REM 7. Crear archivo .env si no existe
if not exist ".env" (
    echo ℹ️  Creando archivo .env...
    if exist ".env.example" (
        copy .env.example .env >nul
        echo ✅ Archivo .env creado desde .env.example
    ) else (
        echo # Backend API > .env
        echo BACKEND_URL=http://localhost:8000 >> .env
        echo SECRET_KEY=your-secret-key-change-in-production >> .env
        echo ✅ Archivo .env básico creado
    )
) else (
    echo ✅ Archivo .env ya existe
)

REM 8. Verificar conectividad con backend
echo ℹ️  Verificando backend en localhost:8000...
curl -s -f http://localhost:8000/health >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Backend detectado y funcionando
) else (
    echo ⚠️  Backend no responde en localhost:8000
    echo ⚠️  Asegúrate de que el backend esté ejecutándose antes de usar el frontend
)

REM 9. Mostrar resumen
echo.
echo ==================================================
echo ✅ 🎉 Instalación completada!
echo ==================================================
echo.
echo 📝 Próximos pasos:
echo.
echo 1. Asegúrate de que el backend esté corriendo:
echo    cd ..\backend ^&^& python run.py
echo.
echo 2. Ejecuta el frontend:
echo    python run.py
echo.
echo 3. Abre en tu navegador:
echo    http://localhost:3001
echo.
echo 👥 Usuarios demo disponibles:
echo    - admin / admin (Administrador^)
echo    - tecnico / tecnico (Técnico^)
echo    - usuario / usuario (Usuario Final^)
echo    - superadmin / superadmin (Super Admin^)
echo.
echo 🔗 URLs útiles:
echo    - Frontend: http://localhost:3001
echo    - Backend API: http://localhost:8000
echo    - API Docs: http://localhost:8000/docs
echo    - Health Check: http://localhost:3001/health
echo.

if %MISSING_TEMPLATES% gtr 0 (
    echo ⚠️  IMPORTANTE: Copia los %MISSING_TEMPLATES% templates faltantes antes de ejecutar.
)

echo 🚀 ¡Listo para ejecutar!
echo.
pause