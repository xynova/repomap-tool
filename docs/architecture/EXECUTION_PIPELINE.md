# Execution Pipeline and Caching Flow

## Overview

This document describes the complete execution pipeline for RepoMap-Tool commands, from CLI invocation to output display, with a detailed breakdown of how caching affects performance at each stage.

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           EXECUTION PIPELINE                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. CLI Command
   ↓
2. Command Handler (Click)
   ↓
3. DI Container (Service Factory)
   ↓
4. Controller (MVC Pattern)
   ↓
5. Domain Services
   ↓
6. Analysis Engines
   ↓
7. Output Manager
   ↓
8. Console Output
```

## Detailed Flow Diagram

### Example: `inspect impact --files file.py`

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 1. CLI COMMAND INVOCATION                                                    │
│    Command: inspect impact --files file.py                                   │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 2. CLICK COMMAND HANDLER                                                      │
│    - Parse arguments/options                                                  │
│    - Load configuration (config file or defaults)                             │
│    - Create Click context                                                    │
│    - Get DI container from context                                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 3. DI CONTAINER INITIALIZATION                                                │
│    - Create or get singleton container                                       │
│    - Initialize services with dependencies                                    │
│    - Inject controllers with services                                         │
│                                                                               │
│    Services Created:                                                          │
│    ├─ PathResolver                                                           │
│    ├─ FileDiscoveryService                                                   │
│    ├─ TreeSitterParser (with TagCache)                                       │
│    ├─ ASTFileAnalyzer                                                        │
│    ├─ ImpactAnalysisEngine                                                   │
│    ├─ ImpactAnalyzer                                                         │
│    ├─ DependencyGraph                                                        │
│    └─ ImpactController                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 4. CONTROLLER EXECUTION (ImpactController.execute())                          │
│    - Validate configuration                                                  │
│    - Call _get_impact_data()                                                 │
│    - Build ViewModel                                                         │
│    - Return ViewModel                                                        │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 5. FILE DISCOVERY (PathResolver.get_all_project_files())                     │
│                                                                               │
│    ┌──────────────────────────────────────────────────────────────────────┐  │
│    │ CACHE LAYER 1: FileDiscoveryService                                  │  │
│    │                                                                      │  │
│    │ Memory Cache:                                                        │  │
│    │ - _all_files_cache (list of all files)                              │  │
│    │ - _code_files_cache (filtered code files)                            │  │
│    │ - _analyzable_files_cache (files for import analysis)                │  │
│    │                                                                      │  │
│    │ Cache Key: Based on exclude_tests parameter                          │  │
│    │ Cache Hit: Returns cached list immediately                           │  │
│    │ Cache Miss: Scans filesystem, filters, stores result                  │  │
│    └──────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│    Process:                                                                   │
│    1. Check memory cache for file list                                       │
│    2. If cache miss:                                                         │
│       - Scan project directory recursively                                    │
│       - Apply FileFilter (exclude patterns, test files, etc.)                │
│       - Return absolute paths                                                 │
│    3. Store in memory cache                                                  │
│    4. Return file list                                                       │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 6. AST ANALYSIS (ASTFileAnalyzer.analyze_multiple_files())                    │
│                                                                               │
│    ┌──────────────────────────────────────────────────────────────────────┐  │
│    │ CACHE LAYER 2: ASTFileAnalyzer                                       │  │
│    │                                                                      │  │
│    │ Memory Cache:                                                        │  │
│    │ - analysis_cache: Dict[str, FileAnalysisResult]                     │  │
│    │                                                                      │  │
│    │ Cache Key: "{file_path}:{analysis_type}"                            │  │
│    │ Cache Hit: Returns cached FileAnalysisResult                        │  │
│    │ Cache Miss: Parses file, analyzes, stores result                      │  │
│    └──────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│    For each file:                                                             │
│    1. Check analysis cache                                                    │
│    2. If cache miss:                                                         │
│       ↓                                                                       │
│    ┌──────────────────────────────────────────────────────────────────────┐ │
│    │ 6a. TREE-SITTER PARSING (TreeSitterParser.get_tags())                 │ │
│    │                                                                        │ │
│    │ ┌──────────────────────────────────────────────────────────────────┐ │ │
│    │ │ CACHE LAYER 3: TreeSitterTagCache (SQLite - Persistent)         │ │ │
│    │ │                                                                  │ │ │
│    │ │ SQLite Database: ~/.repomap-tool/cache/tags.db                   │ │ │
│    │ │ Tables:                                                          │ │ │
│    │ │ - file_cache (file_path, file_hash, mtime, cached_at)            │ │ │
│    │ │ - tags (file_path, name, kind, line, column, ...)                │ │ │
│    │ │                                                                  │ │ │
│    │ │ Cache Validation:                                                │ │ │
│    │ │ - Checks file hash + mtime                                        │ │ │
│    │ │ - Invalidates on file modification                                │ │ │
│    │ │                                                                  │ │ │
│    │ │ Cache Hit: Returns cached tags from SQLite (1-5ms)                │ │ │
│    │ │ Cache Miss: Parses with tree-sitter, stores in SQLite (50-100ms)  │ │ │
│    │ └──────────────────────────────────────────────────────────────────┘ │ │
│    │                                                                        │ │
│    │ Process:                                                               │ │
│    │ 1. Check if file should be excluded (FileFilter)                      │ │
│    │ 2. Check SQLite tag cache                                             │ │
│    │ 3. If cache hit and valid: return cached tags                          │ │
│    │ 4. If cache miss or invalid:                                          │ │
│    │    - Detect language (Python, JS, TS, etc.)                          │ │
│    │    - Load tree-sitter parser for language                             │ │
│    │    - Load query file (.scm) for language                             │ │
│    │    - Parse file with tree-sitter                                      │ │
│    │    - Extract tags using query                                         │ │
│    │    - Store tags in SQLite cache                                       │ │
│    │ 5. Return CodeTag list                                                │ │
│    └──────────────────────────────────────────────────────────────────────┘ │
│                                                                               │
│    3. Extract imports, functions, classes from tags                            │
│    4. Build FileAnalysisResult                                                │
│    5. Store in analysis cache                                                 │
│    6. Return FileAnalysisResult                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 7. IMPACT ANALYSIS (ImpactAnalysisEngine.analyze_file_impact())              │
│                                                                               │
│    ┌──────────────────────────────────────────────────────────────────────┐  │
│    │ CACHE LAYER 4: ImpactAnalyzer                                         │  │
│    │                                                                      │  │
│    │ Memory Cache:                                                        │  │
│    │ - cache: Dict[str, ImpactReport]                                     │  │
│    │                                                                      │  │
│    │ Cache Key: "|".join(sorted(changed_files))                          │  │
│    │ Cache Hit: Returns cached ImpactReport                              │  │
│    │ Cache Miss: Performs analysis, stores result                        │  │
│    └──────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
│    For each changed file:                                                     │
│    1. Check impact cache                                                     │
│    2. If cache miss:                                                         │
│       - Analyze direct dependencies (what this file imports)                │
│       - Analyze reverse dependencies (what imports this file)               │
│       - Calculate impact score                                              │
│       - Assess risk level                                                   │
│       - Suggest test files                                                  │
│       - Build FileImpactAnalysis                                             │
│    3. Store in impact cache                                                  │
│    4. Return FileImpactAnalysis                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 8. VIEW MODEL BUILDING (ImpactController._build_simple_view_model())          │
│    - Aggregate impact analyses                                              │
│    - Calculate overall metrics                                               │
│    - Build ImpactViewModel                                                   │
│    - Calculate token count for LLM optimization                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 9. OUTPUT MANAGEMENT (OutputManager.display())                                │
│    - Get formatter from FormatterRegistry                                    │
│    - Format ViewModel based on output format (text/json)                    │
│    - Use Jinja2 templates for text formatting                               │
│    - Display via ConsoleManager                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│ 10. CONSOLE OUTPUT                                                            │
│     - Rich console formatting                                                │
│     - Hierarchical display                                                  │
│     - Error/success messages                                                │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Caching Layers Summary

### Layer 1: File Discovery Service (Memory Cache)
- **Location**: `FileDiscoveryService._all_files_cache`, `_code_files_cache`, `_analyzable_files_cache`
- **Type**: In-memory dictionary
- **Lifetime**: Per-service-instance (cleared on service recreation)
- **Cache Key**: Based on `exclude_tests` parameter
- **Cache Hit Performance**: ~0.1ms (memory lookup)
- **Cache Miss Performance**: ~100-500ms (filesystem scan)

### Layer 2: AST Analysis Cache (Memory Cache)
- **Location**: `ASTFileAnalyzer.analysis_cache`
- **Type**: In-memory dictionary
- **Lifetime**: Per-analyzer-instance
- **Cache Key**: `"{file_path}:{analysis_type}"`
- **Cache Hit Performance**: ~0.1ms (memory lookup)
- **Cache Miss Performance**: ~50-200ms (parsing + analysis)

### Layer 3: Tree-Sitter Tag Cache (SQLite - Persistent)
- **Location**: `~/.repomap-tool/cache/tags.db`
- **Type**: SQLite database
- **Lifetime**: Persistent across tool restarts
- **Cache Validation**: File hash + modification time (before SQL query)
- **Cache Hit Performance**: ~1-5ms (SQLite query)
- **Cache Miss Performance**: ~50-100ms (tree-sitter parsing + SQL INSERT)
- **Invalidation**: Automatic on file modification or manual clear
- **Query Interface**: 
  - Analyzers call: `tree_sitter_parser.get_tags(file_path)`
  - TreeSitterParser abstracts SQL query execution
  - TreeSitterTagCache executes: `SELECT ... FROM tags WHERE file_path = ?`
- **Storage**: All symbol information per file (name, kind, line, column, etc.)
- **Scope**: File-based keys (not analysis-scope-based), shared across all analyzers

### Layer 4: Impact Analysis Cache (Memory Cache)
- **Location**: `ImpactAnalyzer.cache`
- **Type**: In-memory dictionary
- **Lifetime**: Per-analyzer-instance
- **Cache Key**: `"|".join(sorted(changed_files))`
- **Cache Hit Performance**: ~0.1ms (memory lookup)
- **Cache Miss Performance**: ~500ms-2s (full impact analysis)

### Additional Caches

#### Query Loader Cache (Memory Cache)
- **Location**: `QueryLoader.query_cache`
- **Type**: In-memory dictionary
- **Purpose**: Caches tree-sitter query files (.scm)
- **Cache Key**: Language name (e.g., "python", "javascript")
- **Performance**: Avoids re-reading query files from disk

#### Centrality Calculator Cache (Memory Cache)
- **Location**: `CentralityCalculator.cache`
- **Type**: In-memory dictionary
- **Purpose**: Caches centrality scores (degree, betweenness, pagerank, etc.)
- **Cache Key**: Centrality algorithm name
- **Performance**: Avoids expensive graph calculations

## Cache Invalidation Flow

### Automatic Invalidation

1. **Tree-Sitter Tag Cache**:
   - Validates on every `get_tags()` call
   - Compares file hash + mtime with cached values
   - Automatically invalidates on file modification
   - Database entry deleted if file deleted

2. **File Discovery Cache**:
   - Cleared when service cache is cleared
   - Manual clearing via `FileDiscoveryService.clear_cache()`

3. **AST Analysis Cache**:
   - Cleared when analyzer cache is cleared
   - Manual clearing via `ASTFileAnalyzer.clear_cache()`

4. **Impact Analysis Cache**:
   - Cleared when analyzer cache is cleared
   - Manual clearing via `ImpactAnalyzer.clear_cache()`

### Manual Invalidation

```bash
# Clear all caches
repomap-tool system cache-clear --force

# Clear specific cache
from repomap_tool.core.container import create_container
container = create_container(config)
container.tree_sitter_parser().tag_cache.clear()
```

## Performance Impact

### Without Caching (First Run)
- File discovery: ~500ms
- Tree-sitter parsing (100 files): ~5-10s
- AST analysis (100 files): ~2-5s
- Impact analysis: ~2-5s
- **Total**: ~10-20s for first run

### With Caching (Subsequent Runs)
- File discovery: ~0.1ms (memory cache)
- Tree-sitter parsing (100 files): ~100-500ms (SQLite cache)
- AST analysis (100 files): ~100-500ms (memory cache)
- Impact analysis: ~0.1ms (memory cache) if same files
- **Total**: ~200ms-1s for subsequent runs

### Cache Performance Gains
- **90%+ reduction** in parse times for cached files
- **95%+ reduction** in analysis times for repeated operations
- **Near-instant** file discovery on subsequent runs

## Cache Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    CACHE LIFECYCLE                           │
└─────────────────────────────────────────────────────────────┘

1. Tool Startup
   ↓
2. DI Container Creates Services
   ↓
3. Services Initialize Empty Caches (Memory)
   ↓
4. Tree-Sitter Tag Cache Opens SQLite DB
   ↓
5. Command Execution
   ↓
6. Cache Lookups (Layer 1 → 2 → 3 → 4)
   ↓
7. Cache Miss → Compute → Store
   ↓
8. Cache Hit → Return Cached Value
   ↓
9. Command Complete
   ↓
10. Caches Persist (Memory) or Close (SQLite)
```

## Cache Interactions

```
┌─────────────────────────────────────────────────────────────┐
│              CACHE DEPENDENCY CHAIN                         │
└─────────────────────────────────────────────────────────────┘

ImpactAnalyzer.cache (Memory)
    ↓ (depends on)
ASTFileAnalyzer.analysis_cache (Memory)
    ↓ (depends on)
TreeSitterParser.get_tags() (Abstraction Layer)
    ↓ (queries via SQL)
TreeSitterTagCache (SQLite - Persistent)
    ├─ SQL Query: SELECT ... FROM tags WHERE file_path = ?
    ├─ Stores: All symbol information per file
    ├─ Validates: File hash + mtime
    └─ Shared: Across all analyzers
    ↓ (depends on)
FileDiscoveryService._code_files_cache (Memory)
    ↓ (depends on)
FileSystem
```

### SQL Query Flow

```
Analyzer Layer:
  ASTFileAnalyzer.analyze_file()
    ↓ calls
  tree_sitter_parser.get_tags(file_path)
    
Abstraction Layer:
  TreeSitterParser.get_tags()
    ↓ calls
  tag_cache.get_tags(file_path)
    
SQL Query Layer:
  TreeSitterTagCache.get_tags()
    ↓ executes
  SQL: SELECT name, kind, file, line, column, ... 
       FROM tags WHERE file_path = ?
    ↓ returns
  List[CodeTag]
    
Back to Analyzer:
  Processes tags → FileAnalysisResult
```

## Cache Configuration

### Environment Variables
- `REPOMAP_CACHE_DISABLED=1`: Disables all caching
- `REPOMAP_CACHE_DIR=/custom/path`: Custom cache directory

### Configuration Options
- `CACHE_TTL`: Time-to-live for cache entries (default: 3600s)
- `CACHE_MAX_SIZE`: Maximum cache entries (default: 1000)
- `cache_results`: Enable/disable caching per service

## Best Practices

1. **First Run**: Expect slower performance as caches are built
2. **Subsequent Runs**: Enjoy fast performance with cached results
3. **File Changes**: Cache automatically invalidates modified files
4. **Cache Clearing**: Use `cache-clear` if you suspect stale data
5. **Performance Monitoring**: Use `cache-info` to monitor cache stats

## Troubleshooting

### Cache Not Working
- Check file permissions on cache directory
- Verify cache is not disabled via environment variable
- Check logs for cache errors

### Stale Cache
- Use `cache-clear` command to reset
- Restart tool to clear memory caches
- Check file modification times match cache

### Large Cache Size
- Monitor with `cache-info` command
- Clear old cache entries manually
- Adjust `CACHE_MAX_SIZE` configuration

