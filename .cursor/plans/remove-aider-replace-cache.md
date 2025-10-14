# Remove Aider Dependency and Create Generic Tag Cache

## Overview
Replace aider's RepoMap and its simplified tag cache with a custom tree-sitter tag caching system that stores detailed tag information (full `kind` fields) and works independently of aider.

## Current State Analysis

**What uses aider currently:**
- `src/repomap_tool/core/repo_map.py` - Uses `aider.repomap.RepoMap` for caching
- `src/repomap_tool/code_analysis/ast_file_analyzer.py` - Uses aider's RepoMap
- `src/repomap_tool/code_exploration/tree_builder.py` - Uses aider's RepoMap
- `.aider.tags.cache.v4/` - Aider's cache with simplified `def`/`ref` tags

**Why this is limiting:**
- Aider simplifies tags to `def`/`ref` for LLM optimization
- Loses detailed categorization (class vs function vs method)
- Can't do proper density analysis without re-parsing
- Unnecessary dependency on `aider-chat` package

## Phase 1: Design Generic Tag Cache System

### Create TagCache Service
**File**: `src/repomap_tool/core/tag_cache.py`

```python
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path
import sqlite3
import json
import hashlib
from datetime import datetime

@dataclass
class CachedTag:
    """A cached tag with full tree-sitter information"""
    name: str
    kind: str  # Full kind: 'class.name', 'name.definition.function', etc.
    line: int
    column: int
    end_line: int
    end_column: int
    file_path: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column,
            "file_path": self.file_path,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedTag":
        return cls(**data)

@dataclass
class FileCacheEntry:
    """Cache entry for a single file"""
    file_path: str
    file_hash: str  # SHA256 of file content
    mtime: float
    tags: List[CachedTag]
    cached_at: datetime
    
class TreeSitterTagCache:
    """Generic tag caching system for tree-sitter parsing results"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize cache with SQLite backend"""
        self.cache_dir = cache_dir or Path.home() / ".repomap-tool" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "tags.db"
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS file_cache (
                file_path TEXT PRIMARY KEY,
                file_hash TEXT NOT NULL,
                mtime REAL NOT NULL,
                cached_at REAL NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                name TEXT NOT NULL,
                kind TEXT NOT NULL,
                line INTEGER NOT NULL,
                column INTEGER NOT NULL,
                end_line INTEGER NOT NULL,
                end_column INTEGER NOT NULL,
                FOREIGN KEY (file_path) REFERENCES file_cache(file_path)
                    ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_file 
            ON tags(file_path)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tags_kind 
            ON tags(kind)
        """)
        
        conn.commit()
        conn.close()
        
    def get_tags(self, file_path: str) -> Optional[List[CachedTag]]:
        """Get cached tags for a file if valid"""
        if not self._is_cache_valid(file_path):
            return None
            
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, kind, line, column, end_line, end_column, file_path
            FROM tags WHERE file_path = ?
        """, (file_path,))
        
        tags = [
            CachedTag(*row) for row in cursor.fetchall()
        ]
        
        conn.close()
        return tags
        
    def set_tags(self, file_path: str, tags: List[Dict[str, Any]]):
        """Cache tags for a file"""
        file_hash = self._compute_file_hash(file_path)
        mtime = Path(file_path).stat().st_mtime
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Delete old entry if exists
        cursor.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        
        # Insert file cache entry
        cursor.execute("""
            INSERT INTO file_cache (file_path, file_hash, mtime, cached_at)
            VALUES (?, ?, ?, ?)
        """, (file_path, file_hash, mtime, datetime.now().timestamp()))
        
        # Insert tags
        for tag in tags:
            cursor.execute("""
                INSERT INTO tags (file_path, name, kind, line, column, end_line, end_column)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                file_path,
                tag["name"],
                tag["kind"],
                tag["line"],
                tag["column"],
                tag["end_line"],
                tag["end_column"],
            ))
        
        conn.commit()
        conn.close()
        
    def invalidate_file(self, file_path: str):
        """Invalidate cache for a file"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_cache WHERE file_path = ?", (file_path,))
        conn.commit()
        conn.close()
        
    def clear(self):
        """Clear entire cache"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM file_cache")
        cursor.execute("DELETE FROM tags")
        conn.commit()
        conn.close()
        
    def _is_cache_valid(self, file_path: str) -> bool:
        """Check if cached data is still valid"""
        if not Path(file_path).exists():
            return False
            
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_hash, mtime FROM file_cache WHERE file_path = ?
        """, (file_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
            
        cached_hash, cached_mtime = result
        current_mtime = Path(file_path).stat().st_mtime
        
        # Check if file modified
        if current_mtime > cached_mtime:
            return False
            
        # Check if content changed
        current_hash = self._compute_file_hash(file_path)
        return current_hash == cached_hash
        
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file content"""
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM file_cache")
        file_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM tags")
        tag_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(LENGTH(name) + LENGTH(kind)) FROM tags")
        approx_size = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            "cached_files": file_count,
            "total_tags": tag_count,
            "approx_size_bytes": approx_size,
            "cache_location": str(self.db_path),
        }
```

**Key:** Stores FULL tag information including detailed `kind` field, not simplified like aider.

## Phase 2: Integrate Cache with TreeSitterParser

### Update TreeSitterParser to use cache
**File**: `src/repomap_tool/code_analysis/tree_sitter_parser.py`

```python
class TreeSitterParser:
    def __init__(
        self,
        project_root: Optional[str] = None,
        custom_queries_dir: Optional[str] = None,
        cache: Optional[TreeSitterTagCache] = None,
    ):
        self.project_root = project_root or "."
        self._query_cache: Dict[str, str] = {}
        self.tag_cache = cache or TreeSitterTagCache()
        
    def get_tags(self, file_path: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get tags for a file, using cache if available"""
        if use_cache:
            cached_tags = self.tag_cache.get_tags(file_path)
            if cached_tags is not None:
                return [tag.to_dict() for tag in cached_tags]
        
        # Parse file
        tags = self.parse_file(file_path)
        
        # Cache results
        if use_cache:
            self.tag_cache.set_tags(file_path, tags)
        
        return tags
```

## Phase 3: Remove Aider Dependencies

### Update repo_map.py to use TreeSitterParser only
**File**: `src/repomap_tool/core/repo_map.py`

Remove:
```python
from aider.repomap import RepoMap
from aider.io import InputOutput
```

Replace with:
```python
class RepoMapService:
    def __init__(
        self,
        config: RepoMapConfig,
        console: Console,
        tree_sitter_parser: TreeSitterParser,
        parallel_tag_extractor: Optional[ParallelTagExtractor] = None,
    ):
        # Remove aider RepoMap initialization
        # Use TreeSitterParser directly
        self.parser = tree_sitter_parser
        
    def _get_cached_identifiers(self) -> List[str]:
        """Get all identifiers from our cache"""
        # Use TreeSitterParser's cache instead of aider's
        all_identifiers = set()
        
        for file_path in self.file_paths:
            tags = self.parser.get_tags(file_path)
            for tag in tags:
                all_identifiers.add(tag["name"])
                
        return list(all_identifiers)
```

### Update ast_file_analyzer.py
**File**: `src/repomap_tool/code_analysis/ast_file_analyzer.py`

Remove aider RepoMap usage:
```python
class ASTFileAnalyzer:
    def __init__(
        self, 
        project_root: Optional[str] = None,
        tree_sitter_parser: Optional[TreeSitterParser] = None,
    ):
        self.project_root = project_root
        self.parser = tree_sitter_parser or TreeSitterParser(project_root)
        
    def analyze_file(self, file_path: str, ...) -> FileAnalysisResult:
        # Use TreeSitterParser directly
        tags = self.parser.get_tags(file_path)
        
        # Extract information
        imports = self._extract_imports_from_tags(tags, file_path)
        functions = self._extract_functions_from_tags(tags)
        classes = self._extract_classes_from_tags(tags)
```

### Update tree_builder.py
**File**: `src/repomap_tool/code_exploration/tree_builder.py`

Same pattern - replace aider RepoMap with TreeSitterParser.

## Phase 4: Update DI Container

### Register TagCache service
**File**: `src/repomap_tool/core/container.py`

```python
# Add to Container class:
tag_cache = providers.Singleton(
    TreeSitterTagCache,
    cache_dir=config.cache_dir,
)

tree_sitter_parser = providers.Factory(
    TreeSitterParser,
    project_root=config.project_root,
    custom_queries_dir=config.custom_queries_dir,
    cache=tag_cache,
)

# Update services that used aider
repo_map_service = providers.Factory(
    RepoMapService,
    config=config,
    console=console,
    tree_sitter_parser=tree_sitter_parser,
    parallel_tag_extractor=parallel_tag_extractor,
)

ast_file_analyzer = providers.Factory(
    ASTFileAnalyzer,
    project_root=config.project_root,
    tree_sitter_parser=tree_sitter_parser,
)
```

## Phase 5: Add Cache Management Commands

### Add cache commands to system group
**File**: `src/repomap_tool/cli/commands/system.py`

```python
@system.command()
@click.pass_context
def cache_info(ctx: click.Context):
    """Show cache statistics"""
    from repomap_tool.core.tag_cache import TreeSitterTagCache
    cache = TreeSitterTagCache()
    stats = cache.get_cache_stats()
    
    console = get_console(ctx)
    console.print(f"Cache location: {stats['cache_location']}")
    console.print(f"Cached files: {stats['cached_files']}")
    console.print(f"Total tags: {stats['total_tags']}")
    console.print(f"Size: {stats['approx_size_bytes'] / 1024:.2f} KB")

@system.command()
@click.option("--force", is_flag=True, help="Clear without confirmation")
@click.pass_context
def cache_clear(ctx: click.Context, force: bool):
    """Clear the tag cache"""
    from repomap_tool.core.tag_cache import TreeSitterTagCache
    
    if not force:
        if not click.confirm("Clear all cached tags?"):
            return
            
    cache = TreeSitterTagCache()
    cache.clear()
    console = get_console(ctx)
    console.print("Cache cleared")
```

## Phase 6: Update pyproject.toml

### Remove aider dependency
**File**: `pyproject.toml`

Change:
```toml
dependencies = [
    # Remove: "aider-chat>=0.82.0",
    "networkx>=3.0",
    "diskcache>=5.6.0",
    "grep-ast>=0.1.0",  # Keep for tree-sitter language detection
    "pygments>=2.15.0",
    "tree-sitter>=0.23.0",
    # ... rest
]
```

Update description:
```toml
description = "Portable code analysis tool using tree-sitter"
```

## Phase 7: Migration Guide

### Create migration script
**File**: `scripts/migrate_aider_cache.py`

```python
"""Migrate from aider cache to new TreeSitterTagCache"""
import sqlite3
import pickle
from pathlib import Path
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser

def migrate_aider_cache():
    """Convert aider's cache to new format"""
    aider_cache = Path(".aider.tags.cache.v4/cache.db")
    if not aider_cache.exists():
        print("No aider cache found - nothing to migrate")
        return
        
    new_cache = TreeSitterTagCache()
    parser = TreeSitterParser()
    
    # Read aider cache
    conn = sqlite3.connect(str(aider_cache))
    cursor = conn.cursor()
    cursor.execute("SELECT key FROM Cache")
    files = [row[0] for row in cursor.fetchall() if row[0].endswith('.py')]
    conn.close()
    
    # Re-parse with TreeSitterParser to get detailed tags
    print(f"Migrating {len(files)} files...")
    for file_path in files:
        if Path(file_path).exists():
            try:
                tags = parser.get_tags(file_path, use_cache=False)
                new_cache.set_tags(file_path, tags)
            except Exception as e:
                print(f"Error migrating {file_path}: {e}")
                
    stats = new_cache.get_cache_stats()
    print(f"Migration complete: {stats['cached_files']} files, {stats['total_tags']} tags")
```

## Phase 8: Testing

### Unit tests
**File**: `tests/unit/test_tag_cache.py`
- Test cache storage and retrieval
- Test cache invalidation on file change
- Test file hash checking
- Test cache statistics

### Integration tests
**File**: `tests/integration/test_no_aider.py`
- Test that aider is not imported anywhere
- Test all functionality works without aider
- Test cache persists across sessions
- Test cache management commands

## Phase 9: Documentation Updates

### Update README.md
- Remove references to aider
- Document new caching system
- Add cache management commands

### Update ARCHITECTURE.md
- Document TagCache design
- Explain why we removed aider
- Show cache performance benefits

## Success Criteria

- Zero aider imports in codebase
- All tests pass without aider-chat installed
- Tag cache stores detailed `kind` information
- Cache invalidation works correctly
- Performance is same or better
- All existing functionality preserved
- Cache management commands work
- Migration script successfully converts existing cache

## Benefits

1. **Full tag detail** - Preserve complete tree-sitter categorization
2. **No LLM bias** - Cache designed for code analysis, not LLM feeding
3. **Better performance** - Optimized for our use cases
4. **Smaller dependency** - Remove large aider-chat package
5. **More control** - Own our caching strategy
6. **Cross-language** - Works same way for all languages

## Implementation Checklist

- [ ] Design and implement TreeSitterTagCache with SQLite backend
- [ ] Integrate cache with TreeSitterParser
- [ ] Remove aider RepoMap from repo_map.py
- [ ] Remove aider from ast_file_analyzer.py
- [ ] Remove aider from tree_builder.py
- [ ] Update DI container for new cache service
- [ ] Add cache management CLI commands
- [ ] Remove aider-chat from pyproject.toml
- [ ] Create script to migrate existing aider cache
- [ ] Test everything works without aider installed
- [ ] Update documentation for new cache system

