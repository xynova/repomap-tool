.PHONY: help venv install test lint format mypy security build clean ci docker-deps docker-final

# Virtual environment
VENV_NAME = .venv
VENV_BIN = $(VENV_NAME)/bin
VENV_PYTHON = $(VENV_BIN)/python
VENV_PIP = $(VENV_BIN)/pip

# Docker configuration
DOCKER_IMAGE_NAME ?= repomap-tool
DOCKER_TAG ?= local

# Default target
help:
	@echo "Available commands:"
	@echo "  venv        - Create virtual environment with uv"
	@echo "  install     - Install dependencies in .venv"
	@echo "  test        - Run tests with coverage (parallel)"
	@echo "  test-unit   - Run unit tests (parallel)"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black"
	@echo "  mypy        - Run type checking with mypy"
	@echo "  security    - Run security checks"
	@echo "  build       - Build package"
	@echo "  clean       - Clean build artifacts and venv"
	@echo "  ci          - Run all CI checks"
	@echo "  performance - Run performance tests"
	@echo "  demo        - Run performance demo"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-test     - Run comprehensive Docker tests"
	@echo "  docker-test-ci  - Run Docker tests for CI environment"
	@echo "  docker-clean    - Clean Docker images and containers"
	@echo "  docker-run      - Run Docker container interactively"
	@echo "  ci-all          - Run complete CI (local + Docker)"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Creating virtual environment..."; \
		if command -v uv &> /dev/null; then \
			echo "Using uv for virtual environment..."; \
			uv venv; \
		else \
			echo "Using python -m venv for virtual environment..."; \
			python3 -m venv $(VENV_NAME); \
		fi; \
		echo "Virtual environment created at $(VENV_NAME)"; \
		echo "Activate it with: source $(VENV_NAME)/bin/activate"; \
	else \
		echo "Virtual environment already exists at $(VENV_NAME)"; \
	fi

# Install dependencies
install: venv
	@echo "Installing dependencies..."
	@if command -v uv &> /dev/null; then \
		echo "Using uv for dependency installation..."; \
		uv pip install -e ".[dev]"; \
	else \
		echo "Using pip for dependency installation..."; \
		$(VENV_PIP) install -e ".[dev]"; \
	fi
	@echo "Dependencies installed successfully!"
	@echo "Activate virtual environment with: source $(VENV_NAME)/bin/activate"

# Run tests with coverage
test: install
	$(VENV_PYTHON) -m pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html -n auto

# Run only unit tests
test-unit: install
	REPOMAP_DISABLE_CACHE=1 $(VENV_PYTHON) -m pytest tests/unit/ -v --tb=short -n auto

# Run only integration tests
test-integration: install
	$(VENV_PYTHON) -m pytest tests/integration/ -v -n auto

# Run performance tests
performance: install
	PYTHONPATH=src $(VENV_PYTHON) -m pytest tests/unit/test_performance.py -v

# Run linting checks
lint: install
	$(VENV_PYTHON) -m flake8 src/ tests/ examples/ --max-line-length=88 --extend-ignore=E203,W503,E501,E402,F401,F541,F841,W293,E304
	$(VENV_PYTHON) -m black --check --diff src/ tests/ examples/
	@echo "🔍 Running DI linter..."
	$(VENV_PYTHON) scripts/di_linter.py src/ tests/

# Format code
format: install
	$(VENV_PYTHON) -m black src/ tests/ examples/

# Run type checking with mypy
mypy: install
	$(VENV_PYTHON) -m mypy src/

# Run security checks
security: install
	@if ! $(VENV_PYTHON) -c "import bandit" 2>/dev/null; then \
		echo "❌ Bandit not installed. Run 'make install' first to install dev dependencies."; \
		exit 1; \
	fi
	$(VENV_PYTHON) -m bandit -r src/ -f json -o bandit-report.json
	

# Build package
build: install
	$(VENV_PYTHON) -m build

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts and virtual environment..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -f .coverage
	rm -f coverage.xml
	rm -f bandit-report.json
	rm -rf $(VENV_NAME)/
	rm -rf venv/  # Also clean old venv if it exists
	rm -f .deps-image-tag
	@echo "Cleanup complete!"

# Run code quality checks
check: lint mypy
	@echo "Code quality checks completed!"

# Run all CI checks  
ci: test security build check
	@echo "CI pipeline completed successfully!"

# Run comprehensive nightly tests
nightly: install
	$(VENV_PYTHON) -m pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --durations=10 -n auto
	$(VENV_PYTHON) -m pytest tests/integration/test_self_integration.py -v --durations=10
	$(VENV_PYTHON) -m pytest tests/integration/ -v --durations=10 -n auto

# Run performance demo
demo: install
	cd examples && $(shell pwd)/$(VENV_PYTHON) performance_demo.py

# Build and push base image with dependencies only
docker-deps:
	@echo "🔧 Building base image with dependencies only..."
	./.github/scripts/build-deps-image.sh

# Build final image using cached dependencies
docker-final: docker-deps
	@echo "🔧 Building final image using cached dependencies..."
	./.github/scripts/build-final-image.sh

# Quick development setup
dev-setup: install format lint type-check test

# Test CLI functionality
test-cli: install
	$(VENV_PYTHON) -m repomap_tool.cli --help
	$(VENV_PYTHON) -m repomap_tool.cli system version

# Run with different performance configurations
test-performance-configs:
	@echo "Testing different performance configurations..."
	@echo "1. Default configuration (fail fast):"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig; print('✅ Default config works')"
	@echo "2. Parallel processing enabled:"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig, PerformanceConfig; config = RepoMapConfig(project_root='.', performance=PerformanceConfig(max_workers=4)); print('✅ Parallel config works')"
	@echo "3. Fallback enabled:"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig, PerformanceConfig; config = RepoMapConfig(project_root='.', performance=PerformanceConfig(allow_fallback=True)); print('✅ Fallback config works')"

# Development workflow
dev: dev-setup test-performance-configs test-cli

# Full CI simulation
full-ci: clean install ci test-performance-configs test-cli demo

# Docker targets
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) -f docker/Dockerfile .
	@echo "✅ Docker image built successfully: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"

docker-test: docker-build
	@echo "🧪 Running comprehensive Docker tests..."
	@echo "1. Testing Docker image build..."
	@docker images | grep $(DOCKER_IMAGE_NAME) || (echo "❌ Docker image not found" && exit 1)
	@echo "✅ Docker image exists"
	@echo ""
	@echo "2. Testing basic CLI functionality..."
	@docker run --rm $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) --help || (echo "❌ CLI help failed" && exit 1)
	@echo "✅ CLI help works"
	@echo ""
	@echo "3. Testing system version command..."
	@docker run --rm $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) system version || (echo "❌ Version command failed" && exit 1)
	@echo "✅ Version command works"
	@echo ""
	@echo "4. Running integration tests against real codebase..."
	@chmod +x tests/integration/test_docker_real_codebase.sh
	./tests/integration/test_docker_real_codebase.sh
	@echo "✅ All Docker tests completed successfully"

# Docker test for CI (uses full registry path)
docker-test-ci:
	@echo "🧪 Running comprehensive Docker tests in CI..."
	@echo "1. Testing Docker image availability..."
	@docker images | grep $(DOCKER_IMAGE_NAME) || (echo "❌ Docker image not found" && exit 1)
	@echo "✅ Docker image exists: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"
	@echo ""
	@echo "2. Testing basic CLI functionality..."
	@docker run --rm $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) --help || (echo "❌ CLI help failed" && exit 1)
	@echo "✅ CLI help works"
	@echo ""
	@echo "3. Testing system version command..."
	@docker run --rm $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) system version || (echo "❌ Version command failed" && exit 1)
	@echo "✅ Version command works"
	@echo ""
	@echo "4. Running integration tests against real codebase..."
	@chmod +x tests/integration/test_docker_real_codebase.sh
	./tests/integration/test_docker_real_codebase.sh
	@echo "✅ All Docker tests completed successfully"

docker-clean:
	@echo "🧹 Cleaning Docker artifacts..."
	docker rmi $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || true
	docker system prune -f
	@echo "✅ Docker cleanup complete"

docker-run: docker-build
	@echo "🚀 Running Docker container interactively..."
	@echo "Use 'exit' to leave the container"
	docker run -it --rm -v "$(PWD):/project" $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) bash

# Complete CI workflow (local + Docker)
ci-all: ci docker-test
	@echo "✅ Complete CI workflow completed successfully"
	@echo "🎯 All tests passed in both local and Docker environments"
