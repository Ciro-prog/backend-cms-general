# ================================
# scripts/deploy.sh
# ================================

#!/bin/bash

# Script de deployment para CMS Dinámico
set -e

echo "🚀 Iniciando deployment de CMS Dinámico Backend..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "requirements.txt" ]; then
    error "requirements.txt no encontrado. Ejecuta desde el directorio del backend."
    exit 1
fi

# Verificar variables de entorno requeridas
check_env_vars() {
    log "Verificando variables de entorno..."
    
    required_vars=(
        "MONGODB_URL"
        "REDIS_URL" 
        "CLERK_SECRET_KEY"
        "SECRET_KEY"
        "ENCRYPTION_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Variable de entorno requerida no encontrada: $var"
            exit 1
        fi
    done
    
    log "✅ Variables de entorno verificadas"
}

# Instalar dependencias
install_dependencies() {
    log "Instalando dependencias de Python..."
    
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    log "✅ Dependencias instaladas"
}

# Ejecutar tests
run_tests() {
    log "Ejecutando tests..."
    
    source venv/bin/activate
    
    if command -v pytest &> /dev/null; then
        pytest tests/ -v --tb=short
        log "✅ Tests completados exitosamente"
    else
        warn "pytest no instalado, saltando tests"
    fi
}

# Inicializar base de datos
init_database() {
    log "Inicializando base de datos..."
    
    source venv/bin/activate
    python scripts/init_db.py
    
    log "✅ Base de datos inicializada"
}

# Configurar servicios systemd (para producción)
setup_systemd() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Configurando servicio systemd..."
        
        cat > /etc/systemd/system/cms-dinamico.service << EOF
[Unit]
Description=CMS Dinámico Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

        systemctl daemon-reload
        systemctl enable cms-dinamico
        
        log "✅ Servicio systemd configurado"
    fi
}

# Configurar nginx (para producción)
setup_nginx() {
    if [ "$ENVIRONMENT" = "production" ]; then
        log "Configurando nginx..."
        
        cat > /etc/nginx/sites-available/cms-dinamico << EOF
server {
    listen 80;
    server_name ${DOMAIN_NAME:-localhost};

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    client_max_body_size 100M;
}
EOF

        ln -sf /etc/nginx/sites-available/cms-dinamico /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx
        
        log "✅ Nginx configurado"
    fi
}

# Función principal
main() {
    log "Iniciando deployment..."
    
    # Verificar entorno
    ENVIRONMENT=${ENVIRONMENT:-development}
    log "Entorno: $ENVIRONMENT"
    
    # Ejecutar pasos
    check_env_vars
    install_dependencies
    
    if [ "$SKIP_TESTS" != "true" ]; then
        run_tests
    fi
    
    if [ "$SKIP_DB_INIT" != "true" ]; then
        init_database
    fi
    
    if [ "$ENVIRONMENT" = "production" ]; then
        setup_systemd
        setup_nginx
        
        log "Iniciando servicio..."
        systemctl start cms-dinamico
        systemctl status cms-dinamico
    else
        log "Iniciando servidor de desarrollo..."
        source venv/bin/activate
        python run.py &
    fi
    
    log "🎉 Deployment completado exitosamente!"
    log "API disponible en: http://localhost:8000"
    log "Documentación: http://localhost:8000/docs"
}

# Ejecutar función principal
main "$@"