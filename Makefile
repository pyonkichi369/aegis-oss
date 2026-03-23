.PHONY: help run dev docker test lint clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

run: ## Start the API server
	uvicorn aegis_gov.api:app --reload --port 8000

dev: ## Start with auto-reload and debug logging
	PYTHONPATH=. LOG_LEVEL=DEBUG uvicorn aegis_gov.api:app --reload --port 8000

docker: ## Start with Docker Compose
	docker compose -f docker/docker-compose.yml up --build

docker-down: ## Stop Docker containers
	docker compose -f docker/docker-compose.yml down

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=aegis_gov --cov-report=html --cov-report=term

lint: ## Run linter
	ruff check aegis_gov/ tests/

lint-fix: ## Auto-fix lint issues
	ruff check aegis_gov/ tests/ --fix

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type f -name "*.pyc" -delete 2>/dev/null; true
	rm -rf .pytest_cache htmlcov .coverage dist build *.egg-info
