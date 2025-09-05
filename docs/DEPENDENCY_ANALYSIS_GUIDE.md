# Dependency Analysis Guide

## Overview

The repomap-tool provides comprehensive dependency analysis capabilities to help you understand code relationships, identify critical files, and assess the impact of changes in your projects.

## Features

### 🔍 **Dependency Graph Analysis**
- Build complete dependency graphs for multi-language projects
- Identify import relationships between files
- Detect circular dependencies
- Analyze dependency depth and clustering

### 📊 **Centrality Analysis**
- Calculate file importance using multiple algorithms
- Identify critical files in your codebase
- Rank files by their dependency centrality
- Understand which files have the most impact

### ⚠️ **Impact Assessment**
- Analyze the risk of changing specific files
- Identify affected files and breaking change potential
- Get suggestions for test files to run
- Assess the scope of changes

### 🌐 **Multi-Language Support**
- **Python**: AST-based analysis for accurate import detection
- **JavaScript/TypeScript**: Regex-based parsing for module imports
- **Java**: Import statement analysis
- **Go**: Module import parsing

## CLI Commands

### Analyze Dependencies

Build and analyze the complete dependency graph for your project:

```bash
# Basic analysis
python -m repomap_tool.cli analyze-dependencies /path/to/project

# With options
python -m repomap_tool.cli analyze-dependencies /path/to/project \
  --max-files 1000 \
  --enable-call-graph \
  --enable-impact-analysis \
  --output table
```

**Options:**
- `--max-files`: Maximum files to analyze (100-10000)
- `--enable-call-graph`: Enable function call graph analysis
- `--enable-impact-analysis`: Enable change impact analysis
- `--output`: Output format (json, table, text)
- `--verbose`: Enable verbose output

**Output Example:**
```
Dependency Analysis Results:
  Total Files: 73
  Total Dependencies: 2
  Circular Dependencies: 0
  Leaf Nodes: 72
  Root Nodes: 71
  Graph Construction Time: 0.20s
```

### Show Centrality

Display centrality analysis for project files:

```bash
# Show top centrality files
python -m repomap_tool.cli show-centrality /path/to/project

# Analyze specific file
python -m repomap_tool.cli show-centrality /path/to/project \
  --file src/main.py \
  --output json
```

**Options:**
- `--file`: Specific file to analyze (optional)
- `--output`: Output format (json, table, text)
- `--verbose`: Enable verbose output

**Output Example:**
```
Top Centrality Files:
  1. src/repomap_tool/trees/session_manager.py: 0.0809
  2. src/repomap_tool/trees/tree_builder.py: 0.0809
  3. src/repomap_tool/trees/tree_manager.py: 0.0116
```

### Impact Analysis

Analyze the impact of changes to specific files:

```bash
# Analyze single file
python -m repomap_tool.cli impact-analysis /path/to/project \
  --files src/main.py

# Analyze multiple files
python -m repomap_tool.cli impact-analysis /path/to/project \
  --files src/main.py src/utils.py \
  --output table
```

**Options:**
- `--files`: Files to analyze (required, can specify multiple)
- `--output`: Output format (json, table, text)
- `--verbose`: Enable verbose output

**Output Example:**
```
Impact Analysis: src/main.py
  Risk Score: 0.45
  Affected Files: 1
  Breaking Change Potential: {'src/main.py': 'LOW'}
  Suggested Tests: 0
```

### Find Cycles

Detect circular dependencies in your project:

```bash
# Find circular dependencies
python -m repomap_tool.cli find-cycles /path/to/project

# JSON output
python -m repomap_tool.cli find-cycles /path/to/project \
  --output json
```

**Options:**
- `--output`: Output format (json, table, text)
- `--verbose`: Enable verbose output

**Output Example:**
```
✓ No circular dependencies found
```

Or when cycles exist:
```
Found 2 circular dependencies:
  Cycle 1 (3 files):
    file1.py → file2.py → file3.py → file1.py
```

## Configuration

### Dependency Analysis Settings

You can configure dependency analysis behavior in your configuration:

```python
from repomap_tool.models import RepoMapConfig, DependencyConfig

config = RepoMapConfig(
    project_root="/path/to/project",
    dependencies=DependencyConfig(
        enabled=True,
        max_graph_size=10000,
        enable_call_graph=True,
        enable_impact_analysis=True,
        centrality_algorithms=["degree", "betweenness", "pagerank"],
        performance_threshold_seconds=30.0
    )
)
```

**Configuration Options:**
- `enabled`: Enable/disable dependency analysis
- `max_graph_size`: Maximum files to analyze (100-100000)
- `enable_call_graph`: Enable function call analysis
- `enable_impact_analysis`: Enable change impact analysis
- `centrality_algorithms`: List of centrality algorithms to use
- `performance_threshold_seconds`: Maximum time for graph construction

## Programmatic Usage

### Basic Dependency Analysis

```python
from repomap_tool.models import RepoMapConfig, DependencyConfig
from repomap_tool.core.repo_map import DockerRepoMap

# Configure and initialize
config = RepoMapConfig(
    project_root=".",
    dependencies=DependencyConfig(enabled=True)
)

repomap = DockerRepoMap(config)

# Build dependency graph
dependency_graph = repomap.build_dependency_graph()

# Get graph statistics
stats = dependency_graph.get_graph_statistics()
print(f"Total files: {stats['total_nodes']}")
print(f"Total dependencies: {stats['total_edges']}")
```

### Centrality Analysis

```python
# Get centrality scores for all files
centrality_scores = repomap.get_centrality_scores()

# Find top centrality files
top_files = sorted(
    centrality_scores.items(), 
    key=lambda x: x[1], 
    reverse=True
)[:5]

for file_path, score in top_files:
    print(f"{file_path}: {score:.4f}")
```

### Impact Analysis

```python
# Analyze change impact for a file
impact_report = repomap.analyze_change_impact("src/main.py")

print(f"Risk Score: {impact_report.risk_score:.2f}")
print(f"Affected Files: {len(impact_report.affected_files)}")
print(f"Breaking Change Potential: {impact_report.breaking_change_potential}")
```

### Cycle Detection

```python
# Find circular dependencies
cycles = repomap.find_circular_dependencies()

if cycles:
    print(f"Found {len(cycles)} circular dependencies:")
    for i, cycle in enumerate(cycles, 1):
        print(f"  Cycle {i}: {' → '.join(cycle)}")
else:
    print("No circular dependencies found")
```

## Output Formats

### JSON Output

JSON output provides structured data for programmatic processing:

```json
{
  "total_nodes": 73,
  "total_edges": 2,
  "cycles": 0,
  "leaf_nodes": 72,
  "root_nodes": 71,
  "language_distribution": {
    "py": 73
  }
}
```

### Table Output

Table output provides human-readable formatted results:

```
┌─────────────────────┬─────────┐
│ Metric              │ Value   │
├─────────────────────┼─────────┤
│ Total Files         │ 73      │
│ Total Dependencies  │ 2       │
│ Circular Dependencies│ 0       │
│ Leaf Nodes          │ 72      │
│ Root Nodes          │ 71      │
└─────────────────────┴─────────┘
```

### Text Output

Text output provides simple, readable results:

```
Dependency Analysis Results:
  Total Files: 73
  Total Dependencies: 2
  Circular Dependencies: 0
  Leaf Nodes: 72
  Root Nodes: 71
```

## Best Practices

### 1. **Start Small**
- Begin with smaller projects to understand the tool
- Use `--max-files` to limit analysis scope initially
- Enable verbose output for debugging

### 2. **Regular Analysis**
- Run dependency analysis regularly as part of your workflow
- Check for new circular dependencies after major changes
- Monitor centrality changes over time

### 3. **Performance Considerations**
- Set appropriate `max_graph_size` limits
- Use `performance_threshold_seconds` to catch slow analyses
- Consider caching results for large projects

### 4. **Integration**
- Integrate dependency analysis into CI/CD pipelines
- Use impact analysis before making changes
- Include centrality information in code reviews

## Troubleshooting

### Common Issues

**"Dependency analysis is not enabled"**
- Ensure `DependencyConfig(enabled=True)` in your configuration
- Check that the dependency analysis components are properly initialized

**"File not found in project"**
- Verify the file path is relative to the project root
- Check that the file exists and is accessible

**Performance issues with large projects**
- Reduce `max_graph_size` setting
- Use `--no-progress` to disable progress tracking
- Consider analyzing subdirectories separately

**Invalid output format errors**
- Use only supported formats: `json`, `table`, or `text`
- Check command help for valid options

### Getting Help

- Use `--help` with any command to see available options
- Enable `--verbose` output for detailed information
- Check the logs for error details
- Ensure all required dependencies are installed

## Examples

### Complete Workflow Example

```bash
# 1. Analyze project dependencies
python -m repomap_tool.cli analyze-dependencies . --output table

# 2. Check for circular dependencies
python -m repomap_tool.cli find-cycles . --output text

# 3. Identify critical files
python -m repomap_tool.cli show-centrality . --output table

# 4. Assess change impact
python -m repomap_tool.cli impact-analysis . \
  --files src/main.py src/utils.py \
  --output json
```

### Configuration File Example

```yaml
# config.yaml
project_root: "."
dependencies:
  enabled: true
  max_graph_size: 5000
  enable_call_graph: true
  enable_impact_analysis: true
  centrality_algorithms:
    - "degree"
    - "betweenness"
    - "pagerank"
  performance_threshold_seconds: 60.0
```

This guide covers the essential dependency analysis features. For advanced usage and customization, refer to the API documentation and source code.
