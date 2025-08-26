.PHONY: help setup test lint mypy format clean build docker-build docker-run check ci test-docker

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Setup development environment
	./scripts/setup/setup_venv.sh

test: ## Run functionality tests only
	source venv/bin/activate && pytest tests/ -v

lint: ## Run linting
	source venv/bin/activate && flake8 src/ tests/

mypy: ## Run mypy type checking
	source venv/bin/activate && mypy src/ --config-file pyproject.toml

format: ## Format code
	source venv/bin/activate && black src/ tests/

check: ## Run all quality checks (lint + mypy + format check)
	source venv/bin/activate && flake8 src/ tests/
	source venv/bin/activate && mypy src/ --config-file pyproject.toml
	source venv/bin/activate && black --check src/ tests/ --line-length=88

ci: ## Run comprehensive checks (test + lint + mypy + format check)
	source venv/bin/activate && pytest tests/ -v
	source venv/bin/activate && flake8 src/ tests/
	source venv/bin/activate && mypy src/ --config-file pyproject.toml
	source venv/bin/activate && black --check src/ tests/ --line-length=88

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info/ __pycache__/ .pytest_cache/ htmlcov/

build: ## Build package
	source venv/bin/activate && python setup.py sdist bdist_wheel

docker-build: ## Build Docker image
	docker build -f docker/Dockerfile -t repomap-tool .

install-dev: ## Install in development mode
	source venv/bin/activate && pip install -e .

uninstall: ## Uninstall package
	source venv/bin/activate && pip uninstall repomap-tool -y

test-docker: ## Run Docker-based integration tests
	bash tests/integration/test_integrated_adaptive.sh
