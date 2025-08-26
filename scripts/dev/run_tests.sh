#!/bin/bash
# Test runner script for Docker RepoMap Tool

set -e

echo "🧪 Running comprehensive tests for Docker RepoMap Tool..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'make setup' first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Run tests with coverage
echo "📊 Running pytest with coverage..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

# Run linting
echo "🔍 Running code linting..."
flake8 src/ tests/ --max-line-length=88 --count --show-source --statistics

# Run type checking
echo "🔍 Running type checking..."
mypy src/ --config-file pyproject.toml

# Run code formatting check
echo "🎨 Checking code formatting..."
black --check src/ tests/ --line-length=88

echo "✅ All tests completed successfully!"
