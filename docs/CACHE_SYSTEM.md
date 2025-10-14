# Tree-Sitter Tag Cache System

## Overview

The RepoMap Tool uses a sophisticated caching system built on tree-sitter parsing to store and retrieve detailed code tag information. This system replaces the previous aider-based caching with a more efficient, detailed, and maintainable solution.

## Architecture

### TreeSitterTagCache

The core caching component is `TreeSitterTagCache`, which provides:

- **SQLite Backend**: Persistent storage that survives tool restarts
- **File Validation**: Hash + mtime checking for cache invalidation
- **CodeTag Integration**: Uses the existing `CodeTag` dataclass for consistency
- **Full Tag Details**: Stores complete tree-sitter categorization (not simplified)

### Key Components

```python
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.code_analysis.models import CodeTag

# Create cache
cache = TreeSitterTagCache()

# Store tags
tags = [CodeTag(name="MyClass", kind="class.name", file="/path/file.py", line=1, column=0)]
cache.set_tags("/path/file.py", tags)

# Retrieve tags
cached_tags = cache.get_tags("/path/file.py")
```

## Cache Management

### CLI Commands

The system provides two cache management commands:

```bash
# Show cache statistics
repomap-tool system cache-info

# Clear the cache
repomap-tool system cache-clear

# Clear without confirmation
repomap-tool system cache-clear --force
```

### Cache Statistics

The `cache-info` command shows:

- **Cache Location**: Path to the SQLite database
- **Cached Files**: Number of files in cache
- **Total Tags**: Total number of tags stored
- **Approx Size**: Estimated cache size in KB

## Cache Invalidation

### Automatic Invalidation

The cache automatically invalidates when:

1. **File Modified**: File modification time (mtime) changes
2. **Content Changed**: File content hash changes
3. **File Deleted**: File no longer exists

### Manual Invalidation

```python
# Invalidate specific file
cache.invalidate_file("/path/to/file.py")

# Clear entire cache
cache.clear()
```

## Integration with TreeSitterParser

The cache integrates seamlessly with `TreeSitterParser`:

```python
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.core.tag_cache import TreeSitterTagCache

# Create parser with cache
cache = TreeSitterTagCache()
parser = TreeSitterParser(cache=cache)

# get_tags() automatically uses cache
tags = parser.get_tags("/path/to/file.py")
```

## Database Schema

### file_cache Table

```sql
CREATE TABLE file_cache (
    file_path TEXT PRIMARY KEY,
    file_hash TEXT NOT NULL,
    mtime REAL NOT NULL,
    cached_at REAL NOT NULL
)
```

### tags Table

```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    file TEXT NOT NULL,
    line INTEGER NOT NULL,
    column INTEGER NOT NULL,
    end_line INTEGER,
    end_column INTEGER,
    rel_fname TEXT,
    FOREIGN KEY (file_path) REFERENCES file_cache(file_path)
        ON DELETE CASCADE
)
```

## Performance Benefits

### Compared to Aider Cache

1. **Full Tag Details**: Stores complete `kind` information (class.name, name.definition.function, etc.)
2. **No LLM Bias**: Designed for code analysis, not LLM token optimization
3. **Better Control**: Own caching strategy and validation logic
4. **Smaller Dependencies**: No large aider-chat package
5. **Cross-Language**: Works consistently across all tree-sitter supported languages

### Cache Hit Performance

- **First Parse**: ~50-100ms per file (tree-sitter parsing)
- **Cache Hit**: ~1-5ms per file (SQLite retrieval)
- **Cache Miss**: ~50-100ms per file (re-parse + cache store)

## Configuration

### Cache Directory

Default: `~/.repomap-tool/cache/`

Custom location:
```python
from pathlib import Path
cache = TreeSitterTagCache(cache_dir=Path("/custom/cache/path"))
```

### DI Container Integration

The cache is automatically provided by the DI container:

```python
from repomap_tool.core.container import Container

container = Container()
tag_cache = container.tag_cache()
```

## Migration from Aider

### What Changed

1. **Removed aider-chat dependency**: No longer requires aider-chat package
2. **Deleted .aider.tags.cache.v4/**: Old cache directory removed
3. **New cache location**: `~/.repomap-tool/cache/`
4. **Full tag details**: No more simplified `def`/`ref` tags

### No Migration Needed

The new cache system builds its cache on first use. No migration script is needed - the system will automatically parse and cache files as they are accessed.

## Troubleshooting

### Cache Issues

1. **Cache not working**: Check file permissions on cache directory
2. **Stale cache**: Use `cache-clear` command to reset
3. **Large cache**: Monitor with `cache-info` command

### Performance Issues

1. **Slow first run**: Normal - cache is being built
2. **Slow subsequent runs**: Check if files are being modified frequently
3. **Memory usage**: Cache is disk-based, minimal memory impact

## Development

### Adding New Tag Types

The cache automatically handles any `CodeTag` objects. To add new tag types:

1. Update `CodeTag` dataclass if needed
2. Update tree-sitter query files
3. Cache automatically stores new tag types

### Testing Cache

```python
# Unit tests
pytest tests/unit/test_tag_cache.py

# Integration tests
pytest tests/integration/test_no_aider.py
```

## Future Enhancements

- **Compression**: Compress cache data for large codebases
- **Distributed Cache**: Share cache across multiple tool instances
- **Cache Warming**: Pre-populate cache for common files
- **Analytics**: Track cache hit rates and performance metrics
