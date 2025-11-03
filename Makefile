# ============================================================================
# CONFIGURATION
# ============================================================================

.PHONY: help venv install test test-unit test-unit-no-install test-integration test-integration-no-install test-integration-core test-integration-components test-integration-tree test-integration-cli-light test-integration-cli-heavy test-integration-edge-cases lint format mypy security build clean ci docker-deps docker-final

# Virtual environment configuration
VENV_NAME = .venv
VENV_BIN = $(VENV_NAME)/bin
VENV_PYTHON = $(VENV_BIN)/python
VENV_PIP = $(VENV_BIN)/pip

# Docker configuration
DOCKER_IMAGE_NAME ?= repomap-tool
DOCKER_TAG ?= local


# ============================================================================
# HELP / DEFAULT TARGET
# ============================================================================

help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  venv        - Create virtual environment with uv"
	@echo "  install     - Install dependencies in .venv"
	@echo ""
	@echo "Testing:"
	@echo "  test        - Run all tests with coverage (unit + integration)"
	@echo "  test-unit   - Run unit tests (parallel)"
	@echo "  test-integration - Run integration tests in batches (sequential)"
	@echo "  test-integration-core - Core search/matching tests"
	@echo "  test-integration-components - Component/service tests"
	@echo "  test-integration-tree - Tree/exploration tests"
	@echo "  test-integration-cli-light - Lightweight CLI tests"
	@echo "  test-integration-cli-heavy - Heavy CLI tests (optional, memory-intensive)"
	@echo "  test-integration-edge-cases - Edge case tests"
	@echo "  test-profile - Run tests with memory profiling"
	@echo "  test-profile-single - Run single test with memory profiling"
	@echo "  test-memory-check - Check memory usage of pytest processes"
	@echo "  test-cli   - Test CLI functionality"
	@echo "  performance - Run performance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint        - Run linting checks (flake8, black, DI linter)"
	@echo "  format      - Format code with black"
	@echo "  mypy        - Run type checking with mypy"
	@echo "  security    - Run security checks (bandit)"
	@echo "  check       - Run all code quality checks (lint + mypy)"
	@echo ""
	@echo "Build & Package:"
	@echo "  build       - Build package"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build    - Build Docker image"
	@echo "  docker-test     - Run comprehensive Docker tests"
	@echo "  docker-test-ci  - Run Docker tests for CI environment"
	@echo "  docker-clean    - Clean Docker images and containers"
	@echo "  docker-run      - Run Docker container interactively"
	@echo "  docker-deps     - Build base image with dependencies only"
	@echo "  docker-final    - Build final image using cached dependencies"
	@echo ""
	@echo "Development Workflows:"
	@echo "  dev-setup   - Quick development setup (install, format, lint, test)"
	@echo "  dev         - Full development workflow"
	@echo "  test-performance-configs - Test different performance configurations"
	@echo "  demo        - Run performance demo"
	@echo ""
	@echo "CI & Pipeline:"
	@echo "  ci          - Run all CI checks (build, check, test, security)"
	@echo "  ci-all      - Complete CI workflow (local + Docker)"
	@echo "  nightly     - Run comprehensive nightly tests"
	@echo "  full-ci     - Full CI simulation"
	@echo ""
	@echo "Utilities:"
	@echo "  clean       - Clean build artifacts and venv"
	@echo "  kill-tests  - Force kill any lingering test processes"


# ============================================================================
# SETUP
# ============================================================================

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


# ============================================================================
# TESTING
# ============================================================================

# Run all tests (unit + integration)
test: install
	@$(MAKE) test-unit-no-install
	@$(MAKE) test-integration-no-install
	@echo "✅ All tests completed (unit + integration)"

# --- Unit Tests ---

# Run unit tests (with install check - for standalone use)
test-unit: install
	@$(MAKE) test-unit-no-install

# Run unit tests (no install - assumes install already done)
test-unit-no-install:
	@echo "🧪 Running unit tests..."
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/unit/ -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml -n auto --max-worker-restart=0 --dist=worksteal

# --- Integration Tests ---

# Run integration tests (with install check - for standalone use)
test-integration: install
	@$(MAKE) test-integration-no-install

# Run integration tests in batches (no install - assumes install already done)
# Runs each category sequentially to prevent memory buildup
# Each batch completes and releases memory before the next one starts
test-integration-no-install:
	@echo "🔗 Running integration tests in batches (sequential to prevent memory buildup)..."
	@$(MAKE) test-integration-core || exit 1
	@$(MAKE) test-integration-components || exit 1
	@$(MAKE) test-integration-tree || exit 1
	@$(MAKE) test-integration-cli-light || exit 1
	@$(MAKE) test-integration-edge-cases || exit 1
	@echo "✅ All integration test batches completed"

# Core integration tests - Basic search and matching functionality
test-integration-core:
	@echo "  📦 Batch 1/5: Core integration tests (search/matching)"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_self_integration.py tests/integration/test_real_integration.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 2 --max-worker-restart=0 --dist=worksteal

# Component integration tests - Service factory, dependencies, templates
test-integration-components:
	@echo "  📦 Batch 2/5: Component integration tests (services/components)"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_service_factory_integration.py tests/integration/test_dependency_components_real.py tests/integration/test_template_system_integration.py tests/integration/test_venv_setup.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 2 --max-worker-restart=0 --dist=worksteal

# Tree/exploration integration tests
test-integration-tree:
	@echo "  📦 Batch 3/5: Tree/exploration integration tests"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_tree_integration.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 2 --max-worker-restart=0 --dist=worksteal

# Lightweight CLI integration tests - Basic CLI functionality
test-integration-cli-light:
	@echo "  📦 Batch 4/5: Lightweight CLI integration tests"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_cli_integration.py tests/integration/test_density_command.py tests/integration/test_inspect_commands_integration.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 2 --max-worker-restart=0 --dist=worksteal

# Heavy CLI integration tests - Full CLI with real codebase (most memory-intensive)
test-integration-cli-heavy:
	@echo "  📦 Running heavy CLI integration tests (real codebase, sequential)"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_cli_real_integration.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 1 --max-worker-restart=0

# Edge cases integration tests
test-integration-edge-cases:
	@echo "  📦 Batch 5/5: Edge cases integration tests"
	./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/integration/test_integration_edge_cases.py -v --cov=src --cov-report=term-missing --cov-report=html --cov-report=xml --cov-append -n 2 --max-worker-restart=0 --dist=worksteal

# --- Test Utilities ---

# Run tests with memory profiling (no parallelization for clarity)
test-profile: install
	REPOMAP_MEMORY_PROFILE=true ./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest tests/ -v --tb=short -n 0 -s

# Run single test with memory profiling (no parallelization)
test-profile-single: install
	@echo "📊 Running single test with memory profiling..."
	@if [ -z "$(TEST)" ]; then \
		echo "Usage: make test-profile-single TEST=path.to.test::test_function"; \
		exit 1; \
	fi
	REPOMAP_MEMORY_PROFILE=true ./scripts/run_tests_with_cleanup.sh $(VENV_PYTHON) -m pytest $(TEST) -v -s -n 0

# Check memory usage of pytest processes
test-memory-check: install
	@echo "📊 Checking pytest process memory usage..."
	@$(VENV_PYTHON) -c "from tests.utils.memory_profiler import get_all_pytest_processes; \
		procs = get_all_pytest_processes(); \
		print(f'Found {len(procs)} pytest processes:'); \
		[print(f'  PID {p[\"pid\"]}: {p[\"memory_mb\"]:.1f} MB - {p[\"cmdline\"]}') for p in procs] if procs else print('  No pytest processes found')"

# Test CLI functionality
test-cli: install
	$(VENV_PYTHON) -m repomap_tool.cli --help
	$(VENV_PYTHON) -m repomap_tool.cli system version

# Run performance tests
performance: install
	PYTHONPATH=src $(VENV_PYTHON) -m pytest tests/unit/test_performance.py -v


# ============================================================================
# CODE QUALITY
# ============================================================================

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
	$(VENV_PYTHON) -m mypy src/ --explicit-package-bases

# Run security checks
security: install
	@if ! $(VENV_PYTHON) -c "import bandit" 2>/dev/null; then \
		echo "❌ Bandit not installed. Run 'make install' first to install dev dependencies."; \
		exit 1; \
	fi
	$(VENV_PYTHON) -m bandit -r src/ -f json -o bandit-report.json -ll || true
	@if [ -f bandit-report.json ]; then \
		$(VENV_PYTHON) -c "import json; data = json.load(open('bandit-report.json')); issues = [r for r in data.get('results', []) if r.get('issue_severity') == 'HIGH']; exit(1 if issues else 0)"; \
	else \
		echo "⚠️  Warning: bandit-report.json not found"; \
		exit 1; \
	fi

# Run all code quality checks
check: lint mypy
	@echo "Code quality checks completed!"


# ============================================================================
# BUILD & PACKAGE
# ============================================================================

# Build package
build: install
	$(VENV_PYTHON) -m build


# ============================================================================
# DOCKER
# ============================================================================

# Build and push base image with dependencies only
docker-deps:
	@echo "🔧 Building base image with dependencies only..."
	./.github/scripts/build-deps-image.sh

# Build final image using cached dependencies
docker-final: docker-deps
	@echo "🔧 Building final image using cached dependencies..."
	./.github/scripts/build-final-image.sh

# Build Docker image
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) -f docker/Dockerfile .
	@echo "✅ Docker image built successfully: $(DOCKER_IMAGE_NAME):$(DOCKER_TAG)"

# Run comprehensive Docker tests
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

# Clean Docker images and containers
docker-clean:
	@echo "🧹 Cleaning Docker artifacts..."
	docker rmi $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) 2>/dev/null || true
	docker system prune -f
	@echo "✅ Docker cleanup complete"

# Run Docker container interactively
docker-run: docker-build
	@echo "🚀 Running Docker container interactively..."
	@echo "Use 'exit' to leave the container"
	docker run -it --rm -v "$(PWD):/project" $(DOCKER_IMAGE_NAME):$(DOCKER_TAG) bash


# ============================================================================
# DEVELOPMENT WORKFLOWS
# ============================================================================

# Quick development setup
dev-setup: install format lint mypy test

# Test different performance configurations
test-performance-configs:
	@echo "Testing different performance configurations..."
	@echo "1. Default configuration (fail fast):"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig; print('✅ Default config works')"
	@echo "2. Parallel processing enabled:"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig, PerformanceConfig; config = RepoMapConfig(project_root='.', performance=PerformanceConfig(max_workers=4)); print('✅ Parallel config works')"
	@echo "3. Fallback enabled:"
	PYTHONPATH=src python3 -c "from repomap_tool.models import RepoMapConfig, PerformanceConfig; config = RepoMapConfig(project_root='.', performance=PerformanceConfig(allow_fallback=True)); print('✅ Fallback config works')"

# Full development workflow
dev: dev-setup test-performance-configs test-cli

# Run performance demo
demo: install
	cd examples && $(shell pwd)/$(VENV_PYTHON) performance_demo.py


# ============================================================================
# CI & PIPELINE
# ============================================================================

# Run all CI checks
ci: build check test security
	@echo "CI pipeline completed successfully!"

# Complete CI workflow (local + Docker)
ci-all: format ci docker-test
	@echo "✅ Complete CI workflow completed successfully"
	@echo "🎯 All tests passed in both local and Docker environments"

# Run comprehensive nightly tests
nightly: install
	$(VENV_PYTHON) -m pytest tests/ -v --cov=src --cov-report=xml --cov-report=html --durations=10 -n auto --max-worker-restart=0 --dist=worksteal
	$(VENV_PYTHON) -m pytest tests/integration/test_self_integration.py -v --durations=10
	$(VENV_PYTHON) -m pytest tests/integration/ -v --durations=10 -n auto --max-worker-restart=0 --dist=worksteal

# Full CI simulation
full-ci: clean install ci test-performance-configs test-cli demo


# ============================================================================
# UTILITIES / CLEANUP
# ============================================================================

# Clean build artifacts and virtual environment
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

# Force kill any lingering test processes
kill-tests:
	@echo "💀 Force killing lingering test processes..."
	@pkill -f "pytest.*worker" 2>/dev/null || true
	@pkill -f "python.*pytest" 2>/dev/null || true
	@echo "✅ Test processes terminated"
