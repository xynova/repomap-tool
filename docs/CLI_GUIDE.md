# RepoMap Tool CLI Guide

This guide shows how to use the RepoMap Tool from the command line.

## 🚀 Quick Start

### **Installation**
```bash
# Clone the repository
git clone <repository-url>
cd repomap-tool

# Build and run with Docker (recommended)
make docker-build
make docker-run

# Or run directly with Docker
docker run --rm -v $(pwd):/project repomap-tool analyze /project
```

### **Basic Usage**
```bash
# Inspect a project (comprehensive analysis)
repomap-tool inspect overview /path/to/project

# Find identifiers
repomap-tool inspect find /path/to/project "user authentication"

# Inspect centrality analysis
repomap-tool inspect centrality /path/to/project

# Generate configuration
repomap-tool config /path/to/project

# Show version
repomap-tool version
```

## 📋 Available Commands

### **`inspect`** - Code Inspection and Analysis
Inspect and analyze code repository structure, dependencies, and patterns.

```bash
repomap-tool inspect <subcommand> [OPTIONS]
```

**Subcommands:**
- `find` - Find identifiers using intelligent matching
- `cycles` - Inspect for circular dependencies
- `centrality` - Inspect file importance and centrality
- `impact` - Inspect change impact analysis
- `overview` - Comprehensive project inspection

**Examples:**
```bash
# Find identifiers with fuzzy matching
repomap-tool inspect find /path/to/project "user authentication" --match-type fuzzy

# Inspect centrality analysis
repomap-tool inspect centrality /path/to/project --files auth.py,user.py

# Inspect impact of changes
repomap-tool inspect impact /path/to/project --files auth.py
```

## ⚠️ Deprecated Commands

The following commands are deprecated and will be removed in a future version:

- `repomap-tool analyze` → Use `repomap-tool inspect` instead
- `repomap-tool search` → Use `repomap-tool inspect find` instead

**Migration Guide:**
```bash
# Old commands (deprecated)
repomap-tool analyze /path/to/project
repomap-tool search /path/to/project "query"

# New commands (recommended)
repomap-tool inspect overview /path/to/project
repomap-tool inspect find /path/to/project "query"

# Fuzzy search with custom threshold
repomap-tool search /path/to/project "auth" --match-type fuzzy --fuzzy-threshold 60

# Semantic search
repomap-tool search /path/to/project "data processing" --match-type semantic

# Hybrid search (recommended)
repomap-tool search /path/to/project "user management" --match-type hybrid --limit 20
```

### **`config`** - Configuration Management
Generate and manage configuration files.

```bash
repomap-tool config /path/to/project [OPTIONS]
```

**Options:**
- `--output FILE` - Output configuration file path
- `--template TYPE` - Configuration template (basic, advanced, custom)

**Examples:**
```bash
# Generate basic configuration
repomap-tool config /path/to/project

# Generate configuration file
repomap-tool config /path/to/project --output config.json

# Generate advanced configuration
repomap-tool config /path/to/project --template advanced
```

### **`version`** - Version Information
Display version and build information.

```bash
repomap-tool version
```

## 🐳 Docker Usage

### **Build and Run**
```bash
# Build the Docker image
make docker-build

# Run with Docker
make docker-run

# Or run directly
docker run --rm -v $(pwd):/project repomap-tool analyze /project
```

### **Docker Examples**
```bash
# Analyze current directory
docker run --rm -v $(pwd):/project repomap-tool analyze /project

# Search for specific terms
docker run --rm -v $(pwd):/project repomap-tool search /project "user auth"

# Generate configuration
docker run --rm -v $(pwd):/project repomap-tool config /project
```

## 🎯 Use Cases

### **1. Project Onboarding**
```bash
# Get a quick overview of a new project
repomap-tool analyze /path/to/project --verbose
```

### **2. Code Discovery**
```bash
# Find all authentication-related code
repomap-tool search /path/to/project "authentication login user" --match-type hybrid
```

### **3. Refactoring Planning**
```bash
# Find all usages of a specific pattern
repomap-tool search /path/to/project "process_data" --fuzzy-threshold 70
```

### **4. Architecture Analysis**
```bash
# Analyze project structure
repomap-tool analyze /path/to/project --output architecture.txt
```

## 🔧 Configuration

### **Environment Variables**
- `REPOMAP_CACHE_DIR` - Cache directory path
- `REPOMAP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REPOMAP_CONFIG_FILE` - Configuration file path

### **Configuration File**
Create a `repomap.json` file in your project:

```json
{
  "fuzzy_match": {
    "threshold": 80,
    "strategies": ["prefix", "levenshtein"]
  },
  "semantic_match": {
    "threshold": 70,
    "model": "tfidf"
  },
  "hybrid_match": {
    "fuzzy_weight": 0.6,
    "semantic_weight": 0.4
  },
  "output": {
    "format": "table",
    "limit": 10
  }
}
```

## 🚨 Troubleshooting

### **Common Issues**

**"No module named 'repomap_tool'"**
```bash
# Install in development mode
make install-dev
```

**"Docker daemon not running"**
```bash
# Start Docker Desktop or Docker daemon
# Then try again
make docker-build
```

**"Permission denied"**
```bash
# Use sudo for Docker commands if needed
sudo docker run --rm -v $(pwd):/project repomap-tool analyze /project
```

### **Getting Help**
```bash
# Show help for any command
repomap-tool --help
repomap-tool analyze --help
repomap-tool search --help
```

## 📚 Next Steps

- Check **[Configuration Guide](CONFIGURATION_GUIDE.md)** for advanced options
- Explore **[Matching Algorithms](MATCHING_ALGORITHM_GUIDE.md)** for technical details
