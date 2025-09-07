# RepoMap Tool - Corrected Docker CLI Instructions

## Overview

RepoMap Tool is an intelligent code analysis engine that helps AI assistants navigate and understand large codebases. It combines fuzzy matching and semantic analysis to provide comprehensive code discovery capabilities.

## Quick Reference

### Docker Images
- **Standard Tag**: `repomap-tool:local` (works with any registry)
- **Registry Examples**: 
  - `ghcr.io/xynova/repomap-tool:latest` → tag as `repomap-tool:local`
  - `docker.io/yourorg/repomap-tool:v1.0` → tag as `repomap-tool:local`
  - `your-registry.com/repomap-tool:dev` → tag as `repomap-tool:local`

### Building and Tagging Docker Image
```bash
# Build from source (recommended for development)
docker build -t repomap-tool:local -f docker/Dockerfile .

# Or pull from registry and retag
docker pull ghcr.io/xynova/repomap-tool:latest
docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local

# Or pull any version and retag
docker pull your-registry.com/repomap-tool:v1.2.3
docker tag your-registry.com/repomap-tool:v1.2.3 repomap-tool:local
```

### Basic Docker Command Pattern
```bash
docker run --rm -t -v /path/to/project:/workspace repomap-tool:local <command> /workspace [options]
```

**Note**: The `-t` environment variable eliminates terminal warnings and provides clean output.

## Deployment Scenarios

### Development Environment
```bash
# Build from source
docker build -t repomap-tool:local -f docker/Dockerfile .
```

### Production Environment
```bash
# Pull from registry and retag
docker pull ghcr.io/xynova/repomap-tool:latest
docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local
```

### CI/CD Pipeline
```bash
# Build and push to registry
docker build -t your-registry.com/repomap-tool:${VERSION} -f docker/Dockerfile .
docker push your-registry.com/repomap-tool:${VERSION}

# Retag for local use
docker tag your-registry.com/repomap-tool:${VERSION} repomap-tool:local
```

### Multi-Environment Setup
```bash
# Development
docker tag ghcr.io/xynova/repomap-tool:dev repomap-tool:local

# Staging  
docker tag ghcr.io/xynova/repomap-tool:staging repomap-tool:local

# Production
docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local
```

### Quick Setup Script
Use the provided setup script for easy tagging:
```bash
# Build from source
./scripts/setup-repomap-local.sh build

# Pull from default registry
./scripts/setup-repomap-local.sh pull

# Pull from specific registry/version
./scripts/setup-repomap-local.sh registry ghcr.io/xynova/repomap-tool:v1.0.0
./scripts/setup-repomap-local.sh registry docker.io/yourorg/repomap-tool:dev
```

## Available Commands

### 1. `analyze` - Project Analysis
**Purpose**: Analyzes a project and generates a comprehensive code map.

**Basic Usage**:
```bash
docker run --rm -t -v /path/to/project:/workspace repomap-tool:local analyze /workspace
```

**Options**:
- `--fuzzy` - Enable fuzzy matching
- `--semantic` - Enable semantic matching  
- `--no-fuzzy` - Disable fuzzy matching
- `--no-semantic` - Disable semantic matching
- `--output [json|text|markdown|table]` - Output format (default: json)
- `--verbose` - Verbose output with detailed information
- `--threshold FLOAT` - Match threshold (0.0-1.0, default: 0.7)
- `--max-results INTEGER` - Maximum results to return

**Examples**:
```bash
# Basic analysis with both fuzzy and semantic matching
docker run --rm -t -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic

# Verbose analysis with table output
docker run --rm -t -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic --verbose --output table

# Fuzzy matching only
docker run --rm -t -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --no-semantic
```

### 2. `search` - Code Search
**Purpose**: Search for identifiers, functions, and code patterns using intelligent matching.

**Basic Usage**:
```bash
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "query" /workspace
```

**Options**:
- `--match-type [fuzzy|semantic|hybrid]` - Matching strategy (default: hybrid)
- `--threshold FLOAT` - Match threshold (0.0-1.0, default: 0.7)
- `--max-results INTEGER` - Maximum number of results (default: 10)
- `--output [json|text|table]` - Output format (default: table)
- `--strategies TEXT` - Specific matching strategies
- `--verbose` - Verbose output

**Examples**:
```bash
# Search for authentication-related code
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "authentication" /workspace --match-type hybrid --max-results 15

# Search using config file (no need to specify project path)
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "auth" --config /workspace/.repomap/config.json

# Fuzzy search with custom threshold
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "auth" /workspace --match-type fuzzy --threshold 0.6

# Semantic search for data processing
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "data processing" /workspace --match-type semantic

# JSON output for programmatic use
docker run --rm -v /path/to/project:/workspace repomap-tool:local search identifiers "error handling" /workspace --output json
```

### 3. `config` - Configuration Management
**Purpose**: Generate and manage configuration files for the tool.

**Basic Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local config /workspace
```

**Options**:
- `--output PATH` - Output configuration file path
- `--fuzzy / --no-fuzzy` - Enable/disable fuzzy matching in generated config
- `--semantic / --no-semantic` - Enable/disable semantic matching in generated config
- `--threshold FLOAT` - Match threshold for generated config
- `--cache-size INTEGER` - Cache size for generated config

**Examples**:
```bash
# Generate basic configuration
docker run --rm  -v /path/to/project:/workspace repomap-tool:local config /workspace

# Generate configuration file
docker run --rm  -v /path/to/project:/workspace repomap-tool:local config /workspace --output repomap.json

# Generate configuration with custom settings
docker run --rm  -v /path/to/project:/workspace repomap-tool:local config /workspace --output config.json --threshold 0.8 --cache-size 2000
```

### 4. `explore` - Tree Exploration
**Purpose**: Discover exploration trees from your intent description for intelligent code navigation.

**Basic Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local explore /workspace "intent description"
```

**Options**:
- `--session, -s` - Session ID (or use REPOMAP_SESSION env var)
- `--max-depth` - Maximum tree depth (default: 3)

**Examples**:
```bash
# Basic exploration
docker run --rm  -v /path/to/project:/workspace repomap-tool:local explore /workspace "authentication login errors"

# With custom session and depth
docker run --rm  -v /path/to/project:/workspace repomap-tool:local explore /workspace "database performance issues" --session debug_session --max-depth 5

# Set session via environment variable
docker run --rm -e REPOMAP_SESSION=my_investigation  -v /path/to/project:/workspace repomap-tool:local explore /workspace "API authentication bugs"
```

### 5. `focus` - Tree Focus Management
**Purpose**: Focus on a specific exploration tree within your session.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local focus <tree_id>
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# Focus on specific tree
docker run --rm  repomap-tool:local focus auth_errors_abc123

# With custom session
docker run --rm  repomap-tool:local focus auth_errors_abc123 --session other_session
```

### 6. `expand` - Tree Expansion
**Purpose**: Expand the current focused tree in a specific area.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local expand "area"
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)

**Examples**:
```bash
# Expand current focused tree
docker run --rm  repomap-tool:local expand "password_validation"

# Expand specific tree
docker run --rm  repomap-tool:local expand "error_handling" --tree frontend_auth_def456
```

### 7. `prune` - Tree Pruning
**Purpose**: Remove a branch from the current focused tree.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local prune "area"
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)

**Examples**:
```bash
# Prune current focused tree
docker run --rm  repomap-tool:local prune "logging"

# Prune specific tree
docker run --rm  repomap-tool:local prune "debug_code" --tree auth_errors_abc123
```

### 8. `map` - Tree Visualization
**Purpose**: Generate a repomap from the current tree state.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local map
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)
- `--include-code` - Include code snippets in output

**Examples**:
```bash
# View current focused tree
docker run --rm  repomap-tool:local map

# View specific tree with code
docker run --rm  repomap-tool:local map --tree frontend_auth_def456 --include-code
```

### 9. `list-trees` - Tree Listing
**Purpose**: List all trees in your current session.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local list-trees
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# List trees in current session
docker run --rm  repomap-tool:local list-trees

# List trees in specific session
docker run --rm  repomap-tool:local list-trees --session debug_session
```

### 10. `status` - Session Status
**Purpose**: Show session status and current tree information.

**Basic Usage**:
```bash
docker run --rm  repomap-tool:local status
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# Show current session status
docker run --rm  repomap-tool:local status

# Show specific session status
docker run --rm  repomap-tool:local status --session debug_session
```

### 11. `version` - Version Information
**Purpose**: Display version and build information.

**Usage**:
```bash
docker run --rm repomap-tool:local version
```

### 12. `performance` - Performance Metrics
**Purpose**: Show performance metrics for the project.

**Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local performance /workspace
```

### 13. `analyze-dependencies` - Dependency Analysis
**Purpose**: Analyze project dependencies and build dependency graphs.

**Options**:
- `--max-files INTEGER` - Maximum files to analyze (100-10000, default: 1000)
- `--enable-call-graph` - Enable function call graph analysis
- `--enable-impact-analysis` - Enable change impact analysis
- `--output [json|table|text]` - Output format
- `--verbose` - Verbose output

**Usage**:
```bash
# Basic dependency analysis
docker run --rm -t  -v /path/to/project:/workspace repomap-tool:local analyze-dependencies /workspace

# Analyze all files (up to 10,000)
docker run --rm -t  -v /path/to/project:/workspace repomap-tool:local analyze-dependencies /workspace --max-files 10000

# With call graph and impact analysis
docker run --rm -t  -v /path/to/project:/workspace repomap-tool:local analyze-dependencies /workspace --enable-call-graph --enable-impact-analysis
```

### 14. `find-cycles` - Circular Dependencies
**Purpose**: Find circular dependencies in the project.

**Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local find-cycles /workspace
```

### 15. `impact-analysis` - Impact Analysis
**Purpose**: Analyze impact of changes to specific files.

**Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local impact-analysis /workspace
```

### 16. `show-centrality` - Centrality Analysis
**Purpose**: Show centrality analysis for project files.

**Usage**:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local show-centrality /workspace
```


## Volume Mounting Best Practices

### Project Directory Mounting
Mount your project directory as `/workspace` - the `.repomap` directory will be created inside your project:
```bash
-v /path/to/your/project:/workspace
```

**Benefits**:
- **Project-specific**: Each project has its own `.repomap` directory
- **Portable**: Configuration and cache travel with the project
- **Simplified**: No separate volume mounts needed
- **Intuitive**: `.repomap` is part of the project structure
- **Persistent**: Cache and sessions persist between container runs

### Project Structure
Your project will have this structure:
```
your-project/
├── .repomap/           # Created automatically
│   ├── cache/          # Analysis cache
│   ├── sessions/       # Tree exploration sessions
│   └── config.json     # Configuration file
└── your-source-code/
```

### Complete Example
```bash
docker run --rm \
  -v /path/to/your/project:/workspace \
  repomap-tool:local \
  search /workspace "authentication"
```

## Performance Comparison

### Local Docker vs Virtual Environment
| Operation | Local Docker | Virtual Environment | Performance |
|-----------|--------------|-------------------|-------------|
| **Analysis** | 0.25s | 0.18s | Virtual env 1.4x faster |
| **Search** | 0.28s | 0.19s | Virtual env 1.5x faster |
| **Config** | Instant | Instant | Similar |

### Local Docker vs Remote Docker
| Operation | Local Docker | Remote Docker | Performance |
|-----------|--------------|---------------|-------------|
| **Analysis** | 0.25s | 46s | Local 184x faster |
| **Search** | 0.28s | 1.5s | Local 5.4x faster |
| **Config** | Instant | Multiple seconds | Local much faster |

## Common Use Cases for LLMs

### 1. Code Discovery
When an LLM needs to understand how a specific feature works:

```bash
# Find all authentication-related code
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "authentication" --match-type hybrid --max-results 15

# Find data processing functions
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "data processing" --match-type semantic
```

### 2. Refactoring Planning
When an LLM needs to understand dependencies before making changes:

```bash
# Find all usages of a specific function
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "process_data" --match-type fuzzy --threshold 0.6

# Analyze project structure first
docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic --verbose
```

### 3. Architecture Understanding
When an LLM needs to understand the overall codebase structure:

```bash
# Get comprehensive project analysis
docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic --verbose --output table

# Find related modules
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "database connection" --match-type hybrid
```

### 4. Error Handling Discovery
When an LLM needs to find error handling patterns:

```bash
# Find error handling code
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "error handling exception" --match-type hybrid --max-results 20
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

### 1. Use Consistent Tagging
Always tag your image as `repomap-tool:local` for consistent commands:
```bash
# Build from source
docker build -t repomap-tool:local -f docker/Dockerfile .

# Or pull from registry and retag
docker pull ghcr.io/xynova/repomap-tool:latest
docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local
```

### 2. Use Cache Persistence
Always mount a cache directory to avoid re-analyzing unchanged code:
```bash
```

### 3. Start with Analysis
For large projects, run analysis first to build the code map:
```bash
docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic
```

### 4. Use Appropriate Limits
Limit search results to avoid overwhelming output:
```bash
--max-results 10  # Default
--max-results 20  # For broader searches
--max-results 5   # For focused searches
```

### 5. Choose the Right Match Type
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
sudo docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze /workspace
```

**3. "Docker daemon not running"**
```bash
# Start Docker Desktop or Docker daemon
# On macOS: Start Docker Desktop
# On Linux: sudo systemctl start docker
```

**4. Slow performance**
```bash
# Use consistent tagging for better performance
docker build -t repomap-tool:local -f docker/Dockerfile .

# Or pull from registry and retag
docker pull ghcr.io/xynova/repomap-tool:latest
docker tag ghcr.io/xynova/repomap-tool:latest repomap-tool:local

# Use cache persistence

# Run analysis first for large projects
docker run --rm -t  -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic
```


**6. File limit warnings in dependency analysis**
```bash
# Increase the file limit for large projects
docker run --rm -t  -v /path/to/project:/workspace repomap-tool:local analyze-dependencies /workspace --max-files 10000
```

### Getting Help
```bash
# Show help for any command
docker run --rm repomap-tool:local --help
docker run --rm repomap-tool:local analyze --help
docker run --rm repomap-tool:local search --help
```

## Example Workflows

### Workflow 1: Understanding a New Codebase
```bash
# 1. Get project overview
docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze /workspace --fuzzy --semantic --verbose

# 2. Find main entry points
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "main entry point" --match-type semantic

# 3. Understand authentication
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "authentication login" --match-type hybrid
```

### Workflow 2: Planning a Refactor
```bash
# 1. Find all usages of the function to refactor
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "old_function_name" --match-type fuzzy --threshold 0.6

# 2. Find similar patterns
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "similar functionality" --match-type semantic

# 3. Analyze dependencies
docker run --rm  -v /path/to/project:/workspace repomap-tool:local analyze-dependencies /workspace
```

### Workflow 3: Debugging Issues
```bash
# 1. Find error handling code
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "error handling exception" --match-type hybrid

# 2. Find logging code
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "logging debug" --match-type semantic

# 3. Find validation code
docker run --rm  -v /path/to/project:/workspace repomap-tool:local search /workspace "validation check" --match-type hybrid
```

## Environment Variables

The tool respects these environment variables:

- `REPOMAP_CACHE_DIR` - Cache directory path (default: `/workspace/.repomap/cache`)
- `REPOMAP_SESSION_DIR` - Session storage directory path (default: `/workspace/.repomap/sessions`)
- `REPOMAP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REPOMAP_CONFIG_FILE` - Configuration file path
- `REPOMAP_SESSION` - Session ID for tree exploration (auto-generated if not set)

## Configuration File

Create a `repomap.json` file in your project for custom settings:

```json
{
  "fuzzy_match": {
    "enabled": true,
    "threshold": 70,
    "strategies": ["prefix", "substring", "levenshtein"],
    "cache_results": true
  },
  "semantic_match": {
    "enabled": true,
    "threshold": 0.7,
    "use_tfidf": true,
    "min_word_length": 3,
    "cache_results": true
  },
  "performance": {
    "max_workers": 4,
    "cache_size": 1000,
    "max_memory_mb": 100,
    "enable_progress": true,
    "enable_monitoring": true,
    "parallel_threshold": 10,
    "cache_ttl": 3600,
    "allow_fallback": false
  },
  "output": {
    "format": "table",
    "max_results": 10
  }
}
```

## Best Practices

### General Usage
1. **Build local Docker image** for better performance
2. **Always use cache persistence** for better performance
3. **Start with analysis** for large projects
4. **Use hybrid matching** for comprehensive results
5. **Limit results** to avoid overwhelming output
6. **Use semantic search** when you know functionality but not names
7. **Use fuzzy search** when you know names but not exact spelling
8. **Combine multiple searches** for thorough understanding
9. **Save important results** to files for reference

### Tree Exploration
10. **Use descriptive session names** for easy identification
11. **Set session via environment variable** for consistency
12. **Start with exploration** to discover relevant trees
13. **Focus on high-confidence trees** first
14. **Expand incrementally** to avoid overwhelming results
15. **Prune irrelevant areas** to focus on important code
16. **Use include-code sparingly** for large trees
17. **Check session status** regularly to understand current state

This corrected guide provides accurate Docker CLI instructions that match the actual implementation and includes performance comparisons between different execution methods.
