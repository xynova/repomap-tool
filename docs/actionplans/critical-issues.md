# Critical Issues Action Plan

**Priority**: High  
**Timeline**: Weeks 1-2  
**Status**: 🔴 Not Started

## 🚨 Overview

This plan addresses the most critical issues identified in the code review that affect the tool's reliability, maintainability, and production readiness.

## 📋 Issues Summary

### 1. Code Complexity & Maintainability
- **Issue**: `core.py` is too large (783 lines) with mixed responsibilities
- **Impact**: High - affects maintainability and debugging
- **Priority**: Critical

### 2. Error Handling & Resilience
- **Issue**: Inconsistent and overly broad exception handling
- **Impact**: High - silent failures and poor error reporting
- **Priority**: Critical

### 3. Memory Management
- **Issue**: Unbounded caching without size limits or eviction policies
- **Impact**: Medium - potential memory leaks in long-running operations
- **Priority**: High

### 4. Type Safety
- **Issue**: Unsafe type casting and `Any` types in critical paths
- **Impact**: Medium - potential runtime errors and poor IDE support
- **Priority**: High

## 🎯 Success Criteria

- [ ] `core.py` broken down into focused classes (<200 lines each)
- [ ] Specific exception types defined and used consistently
- [ ] Memory usage monitored and bounded
- [ ] Type safety improved with proper type annotations
- [ ] Error recovery mechanisms implemented

## 📝 Detailed Action Items

### Phase 1: Code Refactoring (Week 1)

#### 1.1 Break Down DockerRepoMap Class

**Current State:**
```python
class DockerRepoMap:
    # 783 lines of mixed responsibilities
    # File scanning, tag extraction, matching, caching, etc.
```

**Target State:**
```python
class ProjectScanner:
    """Handles file discovery and filtering"""
    
class TagExtractor:
    """Handles identifier extraction from files"""
    
class SearchEngine:
    """Coordinates different matchers"""
    
class CacheManager:
    """Handles caching logic with size limits"""
    
class DockerRepoMap:
    """Main orchestrator class (now <100 lines)"""
```

**Tasks:**
- [ ] Create `ProjectScanner` class
- [ ] Create `TagExtractor` class  
- [ ] Create `SearchEngine` class
- [ ] Create `CacheManager` class
- [ ] Refactor `DockerRepoMap` to use new classes
- [ ] Update tests to reflect new structure

#### 1.2 Improve Error Handling

**Current State:**
```python
try:
    tags = self.repo_map.get_tags(file_path, rel_fname)
    if tags:
        all_tags.extend(tags)
except Exception as e:  # Too broad!
    self.logger.warning(f"Failed to get tags for {rel_fname}: {e}")
```

**Target State:**
```python
class RepoMapError(Exception): pass
class TagExtractionError(RepoMapError): pass
class FileAccessError(RepoMapError): pass

try:
    tags = self.repo_map.get_tags(file_path, rel_fname)
    if tags:
        all_tags.extend(tags)
except (FileNotFoundError, PermissionError) as e:
    self.logger.warning(f"File access error for {rel_fname}: {e}")
    # Continue processing other files
except Exception as e:
    self.logger.error(f"Unexpected error extracting tags from {rel_fname}: {e}")
    raise TagExtractionError(f"Failed to extract tags: {e}")
```

**Tasks:**
- [ ] Define custom exception hierarchy
- [ ] Implement specific error handling for different failure modes
- [ ] Add error recovery mechanisms
- [ ] Update logging to include context and severity
- [ ] Add error metrics collection

#### 1.3 Fix Memory Management

**Current State:**
```python
self.match_cache: Dict[str, List[Tuple[str, int]]] = {}
# No cache size limits or eviction policy
```

**Target State:**
```python
class CacheManager:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache = {}
        self._access_times = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl:
                self._access_times[key] = time.time()
                return value
            else:
                self._evict(key)
        return None
    
    def _evict(self, key: str) -> None:
        """Remove expired or least recently used items"""
        if len(self._cache) >= self.max_size:
            # LRU eviction
            oldest_key = min(self._access_times.keys(), 
                           key=lambda k: self._access_times[k])
            del self._cache[oldest_key]
            del self._access_times[oldest_key]
```

**Tasks:**
- [ ] Implement `CacheManager` with LRU eviction
- [ ] Add memory usage monitoring
- [ ] Set appropriate cache size limits
- [ ] Add cache hit/miss metrics
- [ ] Implement cache warming strategies

### Phase 2: Type Safety Improvements (Week 2)

#### 2.1 Improve Type Annotations

**Current State:**
```python
self.repo_map: Optional[Any] = None  # Too generic
def _extract_identifiers(self, project_map: Any) -> Set[str]:  # Unclear contract
```

**Target State:**
```python
from typing import Protocol, Union

class RepoMapProtocol(Protocol):
    def get_tags(self, file_path: str, rel_fname: str) -> List[Tag]: ...
    def get_ranked_tags_map(self, files: List[str], max_tokens: int) -> Optional[str]: ...

class ProjectMap(TypedDict):
    tags: Optional[List[Tag]]
    identifiers: Optional[List[str]]

self.repo_map: Optional[RepoMapProtocol] = None

def _extract_identifiers(self, project_map: ProjectMap) -> Set[str]:
    """Extract identifiers from project map structure."""
```

**Tasks:**
- [ ] Define `RepoMapProtocol` for type safety
- [ ] Create `ProjectMap` TypedDict for structured data
- [ ] Replace `Any` types with specific types
- [ ] Add type validation for configuration
- [ ] Update mypy configuration for stricter checking

#### 2.2 Add Runtime Type Validation

**Current State:**
```python
# No runtime validation of data structures
project_map = {"tags": all_tags} if all_tags else {}
```

**Target State:**
```python
from pydantic import ValidationError

def _validate_project_map(self, data: Dict[str, Any]) -> ProjectMap:
    """Validate and convert project map data."""
    try:
        return ProjectMap(**data)
    except ValidationError as e:
        self.logger.error(f"Invalid project map structure: {e}")
        return ProjectMap(tags=None, identifiers=None)
```

**Tasks:**
- [ ] Add runtime validation for data structures
- [ ] Implement graceful degradation for invalid data
- [ ] Add validation error reporting
- [ ] Create data sanitization utilities

## 🔧 Implementation Guidelines

### Code Organization
```
src/repomap_tool/
├── core/
│   ├── __init__.py
│   ├── project_scanner.py
│   ├── tag_extractor.py
│   ├── search_engine.py
│   └── cache_manager.py
├── exceptions.py
├── protocols.py
└── docker_repomap.py  # Main orchestrator
```

### Testing Strategy
- Unit tests for each new class
- Integration tests for the refactored flow
- Error scenario testing
- Performance regression testing

### Migration Strategy
1. Create new classes alongside existing code
2. Gradually migrate functionality
3. Update tests incrementally
4. Remove old code after validation

## 📊 Metrics & Monitoring

### Code Quality Metrics
- [ ] Cyclomatic complexity < 10 per method
- [ ] Lines of code < 200 per class
- [ ] Test coverage > 80% for new code
- [ ] Type coverage > 95%

### Performance Metrics
- [ ] Memory usage < 100MB for typical projects
- [ ] Cache hit rate > 70%
- [ ] Error rate < 1% of operations
- [ ] Recovery time < 5 seconds

### Error Metrics
- [ ] Track error types and frequencies
- [ ] Monitor error recovery success rates
- [ ] Alert on error rate spikes
- [ ] Log error context for debugging

## 🚀 Rollout Plan

### Week 1: Foundation
- [ ] Create new class structure
- [ ] Implement basic error handling
- [ ] Add memory management
- [ ] Write initial tests

### Week 2: Integration
- [ ] Migrate existing functionality
- [ ] Update CLI integration
- [ ] Add comprehensive error handling
- [ ] Performance testing and optimization

### Week 3: Validation
- [ ] End-to-end testing
- [ ] Performance benchmarking
- [ ] Error scenario testing
- [ ] Documentation updates

## 📝 Checklist

### Phase 1 Completion Criteria
- [ ] `core.py` refactored into focused classes
- [ ] Custom exception hierarchy implemented
- [ ] Cache management with size limits
- [ ] All tests passing
- [ ] Performance benchmarks established

### Phase 2 Completion Criteria
- [ ] Type safety improvements implemented
- [ ] Runtime validation added
- [ ] Mypy passes with strict settings
- [ ] Documentation updated
- [ ] Migration completed

## 🔗 Related Documents

- [Performance Improvements](./performance-improvements.md)
- [Architecture Refactoring](./architecture-refactoring.md)
- [Quality & Testing](./quality-testing.md)

---

**Next Review**: After Phase 1 completion  
**Success Criteria**: All critical issues resolved, code maintainability improved
