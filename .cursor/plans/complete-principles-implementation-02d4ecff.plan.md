<!-- 02d4ecff-79be-46c6-b504-6eabf2b7c0d2 93a7c497-f1dc-4eec-aef3-60106c46acda -->
# Debug Search Issues and Integrate Embeddings

## Phase 0: Debug Basic Search Functionality

### Step 0.1: Verify Tree-Sitter Tag Extraction

**File**: `src/repomap_tool/core/repo_map.py`

In `_get_cached_tags` method (around line 441), add logging:

```python
def _get_cached_tags(self) -> List[Dict[str, Any]]:
    """Get all tags from the aider cache."""
    if not self.repo_map or not hasattr(self.repo_map, "TAGS_CACHE"):
        self.logger.debug("No aider cache available")
        return []
    
    tags_cache = self.repo_map.TAGS_CACHE
    self.logger.debug(f"TAGS_CACHE type: {type(tags_cache)}, size: {len(tags_cache) if tags_cache else 0}")
    
    if not tags_cache:
        self.logger.debug("TAGS_CACHE is empty")
        return []
    
    # Flatten all tags from all files
    all_tags = []
    for file_path, file_tags in tags_cache.items():
        self.logger.debug(f"File {file_path}: {len(file_tags) if file_tags else 0} tags")
        if file_tags:
            all_tags.extend(file_tags)
    
    self.logger.debug(f"Total tags extracted: {len(all_tags)}")
    return all_tags
```

### Step 0.2: Test Identifier Extraction

Run test to see what identifiers are actually being extracted:

```bash
source venv/bin/activate
python -c "
from repomap_tool.core.repo_map import RepoMapService
from repomap_tool.models import RepoMapConfig
from pathlib import Path

config = RepoMapConfig(project_root=Path('.'))
service = RepoMapService(config=config, console=None)
tags = service._get_cached_tags()
print(f'Total tags: {len(tags)}')
print(f'Sample tags: {tags[:5]}')
identifiers = [tag['name'] for tag in tags if 'name' in tag]
print(f'Total identifiers: {len(identifiers)}')
print(f'Sample identifiers: {identifiers[:20]}')
print(f'Contains fuzzy: {any(\"fuzzy\" in id.lower() for id in identifiers)}')
"
```

Expected: Should show if identifiers like "FuzzyMatcher" are being extracted.

### Step 0.3: Test Fuzzy Matcher in Isolation

**File**: `tests/unit/test_fuzzy_matcher_debug.py` (new file)

```python
import pytest
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher

def test_fuzzy_matcher_basic():
    """Test fuzzy matcher with simple identifiers."""
    matcher = FuzzyMatcher(threshold=30)
    
    identifiers = {
        "FuzzyMatcher", "fuzzy_search", "test_fuzzy", 
        "HybridMatcher", "SemanticMatcher", "test_function"
    }
    
    # Test 1: Exact match
    results = matcher.match_identifiers("test", identifiers)
    print(f"Query 'test': {len(results)} results")
    for id, score in results[:5]:
        print(f"  {id}: {score}%")
    
    # Test 2: Fuzzy match
    results = matcher.match_identifiers("fuzzy", identifiers)
    print(f"Query 'fuzzy': {len(results)} results")
    for id, score in results[:5]:
        print(f"  {id}: {score}%")
    
    assert len(results) > 0, "Should find fuzzy-related identifiers"
```

Run: `pytest tests/unit/test_fuzzy_matcher_debug.py -v -s`

### Step 0.4: Check Index vs Search Data Mismatch

Add logging to verify index and search use same data:

**File**: `src/repomap_tool/cli/commands/index.py`

After line 161 (after `project_info = repomap.analyze_project()`), add:

```python
# Debug: Log what was indexed
console.print(f"[cyan]Indexed {project_info.total_identifiers} identifiers from {project_info.total_files} files[/cyan]")

# Debug: Show sample identifiers
if hasattr(repomap, '_get_cached_tags'):
    tags = repomap._get_cached_tags()
    identifiers = [tag['name'] for tag in tags if 'name' in tag]
    console.print(f"[cyan]Sample identifiers: {identifiers[:10]}[/cyan]")
```

### Step 0.5: Fix Cache Invalidation Issue

The issue might be that search is not using the indexed data. Verify cache is being used:

**File**: `src/repomap_tool/core/repo_map.py`

In `search_identifiers` method, before line 345 (before `tags = self._get_cached_tags()`), add:

```python
# Force cache refresh if empty
if not self.repo_map or not hasattr(self.repo_map, 'TAGS_CACHE') or not self.repo_map.TAGS_CACHE:
    self.logger.debug("TAGS_CACHE is empty or missing, forcing refresh")
    project_files = get_project_files(str(self.config.project_root), self.config.verbose)
    if self.repo_map:
        self.repo_map.get_ranked_tags_map(project_files)
```

## Phase 1: Diagnose Search Inconsistency Issues

### Step 1: Add Debug Logging to Search Flow

**File**: `src/repomap_tool/core/repo_map.py`

In `search_identifiers` method (line 340), add comprehensive logging:

```python
def search_identifiers(self, request: SearchRequest) -> SearchResponse:
    start_time = time.time()
    
    # ADD: Debug logging (only shows with --verbose)
    self.logger.debug(f"Search request: query='{request.query}', match_type={request.match_type}, threshold={request.threshold}")
    
    # ALWAYS use tree-sitter - no fallbacks
    tags = self._get_cached_tags()
    
    # ADD: Log tag count
    self.logger.debug(f"Found {len(tags) if tags else 0} cached tags")
    
    if not tags:
        # ... existing code ...
    
    # Extract identifiers for search
    identifiers = [tag["name"] for tag in tags]
    
    # ADD: Log identifier count
    self.logger.debug(f"Extracted {len(identifiers)} identifiers from tags")
    self.logger.debug(f"Sample identifiers: {identifiers[:10]}")
```

### Step 2: Add Logging to Hybrid Matcher

**File**: `src/repomap_tool/code_search/hybrid_matcher.py`

In `match_identifiers` method (line 405), add logging:

```python
def match_identifiers(self, query: str, all_identifiers: Set[str]) -> List[Tuple[str, int]]:
    # ADD: Debug logging (only shows with --verbose)
    logger.debug(f"HybridMatcher.match_identifiers: query='{query}', identifiers={len(all_identifiers)}")
    logger.debug(f"Embedding matcher: {self.embedding_matcher is not None}, enabled={getattr(self.embedding_matcher, 'enabled', False) if self.embedding_matcher else False}")
    
    threshold = get_config("HYBRID_THRESHOLD", 0.1)
    logger.debug(f"Using threshold: {threshold}")
    
    # Get hybrid matches
    hybrid_matches = self.find_hybrid_matches(query, all_identifiers, threshold)
    
    # ADD: Log match count
    logger.debug(f"Found {len(hybrid_matches)} hybrid matches")
    
    # Convert to expected format
    matches = []
    for identifier, overall_score, component_scores in hybrid_matches:
        score = int(overall_score * 100)
        matches.append((identifier, score))
        # ADD: Log first few matches
        if len(matches) <= 5:
            logger.debug(f"Match: {identifier} = {score}% (components: {component_scores})")
    
    return matches
```

### Step 3: Test Search with Debug Logging

Run locally with verbose mode:

```bash
source venv/bin/activate
python -m repomap_tool explore find "test" --verbose
```

Expected output: Should show debug logs revealing where search fails.

## Phase 2: Fix Embedding Matcher Integration

### Step 4: Verify EmbeddingMatcher Initialization

**File**: `src/repomap_tool/code_search/embedding_matcher.py`

Add initialization logging (line 30):

```python
def __init__(self, model_name: str = "nomic-ai/CodeRankEmbed", cache_manager: Optional[any] = None, cache_dir: Optional[str] = None):
    self.model_name = model_name
    self.cache_manager = cache_manager
    self.cache_dir = cache_dir or ".repomap/cache/embeddings"
    self.enabled = False
    self.model = None
    self.embedding_cache: Dict[str, np.ndarray] = {}
    
    try:
        logger.info(f"Initializing EmbeddingMatcher with model: {model_name}")
        logger.debug(f"Cache directory: {self.cache_dir}")
        self.model = SentenceTransformer(model_name, trust_remote_code=True)
        self.enabled = True
        logger.info(f"✓ EmbeddingMatcher initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize EmbeddingMatcher: {e}")
        logger.warning("Embedding-based search will be disabled")
    
    Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
```

### Step 5: Fix DI Container Cache Manager Issue

**File**: `src/repomap_tool/core/container.py`

The plan says `cache_manager=None` but we need it for file tracking. Update line 201:

```python
embedding_matcher: "providers.Singleton[Any]" = cast(
    "providers.Singleton[Any]",
    providers.Singleton(
        "repomap_tool.code_search.embedding_matcher.EmbeddingMatcher",
        model_name=config.embedding.model_name,
        cache_manager=cache_manager,  # FIXED: Use actual cache_manager
        cache_dir=config.embedding.cache_dir,
    ),
)
```

### Step 6: Verify Hybrid Matcher Receives Embedding Matcher

**File**: `src/repomap_tool/code_search/hybrid_matcher.py`

Add logging in `__init__` (line 52):

```python
self.fuzzy_matcher = fuzzy_matcher
self.embedding_matcher = embedding_matcher

# ADD: Debug logging
if self.embedding_matcher:
    logger.debug(f"HybridMatcher received embedding_matcher: {type(self.embedding_matcher).__name__}")
    logger.debug(f"Embedding matcher enabled: {getattr(self.embedding_matcher, 'enabled', False)}")
else:
    logger.debug("HybridMatcher did NOT receive embedding_matcher")
```

## Phase 3: Fix Threshold Issues

### Step 7: Investigate Threshold Filtering

**File**: `src/repomap_tool/code_search/hybrid_matcher.py`

In `find_hybrid_matches` method (around line 360), add logging:

```python
def find_hybrid_matches(self, query: str, all_identifiers: Set[str], threshold: float = 0.3) -> List[Tuple[str, float, Dict[str, float]]]:
    # ADD: Debug logging (only shows with --verbose)
    logger.debug(f"find_hybrid_matches: query='{query}', identifiers={len(all_identifiers)}, threshold={threshold}")
    
    # Build TF-IDF model
    self.build_tfidf_model(all_identifiers)
    
    matches = []
    for identifier in all_identifiers:
        overall_score, component_scores = self.hybrid_similarity(query, identifier)
        
        # ADD: Log first few scores
        if len(matches) < 5:
            logger.debug(f"Similarity for '{identifier}': overall={overall_score:.3f}, components={component_scores}")
        
        if overall_score >= threshold:
            matches.append((identifier, overall_score, component_scores))
    
    # ADD: Log filtering results
    logger.debug(f"Before filtering: {len(all_identifiers)} identifiers")
    logger.debug(f"After threshold {threshold}: {len(matches)} matches")
    
    # Sort by overall score
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches
```

### Step 8: Lower Default Threshold

**File**: `src/repomap_tool/models.py`

Update `SearchRequest` threshold default (around line 380):

```python
threshold: float = Field(
    default=0.3,  # CHANGED from 0.7 to 0.3
    ge=0.0,
    le=1.0,
    description="Minimum similarity threshold (0.0-1.0)"
)
```

## Phase 4: Test and Verify Locally

### Step 9: Install Dependencies Locally

```bash
source venv/bin/activate
pip install sentence-transformers scikit-learn torch
```

### Step 10: Run Local Tests

Test 1: Basic fuzzy search

```bash
python -m repomap_tool explore find "test" --match-type fuzzy --threshold 0.3 --verbose
```

Test 2: Hybrid search with embeddings

```bash
python -m repomap_tool index create .
python -m repomap_tool explore find "search algorithms" --match-type hybrid --threshold 0.3 --verbose
```

Test 3: Verify embedding cache

```bash
ls -la .repomap/cache/embeddings/
```

Expected: Should see `.npy` files for cached embeddings.

### Step 11: Add Unit Tests

**File**: `tests/unit/test_embedding_matcher.py` (new file)

```python
import pytest
from repomap_tool.code_search.embedding_matcher import EmbeddingMatcher

def test_embedding_matcher_initialization():
    matcher = EmbeddingMatcher()
    assert matcher is not None
    # Should gracefully handle missing model
    assert matcher.enabled in [True, False]

def test_embedding_computation():
    matcher = EmbeddingMatcher()
    if matcher.enabled:
        embedding = matcher.get_embedding("test_function")
        assert embedding is not None
        assert embedding.shape[0] > 0

def test_batch_computation():
    matcher = EmbeddingMatcher()
    if matcher.enabled:
        identifiers = {"func1": "/test.py", "func2": "/test.py"}
        matcher.batch_compute_embeddings(identifiers)
        # Verify cache
        assert len(matcher.embedding_cache) > 0
```

## Phase 5: Rebuild Docker with Embeddings

### Step 12: Verify Dockerfile Changes

**File**: `docker/Dockerfile`

Ensure lines 26-32 exist:

```dockerfile
# Install embedding dependencies
RUN pip install sentence-transformers scikit-learn torch

# Download and cache CodeRankEmbed model (happens at build time)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/CodeRankEmbed', trust_remote_code=True)"

# Set environment variable
ENV REPOMAP_EMBEDDING_MODEL=nomic-ai/CodeRankEmbed
```

### Step 13: Rebuild Docker Image

```bash
docker build -f docker/Dockerfile -t repomap-tool:local .
```

Expected: Should download CodeRankEmbed model (~550MB) during build.

### Step 14: Test Docker with Embeddings

```bash
docker run --rm -t -v $(pwd):/workspace repomap-tool:local index create
docker run --rm -t -v $(pwd):/workspace repomap-tool:local explore find "search algorithms" --threshold 0.3 --verbose
```

Expected: Should show embedding matcher initialization logs and use cached embeddings.

## Phase 6: Verify Complete Integration

### Step 15: End-to-End Integration Test

Create test script `test_embedding_integration.sh`:

```bash
#!/bin/bash
set -e

echo "1. Testing index creation with embeddings..."
docker run --rm -t -v $(pwd):/workspace repomap-tool:local index create | tee index.log

echo "2. Verifying embedding cache..."
if [ -d ".repomap/cache/embeddings" ]; then
    echo "✓ Embedding cache directory exists"
    echo "  Files: $(ls .repomap/cache/embeddings | wc -l)"
else
    echo "✗ Embedding cache directory NOT found"
    exit 1
fi

echo "3. Testing search with embeddings..."
docker run --rm -t -v $(pwd):/workspace repomap-tool:local explore find "fuzzy matcher" --threshold 0.3 --verbose | tee search.log

echo "4. Checking for embedding logs..."
if grep -q "EmbeddingMatcher" search.log; then
    echo "✓ Embedding matcher is being used"
else
    echo "✗ Embedding matcher NOT being used"
    exit 1
fi

echo "✓ All integration tests passed!"
```

### Step 16: Performance Verification

Test embedding cache performance:

```bash
# First search (cold cache)
time docker run --rm -t -v $(pwd):/workspace repomap-tool:local explore find "authentication" --threshold 0.3

# Second search (warm cache)
time docker run --rm -t -v $(pwd):/workspace repomap-tool:local explore find "authentication" --threshold 0.3
```

Expected: Second search should be significantly faster (using cached embeddings).

## Success Criteria

1. Search consistently finds results (no more 0 results for common terms)
2. EmbeddingMatcher initializes successfully (logs show initialization)
3. Hybrid matcher receives and uses embedding_matcher
4. Threshold filtering is reasonable (30% default, not 70%)
5. Embeddings are cached during indexing
6. Search uses cached embeddings (fast execution)
7. Docker image includes CodeRankEmbed model
8. All tests pass locally and in Docker

## Rollback Plan

If embeddings cause issues:

1. Set `embedding.enabled = False` in config
2. Hybrid matcher gracefully falls back to fuzzy + TF-IDF
3. Search continues to work without embeddings

### To-dos

- [ ] Create EmbeddingMatcher class with CodeRankEmbed integration
- [ ] Add embedding similarity to hybrid matching strategy
- [ ] Add EmbeddingConfig to models with CodeRankEmbed defaults
- [ ] Add embedding_matcher to DI container and inject into hybrid_matcher
- [ ] Update search engine to handle embedding scores
- [ ] Add CodeRankEmbed model download to Dockerfile
- [ ] Add sentence-transformers and dependencies to pyproject.toml
- [ ] Test embedding search with multi-word phrases and verify Docker build