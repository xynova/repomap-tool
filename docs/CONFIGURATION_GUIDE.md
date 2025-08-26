# RepoMap Tool Configuration Guide

This guide covers all configuration options for the RepoMap Tool, including CLI options, configuration files, and environment variables.

## 🚀 Quick Configuration

### **Basic CLI Configuration**

```bash
# Analyze with fuzzy matching
repomap-tool analyze /path/to/project --fuzzy

# Search with custom thresholds
repomap-tool search /path/to/project "query" --fuzzy-threshold 70 --semantic-threshold 60

# Generate configuration file
repomap-tool config /path/to/project --output config.json
```

## 📋 Configuration Options

### **CLI Command Options**

#### **Global Options**
- `--verbose` - Enable verbose output
- `--output FORMAT` - Output format (table, json, text)
- `--config FILE` - Configuration file path

#### **Analyze Command**
```bash
repomap-tool analyze /path/to/project [OPTIONS]
```

**Options:**
- `--fuzzy` - Enable fuzzy matching
- `--semantic` - Enable semantic matching  
- `--hybrid` - Enable hybrid matching (default)
- `--output FILE` - Output file path (default: stdout)
- `--verbose` - Verbose output

#### **Search Command**
```bash
repomap-tool search /path/to/project "query" [OPTIONS]
```

**Options:**
- `--match-type TYPE` - Matching strategy (fuzzy, semantic, hybrid)
- `--fuzzy-threshold N` - Fuzzy matching threshold (0-100, default: 80)
- `--semantic-threshold N` - Semantic matching threshold (0-100, default: 70)
- `--limit N` - Maximum number of results (default: 10)
- `--output FORMAT` - Output format (table, json, text)

#### **Config Command**
```bash
repomap-tool config /path/to/project [OPTIONS]
```

**Options:**
- `--output FILE` - Output configuration file path
- `--template TYPE` - Configuration template (basic, advanced, custom)

## ⚙️ Configuration Files

### **Basic Configuration**

Create a `repomap.json` file in your project root:

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 80,
    "strategies": ["prefix", "levenshtein"]
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 70,
    "model": "tfidf"
  },
  "hybrid_match": {
    "enabled": true,
    "fuzzy_weight": 0.6,
    "semantic_weight": 0.4
  },
  "output": {
    "format": "table",
    "limit": 10,
    "verbose": false
  },
  "cache": {
    "enabled": true,
    "directory": ".repomap_cache"
  }
}
```

### **Advanced Configuration**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 75,
    "strategies": ["prefix", "levenshtein", "jaro_winkler"],
    "case_sensitive": false,
    "normalize_whitespace": true
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 65,
    "model": "tfidf",
    "max_features": 1000,
    "ngram_range": [1, 2],
    "stop_words": "english"
  },
  "hybrid_match": {
    "enabled": true,
    "fuzzy_weight": 0.55,
    "semantic_weight": 0.45,
    "boost_exact_matches": true,
    "normalize_scores": true
  },
  "output": {
    "format": "json",
    "limit": 20,
    "verbose": true,
    "include_metadata": true,
    "sort_by": "score"
  },
  "cache": {
    "enabled": true,
    "directory": ".repomap_cache",
    "max_size_mb": 100,
    "ttl_hours": 24
  },
  "logging": {
    "level": "INFO",
    "file": "repomap.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### **Project-Specific Configuration**

You can create different configuration files for different projects:

```bash
# Generate configuration for current project
repomap-tool config /path/to/project --output .repomap.json

# Use specific configuration file
repomap-tool analyze /path/to/project --config .repomap.json
```

## 🔧 Environment Variables

### **Core Environment Variables**

```bash
# Cache configuration
export REPOMAP_CACHE_DIR="/path/to/cache"
export REPOMAP_CACHE_ENABLED="true"
export REPOMAP_CACHE_TTL="24"

# Logging configuration
export REPOMAP_LOG_LEVEL="INFO"
export REPOMAP_LOG_FILE="repomap.log"

# Output configuration
export REPOMAP_OUTPUT_FORMAT="table"
export REPOMAP_OUTPUT_LIMIT="10"

# Matching configuration
export REPOMAP_FUZZY_THRESHOLD="80"
export REPOMAP_SEMANTIC_THRESHOLD="70"
export REPOMAP_HYBRID_WEIGHTS="0.6,0.4"
```

### **Development Environment Variables**

```bash
# Development mode
export REPOMAP_DEBUG="true"
export REPOMAP_DEV_MODE="true"

# API configuration
export REPOMAP_API_HOST="localhost"
export REPOMAP_API_PORT="5000"

# Docker configuration
export REPOMAP_DOCKER_IMAGE="repomap-tool"
export REPOMAP_DOCKER_TAG="latest"
```

## 🎯 Configuration Templates

### **Template: Basic**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 80
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 70
  },
  "output": {
    "format": "table",
    "limit": 10
  }
}
```

### **Template: Advanced**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 75,
    "strategies": ["prefix", "levenshtein", "jaro_winkler"]
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 65,
    "model": "tfidf",
    "max_features": 1000
  },
  "hybrid_match": {
    "enabled": true,
    "fuzzy_weight": 0.55,
    "semantic_weight": 0.45
  },
  "output": {
    "format": "json",
    "limit": 20,
    "verbose": true
  },
  "cache": {
    "enabled": true,
    "directory": ".repomap_cache"
  }
}
```

### **Template: Custom**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 90,
    "strategies": ["levenshtein"]
  },
  "semantic_match": {
    "enabled": false
  },
  "output": {
    "format": "text",
    "limit": 5
  }
}
```

## 🔄 Configuration Precedence

Configuration options are applied in the following order (highest to lowest priority):

1. **CLI arguments** - Command-line options
2. **Configuration file** - `repomap.json` or specified config file
3. **Environment variables** - System environment variables
4. **Default values** - Built-in defaults

### **Example Precedence**

```bash
# CLI argument overrides config file
repomap-tool search /path/to/project "query" --fuzzy-threshold 90

# Environment variable overrides default
export REPOMAP_FUZZY_THRESHOLD="85"
repomap-tool search /path/to/project "query"  # Uses 85

# CLI argument overrides environment variable
export REPOMAP_FUZZY_THRESHOLD="85"
repomap-tool search /path/to/project "query" --fuzzy-threshold 90  # Uses 90
```

## 🐳 Docker Configuration

### **Docker Environment Variables**

```bash
# Run with environment variables
docker run --rm \
  -e REPOMAP_FUZZY_THRESHOLD=85 \
  -e REPOMAP_SEMANTIC_THRESHOLD=65 \
  -e REPOMAP_OUTPUT_FORMAT=json \
  -v $(pwd):/project \
  repomap-tool analyze /project
```

### **Docker Configuration File**

Create a `docker-config.json`:

```json
{
  "environment": {
    "REPOMAP_FUZZY_THRESHOLD": "85",
    "REPOMAP_SEMANTIC_THRESHOLD": "65",
    "REPOMAP_OUTPUT_FORMAT": "json"
  },
  "volumes": {
    "cache": "/app/cache",
    "project": "/project"
  }
}
```

## 🚨 Configuration Validation

### **Validation Rules**

- **Thresholds**: Must be between 0 and 100
- **Weights**: Must sum to 1.0 for hybrid matching
- **File paths**: Must be valid and accessible
- **Formats**: Must be one of: table, json, text

### **Validation Examples**

```bash
# Valid configuration
repomap-tool search /path/to/project "query" --fuzzy-threshold 85

# Invalid configuration (will show error)
repomap-tool search /path/to/project "query" --fuzzy-threshold 150
# Error: Fuzzy threshold must be between 0 and 100

# Valid hybrid weights
repomap-tool search /path/to/project "query" --match-type hybrid

# Invalid hybrid weights (will show error)
# Error: Hybrid weights must sum to 1.0
```

## 📚 Configuration Examples

### **Development Setup**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 70
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 60
  },
  "output": {
    "format": "table",
    "verbose": true
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

### **Production Setup**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 85
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 75
  },
  "output": {
    "format": "json",
    "limit": 20
  },
  "cache": {
    "enabled": true,
    "ttl_hours": 48
  },
  "logging": {
    "level": "WARNING"
  }
}
```

### **CI/CD Setup**

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 80
  },
  "semantic_match": {
    "enabled": false
  },
  "output": {
    "format": "json",
    "limit": 50
  },
  "cache": {
    "enabled": false
  }
}
```

## 📚 Next Steps

- Read the **[CLI Guide](README-CLI.md)** for command-line usage
- Check **[API Guide](API_GUIDE.md)** for programmatic configuration
- Explore **[Matching Algorithms](MATCHING_ALGORITHM_GUIDE.md)** for algorithm details
