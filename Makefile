# =============================================================================
# Docker FastAPI Auth Service - Makefile
# =============================================================================

.PHONY: help build up down restart logs test clean backup-user backup-list backup-hash backup-example configure

# Default target
help: ## Show this help message
	@echo "Docker FastAPI Auth Service - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# =============================================================================
# Development Environment
# =============================================================================
## Start only the auth service with its database and redis
.PHONY: dev-auth
dev-auth: ## Start only auth-service, auth-db, and auth-redis
	@echo "Starting Auth service with database and redis..."
	@docker-compose up -d auth-db auth-redis auth-service

build: ## Build all Docker services
	@echo "Building Docker services..."
	docker-compose build

up: ## Start all services
	@echo "Starting services..."
	docker-compose up -d

down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down

restart: ## Restart all services
	@echo "Restarting services..."
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-auth: ## Show logs from auth service only
	docker-compose logs -f auth-service

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "Running tests..."
	docker-compose --profile test run --rm test-runner pytest tests/ -v --tb=short

test-unit: ## Run unit tests only
	@echo "Running unit tests..."
	docker-compose --profile test run --rm test-runner pytest tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "Running integration tests..."
	docker-compose --profile test run --rm test-runner pytest tests/integration/ -v

test-coverage: ## Run tests with coverage report
	@echo "Running tests with coverage..."
	docker-compose --profile test run --rm test-runner pytest --cov=app --cov-report=html tests/

# =============================================================================
# Configuration Wizard
# =============================================================================
configure: ## Run interactive configuration wizard to generate .env
	@echo "Starting configuration wizard..."
	@./scripts/configure.sh

# =============================================================================
# Backup User Management
# =============================================================================

backup-hash: ## Generate SHA256 hash for a password
	@echo "Usage: make backup-hash PASSWORD=your_password"
	@if [ -z "$(PASSWORD)" ]; then \
		echo "Error: PASSWORD is required"; \
		echo "Example: make backup-hash PASSWORD=mypassword123"; \
		exit 1; \
	fi
	@./scripts/manage-backup-users.sh hash "$(PASSWORD)"

backup-create: ## Create a new backup user
	@echo "Usage: make backup-create USERNAME=username PASSWORD=password [ADMIN=true] [PERMISSIONS='{'\"services\":[\"*\"]}'] [EMAIL=email] [FULL_NAME='Full Name']"
	@if [ -z "$(USERNAME)" ] || [ -z "$(PASSWORD)" ]; then \
		echo "Error: USERNAME and PASSWORD are required"; \
		echo "Example: make backup-create USERNAME=admin PASSWORD=mypass123 ADMIN=true"; \
		exit 1; \
	fi
	@./scripts/manage-backup-users.sh create-user "$(USERNAME)" "$(PASSWORD)" "$(ADMIN)" "$(PERMISSIONS)" "$(EMAIL)" "$(FULL_NAME)"

backup-list: ## List all configured backup users
	@echo "Listing backup users..."
	@./scripts/manage-backup-users.sh list-users

backup-example: ## Show example backup users configuration
	@echo "Showing example configuration..."
	@./scripts/manage-backup-users.sh example-config

# =============================================================================
# Database Management
# =============================================================================

db-init: ## Initialize database (run migrations)
	@echo "Initializing database..."
	docker-compose exec auth-service python -c "from app.database import init_db; init_db()"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "Resetting database..."
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down; \
		docker volume rm docker-fastapi-auth_postgres_data 2>/dev/null || true; \
		docker volume rm docker-fastapi-auth_redis_data 2>/dev/null || true; \
		docker-compose up -d postgres redis; \
		sleep 5; \
		make db-init; \
	else \
		echo "Database reset cancelled."; \
	fi

# =============================================================================
# Health Checks
# =============================================================================

health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost:8008/health | python3 -m json.tool || echo "Service not responding"

status: ## Show service status
	@echo "Service Status:"
	@echo "==============="
	@docker-compose ps
	@echo ""
	@echo "Health Check:"
	@make health

# =============================================================================
# Cleanup
# =============================================================================

clean: ## Clean up Docker resources
	@echo "Cleaning up..."
	docker-compose down -v
	docker system prune -f

clean-all: ## Clean up everything including volumes (WARNING: This deletes all data)
	@echo "WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		docker-compose down -v --remove-orphans; \
		docker system prune -f --volumes; \
		docker image prune -f; \
	else \
		echo "Cleanup cancelled."; \
	fi

# =============================================================================
# Development Helpers
# =============================================================================

shell: ## Open shell in auth service container
	docker-compose exec auth-service bash

shell-db: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U atrium_auth -d atrium_auth

format: ## Format Python code with black
	docker-compose exec auth-service black app/ tests/

lint: ## Lint Python code with flake8
	docker-compose exec auth-service flake8 app/ tests/

# =============================================================================
# Production Deployment
# =============================================================================

deploy: ## Deploy to production (build and start)
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml up -d --build

deploy-logs: ## Show production logs
	docker-compose logs -f --tail=100

# =============================================================================
# Quick Setup for New Developers
# =============================================================================

setup: ## Quick setup for new developers
	@echo "Setting up development environment..."
	@echo "1. Building services..."
	make build
	@echo "2. Starting services..."
	make up
	@echo "3. Waiting for services to be ready..."
	sleep 10
	@echo "4. Initializing database..."
	make db-init
	@echo "5. Running tests..."
	make test
	@echo "Setup complete! 🎉"
	@echo ""
	@echo "Next steps:"
	@echo "- Configure OAuth credentials in .env"
	@echo "- Run 'make backup-create' to add backup users"
	@echo "- Visit http://localhost:8008/health to check status"

# =============================================================================
# Examples and Documentation
# =============================================================================

examples: ## Show usage examples
	@echo "Docker FastAPI Auth Service - Usage Examples:"
	@echo "=========================================="
	@echo ""
	@echo "# Start development environment"
	@echo "make setup"
	@echo ""
	@echo "# Create backup users"
	@echo "make backup-create USERNAME=admin PASSWORD=secure123 ADMIN=true"
	@echo "make backup-create USERNAME=operator PASSWORD=op123 ADMIN=false PERMISSIONS='{"services":["read","write"]}'"
	@echo ""
	@echo "# List backup users"
	@echo "make backup-list"
	@echo ""
	@echo "# Run tests"
	@echo "make test"
	@echo ""
	@echo "# Check service health"
	@echo "make health"
	@echo ""
	@echo "# View logs"
	@echo "make logs"
	@echo ""
	@echo "# Clean up"
	@echo "make clean"
