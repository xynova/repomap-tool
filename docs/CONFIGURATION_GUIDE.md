# RepoMap Tool Configuration Guide

This guide covers all configuration options for the RepoMap Tool, including CLI options, configuration files, and environment variables.

## 🚀 Quick Configuration

### **Basic CLI Configuration**

```bash
# Analyze with fuzzy matching
repomap-tool analyze /path/to/project --fuzzy

# Search with custom thresholds (project path optional if config exists)
repomap-tool search "query" /path/to/project --threshold 0.7

# Search using config file project_root (no need to specify project path)
repomap-tool search "query" --config config.json

# Generate configuration file
repomap-tool config /path/to/project --output config.json
```

### **🎯 Improved Usability**

The search command now supports **optional project paths** when a configuration file is available:

```bash
# After creating a config file, you can search without specifying the project path
repomap-tool index config /path/to/project --output .repomap/config.json
repomap-tool search "my_function"  # Uses project_root from config file

# Or specify a config file explicitly
repomap-tool search "my_function" --config /path/to/config.json

# Traditional usage still works
repomap-tool search "my_function" /path/to/project
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
repomap-tool search "query" [PROJECT_PATH] [OPTIONS]
```

**Arguments:**
- `query` - Search query (required)
- `PROJECT_PATH` - Project directory path (optional if config file exists)

**Options:**
- `--config FILE` - Configuration file path (optional)
- `--match-type TYPE` - Matching strategy (fuzzy, semantic, hybrid)
- `--threshold N` - Match threshold (0.0-1.0, default: 0.7)
- `--max-results N` - Maximum number of results (default: 10)
- `--output FORMAT` - Output format (json, text, table)

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

Environment variables provide a powerful way to override configuration settings without modifying files. They take precedence over file-based configuration but are overridden by CLI arguments.

### **Core Configuration Variables**

```bash
# Basic settings
export REPOMAP_VERBOSE="true"
export REPOMAP_LOG_LEVEL="DEBUG"
export REPOMAP_OUTPUT_FORMAT="json"
export REPOMAP_MAX_RESULTS="100"
export REPOMAP_REFRESH_CACHE="true"

# Cache configuration
export REPOMAP_CACHE_DIR="/path/to/cache"
export CACHE_DIR="/path/to/cache"  # Legacy support
```

### **Performance Configuration Variables**

```bash
# Parallel processing
export REPOMAP_MAX_WORKERS="8"
export REPOMAP_PARALLEL_THRESHOLD="20"
export REPOMAP_ALLOW_FALLBACK="false"

# Memory and caching
export REPOMAP_CACHE_SIZE="2000"
export REPOMAP_MAX_MEMORY_MB="200"
export REPOMAP_CACHE_TTL="7200"

# Progress and monitoring
export REPOMAP_ENABLE_PROGRESS="true"
export REPOMAP_ENABLE_MONITORING="true"
```

### **Fuzzy Matching Configuration Variables**

```bash
# Fuzzy matching settings
export REPOMAP_FUZZY_THRESHOLD="85"
export REPOMAP_FUZZY_STRATEGIES="levenshtein,jaro_winkler,prefix"
export REPOMAP_FUZZY_CACHE_RESULTS="true"
```

### **Semantic Matching Configuration Variables**

```bash
# Semantic matching settings
export REPOMAP_SEMANTIC_ENABLED="true"
export REPOMAP_SEMANTIC_THRESHOLD="0.8"
export REPOMAP_SEMANTIC_USE_TFIDF="true"
export REPOMAP_SEMANTIC_MIN_WORD_LENGTH="3"
export REPOMAP_SEMANTIC_CACHE_RESULTS="true"
```

### **Tree Exploration Configuration Variables**

```bash
# Tree settings
export REPOMAP_TREE_MAX_DEPTH="5"
export REPOMAP_TREE_MAX_TREES_PER_SESSION="20"
export REPOMAP_TREE_ENTRYPOINT_THRESHOLD="0.8"
export REPOMAP_TREE_ENABLE_CODE_SNIPPETS="true"
export REPOMAP_TREE_CACHE_STRUCTURES="true"
```

### **Dependency Analysis Configuration Variables**

```bash
# Dependency analysis settings
export REPOMAP_DEP_CACHE_GRAPHS="true"
export REPOMAP_DEP_MAX_GRAPH_SIZE="5000"
export REPOMAP_DEP_ENABLE_CALL_GRAPH="true"
export REPOMAP_DEP_ENABLE_IMPACT_ANALYSIS="true"
export REPOMAP_DEP_CENTRALITY_ALGORITHMS="degree,betweenness,pagerank"
export REPOMAP_DEP_MAX_CENTRALITY_CACHE_SIZE="500"
export REPOMAP_DEP_PERFORMANCE_THRESHOLD_SECONDS="15.0"
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

1. **CLI arguments** - Command-line options (highest priority)
2. **Environment variables** - System environment variables
3. **Configuration file** - `repomap.json` or specified config file
4. **Default values** - Built-in defaults (lowest priority)

### **Example Precedence**

```bash
# Environment variable overrides config file
export REPOMAP_FUZZY_THRESHOLD="85"
repomap-tool search /path/to/project "query"  # Uses 85 (env var overrides file)

# CLI argument overrides environment variable
export REPOMAP_FUZZY_THRESHOLD="85"
repomap-tool search /path/to/project "query" --fuzzy-threshold 90  # Uses 90 (CLI overrides env var)

# Complete precedence chain example:
# 1. Config file sets fuzzy_threshold: 70
# 2. Environment variable REPOMAP_FUZZY_THRESHOLD="80" overrides file
# 3. CLI argument --fuzzy-threshold 90 overrides environment variable
# Final result: fuzzy_threshold = 90
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

### **Improved Search Workflow**

```bash
# 1. Create a configuration file for your project
repomap-tool index config /path/to/my-project --output .repomap/config.json

# 2. Now you can search without specifying the project path every time
repomap-tool search "UserService"                    # Uses project_root from config
repomap-tool search "database" --threshold 0.8       # Uses project_root from config
repomap-tool search "auth" --output json             # Uses project_root from config

# 3. Or specify a different config file
repomap-tool search "UserService" --config /path/to/other-config.json

# 4. Traditional usage still works for one-off searches
repomap-tool search "UserService" /path/to/different-project
```

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

- Read the **[CLI Guide](CLI_GUIDE.md)** for command-line usage
- Explore **[Matching Algorithms](MATCHING_ALGORITHM_GUIDE.md)** for algorithm details
