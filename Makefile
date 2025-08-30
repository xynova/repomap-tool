.PHONY: help setup test lint mypy format clean build docker-build docker-run check ci test-docker test-docker-real

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup development environment
	./scripts/setup/setup_venv.sh

test: ## Run functionality tests only
	venv/bin/pytest tests/ -v

lint: ## Run linting
	venv/bin/flake8 src/ tests/

mypy: ## Run mypy type checking
	venv/bin/mypy src/ --config-file pyproject.toml

format: ## Format code
	venv/bin/black src/ tests/

check: ## Run all quality checks (lint + mypy + format check)
	venv/bin/flake8 src/ tests/
	venv/bin/mypy src/ --config-file pyproject.toml
	venv/bin/black --check src/ tests/ --line-length=88

ci: ## Run comprehensive checks (test + lint + mypy + format check)
	venv/bin/pytest tests/ -v
	venv/bin/flake8 src/ tests/
	venv/bin/mypy src/ --config-file pyproject.toml
	venv/bin/black --check src/ tests/ --line-length=88

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ htmlcov/

build: ## Build package
	venv/bin/python setup.py sdist bdist_wheel

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t repomap-tool .

install-dev: ## Install in development mode
	venv/bin/pip install -e .

uninstall: ## Uninstall package
	venv/bin/pip uninstall repomap-tool -y

test-docker: ## Run Docker-based integration tests (small test project)
	bash tests/integration/test_integrated_adaptive.sh

test-docker-real: ## Run Docker tests against real codebase
	bash tests/integration/test_docker_real_codebase.sh

test-self-integration: ## Run self-integration tests (repomap-tool testing itself)
	venv/bin/pytest tests/integration/test_self_integration.py -v

test-integration: ## Run all integration tests
	venv/bin/pytest tests/integration/ -v
