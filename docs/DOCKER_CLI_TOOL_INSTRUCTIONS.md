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

### 4. `explore` - Tree Exploration
**Purpose**: Discover exploration trees from your intent description for intelligent code navigation.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "intent description"
```

**Options**:
- `--session, -s` - Session ID (or use REPOMAP_SESSION env var)
- `--max-depth` - Maximum tree depth (default: 3)

**Examples**:
```bash
# Basic exploration
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "authentication login errors"

# With custom session and depth
docker run --rm -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "database performance issues" --session debug_session --max-depth 5

# Set session via environment variable
docker run --rm -e REPOMAP_SESSION=my_investigation -v $(pwd)/.repomap:/app/cache -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "API authentication bugs"
```

### 5. `focus` - Tree Focus Management
**Purpose**: Focus on a specific exploration tree within your session.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest focus <tree_id>
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# Focus on specific tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest focus auth_errors_abc123

# With custom session
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest focus auth_errors_abc123 --session other_session
```

### 6. `expand` - Tree Expansion
**Purpose**: Expand the current focused tree in a specific area.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest expand "area"
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)

**Examples**:
```bash
# Expand current focused tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest expand "password_validation"

# Expand specific tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest expand "error_handling" --tree frontend_auth_def456
```

### 7. `prune` - Tree Pruning
**Purpose**: Remove a branch from the current focused tree.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest prune "area"
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)

**Examples**:
```bash
# Prune current focused tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest prune "logging"

# Prune specific tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest prune "debug_code" --tree auth_errors_abc123
```

### 8. `map` - Tree Visualization
**Purpose**: Generate a repomap from the current tree state.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest map
```

**Options**:
- `--session, -s` - Session ID
- `--tree, -t` - Tree ID (uses current focus if not specified)
- `--include-code` - Include code snippets in output

**Examples**:
```bash
# View current focused tree
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest map

# View specific tree with code
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest map --tree frontend_auth_def456 --include-code
```

### 9. `list-trees` - Tree Listing
**Purpose**: List all trees in your current session.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest list-trees
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# List trees in current session
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest list-trees

# List trees in specific session
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest list-trees --session debug_session
```

### 10. `status` - Session Status
**Purpose**: Show session status and current tree information.

**Basic Usage**:
```bash
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest status
```

**Options**:
- `--session, -s` - Session ID

**Examples**:
```bash
# Show current session status
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest status

# Show specific session status
docker run --rm -v $(pwd)/.repomap:/app/cache ghcr.io/xynova/repomap-tool:latest status --session debug_session
```

### 11. `version` - Version Information
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

### Session Persistence
Mount a session directory to persist tree exploration sessions across container restarts:
```bash
-v $(pwd)/.repomap/sessions:/app/sessions
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
  -v $(pwd)/.repomap/sessions:/app/sessions \
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

## Tree Exploration Use Cases for LLMs

### 1. Deep Code Investigation
When an LLM needs to understand complex, interconnected code:

```bash
# Start exploration session for authentication issues
docker run --rm -e REPOMAP_SESSION=auth_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "authentication login errors"

# Focus on the most relevant tree
docker run --rm -e REPOMAP_SESSION=auth_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus auth_errors_abc123

# View the tree structure
docker run --rm -e REPOMAP_SESSION=auth_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map --include-code

# Expand in specific areas
docker run --rm -e REPOMAP_SESSION=auth_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "password_validation"
```

### 2. Bug Investigation
When an LLM needs to trace through code to find the root cause:

```bash
# Start investigation session
docker run --rm -e REPOMAP_SESSION=bug_investigation -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "database connection timeout errors"

# Check session status
docker run --rm -e REPOMAP_SESSION=bug_investigation -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest status

# Focus on the most relevant tree
docker run --rm -e REPOMAP_SESSION=bug_investigation -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus db_timeout_xyz789

# Expand error handling areas
docker run --rm -e REPOMAP_SESSION=bug_investigation -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "error_handling"
```

### 3. Feature Implementation Planning
When an LLM needs to understand existing patterns before implementing new features:

```bash
# Explore existing patterns
docker run --rm -e REPOMAP_SESSION=feature_planning -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "user management CRUD operations"

# List all discovered trees
docker run --rm -e REPOMAP_SESSION=feature_planning -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest list-trees

# Focus on the most relevant pattern
docker run --rm -e REPOMAP_SESSION=feature_planning -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus user_crud_abc123

# Expand to see implementation details
docker run --rm -e REPOMAP_SESSION=feature_planning -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "validation"
```

### 4. Code Review and Quality Assessment
When an LLM needs to understand code quality and patterns:

```bash
# Explore code quality patterns
docker run --rm -e REPOMAP_SESSION=code_review -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "error handling logging patterns"

# Focus on the most comprehensive tree
docker run --rm -e REPOMAP_SESSION=code_review -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus error_patterns_def456

# View with code snippets
docker run --rm -e REPOMAP_SESSION=code_review -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map --include-code

# Prune irrelevant areas
docker run --rm -e REPOMAP_SESSION=code_review -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest prune "debug_code"
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

## Tree Exploration Workflows

### Workflow 4: Deep Bug Investigation
```bash
# 1. Start exploration session
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "authentication timeout errors"

# 2. Check what trees were discovered
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest list-trees

# 3. Focus on the most relevant tree
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus auth_timeout_abc123

# 4. View the tree structure
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map --include-code

# 5. Expand in error handling areas
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "error_handling"

# 6. Check session status
docker run --rm -e REPOMAP_SESSION=bug_debug -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest status
```

### Workflow 5: Feature Implementation Planning
```bash
# 1. Explore existing patterns
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "user management CRUD operations"

# 2. List all discovered trees
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest list-trees

# 3. Focus on the most comprehensive pattern
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus user_crud_xyz789

# 4. View with code snippets
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map --include-code

# 5. Expand validation patterns
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "validation"

# 6. Prune irrelevant areas
docker run --rm -e REPOMAP_SESSION=feature_plan -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest prune "debug_code"
```

### Workflow 6: Code Quality Assessment
```bash
# 1. Start quality assessment session
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions -v /path/to/project:/workspace ghcr.io/xynova/repomap-tool:latest explore /workspace "error handling logging patterns"

# 2. Focus on the most comprehensive tree
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest focus error_patterns_def456

# 3. View tree structure
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map

# 4. Expand logging areas
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "logging"

# 5. Expand error handling
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest expand "error_handling"

# 6. Final view with code
docker run --rm -e REPOMAP_SESSION=quality_check -v $(pwd)/.repomap:/app/cache -v $(pwd)/.repomap/sessions:/app/sessions ghcr.io/xynova/repomap-tool:latest map --include-code
```

## Tree Exploration Best Practices

### Session Management
- **Use descriptive session names** for easy identification
- **Set session via environment variable** for consistency across commands
- **Check session status** regularly to understand current state
- **Use different sessions** for different investigations

### Tree Navigation
- **Start with exploration** to discover relevant trees
- **Focus on high-confidence trees** first
- **Use list-trees** to see all available options
- **Expand incrementally** to avoid overwhelming results
- **Prune irrelevant areas** to focus on important code

### Performance Optimization
- **Use cache persistence** for faster subsequent operations
- **Limit tree depth** for large codebases
- **Focus on specific trees** rather than exploring everything
- **Use include-code sparingly** for large trees

## Integration with AI Assistants

### For LLM Context Gathering
When an LLM needs to understand code context:

1. **Start with analysis** to build the code map
2. **Use semantic search** to find related functionality
3. **Use fuzzy search** to find specific names
4. **Use hybrid search** for comprehensive results
5. **Use tree exploration** for deep, interconnected code understanding

### For Code Generation
When an LLM needs to generate code:

1. **Search for similar patterns** using semantic matching
2. **Find existing implementations** using fuzzy matching
3. **Understand dependencies** using analysis
4. **Check for conflicts** using comprehensive search
5. **Explore existing patterns** using tree exploration

### For Code Review
When an LLM needs to review code:

1. **Find related code** that might be affected
2. **Check for similar patterns** across the codebase
3. **Understand the broader context** using analysis
4. **Identify potential issues** using comprehensive search
5. **Explore code quality patterns** using tree exploration

### For Bug Investigation
When an LLM needs to debug issues:

1. **Start exploration session** with error description
2. **Focus on relevant trees** based on confidence scores
3. **Expand error handling areas** to understand failure modes
4. **Use map with code** to see implementation details
5. **Prune irrelevant areas** to focus on the problem

## Best Practices

### General Usage
1. **Always use cache persistence** for better performance
2. **Start with analysis** for large projects
3. **Use hybrid matching** for comprehensive results
4. **Limit results** to avoid overwhelming output
5. **Use semantic search** when you know functionality but not names
6. **Use fuzzy search** when you know names but not exact spelling
7. **Combine multiple searches** for thorough understanding
8. **Save important results** to files for reference

### Tree Exploration
9. **Use descriptive session names** for easy identification
10. **Set session via environment variable** for consistency
11. **Start with exploration** to discover relevant trees
12. **Focus on high-confidence trees** first
13. **Expand incrementally** to avoid overwhelming results
14. **Prune irrelevant areas** to focus on important code
15. **Use include-code sparingly** for large trees
16. **Check session status** regularly to understand current state

## Environment Variables

The tool respects these environment variables:

- `REPOMAP_CACHE_DIR` - Cache directory path (default: `/app/cache`)
- `REPOMAP_SESSION_DIR` - Session storage directory path (default: `/app/sessions`)
- `REPOMAP_LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `REPOMAP_CONFIG_FILE` - Configuration file path
- `REPOMAP_SESSION` - Session ID for tree exploration (auto-generated if not set)

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

This comprehensive guide should help LLMs effectively use the RepoMap Tool Docker CLI for code analysis, discovery, and tree exploration tasks. The tool provides both traditional search capabilities and advanced tree-based exploration for deep code understanding.
