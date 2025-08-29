#!/bin/bash
# Self-Integration Test Runner for repomap-tool
#
# This script runs comprehensive integration tests that test the repomap-tool
# against itself, covering all major functionality.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  repomap-tool Self-Integration Tests  ${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Check if we're in the right directory
if [[ ! -f "$PROJECT_ROOT/src/repomap_tool/core.py" ]]; then
    echo -e "${RED}Error: Not in repomap-tool project root${NC}"
    echo "Expected to find: $PROJECT_ROOT/src/repomap_tool/core.py"
    exit 1
fi

echo -e "${YELLOW}Project root: $PROJECT_ROOT${NC}"
echo

# Check Python environment
echo -e "${BLUE}Checking Python environment...${NC}"
if ! command -v python &> /dev/null; then
    echo -e "${RED}Error: python not found${NC}"
    exit 1
fi

PYTHON_VERSION=$(python --version)
echo -e "${GREEN}Python version: $PYTHON_VERSION${NC}"

# Check if pytest is available
if ! python -c "import pytest" 2>/dev/null; then
    echo -e "${YELLOW}Installing pytest...${NC}"
    pip install pytest
fi

# Check if required dependencies are available
echo -e "${BLUE}Checking dependencies...${NC}"
MISSING_DEPS=()

# Check for pydantic
if ! python -c "import pydantic" 2>/dev/null; then
    MISSING_DEPS+=("pydantic")
fi

# Check for click
if ! python -c "import click" 2>/dev/null; then
    MISSING_DEPS+=("click")
fi

# Check for rich
if ! python -c "import rich" 2>/dev/null; then
    MISSING_DEPS+=("rich")
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Installing missing dependencies: ${MISSING_DEPS[*]}${NC}"
    pip install "${MISSING_DEPS[@]}"
fi

echo -e "${GREEN}Dependencies check complete${NC}"
echo

# Check if virtual environment exists
if [[ -d "$PROJECT_ROOT/venv" ]]; then
    echo -e "${BLUE}Found virtual environment, activating...${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
    echo -e "${GREEN}Virtual environment activated${NC}"
else
    echo -e "${YELLOW}No virtual environment found, using system Python${NC}"
    echo -e "${YELLOW}Consider running: ./scripts/setup/setup_venv.sh${NC}"
fi

# Set up Python path
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

# Run the self-integration tests
echo -e "${BLUE}Running self-integration tests...${NC}"
echo

cd "$PROJECT_ROOT"

# Run tests with verbose output and coverage
python -m pytest tests/integration/test_self_integration.py \
    -v \
    --tb=short \
    --color=yes \
    --durations=10 \
    --maxfail=3

TEST_EXIT_CODE=$?

echo
echo -e "${BLUE}========================================${NC}"

if [[ $TEST_EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}✅ All self-integration tests passed!${NC}"
    echo
    echo -e "${GREEN}Test Summary:${NC}"
    echo -e "  • Default analysis (classes, functions, etc.)"
    echo -e "  • Fuzzy search (independent)"
    echo -e "  • Semantic search (independent)"
    echo -e "  • Hybrid search (fuzzy + semantic combination)"
    echo -e "  • Specific identifier search"
    echo -e "  • Context inclusion"
    echo -e "  • Result ranking"
    echo -e "  • Error handling"
    echo -e "  • Performance benchmarking"
else
    echo -e "${RED}❌ Some self-integration tests failed${NC}"
    echo -e "${YELLOW}Check the output above for details${NC}"
fi

echo -e "${BLUE}========================================${NC}"

# Optional: Run with coverage
if command -v coverage &> /dev/null; then
    echo
    echo -e "${BLUE}Running with coverage...${NC}"
    coverage run -m pytest tests/integration/test_self_integration.py -v
    coverage report --show-missing
elif python -c "import coverage" 2>/dev/null; then
    echo
    echo -e "${BLUE}Running with coverage...${NC}"
    python -m coverage run -m pytest tests/integration/test_self_integration.py -v
    python -m coverage report --show-missing
fi

exit $TEST_EXIT_CODE
