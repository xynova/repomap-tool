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
# Analyze a project
repomap-tool analyze /path/to/project

# Search for identifiers
repomap-tool search /path/to/project "user authentication"

# Generate configuration
repomap-tool config /path/to/project

# Show version
repomap-tool version
```

## 📋 Available Commands

### **`analyze`** - Project Analysis
Analyzes a project and generates a comprehensive code map.

```bash
repomap-tool analyze /path/to/project [OPTIONS]
```

**Options:**
- `--fuzzy` - Enable fuzzy matching
- `--semantic` - Enable semantic matching
- `--hybrid` - Enable hybrid matching (default)
- `--output FILE` - Output file path (default: stdout)
- `--verbose` - Verbose output

**Examples:**
```bash
# Basic analysis
repomap-tool analyze /path/to/project

# With fuzzy matching
repomap-tool analyze /path/to/project --fuzzy

# With semantic matching
repomap-tool analyze /path/to/project --semantic

# Hybrid analysis (recommended)
repomap-tool analyze /path/to/project --hybrid --verbose
```

### **`search`** - Identifier Search
Search for identifiers using fuzzy and semantic matching.

```bash
repomap-tool search /path/to/project "query" [OPTIONS]
```

**Options:**
- `--match-type TYPE` - Matching strategy (fuzzy, semantic, hybrid)
- `--fuzzy-threshold N` - Fuzzy matching threshold (0-100, default: 80)
- `--semantic-threshold N` - Semantic matching threshold (0-100, default: 70)
- `--limit N` - Maximum number of results (default: 10)
- `--output FORMAT` - Output format (table, json, text)

**Examples:**
```bash
# Search for authentication-related code
repomap-tool search /path/to/project "user authentication"

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

- Read the **[API Guide](API_GUIDE.md)** for programmatic access
- Check **[Configuration Guide](CONFIGURATION_GUIDE.md)** for advanced options
- Explore **[Matching Algorithms](MATCHING_ALGORITHM_GUIDE.md)** for technical details
