# Architecture Refactoring Action Plan

**Priority**: High  
**Timeline**: Weeks 1-3  
**Status**: 🔴 Not Started

## 🏗️ Overview

This plan addresses the architectural issues identified in the code review, focusing on breaking down the monolithic `DockerRepoMap` class and improving the overall modularity and maintainability of the codebase.

## 📊 Current Architecture Analysis

### Problem Areas
1. **Monolithic Design**: `DockerRepoMap` class (783 lines) handles multiple responsibilities
2. **Tight Coupling**: Components are tightly coupled, making testing and maintenance difficult
3. **Mixed Concerns**: File scanning, tag extraction, matching, and caching all in one class
4. **Poor Separation**: Business logic mixed with infrastructure concerns

### Current Structure
```
src/repomap_tool/
├── core.py (783 lines) - Monolithic DockerRepoMap class
├── models.py (256 lines) - Pydantic models
├── cli.py (401 lines) - CLI interface
├── matchers/ - Matching algorithms
└── api/ - API server
```

## 🎯 Success Criteria

- [ ] `DockerRepoMap` class reduced to <100 lines
- [ ] Clear separation of concerns across modules
- [ ] Improved testability with dependency injection
- [ ] Better error handling and recovery
- [ ] Enhanced configurability and extensibility
- [ ] Maintained backward compatibility

## 📝 Detailed Action Items

### Phase 1: Core Architecture Redesign (Week 1)

#### 1.1 Define New Architecture

**Target Architecture:**
```
src/repomap_tool/
├── core/
│   ├── __init__.py
│   ├── project_scanner.py      # File discovery and filtering
│   ├── tag_extractor.py        # Identifier extraction
│   ├── search_engine.py        # Search coordination
│   ├── cache_manager.py        # Caching logic
│   └── docker_repomap.py       # Main orchestrator (<100 lines)
├── exceptions.py               # Custom exception hierarchy
├── protocols.py                # Type protocols and interfaces
├── models.py                   # Pydantic models (existing)
├── cli.py                      # CLI interface (existing)
└── matchers/                   # Matching algorithms (existing)
```

**Design Principles:**
- **Single Responsibility**: Each class has one clear purpose
- **Dependency Injection**: Components receive dependencies through constructor
- **Interface Segregation**: Small, focused interfaces
- **Open/Closed**: Open for extension, closed for modification

#### 1.2 Create Core Components

**ProjectScanner Class:**
```python
from pathlib import Path
from typing import List, Set
import os
import logging

class ProjectScanner:
    """Handles file discovery and filtering based on project configuration."""
    
    def __init__(self, project_root: Path, gitignore_patterns: List[str], supported_extensions: Set[str]):
        self.project_root = project_root
        self.gitignore_patterns = gitignore_patterns
        self.supported_extensions = supported_extensions
        self.logger = logging.getLogger(__name__)
    
    def scan_files(self) -> List[Path]:
        """Scan project files, respecting .gitignore and file type filters."""
        files = []
        
        for root, dirs, filenames in os.walk(self.project_root):
            # Filter directories
            dirs[:] = self._filter_directories(root, dirs)
            
            # Process files
            for filename in filenames:
                file_path = Path(root) / filename
                if self._should_include_file(file_path):
                    files.append(file_path)
        
        self.logger.info(f"Found {len(files)} files in project")
        return files
    
    def _filter_directories(self, root: str, dirs: List[str]) -> List[str]:
        """Filter directories based on gitignore patterns."""
        return [
            d for d in dirs 
            if not self._is_ignored_directory(Path(root) / d)
        ]
    
    def _is_ignored_directory(self, dir_path: Path) -> bool:
        """Check if directory should be ignored."""
        return should_ignore_file(dir_path, self.gitignore_patterns, self.project_root)
    
    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in analysis."""
        # Check gitignore
        if should_ignore_file(file_path, self.gitignore_patterns, self.project_root):
            return False
        
        # Check file extension
        return file_path.suffix.lower() in self.supported_extensions
```

**TagExtractor Class:**
```python
from typing import List, Protocol, Optional
from pathlib import Path
import logging

class RepoMapProtocol(Protocol):
    """Protocol for RepoMap-like objects."""
    def get_tags(self, file_path: str, rel_fname: str) -> List[Tag]: ...
    def get_ranked_tags_map(self, files: List[str], max_tokens: int) -> Optional[str]: ...

class TagExtractor:
    """Handles identifier extraction from project files."""
    
    def __init__(self, repo_map: RepoMapProtocol, project_root: Path):
        self.repo_map = repo_map
        self.project_root = project_root
        self.logger = logging.getLogger(__name__)
    
    def extract_tags_from_files(self, files: List[Path]) -> List[Tag]:
        """Extract tags from multiple files."""
        all_tags = []
        
        for file_path in files:
            try:
                tags = self._extract_tags_from_file(file_path)
                all_tags.extend(tags)
            except Exception as e:
                self.logger.warning(f"Failed to extract tags from {file_path}: {e}")
        
        self.logger.info(f"Extracted {len(all_tags)} tags from {len(files)} files")
        return all_tags
    
    def _extract_tags_from_file(self, file_path: Path) -> List[Tag]:
        """Extract tags from a single file."""
        rel_fname = str(file_path.relative_to(self.project_root))
        tags = self.repo_map.get_tags(str(file_path), rel_fname)
        return tags or []
    
    def extract_identifiers(self, project_map: Dict[str, Any]) -> Set[str]:
        """Extract identifiers from project map structure."""
        identifiers: Set[str] = set()
        
        if not project_map:
            return identifiers
        
        # Handle string format (real aider RepoMap)
        if isinstance(project_map, str):
            identifiers.update(self._extract_from_string(project_map))
        
        # Handle dictionary format
        elif isinstance(project_map, dict):
            identifiers.update(self._extract_from_dict(project_map))
        
        return identifiers
    
    def _extract_from_string(self, project_map: str) -> Set[str]:
        """Extract identifiers from string representation."""
        import re
        
        patterns = [
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)",
        ]
        
        identifiers = set()
        for pattern in patterns:
            matches = re.findall(pattern, project_map)
            identifiers.update(matches)
        
        return identifiers
    
    def _extract_from_dict(self, project_map: Dict[str, Any]) -> Set[str]:
        """Extract identifiers from dictionary structure."""
        identifiers: Set[str] = set()
        
        # Handle tags
        if "tags" in project_map and project_map["tags"]:
            for tag in project_map["tags"]:
                if hasattr(tag, "name") and tag.name:
                    identifiers.add(tag.name)
        
        # Handle direct identifiers
        if "identifiers" in project_map and project_map["identifiers"]:
            if isinstance(project_map["identifiers"], (list, set, tuple)):
                identifiers.update(project_map["identifiers"])
        
        return identifiers
```

**SearchEngine Class:**
```python
from typing import List, Optional, Dict, Any
from .matchers.fuzzy_matcher import FuzzyMatcher
from .matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
from .matchers.hybrid_matcher import HybridMatcher
from ..models import SearchRequest, SearchResponse, MatchResult

class SearchEngine:
    """Coordinates different matching strategies and manages search operations."""
    
    def __init__(self, config: RepoMapConfig):
        self.config = config
        self.fuzzy_matcher: Optional[FuzzyMatcher] = None
        self.semantic_matcher: Optional[AdaptiveSemanticMatcher] = None
        self.hybrid_matcher: Optional[HybridMatcher] = None
        self._initialize_matchers()
    
    def _initialize_matchers(self) -> None:
        """Initialize matching components based on configuration."""
        if self.config.fuzzy_match.enabled:
            self.fuzzy_matcher = FuzzyMatcher(
                threshold=self.config.fuzzy_match.threshold,
                strategies=self.config.fuzzy_match.strategies,
                cache_results=self.config.fuzzy_match.cache_results,
                verbose=self.config.verbose,
            )
        
        if self.config.semantic_match.enabled:
            self.semantic_matcher = AdaptiveSemanticMatcher(verbose=self.config.verbose)
        
        if self.config.fuzzy_match.enabled and self.config.semantic_match.enabled:
            self.hybrid_matcher = HybridMatcher(
                fuzzy_threshold=self.config.fuzzy_match.threshold,
                semantic_threshold=self.config.semantic_match.threshold,
                verbose=self.config.verbose,
            )
    
    def search(self, request: SearchRequest, identifiers: Set[str]) -> SearchResponse:
        """Perform search using the appropriate matching strategy."""
        start_time = time.time()
        
        try:
            if request.match_type == "fuzzy" and self.fuzzy_matcher:
                results = self._fuzzy_search(request, identifiers)
            elif request.match_type == "semantic" and self.semantic_matcher:
                results = self._semantic_search(request, identifiers)
            elif request.match_type == "hybrid" and self.hybrid_matcher:
                results = self._hybrid_search(request, identifiers)
            else:
                results = []
            
            search_time = (time.time() - start_time) * 1000
            
            return SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=len(results),
                results=results,
                search_time_ms=search_time,
                cache_hit=False,  # TODO: Implement cache checking
                metadata={
                    "strategies_used": request.strategies or [],
                    "identifiers_searched": len(identifiers)
                }
            )
        
        except Exception as e:
            search_time = (time.time() - start_time) * 1000
            return SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=0,
                results=[],
                search_time_ms=search_time,
                cache_hit=False,
                error=str(e),
                metadata={}
            )
    
    def _fuzzy_search(self, request: SearchRequest, identifiers: Set[str]) -> List[MatchResult]:
        """Perform fuzzy search."""
        if not self.fuzzy_matcher:
            return []
        
        strategies = request.strategies or self.config.fuzzy_match.strategies
        matches = self.fuzzy_matcher.match_identifiers(request.query, identifiers)
        
        results = []
        for identifier, score in matches:
            if score >= request.threshold * 100:
                results.append(MatchResult(
                    identifier=identifier,
                    score=score / 100.0,
                    match_type="fuzzy",
                    context="",
                    file_path=""
                ))
        
        return results
    
    def _semantic_search(self, request: SearchRequest, identifiers: Set[str]) -> List[MatchResult]:
        """Perform semantic search."""
        if not self.semantic_matcher:
            return []
        
        # Learn from identifiers if not already done
        self.semantic_matcher.learn_from_identifiers(identifiers)
        
        matches = self.semantic_matcher.match_identifiers(request.query, identifiers)
        
        results = []
        for identifier, score in matches:
            if score >= request.threshold:
                results.append(MatchResult(
                    identifier=identifier,
                    score=score,
                    match_type="semantic",
                    context="",
                    file_path=""
                ))
        
        return results
    
    def _hybrid_search(self, request: SearchRequest, identifiers: Set[str]) -> List[MatchResult]:
        """Perform hybrid search."""
        if not self.hybrid_matcher:
            return []
        
        matches = self.hybrid_matcher.match_identifiers(request.query, identifiers)
        
        results = []
        for identifier, score in matches:
            if score >= request.threshold:
                results.append(MatchResult(
                    identifier=identifier,
                    score=score,
                    match_type="hybrid",
                    context="",
                    file_path=""
                ))
        
        return results
```

**CacheManager Class:**
```python
from typing import Any, Optional, Dict
import time
from collections import OrderedDict

class CacheManager:
    """Manages caching with size limits and eviction policies."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = OrderedDict()
        self._access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache with TTL checking."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                # Update access time for LRU
                self._access_times[key] = time.time()
                self._cache.move_to_end(key)
                return value
            else:
                self._evict(key)
        return None
    
    def put(self, key: str, value: Any) -> None:
        """Put value in cache with size limits."""
        # Check size limits
        if len(self._cache) >= self.max_size:
            self._evict_oldest()
        
        self._cache[key] = (value, time.time())
        self._access_times[key] = time.time()
    
    def _evict_oldest(self) -> None:
        """Evict least recently used items."""
        if not self._cache:
            return
        
        oldest_key = min(self._access_times.keys(), 
                        key=lambda k: self._access_times[k])
        self._evict(oldest_key)
    
    def _evict(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]
    
    def clear(self) -> None:
        """Clear all cached items."""
        self._cache.clear()
        self._access_times.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl
        }
```

### Phase 2: Refactored DockerRepoMap (Week 2)

#### 2.1 New DockerRepoMap Class

**Refactored Main Class:**
```python
from typing import Optional, List, Set
from pathlib import Path
import logging
import time
from datetime import datetime

from .core.project_scanner import ProjectScanner
from .core.tag_extractor import TagExtractor
from .core.search_engine import SearchEngine
from .core.cache_manager import CacheManager
from ..models import RepoMapConfig, SearchRequest, SearchResponse, ProjectInfo
from ..exceptions import RepoMapError, TagExtractionError

class DockerRepoMap:
    """Main orchestrator for Docker RepoMap functionality."""
    
    def __init__(self, config: RepoMapConfig):
        """Initialize Docker RepoMap with validated configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info(f"Initialized DockerRepoMap for {self.config.project_root}")
    
    def _initialize_components(self) -> None:
        """Initialize all core components."""
        # Initialize RepoMap (aider dependency)
        self.repo_map = self._create_repo_map()
        
        # Initialize core components
        self.project_scanner = ProjectScanner(
            project_root=self.config.project_root,
            gitignore_patterns=self._load_gitignore_patterns(),
            supported_extensions={".py", ".js", ".java", ".cpp", ".c", ".h"}
        )
        
        self.tag_extractor = TagExtractor(
            repo_map=self.repo_map,
            project_root=self.config.project_root
        )
        
        self.search_engine = SearchEngine(self.config)
        
        self.cache_manager = CacheManager(
            max_size=1000,
            ttl=3600
        )
    
    def _create_repo_map(self) -> Optional[RepoMapProtocol]:
        """Create RepoMap instance or return None if not available."""
        if not AIDER_AVAILABLE:
            return None
        
        try:
            from aider.io import InputOutput
            from aider.models import Model, DEFAULT_MODEL_NAME
            
            io = InputOutput()
            model = Model(DEFAULT_MODEL_NAME)
            
            return RepoMap(
                map_tokens=self.config.map_tokens,
                root=str(self.config.project_root),
                main_model=model,
                io=io,
                verbose=self.config.verbose,
                refresh="auto" if self.config.refresh_cache else "no",
            )
        except Exception as e:
            self.logger.warning(f"Failed to create RepoMap: {e}")
            return None
    
    def _load_gitignore_patterns(self) -> List[str]:
        """Load gitignore patterns from project root."""
        gitignore_path = self.config.project_root / ".gitignore"
        return parse_gitignore(gitignore_path)
    
    def analyze_project(self) -> ProjectInfo:
        """Analyze project and return comprehensive project information."""
        start_time = time.time()
        
        try:
            # Scan project files
            project_files = self.project_scanner.scan_files()
            
            if not project_files:
                return self._create_empty_project_info()
            
            # Extract tags from files
            all_tags = self.tag_extractor.extract_tags_from_files(project_files)
            
            # Extract identifiers
            project_map = {"tags": all_tags} if all_tags else {}
            all_identifiers = self.tag_extractor.extract_identifiers(project_map)
            
            # Analyze file types and identifier types
            file_types = self._analyze_file_types(project_files)
            identifier_types = self._analyze_identifier_types(all_identifiers)
            
            analysis_time = (time.time() - start_time) * 1000
            
            # Create project info
            project_info = ProjectInfo(
                project_root=str(self.config.project_root),
                total_files=len(project_files),
                total_identifiers=len(all_identifiers),
                file_types=file_types,
                identifier_types=identifier_types,
                analysis_time_ms=analysis_time,
                cache_size_bytes=self._get_cache_size(),
                last_updated=datetime.now(),
            )
            
            self.logger.info(f"Project analysis complete: {project_info}")
            return project_info
            
        except Exception as e:
            self.logger.error(f"Project analysis failed: {e}")
            raise RepoMapError(f"Failed to analyze project: {e}")
    
    def search_identifiers(self, request: SearchRequest) -> SearchResponse:
        """Search for identifiers using the specified matching strategy."""
        try:
            # Get project files and extract identifiers
            project_files = self.project_scanner.scan_files()
            
            if not project_files:
                return self._create_empty_search_response(request)
            
            all_tags = self.tag_extractor.extract_tags_from_files(project_files)
            project_map = {"tags": all_tags} if all_tags else {}
            all_identifiers = self.tag_extractor.extract_identifiers(project_map)
            
            # Perform search
            return self.search_engine.search(request, all_identifiers)
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=0,
                results=[],
                search_time_ms=0,
                cache_hit=False,
                error=str(e),
                metadata={}
            )
    
    def _create_empty_project_info(self) -> ProjectInfo:
        """Create empty project info for projects with no files."""
        return ProjectInfo(
            project_root=str(self.config.project_root),
            total_files=0,
            total_identifiers=0,
            file_types={},
            identifier_types={
                "variables": 0,
                "functions": 0,
                "classes": 0,
                "constants": 0,
                "other": 0,
            },
            analysis_time_ms=0,
            cache_size_bytes=self._get_cache_size(),
            last_updated=datetime.now(),
        )
    
    def _create_empty_search_response(self, request: SearchRequest) -> SearchResponse:
        """Create empty search response for projects with no files."""
        return SearchResponse(
            query=request.query,
            match_type=request.match_type,
            threshold=request.threshold,
            total_results=0,
            results=[],
            search_time_ms=0,
            cache_hit=False,
            metadata={
                "strategies_used": request.strategies or [],
                "identifiers_searched": 0
            }
        )
    
    def _analyze_file_types(self, files: List[Path]) -> Dict[str, int]:
        """Analyze file types in the project."""
        file_types: Dict[str, int] = {}
        for file_path in files:
            ext = file_path.suffix.lower()
            file_types[ext] = file_types.get(ext, 0) + 1
        return file_types
    
    def _analyze_identifier_types(self, identifiers: Set[str]) -> Dict[str, int]:
        """Analyze types of identifiers in the project."""
        types = {
            "functions": 0,
            "classes": 0,
            "variables": 0,
            "constants": 0,
            "other": 0,
        }
        
        for identifier in identifiers:
            if not identifier or not isinstance(identifier, str):
                continue
            
            try:
                if identifier.isupper():
                    types["constants"] += 1
                elif identifier[0].isupper():
                    types["classes"] += 1
                elif identifier.endswith("()"):
                    types["functions"] += 1
                elif identifier.islower():
                    types["variables"] += 1
                else:
                    types["other"] += 1
            except (IndexError, AttributeError):
                types["other"] += 1
        
        return types
    
    def _get_cache_size(self) -> Optional[int]:
        """Get cache size in bytes."""
        if self.config.cache_dir:
            try:
                cache_path = Path(self.config.cache_dir)
                return sum(
                    f.stat().st_size for f in cache_path.rglob("*") if f.is_file()
                )
            except Exception:
                return None
        return None
```

### Phase 3: Exception Hierarchy and Protocols (Week 3)

#### 3.1 Custom Exception Hierarchy

**exceptions.py:**
```python
"""Custom exception hierarchy for repomap-tool."""

class RepoMapError(Exception):
    """Base exception for all repomap-tool errors."""
    pass

class ConfigurationError(RepoMapError):
    """Raised when configuration is invalid."""
    pass

class FileAccessError(RepoMapError):
    """Raised when file access fails."""
    pass

class TagExtractionError(RepoMapError):
    """Raised when tag extraction fails."""
    pass

class SearchError(RepoMapError):
    """Raised when search operations fail."""
    pass

class CacheError(RepoMapError):
    """Raised when cache operations fail."""
    pass

class ValidationError(RepoMapError):
    """Raised when data validation fails."""
    pass
```

#### 3.2 Type Protocols

**protocols.py:**
```python
"""Type protocols and interfaces for repomap-tool."""

from typing import Protocol, List, Optional, Dict, Any
from pathlib import Path

class Tag(Protocol):
    """Protocol for tag objects."""
    name: str
    kind: str

class RepoMapProtocol(Protocol):
    """Protocol for RepoMap-like objects."""
    def get_tags(self, file_path: str, rel_fname: str) -> List[Tag]: ...
    def get_ranked_tags_map(self, files: List[str], max_tokens: int) -> Optional[str]: ...

class ProjectScannerProtocol(Protocol):
    """Protocol for project scanner objects."""
    def scan_files(self) -> List[Path]: ...

class TagExtractorProtocol(Protocol):
    """Protocol for tag extractor objects."""
    def extract_tags_from_files(self, files: List[Path]) -> List[Tag]: ...
    def extract_identifiers(self, project_map: Dict[str, Any]) -> Set[str]: ...

class SearchEngineProtocol(Protocol):
    """Protocol for search engine objects."""
    def search(self, request: SearchRequest, identifiers: Set[str]) -> SearchResponse: ...

class CacheManagerProtocol(Protocol):
    """Protocol for cache manager objects."""
    def get(self, key: str) -> Optional[Any]: ...
    def put(self, key: str, value: Any) -> None: ...
    def clear(self) -> None: ...
    def get_stats(self) -> Dict[str, Any]: ...
```

## 🔧 Implementation Guidelines

### Migration Strategy
1. **Parallel Development**: Create new classes alongside existing code
2. **Gradual Migration**: Migrate functionality piece by piece
3. **Backward Compatibility**: Maintain existing API during transition
4. **Testing**: Update tests incrementally as components are migrated

### Testing Strategy
```python
# Test each component independently
def test_project_scanner():
    scanner = ProjectScanner(project_root, gitignore_patterns, supported_extensions)
    files = scanner.scan_files()
    assert len(files) > 0

def test_tag_extractor():
    extractor = TagExtractor(mock_repo_map, project_root)
    tags = extractor.extract_tags_from_files(files)
    assert len(tags) > 0

def test_search_engine():
    engine = SearchEngine(config)
    response = engine.search(request, identifiers)
    assert response.total_results >= 0

def test_cache_manager():
    cache = CacheManager(max_size=100, ttl=3600)
    cache.put("key", "value")
    assert cache.get("key") == "value"
```

### Dependency Injection
```python
# Allow dependency injection for testing
class DockerRepoMap:
    def __init__(
        self, 
        config: RepoMapConfig,
        project_scanner: Optional[ProjectScannerProtocol] = None,
        tag_extractor: Optional[TagExtractorProtocol] = None,
        search_engine: Optional[SearchEngineProtocol] = None,
        cache_manager: Optional[CacheManagerProtocol] = None
    ):
        self.config = config
        
        # Use injected dependencies or create defaults
        self.project_scanner = project_scanner or self._create_project_scanner()
        self.tag_extractor = tag_extractor or self._create_tag_extractor()
        self.search_engine = search_engine or self._create_search_engine()
        self.cache_manager = cache_manager or self._create_cache_manager()
```

## 📊 Architecture Metrics

### Code Quality Metrics
- **Cyclomatic Complexity**: <10 per method
- **Lines of Code**: <200 per class
- **Coupling**: Low coupling between components
- **Cohesion**: High cohesion within components

### Performance Metrics
- **Memory Usage**: Reduced memory footprint
- **Initialization Time**: Faster component initialization
- **Test Execution**: Faster test execution with isolated components

### Maintainability Metrics
- **Test Coverage**: >90% for new components
- **Documentation**: 100% documented public APIs
- **Type Coverage**: 100% type annotations

## 🚀 Rollout Plan

### Week 1: Core Components
- [ ] Create ProjectScanner class
- [ ] Create TagExtractor class
- [ ] Create SearchEngine class
- [ ] Create CacheManager class
- [ ] Write unit tests for each component

### Week 2: Main Orchestrator
- [ ] Refactor DockerRepoMap class
- [ ] Implement dependency injection
- [ ] Update integration tests
- [ ] Maintain backward compatibility

### Week 3: Polish & Validation
- [ ] Add exception hierarchy
- [ ] Create type protocols
- [ ] Update documentation
- [ ] Performance testing
- [ ] End-to-end validation

## 📝 Checklist

### Phase 1 Completion Criteria
- [ ] All core components implemented
- [ ] Unit tests passing for each component
- [ ] Clear separation of concerns achieved
- [ ] Dependency injection working

### Phase 2 Completion Criteria
- [ ] DockerRepoMap refactored to <100 lines
- [ ] Backward compatibility maintained
- [ ] Integration tests updated and passing
- [ ] Performance benchmarks established

### Phase 3 Completion Criteria
- [ ] Exception hierarchy implemented
- [ ] Type protocols defined
- [ ] Documentation updated
- [ ] Architecture validation complete

## 🔗 Related Documents

- [Critical Issues](./critical-issues.md)
- [Performance Improvements](./performance-improvements.md)
- [Quality & Testing](./quality-testing.md)

---

**Next Review**: After Phase 3 completion  
**Success Criteria**: Modular architecture, improved maintainability, backward compatibility maintained
