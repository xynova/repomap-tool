# RepoMap Tool - Docker CLI Instructions for LLMs

## Overview

RepoMap Tool is an intelligent code analysis engine that helps AI assistants navigate and understand large codebases. It combines fuzzy matching and semantic analysis to provide comprehensive code discovery capabilities.

## Quick Reference

### Docker Image
- **Latest Release**: `ghcr.io/xynova/repomap-tool:latest`
- **Nightly Build**: `ghcr.io/xynova/repomap-tool:nightly`
- **Local Build**: `repomap-tool:latest`

### Basic Docker Command Pattern
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest <command> /workspace [options]
```

## Available Commands

### 1. `analyze` - Project Analysis
**Purpose**: Analyzes a project and generates a comprehensive code map.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace
```

**Options**:
- `--fuzzy` - Enable fuzzy matching only
- `--semantic` - Enable semantic matching only  
- `--hybrid` - Enable hybrid matching (default, recommended)
- `--output FILE` - Output file path (default: stdout)
- `--verbose` - Verbose output with detailed information

**Examples**:
```bash
# Basic analysis with hybrid matching
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace

# Verbose analysis with output file
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --verbose --output analysis.txt

# Fuzzy matching only
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --fuzzy
```

### 2. `search` - Code Search
**Purpose**: Search for identifiers, functions, and code patterns using intelligent matching.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "query"
```

**Options**:
- `--match-type TYPE` - Matching strategy (fuzzy, semantic, hybrid)
- `--fuzzy-threshold N` - Fuzzy matching threshold (0-100, default: 80)
- `--semantic-threshold N` - Semantic matching threshold (0-100, default: 70)
- `--limit N` - Maximum number of results (default: 10)
- `--output FORMAT` - Output format (table, json, text)

**Examples**:
```bash
# Search for authentication-related code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "user authentication"

# Fuzzy search with custom threshold
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "auth" --match-type fuzzy --fuzzy-threshold 60

# Semantic search for data processing
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "data processing" --match-type semantic

# Hybrid search with more results
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "user management" --match-type hybrid --limit 20

# JSON output for programmatic use
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "error handling" --output json
```

### 3. `config` - Configuration Management
**Purpose**: Generate and manage configuration files for the tool.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest config /workspace
```

**Options**:
- `--output FILE` - Output configuration file path
- `--template TYPE` - Configuration template (basic, advanced, custom)

**Examples**:
```bash
# Generate basic configuration
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest config /workspace

# Generate configuration file
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest config /workspace --output repomap.json

# Generate advanced configuration
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest config /workspace --template advanced
```

### 4. `version` - Version Information
**Purpose**: Display version and build information.

**Usage**:
```bash
docker run --rm ghcr.io/xynova/repomap-tool:latest version
```

## Volume Mounting Best Practices

### Cache Persistence
Always mount a cache directory to improve performance across runs:
```bash
-v $(pwd)/.repomap:/app/cache
```

### Project Access
Mount your project directory as `/workspace`:
```bash
-v /path/to/your/project:/workspace
```

### Complete Example
```bash
docker run --rm \
  -v $(pwd)/.repomap:/app/cache \
  -v /path/to/your/project:/workspace \
  ghcr.io/xynova/repomap-tool:latest \
  search /workspace "authentication"
```

## Common Use Cases for LLMs

### 1. Code Discovery
When an LLM needs to understand how a specific feature works:

```bash
# Find all authentication-related code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "user login authentication" --match-type hybrid --limit 15

# Find data processing functions
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "data processing pipeline" --match-type semantic
```

### 2. Refactoring Planning
When an LLM needs to understand dependencies before making changes:

```bash
# Find all usages of a specific function
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "process_data" --fuzzy-threshold 70

# Analyze project structure first
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --verbose
```

### 3. Architecture Understanding
When an LLM needs to understand the overall codebase structure:

```bash
# Get comprehensive project analysis
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --hybrid --verbose --output architecture.txt

# Find related modules
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "database connection" --match-type hybrid
```

### 4. Error Handling Discovery
When an LLM needs to find error handling patterns:

```bash
# Find error handling code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "error handling exception" --match-type hybrid --limit 20
```

## Search Strategies Explained

### Fuzzy Matching
Best for finding code when you know part of the name or there are naming variations.

**Example**: Searching for "userAuth" will find:
- `userAuth`
- `user_auth` 
- `UserAuth`
- `authenticateUser`
- `userAuthentication`

### Semantic Matching
Best for finding code based on what it does, regardless of naming.

**Example**: Searching for "user authentication" will find:
- Functions that handle login/logout
- Password validation code
- Session management
- Authorization checks
- Security-related utilities

### Hybrid Matching (Recommended)
Combines both fuzzy and semantic approaches for comprehensive results.

**Example**: Searching for "data processing" will find:
- Functions with "process" in the name (fuzzy)
- Functions that transform or manipulate data (semantic)
- Related utilities and helpers
- Pipeline components

## Performance Tips

### 1. Use Cache Persistence
Always mount a cache directory to avoid re-analyzing unchanged code:
```bash
-v $(pwd)/.repomap:/app/cache
```

### 2. Start with Analysis
For large projects, run analysis first to build the code map:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace
```

### 3. Use Appropriate Limits
Limit search results to avoid overwhelming output:
```bash
--limit 10  # Default
--limit 20  # For broader searches
--limit 5   # For focused searches
```

### 4. Choose the Right Match Type
- **Fuzzy**: When you know the exact name or similar names
- **Semantic**: When you know the functionality but not the name
- **Hybrid**: For comprehensive results (recommended)

## Troubleshooting

### Common Issues

**1. "No such file or directory"**
```bash
# Ensure the project path is correct and accessible
ls -la /path/to/your/project
```

**2. "Permission denied"**
```bash
# Check Docker permissions or use sudo
sudo docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace
```

**3. "Docker daemon not running"**
```bash
# Start Docker Desktop or Docker daemon
# On macOS: Start Docker Desktop
# On Linux: sudo systemctl start docker
```

**4. Slow performance**
```bash
# Use cache persistence
-v $(pwd)/.repomap:/app/cache

# Run analysis first for large projects
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace
```

### Getting Help
```bash
# Show help for any command
docker run --rm ghcr.io/xynova/repomap-tool:latest --help
docker run --rm ghcr.io/xynova/repomap-tool:latest analyze --help
docker run --rm ghcr.io/xynova/repomap-tool:latest search --help
```

## Example Workflows

### Workflow 1: Understanding a New Codebase
```bash
# 1. Get project overview
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --verbose

# 2. Find main entry points
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "main entry point" --match-type semantic

# 3. Understand authentication
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "authentication login" --match-type hybrid
```

### Workflow 2: Planning a Refactor
```bash
# 1. Find all usages of the function to refactor
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "old_function_name" --fuzzy-threshold 70

# 2. Find similar patterns
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "similar functionality" --match-type semantic

# 3. Analyze dependencies
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest analyze /workspace --output dependencies.txt
```

### Workflow 3: Debugging Issues
```bash
# 1. Find error handling code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "error handling exception" --match-type hybrid

# 2. Find logging code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "logging debug" --match-type semantic

# 3. Find validation code
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest search /workspace "validation check" --match-type hybrid
```

## Integration with AI Assistants

### For LLM Context Gathering
When an LLM needs to understand code context:

1. **Start with analysis** to build the code map
2. **Use semantic search** to find related functionality
3. **Use fuzzy search** to find specific names
4. **Use hybrid search** for comprehensive results

### For Code Generation
When an LLM needs to generate code:

1. **Search for similar patterns** using semantic matching
2. **Find existing implementations** using fuzzy matching
3. **Understand dependencies** using analysis
4. **Check for conflicts** using comprehensive search

### For Code Review
When an LLM needs to review code:

1. **Find related code** that might be affected
2. **Check for similar patterns** across the codebase
3. **Understand the broader context** using analysis
4. **Identify potential issues** using comprehensive search

## Best Practices

1. **Always use cache persistence** for better performance
2. **Start with analysis** for large projects
3. **Use hybrid matching** for comprehensive results
4. **Limit results** to avoid overwhelming output
5. **Use semantic search** when you know functionality but not names
6. **Use fuzzy search** when you know names but not exact spelling
7. **Combine multiple searches** for thorough understanding
8. **Save important results** to files for reference

## Environment Variables

The tool respects these environment variables:

- `REPOMAP_CACHE_DIR` - Cache directory path (default: `/app/cache`)
- `REPOMAP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REPOMAP_CONFIG_FILE` - Configuration file path

## Configuration File

Create a `repomap.json` file in your project for custom settings:

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

This comprehensive guide should help LLMs effectively use the RepoMap Tool Docker CLI for code analysis and discovery tasks.
