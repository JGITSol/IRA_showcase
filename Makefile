.PHONY: help install test lint format check-format typecheck security clean build up down restart logs shell-db shell-web shell-redis init-db test-db migrate upgrade-db downgrade-db logs-db logs-web logs-redis lint-fix check-types check-security check-tests check-all

# Default target executed when no arguments are given to make.
help:
	@echo 'Available targets:'
	@echo '  install         Install development dependencies'
	@echo '  test           Run tests'
	@echo '  lint           Run code linters'
	@echo '  format         Format code'
	@echo '  check-format   Check code formatting'
	@echo '  typecheck      Run static type checking'
	@echo '  security       Run security checks'
	@echo '  clean          Remove Python file artifacts'
	@echo '  build          Build or rebuild services'
	@echo '  up             Create and start containers'
	@echo '  down           Stop and remove containers, networks, images, and volumes'
	@echo '  restart        Restart services'
	@echo '  logs           View output from containers'
	@echo '  shell-db       Open a shell in the database container'
	@echo '  shell-web      Open a shell in the web container'
	@echo '  shell-redis    Open a shell in the Redis container'
	@echo '  init-db        Initialize the database'
	@echo '  test-db        Run database tests'
	@echo '  migrate        Create a new database migration'
	@echo '  upgrade-db     Upgrade database to the latest revision'
	@echo '  downgrade-db   Downgrade database by one revision'
	@echo '  check-all      Run all checks (lint, typecheck, security, tests)'

# Install development dependencies
install:
	@echo "Installing development dependencies..."
	pip install -e ".[dev]"

# Run tests
test:
	@echo "Running tests..."
	pytest -v --cov=app --cov-report=term-missing --cov-report=xml:coverage.xml tests/

# Run code linters
lint:
	@echo "Running linters..."
	ruff check .
	black --check .
	isort --check-only .

# Format code
format:
	@echo "Formatting code..."
	black .
	isort .

# Check code formatting
check-format:
	@echo "Checking code formatting..."
	black --check .
	isort --check-only .

# Run static type checking
typecheck:
	@echo "Running static type checking..."
	mypy .

# Run security checks
security:
	@echo "Running security checks..."
	bandit -r app/
	safety check

# Remove Python file artifacts
clean:
	@echo "Cleaning up..."
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.py[co]' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -exec rm -rf {} +

# Build or rebuild services
build:
	@echo "Building services..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml build

# Create and start containers
up:
	@echo "Starting services..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Stop and remove containers, networks, images, and volumes
down:
	@echo "Stopping and removing services..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml down -v --remove-orphans

# Restart services
restart:
	@echo "Restarting services..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml restart

# View output from containers
logs:
	@echo "Showing logs..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f

# Open a shell in the database container
shell-db:
	@echo "Opening database shell..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec db psql -U $$(grep DB_USER .env | cut -d '=' -f2) -d $$(grep DB_NAME .env | cut -d '=' -f2)

# Open a shell in the web container
shell-web:
	@echo "Opening web shell..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web bash

# Open a shell in the Redis container
shell-redis:
	@echo "Opening Redis shell..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec redis redis-cli

# Initialize the database
init-db:
	@echo "Initializing database..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web python -m app.db.init_db

# Run database tests
test-db:
	@echo "Running database tests..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web python -m pytest tests/db/ -v

# Create a new database migration
migrate:
	@echo "Creating a new database migration..."
	@read -p "Enter migration message: " message; \
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web alembic revision --autogenerate -m "$$message"

# Upgrade database to the latest revision
upgrade-db:
	@echo "Upgrading database..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web alembic upgrade head

# Downgrade database by one revision
downgrade-db:
	@echo "Downgrading database..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml exec web alembic downgrade -1

# View database logs
logs-db:
	@echo "Showing database logs..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f db

# View web logs
logs-web:
	@echo "Showing web logs..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f web

# View Redis logs
logs-redis:
	@echo "Showing Redis logs..."
	docker-compose -f docker-compose.yml -f docker-compose.override.yml logs -f redis

# Fix linting issues
lint-fix:
	@echo "Fixing linting issues..."
	black .
	isort .
	ruff --fix .

# Run all checks
check-all: lint typecheck security test
	@echo "All checks completed successfully!"
