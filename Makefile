# ================================
# Makefile
# ================================

.PHONY: help install test run clean deploy docker-build docker-run

# Variables
PYTHON = python3
PIP = pip
VENV = venv
DOCKER_IMAGE = cms-dinamico-backend

help: ## Mostrar ayuda
	@echo "Comandos disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instalar dependencias
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && $(PIP) install --upgrade pip
	. $(VENV)/bin/activate && $(PIP) install -r requirements.txt

test: ## Ejecutar tests
	. $(VENV)/bin/activate && pytest tests/ -v

test-coverage: ## Ejecutar tests con coverage
	. $(VENV)/bin/activate && pytest --cov=app tests/ --cov-report=html

run: ## Ejecutar servidor de desarrollo
	. $(VENV)/bin/activate && python run.py

run-prod: ## Ejecutar servidor de producción
	. $(VENV)/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

clean: ## Limpiar archivos temporales
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

lint: ## Ejecutar linter
	. $(VENV)/bin/activate && flake8 app tests
	. $(VENV)/bin/activate && black --check app tests

format: ## Formatear código
	. $(VENV)/bin/activate && black app tests
	. $(VENV)/bin/activate && isort app tests

init-db: ## Inicializar base de datos
	. $(VENV)/bin/activate && python scripts/init_db.py

create-admin: ## Crear usuario administrador
	. $(VENV)/bin/activate && python scripts/create_admin.py

deploy: ## Deploy a producción
	chmod +x scripts/deploy.sh
	./scripts/deploy.sh

docker-build: ## Construir imagen Docker
	docker build -t $(DOCKER_IMAGE) .

docker-run: ## Ejecutar con Docker
	docker-compose up -d

docker-logs: ## Ver logs de Docker
	docker-compose logs -f backend

docker-stop: ## Detener Docker
	docker-compose down

backup-db: ## Backup de MongoDB
	mongodump --uri="$(MONGODB_URL)" --out="backups/$(shell date +%Y%m%d_%H%M%S)"

restore-db: ## Restaurar MongoDB (uso: make restore-db BACKUP_DIR=backups/20250119_103000)
	mongorestore --uri="$(MONGODB_URL)" --drop "$(BACKUP_DIR)"