#!/bin/bash

# Setup Virtual Environment for Docker RepoMap
# This script creates an isolated environment for testing

set -e

echo "🐍 Setting up virtual environment for Docker RepoMap..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -e .[dev]

# Create .env file for environment variables
echo "⚙️ Creating .env file..."
cat > .env << 'EOF'
# Docker RepoMap Environment Variables
PYTHONPATH=${PYTHONPATH}:${PWD}
CACHE_DIR=${PWD}/cache
VERBOSE=true

# Development settings
DEBUG=true
LOG_LEVEL=DEBUG
EOF

# Create cache directory
echo "📁 Creating cache directory..."
mkdir -p cache

# Create test configuration
echo "🧪 Creating test configuration..."
cat > pytest.ini << 'EOF'
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --cov=.
    --cov-report=html
    --cov-report=term-missing
EOF

# Create .gitignore for the venv
echo "📝 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Virtual Environment
venv/
env/
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Cache
cache/
.aider.tags.cache.v4/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Logs
*.log
logs/
EOF

# Create activation script for easy access
echo "📝 Creating activation script..."
cat > activate_venv.sh << 'EOF'
#!/bin/bash
# Quick activation script for the virtual environment

if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run setup_venv.sh first."
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

echo "✅ Virtual environment activated!"
echo "📦 Installed packages:"
pip list

echo ""
echo "🚀 You can now run:"
echo "  python external_repomap.py /path/to/project --fuzzy-match"
echo "  pytest tests/"
echo "  python -m black ."
echo ""
EOF

chmod +x activate_venv.sh

# Create test runner script
echo "📝 Creating test runner script..."
cat > run_tests.sh << 'EOF'
#!/bin/bash
# Test runner script

set -e

echo "🧪 Running tests in virtual environment..."

# Activate virtual environment
source venv/bin/activate

# Run tests
echo "Running pytest..."
pytest tests/ -v

# Run linting
echo "Running black..."
python -m black . --check

echo "Running flake8..."
python -m flake8 . --max-line-length=88

echo "✅ All tests passed!"
EOF

chmod +x run_tests.sh

# Create development server script
echo "📝 Creating development server script..."
cat > run_dev_server.sh << 'EOF'
#!/bin/bash
# Development server script

set -e

echo "🚀 Starting development server..."

# Activate virtual environment
source venv/bin/activate

# Set development environment variables
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run the API server
python enhanced_api_server.py
EOF

chmod +x run_dev_server.sh

# Test the installation
echo "🧪 Testing installation..."
source venv/bin/activate

# Test imports
echo "Testing imports..."
python -c "
try:
    from fuzzy_matcher import FuzzyMatcher
    print('✅ fuzzy_matcher imported successfully')
except ImportError as e:
    print(f'❌ fuzzy_matcher import failed: {e}')

try:
    from adaptive_semantic_matcher import AdaptiveSemanticMatcher
    print('✅ adaptive_semantic_matcher imported successfully')
except ImportError as e:
    print(f'❌ adaptive_semantic_matcher import failed: {e}')

try:
    from hybrid_matcher import HybridMatcher
    print('✅ hybrid_matcher imported successfully')
except ImportError as e:
    print(f'❌ hybrid_matcher import failed: {e}')

try:
    from external_repomap import DockerRepoMap
    print('✅ external_repomap imported successfully')
except ImportError as e:
    print(f'❌ external_repomap import failed: {e}')
"

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Activate the environment: source venv/bin/activate"
echo "2. Or use the quick script: ./activate_venv.sh"
echo "3. Run tests: ./run_tests.sh"
echo "4. Start dev server: ./run_dev_server.sh"
echo ""
echo "🔧 Available scripts:"
echo "  ./activate_venv.sh  - Quick activation"
echo "  ./run_tests.sh      - Run all tests"
echo "  ./run_dev_server.sh - Start development server"
echo ""
echo "📁 Directory structure:"
echo "  venv/               - Virtual environment"
echo "  cache/              - Cache directory"
echo "  .env                - Environment variables"
echo "  pytest.ini          - Test configuration"
echo "  .gitignore          - Git ignore rules"
