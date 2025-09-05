# Tree Exploration Guide

## Overview

The Tree Exploration feature provides intelligent, context-aware code exploration using tree-based navigation. Instead of static code analysis, it creates dynamic exploration trees that can be expanded, pruned, and focused based on your current investigation needs.

## Key Concepts

### 🌳 Exploration Trees
- **Hierarchical Structure**: Code is organized into logical trees starting from entrypoints
- **Dynamic Expansion**: Trees can grow and shrink based on your exploration focus
- **Context Awareness**: Trees are built using semantic analysis of your codebase

### 🎯 Entrypoints
- **Smart Discovery**: Automatically finds relevant code starting points based on your intent
- **Semantic Matching**: Uses existing semantic and fuzzy matching to identify relevant code
- **Confidence Scoring**: Each entrypoint has a relevance score to help prioritize exploration

### 📋 Sessions
- **Stateful Exploration**: Maintains exploration state across CLI invocations
- **Multiple Trees**: Each session can contain multiple exploration trees
- **Focus Management**: Switch between trees and maintain current exploration context

## Quick Start

### 1. Start an Exploration Session

```bash
# Set a session ID (optional, will auto-generate if not set)
export REPOMAP_SESSION="my_auth_investigation"

# Explore a project with your intent
repomap-tool explore /path/to/project "authentication login errors"
```

**Expected Output:**
```
💡 Using session: my_auth_investigation
Set: export REPOMAP_SESSION=my_auth_investigation

🔍 Found 3 exploration contexts:
  • Auth Error Handling [id: auth_errors_abc123] (confidence: 0.92)
  • Frontend Auth Flow [id: frontend_auth_def456] (confidence: 0.87)
  • Auth Validation [id: auth_validation_ghi789] (confidence: 0.81)

💡 Next steps:
  repomap-tool focus <tree_id>    # Focus on specific tree
  repomap-tool map                # View current tree
```

### 2. Focus on a Specific Tree

```bash
# Focus on the Auth Error Handling tree
repomap-tool focus auth_errors_abc123
```

**Expected Output:**
```
✅ Focused on tree: auth_errors_abc123
```

### 3. View the Tree Structure

```bash
# View the current tree
repomap-tool map

# Include code snippets
repomap-tool map --include-code
```

**Expected Output:**
```
🌳 Exploration Tree: Auth Error Handling
📍 Root: AuthErrorHandler
🎯 Confidence: 0.92
📊 Nodes: 5

├── AuthErrorHandler (src/auth/error_handler.py:15)
│   ├── handle_login_error (src/auth/error_handler.py:42)
│   ├── validate_credentials (src/auth/error_handler.py:68)
│   └── log_auth_failure (src/auth/error_handler.py:85)
├── LoginValidator (src/auth/validators.py:12)
└── AuthExceptions (src/auth/exceptions.py:8)

🔍 Available expansions:
  • validation - expand with: repomap-tool expand "validation"
  • error_handling - expand with: repomap-tool expand "error_handling"
```

### 4. Expand the Tree

```bash
# Expand in the validation area
repomap-tool expand "validation"
```

**Expected Output:**
```
✅ Expanded tree in area: validation
```

### 5. Check Session Status

```bash
# View current session status
repomap-tool status
```

**Expected Output:**
```
📊 Session Status: my_auth_investigation
═══════════════════════════════════════

🎯 Current Focus: auth_errors_abc123
📅 Session Started: 2024-01-01 09:15:30
🕐 Last Activity: 2024-01-01 10:45:22

🌳 Exploration Trees (3 total):
  1. 🎯 auth_errors_abc123 [FOCUSED] - Auth Error Handling
  2. 📋 frontend_auth_def456 - Frontend Auth Flow  
  3. 📋 auth_validation_ghi789 - Auth Validation

💡 Quick Actions:
  repomap-tool map                          # View current focused tree
  repomap-tool expand <area>               # Expand current tree
  repomap-tool prune <area>                # Prune current tree
```

## Command Reference

### Core Commands

#### `explore <project_path> <intent>`
Discovers exploration trees from your intent description.

**Options:**
- `--session, -s`: Session ID (or use REPOMAP_SESSION env var)
- `--max-depth`: Maximum tree depth (default: 3)

**Examples:**
```bash
# Basic exploration
repomap-tool explore . "database performance issues"

# With custom session and depth
repomap-tool explore /my-project "API authentication bugs" --session debug_session --max-depth 5
```

#### `focus <tree_id>`
Sets focus to a specific exploration tree within your session.

**Options:**
- `--session, -s`: Session ID

**Examples:**
```bash
# Focus on specific tree
repomap-tool focus auth_errors_abc123

# With custom session
repomap-tool focus auth_errors_abc123 --session other_session
```

#### `expand <area>`
Expands the current focused tree in a specific area.

**Options:**
- `--session, -s`: Session ID
- `--tree, -t`: Tree ID (uses current focus if not specified)

**Examples:**
```bash
# Expand current focused tree
repomap-tool expand "password_validation"

# Expand specific tree
repomap-tool expand "error_handling" --tree frontend_auth_def456
```

#### `prune <area>`
Removes a branch from the current focused tree.

**Options:**
- `--session, -s`: Session ID
- `--tree, -t`: Tree ID (uses current focus if not specified)

**Examples:**
```bash
# Prune current focused tree
repomap-tool prune "logging"

# Prune specific tree
repomap-tool prune "debug_code" --tree auth_errors_abc123
```

#### `map`
Generates a repomap from the current tree state.

**Options:**
- `--session, -s`: Session ID
- `--tree, -t`: Tree ID (uses current focus if not specified)
- `--include-code`: Include code snippets in output

**Examples:**
```bash
# View current focused tree
repomap-tool map

# View specific tree with code
repomap-tool map --tree frontend_auth_def456 --include-code
```

### Session Management Commands

#### `list-trees`
Lists all trees in your current session.

**Options:**
- `--session, -s`: Session ID

**Examples:**
```bash
# List trees in current session
repomap-tool list-trees

# List trees in specific session
repomap-tool list-trees --session other_session
```

#### `status`
Shows detailed session status and current tree information.

**Options:**
- `--session, -s`: Session ID

**Examples:**
```bash
# Show current session status
repomap-tool status

# Show specific session status
repomap-tool status --session other_session
```

## Session Management

### Session IDs
Sessions are identified by unique IDs that persist across CLI invocations.

**Setting Session ID:**
```bash
# Via environment variable (recommended)
export REPOMAP_SESSION="my_investigation"

# Via CLI parameter (override)
repomap-tool explore . "bugs" --session quick_check
```

**Auto-generated Sessions:**
If no session ID is provided, one will be automatically generated:
```
💡 Using session: explore_1704067200
Set: export REPOMAP_SESSION=explore_1704067200
```

### Session Persistence
- Sessions are automatically saved to disk
- State persists across CLI invocations
- Multiple independent sessions can run simultaneously
- Sessions are stored in temporary directory by default

### Session Cleanup
Old sessions are automatically cleaned up after 24 hours of inactivity.

## Advanced Features

### Tree Clustering
Entrypoints are automatically clustered into logical groups with meaningful titles:

**Example Clusters:**
- "Auth Error Handling" - Authentication and error handling code
- "Database API" - Database-related API endpoints
- "Frontend Validation" - Frontend validation components
- "Cache Optimization" - Caching and performance code

### Semantic Analysis
Trees leverage existing semantic matching capabilities:

- **Category Extraction**: Automatically identifies semantic categories
- **Context Generation**: Creates meaningful titles from semantic analysis
- **Confidence Scoring**: Provides confidence scores for clusters and trees

### Dynamic Tree Building
Trees are built using existing aider infrastructure:

- **Dependency Analysis**: Uses existing dependency information
- **Symbol Discovery**: Leverages existing symbol extraction
- **Code Context**: Integrates with existing code analysis tools

## Best Practices

### 1. Start with Clear Intent
```bash
# Good: Specific, focused intent
repomap-tool explore . "authentication login validation errors"

# Avoid: Too vague
repomap-tool explore . "bugs"
```

### 2. Use Meaningful Session Names
```bash
# Good: Descriptive session names
export REPOMAP_SESSION="auth_bug_investigation_$(date +%Y%m%d)"

# Avoid: Generic names
export REPOMAP_SESSION="test"
```

### 3. Iterative Exploration
```bash
# Start with broad exploration
repomap-tool explore . "authentication issues"

# Focus on most relevant tree
repomap-tool focus auth_errors_abc123

# Expand in specific areas
repomap-tool expand "password_validation"
repomap-tool expand "error_handling"

# Prune irrelevant areas
repomap-tool prune "logging"
```

### 4. Session Organization
```bash
# Different sessions for different investigations
export REPOMAP_SESSION="frontend_performance"
repomap-tool explore . "React component optimization"

export REPOMAP_SESSION="backend_security"
repomap-tool explore . "API authentication vulnerabilities"
```

## Troubleshooting

### Common Issues

#### No Entrypoints Found
```
⚠️  No high-confidence entrypoints found for intent: "quantum flux capacitor"
```

**Solutions:**
- Try broader, more common terms
- Use existing search functionality first
- Check that semantic/fuzzy matching is enabled

#### Session Not Found
```
❌ Session 'nonexistent_session' not found
```

**Solutions:**
- Check available sessions with `repomap-tool list-trees`
- Use `export REPOMAP_SESSION=<session_id>` to set session
- Create new session with `repomap-tool explore`

#### Tree Not Found
```
❌ Tree 'nonexistent_tree' not found in session 'my_session'
```

**Solutions:**
- List trees in session: `repomap-tool list-trees`
- Check session status: `repomap-tool status`
- Verify tree ID spelling

### Performance Tips

- **Limit Tree Depth**: Use `--max-depth` to control tree size
- **Focus on Relevant Areas**: Use `focus` to narrow exploration scope
- **Prune Unnecessary Branches**: Remove irrelevant code areas with `prune`
- **Use Sessions**: Organize investigations into separate sessions

## Integration with Existing Tools

The Tree Exploration feature is built on top of existing repomap-tool infrastructure:

- **Semantic Matching**: Uses existing `DomainSemanticMatcher`
- **Fuzzy Matching**: Integrates with existing `FuzzyMatcher`
- **Symbol Extraction**: Leverages existing symbol discovery
- **Dependency Analysis**: Uses existing aider infrastructure
- **Configuration**: Extends existing `RepoMapConfig` with `TreeConfig`

## Examples

### Authentication Bug Investigation
```bash
# Start investigation
export REPOMAP_SESSION="auth_bug_investigation"
repomap-tool explore . "authentication login errors"

# Focus on most relevant tree
repomap-tool focus auth_errors_abc123

# Explore validation area
repomap-tool expand "validation"

# View expanded tree
repomap-tool map --include-code

# Check status
repomap-tool status
```

### Performance Optimization
```bash
# Start performance investigation
export REPOMAP_SESSION="performance_optimization"
repomap-tool explore . "database query performance issues"

# Focus on database tree
repomap-tool focus db_performance_xyz789

# Expand query optimization area
repomap-tool expand "query_optimization"

# View tree structure
repomap-tool map
```

### Multi-Session Development
```bash
# Frontend work
export REPOMAP_SESSION="frontend_refactor"
repomap-tool explore . "React component optimization"

# Backend work (different session)
export REPOMAP_SESSION="backend_api_fixes"
repomap-tool explore . "API response time issues"

# Switch between sessions as needed
repomap-tool status --session frontend_refactor
repomap-tool status --session backend_api_fixes
```

## Conclusion

Tree Exploration provides a powerful, context-aware approach to code investigation. By combining semantic analysis with dynamic tree structures, it enables focused, efficient exploration of complex codebases.

Start with the basic workflow, experiment with different intents, and use sessions to organize your investigations. The system will learn from your exploration patterns and provide increasingly relevant results.
