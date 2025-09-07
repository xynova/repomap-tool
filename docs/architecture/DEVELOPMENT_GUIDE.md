# RepoMap-Tool Development Guide

## 🐍 **Virtual Environment Setup**

This guide explains how to set up and use the isolated development environment for RepoMap-Tool.

## 🚀 **Quick Start**

### **1. Setup Virtual Environment**
```bash
# Make the setup script executable
chmod +x setup_venv.sh

# Run the setup script
./setup_venv.sh
```

### **2. Activate Environment**
```bash
# Option 1: Use the quick activation script
./activate_venv.sh

# Option 2: Manual activation
source venv/bin/activate
```

### **3. Test Installation**
```bash
# Run tests
./run_tests.sh

# Start development server
./run_dev_server.sh
```

## 📁 **Directory Structure After Setup**

```
docker-repomap/
├── 📁 venv/                    # Virtual environment
├── 📁 cache/                   # Cache directory
├── 📄 .env                     # Environment variables
├── 📄 pytest.ini              # Test configuration
├── 📄 .gitignore              # Git ignore rules
├── 📄 setup_venv.sh           # Setup script
├── 📄 activate_venv.sh        # Quick activation
├── 📄 run_tests.sh            # Test runner
├── 📄 run_dev_server.sh       # Dev server
├── 📄 Dockerfile.venv         # Docker with venv
├── 📄 docker-compose.dev.yml  # Development compose
└── [existing files...]
```

## 🔧 **Development Workflow**

### **Local Development**

1. **Activate Environment**
   ```bash
   source venv/bin/activate
   ```

2. **Run Tests**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test
   pytest tests/test_fuzzy_matcher.py -v
   
   # Run with coverage
   pytest tests/ --cov=. --cov-report=html
   ```

3. **Code Quality**
   ```bash
   # Format code
   black .
   
   # Check formatting
   black . --check
   
   # Lint code
   flake8 . --max-line-length=88
   
   # Type checking
   mypy .
   ```

4. **Run Tool**
   ```bash
   # Basic usage
   python external_repomap.py /path/to/project --fuzzy-match
   
   # Advanced usage
   python external_repomap.py /path/to/project \
       --mentioned-idents "auth,user,login" \
       --fuzzy-match \
       --fuzzy-threshold 70 \
       --adaptive-semantic \
       --semantic-threshold 0.2
   ```

### **Docker Development**

1. **Build Development Image**
   ```bash
   docker build -f Dockerfile.venv -t repomap-dev .
   ```

2. **Run Development Container**
   ```bash
   # Interactive shell
   docker run -it --rm \
       -v $(pwd):/app \
       -v $(pwd)/cache:/app/cache \
       -v ../aider:/aider \
       repomap-dev /bin/bash
   
   # Run tool directly
   docker run --rm \
       -v /path/to/project:/project \
       -v $(pwd)/cache:/app/cache \
       repomap-dev \
       python external_repomap.py /project --fuzzy-match
   ```

3. **Use Docker Compose**
   ```bash
   # Development environment
   docker-compose -f docker-compose.dev.yml up repomap-dev
   
   # API server
   docker-compose -f docker-compose.dev.yml up repomap-api-dev
   
   # Run tests
   docker-compose -f docker-compose.dev.yml up repomap-test
   ```

## 🧪 **Testing**

### **Test Structure**
```
tests/
├── test_adaptive_matcher.py
├── test_hybrid_matcher.py
├── test_fuzzy_matcher.py
├── test_semantic_matcher.py
└── test_integrated_adaptive.sh
```

### **Running Tests**

```bash
# All tests
./run_tests.sh

# Specific test file
pytest tests/test_fuzzy_matcher.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html

# Debug mode
pytest tests/ -v -s --pdb
```

### **Writing Tests**

```python
# Example test structure
import pytest
from fuzzy_matcher import FuzzyMatcher

class TestFuzzyMatcher:
    def test_basic_matching(self):
        matcher = FuzzyMatcher(threshold=70)
        query = "auth"
        identifiers = {"authentication", "auth_token", "user_auth"}
        
        results = matcher.match_identifiers(query, identifiers)
        
        assert len(results) > 0
        assert any("auth" in result[0] for result in results)
```

## 🔍 **Debugging**

### **Environment Variables**
```bash
# Set debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Run with debug output
python external_repomap.py /path/to/project --verbose
```

### **Logging**
```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### **Interactive Debugging**
```bash
# Start Python shell with environment
source venv/bin/activate
python -i

# Import and test
>>> from fuzzy_matcher import FuzzyMatcher
>>> matcher = FuzzyMatcher()
>>> # Test interactively
```

## 📦 **Package Development**

### **Testing Package Installation**
```bash
# Build package
python setup.py sdist bdist_wheel

# Install in development mode
pip install -e .

# Test installation
python -c "import repomap_tool; print('Package installed successfully')"
```

### **Dependency Management**
```bash
# Update requirements
pip freeze > requirements.txt

# Install new dependency
pip install new-package
pip freeze > requirements.txt
```

## 🐳 **Docker Development**

### **Building Images**
```bash
# Development image
docker build -f Dockerfile.venv -t repomap-dev .

# Production image
docker build -f Dockerfile -t repomap-prod .
```

### **Running Containers**
```bash
# Development container with volume mounts
docker run -it --rm \
    -v $(pwd):/app \
    -v $(pwd)/cache:/app/cache \
    -v ../aider:/aider \
    -e DEBUG=true \
    repomap-dev

# Production container
docker run --rm \
    -v /path/to/project:/project \
    repomap-prod /project
```

### **Docker Compose Services**
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up

# Start specific service
docker-compose -f docker-compose.dev.yml up repomap-dev

# Run tests in container
docker-compose -f docker-compose.dev.yml run repomap-test
```

## 🔄 **Continuous Integration**

### **GitHub Actions Example**
```yaml
name: Test RepoMap-Tool

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
          pip install pytest pytest-cov black flake8
      
      - name: Run tests
        run: |
          source venv/bin/activate
          pytest tests/ --cov=. --cov-report=xml
      
      - name: Run linting
        run: |
          source venv/bin/activate
          black . --check
          flake8 . --max-line-length=88
```

## 🚨 **Troubleshooting**

### **Common Issues**

1. **Import Errors**
   ```bash
   # Make sure virtual environment is activated
   source venv/bin/activate
   
   # Check Python path
   echo $PYTHONPATH
   
   # Reinstall dependencies
   pip install -r requirements.txt
   ```

2. **Aider Import Errors**
   ```bash
   # Check if aider is installed
   pip list | grep aider
   
   # Install aider in development mode
   pip install -e ../aider
   ```

3. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   
   # Rebuild without cache
   docker build --no-cache -f Dockerfile.venv -t repomap-dev .
   ```

4. **Permission Issues**
   ```bash
   # Make scripts executable
   chmod +x *.sh
   
   # Fix file permissions
   sudo chown -R $USER:$USER .
   ```

## 📚 **Additional Resources**

- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **Docker Development**: https://docs.docker.com/develop/
- **Pytest Documentation**: https://docs.pytest.org/
- **Black Code Formatter**: https://black.readthedocs.io/
- **Flake8 Linter**: https://flake8.pycqa.org/

---

*This development environment provides a clean, isolated space for testing and developing the RepoMap-Tool tool while maintaining all the benefits of the aider integration.*
