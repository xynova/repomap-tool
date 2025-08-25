# Docker RepoMap Tool

A portable code analysis tool that leverages aider libraries to generate comprehensive code maps with fuzzy and semantic matching capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Docker (optional)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd docker-repomap

# Setup development environment
make setup

# Install in development mode
make install-dev
```

### Usage

```bash
# Run the tool directly
python src/external_repomap.py /path/to/your/project

# Or use the new CLI (after make install-dev)
repomap-tool analyze /path/to/your/project
repomap-tool search /path/to/your/project "query"
repomap-tool config /path/to/your/project

# Use Docker
make docker-build
make docker-run
```

### CLI Commands

```bash
# Analyze a project
repomap-tool analyze /path/to/project --fuzzy --semantic

# Search for identifiers
repomap-tool search /path/to/project "user_auth" --match-type hybrid

# Generate configuration
repomap-tool config /path/to/project --output config.json

# Show version
repomap-tool version
```

## 🛠️ Development

### Available Commands

```bash
make help          # Show all available commands
make setup         # Setup development environment
make test          # Run tests
make lint          # Run linting (flake8)
make typecheck     # Run type checking (mypy)
make format        # Format code (black)
make clean         # Clean build artifacts
make build         # Build package
make docker-build  # Build Docker image
make docker-run    # Run Docker container
```

### Type Checking

This project uses **mypy** for static type checking:

```bash
# Run type checking
make typecheck

# Or directly
mypy src/ --config-file pyproject.toml
```

**Configuration:**
- Strict type checking enabled
- Requires type annotations for all functions
- Ignores missing imports for external libraries
- Excludes test files and cache directories

### Code Quality

- **Linting**: flake8 with max line length 88
- **Formatting**: black with line length 88
- **Type Checking**: mypy with strict settings
- **Testing**: pytest with coverage reporting
- **Dependencies**: Managed via `pyproject.toml` (modern Python standard)

## 📁 Project Structure

```
docker-repomap/
├── api/                    # API server and client examples
├── config/                 # Configuration files
├── docker/                 # Docker configurations
├── docs/                   # Documentation
├── examples/               # Usage examples
├── scripts/                # Utility scripts
├── src/                    # Main source code
│   ├── matchers/          # Matching algorithms
│   ├── repomap_tool/      # Main package
│   └── external_repomap.py # Entry point
├── tests/                  # Test files
├── Makefile               # Build automation
├── pyproject.toml         # Modern Python package config
├── setup.py               # Traditional package setup
├── mypy.ini              # Type checking configuration
└── README.md              # This file
```

## 🔧 Features

- **Fuzzy Matching**: String-based similarity matching
- **Semantic Matching**: Conceptual similarity using TF-IDF
- **Hybrid Matching**: Combines both approaches for comprehensive results
- **Docker Support**: Containerized deployment
- **API Server**: RESTful API for integration
- **Type Safety**: Full mypy support with strict type checking
- **Pydantic Integration**: Structured data validation and configuration management

## 📚 Documentation

- [Integration Guide](docs/README_INTEGRATION_SUMMARY.md)
- [API Documentation](docs/api/)
- [Development Guide](docs/guides/)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and type checking: `make test && make typecheck`
5. Format your code: `make format`
6. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.
