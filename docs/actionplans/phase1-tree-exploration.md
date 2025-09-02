# Phase 1: Tree-Based Exploration Implementation

## Overview
**Goal:** Implement the core tree-based code exploration workflow that IS the main functionality of the repomap tool.

**Duration:** 2-3 weeks  
**Effort:** Medium  
**Impact:** Critical  
**Priority:** Essential (The Core Tool)

## Current State vs Target State

### Current State
- Static analysis with generic file listings
- No structured exploration workflow
- No entrypoint discovery or tree building
- No session-based exploration state
- One-size-fits-all repomap output

### Target State
- **Smart Entrypoint Discovery:** Find relevant code entry points based on intent
- **Tree-Based Exploration:** Build contextual trees from entrypoints
- **Tree Manipulation:** Expand, prune, and refine trees dynamically
- **Session Management:** External session control via CLI/env vars
- **Stateful Focus:** Maintain exploration state within sessions
- **Tree Mapping:** Generate focused repomaps from current tree state

## Technical Architecture

### New Components to Add

```
src/repomap_tool/trees/
├── __init__.py
├── discovery_engine.py      # Smart entrypoint discovery using existing semantic/fuzzy
├── tree_builder.py          # Build exploration trees from entrypoints
├── tree_manager.py          # Tree manipulation (expand, prune, focus)
├── tree_mapper.py           # Generate repomaps from tree state
├── session_manager.py       # External session state management
└── tree_clusters.py         # Cluster entrypoints into logical trees
```

### Core Classes to Implement

```python
class EntrypointDiscoverer:
    """Discovers relevant entrypoints using existing semantic/fuzzy matching"""
    
class ExplorationTree:
    """Represents a tree of related code starting from entrypoints"""
    
class TreeBuilder:
    """Builds exploration trees from discovered entrypoints"""
    
class TreeManager:
    """Manages tree state, expansion, pruning, and focus"""
    
class TreeMapper:
    """Generates repomaps from current tree exploration state"""
    
class SessionManager:
    """Manages external session state (CLI/ENV controlled)"""
    
class TreeClusterer:
    """Groups entrypoints into logical clusters with meaningful titles"""
```

### Smart Title Generation Strategy

The tool generates meaningful titles like "Auth Error Handling" by leveraging **existing semantic analysis**:

```python
# How "Auth Error Handling" is generated:

# Step 1: Extract semantic categories using existing get_semantic_categories()
entrypoints = ["AuthErrorHandler", "LoginValidator", "InvalidCredentialsError"]

for entrypoint in entrypoints:
    categories = semantic_matcher.get_semantic_categories(entrypoint)
    # AuthErrorHandler → ["authentication", "error_handling", "api_development"]
    # LoginValidator → ["authentication", "validation"] 
    # InvalidCredentialsError → ["authentication", "error_handling"]

# Step 2: Count category frequencies
category_counts = Counter([
    "authentication", "error_handling", "api_development",  # from AuthErrorHandler
    "authentication", "validation",                         # from LoginValidator
    "authentication", "error_handling"                      # from InvalidCredentialsError
])
# Result: {"authentication": 3, "error_handling": 2, "validation": 1, "api_development": 1}

# Step 3: Apply title formatting rules
top_2_categories = ["authentication", "error_handling"]
title_rules[("authentication", "error_handling")] = "Auth Error Handling"
# Result: "Auth Error Handling" ✅
```

**Key Insight:** No complex AI needed - just smart combination of existing semantic categorization with good naming rules!

## Technical Architecture Overview

### System Flow Diagram
```
User Intent ("authentication bugs") 
    ↓
EntrypointDiscoverer (uses existing semantic/fuzzy matching)
    ↓ 
[entrypoint1, entrypoint2, entrypoint3] with scores
    ↓
TreeClusterer (groups by semantic categories)
    ↓
[cluster1: "Auth Error Handling", cluster2: "Auth API Flow"]
    ↓
TreeBuilder (builds hierarchy using aider RepoMap)
    ↓
ExplorationTree objects with tree structure
    ↓
SessionManager (persists to external session)
    ↓
TreeManager (handles focus, expand, prune operations)
    ↓
TreeMapper (generates focused repomap output)
```

### Data Flow Architecture

```python
# Input: User intent string
intent = "authentication login errors"

# Stage 1: Discovery (uses existing capabilities)
entrypoints = EntrypointDiscoverer(repo_map).discover_entrypoints(project_path, intent)
# Output: [Entrypoint(id="AuthErrorHandler", score=0.9), ...]

# Stage 2: Clustering (new semantic analysis)
clusters = TreeClusterer().cluster_entrypoints(entrypoints)  
# Output: [TreeCluster(name="Auth Error Handling", entrypoints=[...]), ...]

# Stage 3: Tree Building (uses aider infrastructure)
trees = []
for cluster in clusters:
    tree = TreeBuilder(repo_map).build_exploration_tree(cluster.entrypoints[0])
    trees.append(tree)
# Output: [ExplorationTree(tree_id="auth_errors_x1y2", structure=TreeNode(...)), ...]

# Stage 4: Session Management (new external state)
session = SessionManager().get_or_create_session(session_id, project_path)
for tree in trees:
    session.exploration_trees[tree.tree_id] = tree
SessionManager().persist_session(session)

# Stage 5: User Interaction (CLI commands)
TreeManager().focus_tree(session_id, "auth_errors_x1y2")  # stateful
TreeManager().expand_tree(session_id, "password_validation")  # dynamic
output = TreeMapper().generate_tree_map(tree, include_code=True)  # focused output
```

### Component Integration Map

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Existing Layer    │    │    New Tree Layer   │    │   Enhancement Layer │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ DockerRepoMap       │◄──►│ EntrypointDiscoverer│    │ TreeManager         │
│ SemanticMatcher     │◄──►│ TreeClusterer       │◄──►│ TreeMapper          │
│ FuzzyMatcher        │    │ TreeBuilder         │    │ SessionManager      │
│ aider.RepoMap       │◄──►│ ExplorationTree     │    │                     │
│ Symbol Extraction   │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### File Structure & Dependencies

```
src/repomap_tool/trees/
├── __init__.py                 # Package initialization
├── discovery_engine.py         # Uses: DockerRepoMap, SemanticMatcher, FuzzyMatcher
├── tree_builder.py            # Uses: aider.RepoMap, discovery_engine
├── tree_clusters.py           # Uses: SemanticMatcher, discovery_engine  
├── tree_manager.py            # Uses: SessionManager, TreeBuilder
├── tree_mapper.py             # Uses: DockerRepoMap, tree data structures
└── session_manager.py         # Uses: File system, pickle/json serialization

# Modified files:
src/repomap_tool/cli.py         # New commands: explore, focus, expand, prune, map
src/repomap_tool/models.py      # New models: TreeNode, ExplorationTree, etc.
```

### Critical Technical Decisions

1. **Session Storage**: Use file-based persistence (JSON/pickle) in temp directory
2. **Tree Building**: Leverage existing `aider.RepoMap.get_tags()` for dependencies
3. **Semantic Analysis**: Use existing `SemanticMatcher.get_semantic_categories()`
4. **State Management**: External session control via CLI params/env vars
5. **Tree Structure**: Hierarchical TreeNode objects with parent/child relationships

## Quality Standards & Anti-Patterns

### ✅ What Good Looks Like

#### **1. Smart Entrypoint Discovery**
```python
# GOOD: Uses existing semantic analysis properly
def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
    all_symbols = self.repo_map.get_tags()  # Use existing infrastructure
    relevant_entrypoints = []
    
    # Proper semantic scoring
    for symbol in all_symbols:
        similarity = self.semantic_matcher.calculate_similarity(intent, symbol)
        if similarity > self.threshold:  # Configurable threshold
            entrypoint = self._create_entrypoint(symbol, similarity)
            relevant_entrypoints.append(entrypoint)
    
    return self._deduplicate_entrypoints(relevant_entrypoints)  # Remove duplicates

# GOOD: Meaningful title generation
titles = ["Auth Error Handling", "Payment Gateway Integration", "Database Query Optimization"]
# Clear, human-readable, follows domain patterns
```

#### **2. Proper Tree Structure**
```python
# GOOD: Hierarchical tree with proper relationships
tree_structure = {
    "AuthErrorHandler": {
        "children": ["handle_login_error", "validate_credentials"],
        "depth": 0,
        "expanded": True
    },
    "handle_login_error": {
        "children": ["check_password", "log_failure"],
        "depth": 1,
        "expanded": False
    }
}
# Clear parent-child relationships, respects depth limits, tracks expansion state
```

#### **3. Robust Session Management**
```python
# GOOD: External session control with proper error handling
def get_or_create_session(self, session_id: str, project_path: str) -> ExplorationSession:
    try:
        session = self.session_store.load_session(session_id)
        if session and session.project_path == project_path:
            return session
    except (FileNotFoundError, CorruptedSessionError):
        logger.warning(f"Session {session_id} not found or corrupted, creating new")
    
    return ExplorationSession(session_id, project_path)
# Handles missing sessions, validates project paths, graceful error recovery
```

#### **4. Performance-Conscious Implementation**
```python
# GOOD: Efficient caching and lazy loading
class TreeBuilder:
    def __init__(self):
        self.entrypoint_cache = {}  # Cache discovered entrypoints
        self.tree_cache = {}        # Cache built trees
    
    def build_exploration_tree(self, entrypoint: Entrypoint, max_depth: int = 3):
        cache_key = f"{entrypoint.identifier}_{max_depth}"
        if cache_key in self.tree_cache:
            return self.tree_cache[cache_key]
        
        # Build tree with depth limits
        tree = self._build_tree_recursive(entrypoint, 0, max_depth)
        self.tree_cache[cache_key] = tree
        return tree
# Respects performance constraints, uses caching, limits depth
```

### ❌ What NOT Good Looks Like (Anti-Patterns)

#### **1. Lazy Entrypoint Discovery (AVOID)**
```python
# BAD: Hardcoded patterns instead of using semantic analysis
def discover_entrypoints_WRONG(self, intent: str):
    if "auth" in intent:
        return ["AuthController", "LoginService"]  # Hardcoded!
    elif "database" in intent:
        return ["DatabaseManager", "QueryBuilder"]  # Brittle!
    else:
        return []  # Gives up too easily!

# BAD: Poor title generation
titles = ["stuff1", "things2", "code_components"]  # Meaningless
# WHY BAD: Doesn't leverage existing semantic capabilities, not scalable
```

#### **2. Broken Tree Structure (AVOID)**
```python
# BAD: Flat structure pretending to be a tree
fake_tree = {
    "nodes": ["AuthErrorHandler", "handle_login_error", "validate_credentials"],
    "relationships": "unclear"
}
# No hierarchy, no parent-child relationships, no depth tracking

# BAD: Infinite recursion risk
def build_tree_WRONG(self, node):
    for child in get_all_possible_children(node):  # No depth limit!
        child.children = build_tree_WRONG(child)   # Stack overflow risk!
# WHY BAD: No safeguards, can crash on complex codebases
```

#### **3. Brittle Session Management (AVOID)**
```python
# BAD: Internal state management
class BadSessionManager:
    def __init__(self):
        self.current_session = None  # Global state!
        self.sessions = {}           # Internal only!
    
    def switch_session(self, session_id):
        self.current_session = session_id  # No external control!

# BAD: No error handling
def load_session_WRONG(self, session_id):
    return pickle.load(open(f"/tmp/{session_id}.pkl"))  # Can crash!
# WHY BAD: Not externally controlled, fragile, no error recovery
```

#### **4. Performance Killers (AVOID)**
```python
# BAD: Rebuilds everything on every operation
def expand_tree_WRONG(self, expansion_area):
    # Rebuilds entire tree from scratch!
    tree = self.build_complete_tree_from_scratch()  # Expensive!
    return tree.filter_by_area(expansion_area)      # Wasteful!

# BAD: No caching or limits
def get_all_symbols_WRONG(self):
    symbols = []
    for file in os.walk(project_path):  # Scans entire filesystem!
        symbols.extend(parse_file(file)) # No caching!
    return symbols  # Runs every time!
# WHY BAD: Ignores performance requirements, doesn't scale
```

### 🚨 Shortcut Prevention Checklist

#### **Before Claiming "Done" - Verify:**

1. **Semantic Integration**
   - [ ] Uses `SemanticMatcher.get_semantic_categories()` - not hardcoded patterns
   - [ ] Leverages existing TF-IDF analysis - not simple string matching
   - [ ] Title generation uses actual domain categories - not made-up names

2. **Tree Structure Integrity**
   - [ ] Proper parent-child relationships in TreeNode objects
   - [ ] Respects max_depth limits to prevent infinite recursion
   - [ ] Tracks expansion/pruning state correctly
   - [ ] Can handle circular dependencies gracefully

3. **Session Management Robustness**
   - [ ] External session control via CLI params/env vars
   - [ ] Handles missing/corrupted sessions without crashing
   - [ ] Multiple independent sessions work simultaneously
   - [ ] Session state persists across CLI invocations

4. **Performance Standards**
   - [ ] Entrypoint discovery < 5 seconds for 1000+ files
   - [ ] Tree building < 10 seconds for complex trees
   - [ ] Session operations < 1 second
   - [ ] Memory usage scales linearly with tree size

5. **Error Handling**
   - [ ] Graceful degradation when semantic analysis fails
   - [ ] Helpful error messages with suggested actions
   - [ ] Fallback strategies for edge cases
   - [ ] No silent failures or crashes

### 🎯 Acceptance Tests (Must Pass)

```python
# Test 1: Semantic Integration
def test_uses_existing_semantic_analysis():
    discoverer = EntrypointDiscoverer(repo_map)
    entrypoints = discoverer.discover_entrypoints("/project", "authentication bugs")
    
    # MUST use semantic_matcher.get_semantic_categories()
    assert any("authentication" in ep.categories for ep in entrypoints)
    assert any("error_handling" in ep.categories for ep in entrypoints)

# Test 2: Title Generation Quality  
def test_meaningful_title_generation():
    clusterer = TreeClusterer()
    title = clusterer._generate_context_name(auth_entrypoints)
    
    # MUST be human-readable and meaningful
    assert title in ["Auth Error Handling", "Authentication Flow", "Auth Validation"]
    assert title != "code_components"  # Generic fallback not allowed

# Test 3: External Session Control
def test_external_session_control():
    os.environ['REPOMAP_SESSION'] = 'test_session'
    session_manager = SessionManager()
    
    # MUST respect external session ID
    session = session_manager.get_or_create_session(None, "/project")
    assert session.session_id == 'test_session'

# Test 4: Performance Requirements
def test_performance_requirements():
    start_time = time.time()
    entrypoints = discoverer.discover_entrypoints(large_project, "performance issues")
    discovery_time = time.time() - start_time
    
    # MUST meet performance targets
    assert discovery_time < 5.0  # 5 second limit
    assert len(entrypoints) > 0   # Must find something
```

### 🚫 Automatic Failure Conditions

**Implementation FAILS if:**
- Uses hardcoded patterns instead of semantic analysis
- Builds flat lists instead of hierarchical trees
- Internal-only session management (not externally controlled)
- No error handling or graceful degradation
- Doesn't meet performance requirements
- Generic titles like "Code Components" for everything
- Silent failures or crashes on edge cases

## Implementation Plan

### Week 1: Core Tree Infrastructure

#### Day 1-2: Session Management & Entrypoint Discovery
**Files to Create:**
- `src/repomap_tool/trees/__init__.py`
- `src/repomap_tool/trees/session_manager.py`
- `src/repomap_tool/trees/discovery_engine.py`

**External Session Management:**
```python
class SessionManager:
    def __init__(self):
        self.session_store = SessionStore()
        
    def get_session_id(self, cli_session: Optional[str] = None) -> str:
        """Get session ID from CLI parameter or environment"""
        session_id = cli_session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            session_id = f"session_{int(time.time())}"
        return session_id
        
    def get_or_create_session(self, session_id: str, project_path: str) -> ExplorationSession:
        """Get existing session or create new one"""
        session = self.session_store.load_session(session_id)
        if not session:
            session = ExplorationSession(session_id, project_path)
        return session

class ExplorationSession:
    def __init__(self, session_id: str, project_path: str):
        self.session_id = session_id
        self.project_path = project_path
        self.exploration_trees: Dict[str, ExplorationTree] = {}
        self.current_focus: Optional[str] = None
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
```

**Smart Entrypoint Discovery:**
```python
class EntrypointDiscoverer:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        self.semantic_matcher = repo_map.semantic_matcher
        self.fuzzy_matcher = repo_map.fuzzy_matcher
        
    def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
        """Find relevant entrypoints using existing semantic/fuzzy matching"""
        
        # Get all project symbols
        all_symbols = self.repo_map.get_tags()
        relevant_entrypoints = []
        
        # Use existing semantic matching to find relevant symbols
        if self.semantic_matcher:
            for symbol in all_symbols:
                similarity = self.semantic_matcher.calculate_similarity(intent, symbol)
                if similarity > 0.6:
                    entrypoint = self._create_entrypoint(symbol, similarity)
                    relevant_entrypoints.append(entrypoint)
        
        # Use existing fuzzy matching for additional matches
        if self.fuzzy_matcher:
            fuzzy_matches = self.fuzzy_matcher.find_similar(intent, all_symbols)
            for match in fuzzy_matches:
                if match.score > 0.7:
                    entrypoint = self._create_entrypoint(match.symbol, match.score)
                    relevant_entrypoints.append(entrypoint)
        
        return self._deduplicate_entrypoints(relevant_entrypoints)
    
    def _create_entrypoint(self, symbol: str, score: float) -> Entrypoint:
        """Create entrypoint from symbol with structural context"""
        return Entrypoint(
            identifier=symbol,
            location=self._get_symbol_location(symbol),
            score=score,
            structural_context=self._get_structural_context(symbol)
        )
```

#### Day 3-4: Tree Building & Clustering
**Files to Create:**
- `src/repomap_tool/trees/tree_builder.py`
- `src/repomap_tool/trees/tree_clusters.py`

**Tree Building from Entrypoints:**
```python
class TreeBuilder:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        
    def build_exploration_tree(self, entrypoint: Entrypoint, max_depth: int = 3) -> ExplorationTree:
        """Build exploration tree from entrypoint using existing aider infrastructure"""
        
        tree = ExplorationTree(
            tree_id=f"tree_{uuid4().hex[:8]}",
            root_entrypoint=entrypoint,
            max_depth=max_depth
        )
        
        # Use existing aider RepoMap to get dependencies and call graph
        if self.repo_map.repo_map:
            # Get tags and dependencies for this entrypoint
            abs_path = os.path.join(self.repo_map.config.project_root, entrypoint.location)
            tags = self.repo_map.repo_map.get_tags(abs_path, entrypoint.location)
            
            # Build tree structure from dependencies
            tree_structure = self._build_tree_structure(entrypoint, tags, max_depth)
            tree.tree_structure = tree_structure
            
        return tree
    
    def _build_tree_structure(self, entrypoint: Entrypoint, tags: List, depth: int) -> TreeNode:
        """Build hierarchical tree structure from entrypoint"""
        root = TreeNode(
            identifier=entrypoint.identifier,
            location=entrypoint.location,
            node_type="entrypoint",
            depth=0
        )
        
        # Recursively build tree using aider's dependency information
        self._expand_node(root, tags, depth)
        
        return root

class TreeClusterer:
    def __init__(self):
        self.context_patterns = self._load_context_patterns()
        
    def cluster_entrypoints(self, entrypoints: List[Entrypoint]) -> List[TreeCluster]:
        """Group entrypoints into logical clusters (frontend, backend, infrastructure)"""
        
        clusters = defaultdict(list)
        
        for entrypoint in entrypoints:
            context = self._classify_context(entrypoint)
            clusters[context].append(entrypoint)
        
        tree_clusters = []
        for context, entrypoints in clusters.items():
            cluster = TreeCluster(
                context_name=self._generate_context_name(context),
                entrypoints=entrypoints,
                confidence=self._calculate_cluster_confidence(entrypoints)
            )
            tree_clusters.append(cluster)
            
        return sorted(tree_clusters, key=lambda x: x.confidence, reverse=True)
    
    def _classify_context(self, entrypoint: Entrypoint) -> str:
        """Classify entrypoint into context using existing semantic analysis"""
        # Use existing semantic matcher to get categories
        categories = self.semantic_matcher.get_semantic_categories(entrypoint.identifier)
        
        if categories:
            return categories[0]  # Use primary category
        
        # Fallback to path-based classification
        return self._classify_from_path(entrypoint.location)
    
    def _generate_context_name(self, entrypoints: List[Entrypoint]) -> str:
        """Generate meaningful title from entrypoints using existing semantic analysis"""
        from collections import Counter
        
        # Step 1: Collect semantic categories from all entrypoints
        all_categories = []
        for entrypoint in entrypoints:
            # Use existing semantic matcher
            categories = self.semantic_matcher.get_semantic_categories(entrypoint.identifier)
            all_categories.extend(categories)
            
            # Add path-based context
            path_context = self._extract_path_context(entrypoint.location)
            if path_context:
                all_categories.append(path_context)
        
        # Step 2: Count category frequencies
        category_counts = Counter(all_categories)
        
        # Step 3: Generate title from dominant categories
        return self._format_title_from_categories(category_counts)
    
    def _format_title_from_categories(self, category_counts: Counter) -> str:
        """Format human-readable title from semantic categories"""
        if not category_counts:
            return "Code Components"
        
        # Get top 2 most frequent categories
        top_categories = category_counts.most_common(2)
        primary = top_categories[0][0]
        secondary = top_categories[1][0] if len(top_categories) > 1 else None
        
        # Title generation rules based on category combinations
        title_rules = {
            ("authentication", "error_handling"): "Auth Error Handling",
            ("authentication", "validation"): "Auth Validation", 
            ("authentication", "api_development"): "Auth API Flow",
            ("database", "api_development"): "Database API",
            ("database", "performance"): "Database Optimization",
            ("api_development", "error_handling"): "API Error Handling",
            ("security", "validation"): "Security Validation",
            ("network", "api_development"): "Network API",
            ("file_operations", "data_processing"): "File Processing",
            ("caching", "performance"): "Cache Optimization"
        }
        
        # Try specific combination first
        combination_key = (primary, secondary)
        if combination_key in title_rules:
            return title_rules[combination_key]
        
        # Fallback to single category formatting
        single_category_rules = {
            "authentication": "Authentication Flow",
            "error_handling": "Error Handling",
            "database": "Database Components", 
            "api_development": "API Endpoints",
            "security": "Security Components",
            "validation": "Validation Logic",
            "file_operations": "File Operations",
            "network": "Network Components",
            "caching": "Caching Layer",
            "performance": "Performance Components"
        }
        
        if primary in single_category_rules:
            return single_category_rules[primary]
        
        # Final fallback - make it readable
        return f"{primary.replace('_', ' ').title()} Components"
    
    def _extract_path_context(self, file_path: str) -> Optional[str]:
        """Extract semantic context from file path"""
        path_mappings = {
            "auth": "authentication",
            "error": "error_handling",
            "api": "api_development", 
            "db": "database",
            "database": "database",
            "cache": "caching",
            "security": "security",
            "validation": "validation"
        }
        
        path_lower = file_path.lower()
        for keyword, category in path_mappings.items():
            if keyword in path_lower:
                return category
        
        return None
```

#### Day 5: Core Tree Data Structures
**Files to Create:**
- `src/repomap_tool/models.py` (extend existing)

**Tree Data Models:**
```python
class TreeNode:
    def __init__(self, identifier: str, location: str, node_type: str, depth: int):
        self.identifier = identifier      # function/class name
        self.location = location          # file:line
        self.node_type = node_type        # entrypoint, function, class, import
        self.depth = depth                # depth in tree
        self.children: List[TreeNode] = []
        self.parent: Optional[TreeNode] = None
        self.expanded: bool = False       # whether this node has been expanded
        self.structural_info: Dict = {}   # dependencies, calls, etc.

class ExplorationTree:
    def __init__(self, tree_id: str, root_entrypoint: Entrypoint, max_depth: int = 3):
        self.tree_id = tree_id
        self.root_entrypoint = root_entrypoint
        self.max_depth = max_depth
        self.tree_structure: Optional[TreeNode] = None
        self.expanded_areas: Set[str] = set()
        self.pruned_areas: Set[str] = set()
        self.context_name: str = ""
        self.confidence: float = 0.0
        self.created_at = datetime.now()
        self.last_modified = datetime.now()

class TreeCluster:
    def __init__(self, context_name: str, entrypoints: List[Entrypoint], confidence: float):
        self.context_name = context_name  # "Frontend Auth Flow"
        self.entrypoints = entrypoints
        self.confidence = confidence
        self.tree_id = f"{context_name.lower().replace(' ', '_')}_{uuid4().hex[:8]}"

class Entrypoint:
    def __init__(self, identifier: str, location: str, score: float):
        self.identifier = identifier      # function/class name
        self.location = location          # file:line
        self.score = score               # relevance score from discovery
        self.structural_context: Dict = {} # dependencies, complexity, etc.
```

### Week 2: Tree Manipulation & Navigation

#### Day 6-7: Tree Manager
**Files to Create:**
- `src/repomap_tool/trees/tree_manager.py`

**Tree State Management:**
```python
class TreeManager:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        self.session_manager = SessionManager()
        self.tree_builder = TreeBuilder(repo_map)
        
    def focus_tree(self, session_id: str, tree_id: str):
        """Set focus to specific tree (stateful within session)"""
        session = self.session_manager.get_session(session_id)
        if session and tree_id in session.exploration_trees:
            session.current_focus = tree_id
            session.last_activity = datetime.now()
            self.session_manager.persist_session(session)
            
    def expand_tree(self, session_id: str, expansion_area: str, tree_id: Optional[str] = None):
        """Expand tree in specific area"""
        session = self.session_manager.get_session(session_id)
        target_tree_id = tree_id or session.current_focus
        
        if target_tree_id and target_tree_id in session.exploration_trees:
            tree = session.exploration_trees[target_tree_id]
            
            # Find expansion point in tree
            expansion_node = self._find_expansion_point(tree, expansion_area)
            if expansion_node:
                # Expand this node using existing aider infrastructure
                self._expand_tree_node(expansion_node, tree)
                tree.expanded_areas.add(expansion_area)
                tree.last_modified = datetime.now()
                
                self.session_manager.persist_session(session)
                
    def prune_tree(self, session_id: str, prune_area: str, tree_id: Optional[str] = None):
        """Remove branch from tree"""
        session = self.session_manager.get_session(session_id)
        target_tree_id = tree_id or session.current_focus
        
        if target_tree_id and target_tree_id in session.exploration_trees:
            tree = session.exploration_trees[target_tree_id]
            
            # Find and remove branch
            self._prune_tree_branch(tree, prune_area)
            tree.pruned_areas.add(prune_area)
            tree.last_modified = datetime.now()
            
            self.session_manager.persist_session(session)
    
    def get_tree_state(self, session_id: str, tree_id: Optional[str] = None) -> Optional[ExplorationTree]:
        """Get current tree state"""
        session = self.session_manager.get_session(session_id)
        target_tree_id = tree_id or session.current_focus
        
        if target_tree_id and target_tree_id in session.exploration_trees:
            return session.exploration_trees[target_tree_id]
        
        return None
    
    def _expand_tree_node(self, node: TreeNode, tree: ExplorationTree):
        """Expand specific tree node using aider infrastructure"""
        # Use existing repo_map to get dependencies and build sub-tree
        if self.repo_map.repo_map and node.depth < tree.max_depth:
            # Get more detailed information about this node
            abs_path = os.path.join(self.repo_map.config.project_root, node.location)
            tags = self.repo_map.repo_map.get_tags(abs_path, node.location)
            
            # Add children nodes based on dependencies/calls
            for tag in tags:
                if hasattr(tag, 'name') and tag.name != node.identifier:
                    child = TreeNode(
                        identifier=tag.name,
                        location=f"{node.location}",  # Same file for now
                        node_type="function" if hasattr(tag, 'kind') and tag.kind == 'function' else "symbol",
                        depth=node.depth + 1
                    )
                    child.parent = node
                    node.children.append(child)
                    
            node.expanded = True
```

#### Day 8-9: Tree Mapping
**Files to Create:**
- `src/repomap_tool/trees/tree_mapper.py`

**Generate Repomaps from Trees:**
```python
class TreeMapper:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        
    def generate_tree_map(self, tree: ExplorationTree, include_code: bool = True) -> str:
        """Generate repomap from current tree state"""
        
        if not tree.tree_structure:
            return "❌ Tree structure not available"
            
        output = f"🌳 Exploration Tree: {tree.context_name}\n"
        output += f"📍 Root: {tree.root_entrypoint.identifier}\n\n"
        
        # Generate hierarchical tree representation
        tree_repr = self._generate_tree_representation(tree.tree_structure, include_code)
        output += tree_repr
        
        # Show expansion/pruning history
        if tree.expanded_areas:
            output += f"\n✅ Expanded areas: {', '.join(tree.expanded_areas)}"
        if tree.pruned_areas:
            output += f"\n✂️ Pruned areas: {', '.join(tree.pruned_areas)}"
            
        # Show available expansion points
        expansion_points = self._find_expansion_opportunities(tree)
        if expansion_points:
            output += f"\n\n🔍 Available expansions:"
            for point in expansion_points:
                output += f"\n  • {point} - expand with: repomap-tool expand \"{point}\""
                
        return output
    
    def _generate_tree_representation(self, node: TreeNode, include_code: bool, prefix: str = "") -> str:
        """Generate hierarchical tree representation"""
        output = f"{prefix}├── {node.identifier}"
        
        if node.location:
            output += f" ({node.location})"
            
        if include_code and node.node_type in ["function", "class"]:
            # Get actual code snippet using existing infrastructure
            code_snippet = self._get_code_snippet(node)
            if code_snippet:
                output += f"\n{prefix}│   └── {code_snippet}"
        
        output += "\n"
        
        # Recursively add children
        for i, child in enumerate(node.children):
            child_prefix = prefix + ("│   " if i < len(node.children) - 1 else "    ")
            output += self._generate_tree_representation(child, include_code, child_prefix)
            
        return output
    
    def _get_code_snippet(self, node: TreeNode) -> Optional[str]:
        """Get relevant code snippet for tree node"""
        try:
            # Use existing repo_map infrastructure to get code details
            if self.repo_map.repo_map:
                abs_path = os.path.join(self.repo_map.config.project_root, node.location.split(':')[0])
                if os.path.exists(abs_path):
                    with open(abs_path, 'r') as f:
                        lines = f.readlines()
                        # Find the function/class definition
                        for i, line in enumerate(lines):
                            if node.identifier in line and ('def ' in line or 'class ' in line):
                                return line.strip()
        except Exception:
            pass
        return None
```

#### Day 10: CLI Integration
**Files to Modify:**
- `src/repomap_tool/cli.py`

**Core Tree Exploration CLI:**
```python
@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.argument("intent", type=str)
@click.option("--session", "-s", help="Session ID (or use REPOMAP_SESSION env var)")
@click.option("--max-depth", default=3, help="Maximum tree depth")
def explore(project_path: str, intent: str, session: Optional[str], max_depth: int):
    """Discover exploration trees from intent"""
    
    session_id = session or os.environ.get('REPOMAP_SESSION')
    if not session_id:
        session_id = f"explore_{int(time.time())}"
        console.print(f"💡 Using session: {session_id}")
        console.print(f"Set: export REPOMAP_SESSION={session_id}")
    
    config = create_default_config(project_path)
    repo_map = DockerRepoMap(config)
    
    # Discover entrypoints
    discoverer = EntrypointDiscoverer(repo_map)
    entrypoints = discoverer.discover_entrypoints(project_path, intent)
    
    # Cluster into trees
    clusterer = TreeClusterer()
    clusters = clusterer.cluster_entrypoints(entrypoints)
    
    # Build exploration trees
    tree_builder = TreeBuilder(repo_map)
    session_manager = SessionManager()
    session = session_manager.get_or_create_session(session_id, project_path)
    
    console.print(f"🔍 Found {len(clusters)} exploration contexts:")
    
    for cluster in clusters:
        # Build tree from cluster
        tree = tree_builder.build_exploration_tree(cluster.entrypoints[0], max_depth)
        tree.context_name = cluster.context_name
        tree.confidence = cluster.confidence
        
        # Store in session
        session.exploration_trees[tree.tree_id] = tree
        
        console.print(f"  • {tree.context_name} [id: {tree.tree_id}] (confidence: {tree.confidence:.2f})")
    
    session_manager.persist_session(session)
    
    console.print(f"\n💡 Next steps:")
    console.print(f"  repomap-tool focus <tree_id>    # Focus on specific tree")
    console.print(f"  repomap-tool map                # View current tree")

@cli.command()
@click.argument("tree_id", type=str)
@click.option("--session", "-s", help="Session ID")
def focus(tree_id: str, session: Optional[str]):
    """Focus on specific exploration tree (stateful)"""
    
    session_id = session or os.environ.get('REPOMAP_SESSION')
    if not session_id:
        console.print("❌ No session specified")
        return
    
    config = create_default_config(".")  # Project path from session
    repo_map = DockerRepoMap(config)
    tree_manager = TreeManager(repo_map)
    
    tree_manager.focus_tree(session_id, tree_id)
    console.print(f"✅ Focused on tree: {tree_id}")

@cli.command()
@click.argument("expansion_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def expand(expansion_area: str, session: Optional[str], tree: Optional[str]):
    """Expand tree in specific area"""
    
    session_id = session or os.environ.get('REPOMAP_SESSION')
    if not session_id:
        console.print("❌ No session specified")
        return
    
    config = create_default_config(".")
    repo_map = DockerRepoMap(config)
    tree_manager = TreeManager(repo_map)
    
    tree_manager.expand_tree(session_id, expansion_area, tree)
    console.print(f"✅ Expanded tree in area: {expansion_area}")

@cli.command()
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
@click.option("--include-code", is_flag=True, help="Include code snippets")
def map(session: Optional[str], tree: Optional[str], include_code: bool):
    """Generate repomap from current tree state"""
    
    session_id = session or os.environ.get('REPOMAP_SESSION')
    if not session_id:
        console.print("❌ No session specified")
        return
    
    config = create_default_config(".")
    repo_map = DockerRepoMap(config)
    tree_manager = TreeManager(repo_map)
    tree_mapper = TreeMapper(repo_map)
    
    current_tree = tree_manager.get_tree_state(session_id, tree)
    if not current_tree:
        console.print("❌ No tree found. Use 'repomap-tool focus <tree_id>' first")
        return
    
    tree_map = tree_mapper.generate_tree_map(current_tree, include_code)
    console.print(tree_map)
```

### Week 3: Testing, Optimization, and Documentation

#### Day 11-12: Comprehensive Testing
**Files to Create:**
- `tests/unit/test_entrypoint_discovery.py`
- `tests/unit/test_tree_builder.py`
- `tests/unit/test_tree_manager.py`
- `tests/unit/test_tree_mapper.py`
- `tests/integration/test_tree_exploration_workflow.py`

**Test Coverage:**
- **Entrypoint Discovery:** Semantic/fuzzy matching integration, relevance scoring
- **Tree Building:** Tree structure creation, depth limits, node relationships
- **Tree Management:** Focus, expand, prune operations, state persistence
- **Session Management:** External session control, multi-session isolation
- **Tree Mapping:** Repomap generation, code snippet extraction
- **CLI Integration:** All tree exploration commands, session parameter handling

#### Day 13-14: Performance Optimization
**Focus Areas:**
- Tree building performance for large codebases
- Session state persistence optimization
- Memory management for tree structures
- Caching of entrypoint discovery results

#### Day 15: Documentation and Examples
**Files to Create:**
- `docs/TREE_EXPLORATION_GUIDE.md`
- `examples/tree_exploration/basic_workflow.sh`
- `examples/tree_exploration/advanced_tree_operations.sh`

## API Changes

### New CLI Commands
```bash
# Core tree exploration workflow
repomap-tool explore /project "intent description" [--session session_id] [--max-depth N]
repomap-tool focus <tree_id> [--session session_id]
repomap-tool expand <area> [--session session_id] [--tree tree_id]
repomap-tool prune <area> [--session session_id] [--tree tree_id]
repomap-tool map [--session session_id] [--tree tree_id] [--include-code]

# Session and tree management
repomap-tool list-trees [--session session_id]
repomap-tool status [--session session_id]
repomap-tool tree-info <tree_id> [--session session_id]
```

### Session Control
```bash
# Via environment variable (recommended)
export REPOMAP_SESSION="my_exploration_session"
repomap-tool explore /project "authentication bugs"

# Via CLI parameter (override)
repomap-tool --session "quick_check" map
```

## Configuration Changes

### New Tree Config
```python
class TreeConfig(BaseModel):
    enabled: bool = True
    max_depth: int = 3
    max_trees_per_session: int = 10
    entrypoint_threshold: float = 0.6
    enable_code_snippets: bool = True
    cache_tree_structures: bool = True

class RepoMapConfig(BaseModel):
    # ... existing fields ...
    trees: TreeConfig = TreeConfig()
```

## Success Metrics

### Functional Metrics
- [ ] Entrypoint discovery finds relevant code entry points 90%+ of the time
- [ ] Tree building creates logical hierarchical structures
- [ ] Tree expansion/pruning works correctly with existing aider infrastructure
- [ ] Session management maintains state across CLI invocations
- [ ] Tree mapping generates useful, focused repomaps

### Performance Metrics
- [ ] Entrypoint discovery completes in < 5 seconds for 1000+ file projects
- [ ] Tree building completes in < 10 seconds for complex trees
- [ ] Session state persistence < 1 second
- [ ] Memory usage scales linearly with tree size

### User Experience Metrics
- [ ] Developers can quickly find relevant code starting points
- [ ] Tree exploration provides logical, intuitive navigation
- [ ] Session workflow feels natural and stateful
- [ ] Generated repomaps are focused and useful

## User Experience Examples

### Example 1: Debugging Authentication Issues

#### Step 1: Initial Discovery
```bash
$ export REPOMAP_SESSION="debug_auth_$(date +%s)"
$ repomap-tool explore /project "authentication login errors"

💡 Using session: debug_auth_1704067200
Set: export REPOMAP_SESSION=debug_auth_1704067200

🔍 Found 3 exploration contexts:
  • Frontend Auth Flow [id: frontend_auth_a1b2c3d4] (confidence: 0.92)
  • Backend Auth Service [id: backend_auth_e5f6g7h8] (confidence: 0.87)
  • Auth Error Handling [id: auth_errors_i9j0k1l2] (confidence: 0.81)

💡 Next steps:
  repomap-tool focus <tree_id>    # Focus on specific tree
  repomap-tool map                # View current tree
```

#### Step 2: Focus on Error Handling
```bash
$ repomap-tool focus auth_errors_i9j0k1l2
✅ Focused on tree: auth_errors_i9j0k1l2

$ repomap-tool map
🌳 Exploration Tree: Auth Error Handling
📍 Root: AuthErrorHandler

├── AuthErrorHandler (src/auth/error_handler.py:15)
│   ├── handle_login_error (src/auth/error_handler.py:42)
│   ├── validate_credentials (src/auth/error_handler.py:68)
│   └── log_auth_failure (src/auth/error_handler.py:85)
├── LoginValidator (src/auth/validators.py:12)
│   └── check_password_strength (src/auth/validators.py:23)
└── AuthExceptions (src/auth/exceptions.py:8)
    ├── InvalidCredentialsError (src/auth/exceptions.py:12)
    └── AccountLockedError (src/auth/exceptions.py:18)

🔍 Available expansions:
  • password_validation - expand with: repomap-tool expand "password_validation"
  • session_management - expand with: repomap-tool expand "session_management"
  • rate_limiting - expand with: repomap-tool expand "rate_limiting"
```

#### Step 3: Expand and Refine
```bash
$ repomap-tool expand "password_validation"
✅ Expanded tree in area: password_validation

$ repomap-tool map --include-code
🌳 Exploration Tree: Auth Error Handling
📍 Root: AuthErrorHandler

├── AuthErrorHandler (src/auth/error_handler.py:15)
│   ├── handle_login_error (src/auth/error_handler.py:42)
│   │   └── def handle_login_error(self, error: AuthError) -> ErrorResponse:
│   ├── validate_credentials (src/auth/error_handler.py:68)
│   │   └── def validate_credentials(self, username: str, password: str) -> bool:
│   └── log_auth_failure (src/auth/error_handler.py:85)
├── LoginValidator (src/auth/validators.py:12)
│   ├── check_password_strength (src/auth/validators.py:23)
│   │   └── def check_password_strength(self, password: str) -> ValidationResult:
│   ├── validate_password_format (src/auth/validators.py:45)  # 🆕 EXPANDED
│   │   └── def validate_password_format(self, password: str) -> bool:
│   └── check_common_passwords (src/auth/validators.py:67)   # 🆕 EXPANDED
│       └── def check_common_passwords(self, password: str) -> bool:
└── AuthExceptions (src/auth/exceptions.py:8)
    ├── InvalidCredentialsError (src/auth/exceptions.py:12)
    ├── WeakPasswordError (src/auth/exceptions.py:24)        # 🆕 EXPANDED
    └── AccountLockedError (src/auth/exceptions.py:18)

✅ Expanded areas: password_validation

$ repomap-tool prune "logging" 
✅ Pruned tree in area: logging
✂️ Pruned areas: logging
```

### Example 2: Feature Development Discovery

```bash
$ export REPOMAP_SESSION="payment_feature"
$ repomap-tool explore /ecommerce-app "payment processing checkout flow"

🔍 Found 4 exploration contexts:
  • Payment Gateway Integration [id: payment_gateway_x1y2z3] (confidence: 0.95)
  • Checkout UI Components [id: checkout_ui_a4b5c6] (confidence: 0.89)
  • Order Processing Pipeline [id: order_pipeline_d7e8f9] (confidence: 0.83)
  • Payment Security & Validation [id: payment_security_g0h1i2] (confidence: 0.76)

$ repomap-tool focus payment_gateway_x1y2z3
$ repomap-tool map

🌳 Exploration Tree: Payment Gateway Integration
📍 Root: PaymentGateway

├── PaymentGateway (src/payments/gateway.py:20)
│   ├── process_payment (src/payments/gateway.py:45)
│   ├── handle_webhook (src/payments/gateway.py:78)
│   └── refund_payment (src/payments/gateway.py:102)
├── StripeConnector (src/payments/providers/stripe.py:15)
│   └── create_payment_intent (src/payments/providers/stripe.py:32)
├── PayPalConnector (src/payments/providers/paypal.py:18)
└── PaymentValidator (src/payments/validation.py:12)
    ├── validate_card_details (src/payments/validation.py:25)
    └── check_fraud_rules (src/payments/validation.py:58)

🔍 Available expansions:
  • webhook_handlers - expand with: repomap-tool expand "webhook_handlers"
  • error_recovery - expand with: repomap-tool expand "error_recovery"
  • payment_methods - expand with: repomap-tool expand "payment_methods"
```

### Example 3: Multi-Session Parallel Work

#### Developer A: Frontend Work
```bash
$ export REPOMAP_SESSION="frontend_refactor"
$ repomap-tool explore /project "React component optimization"

🔍 Found 2 exploration contexts:
  • Component Performance [id: component_perf_abc123] (confidence: 0.91)
  • State Management [id: state_mgmt_def456] (confidence: 0.84)
```

#### Developer B: Backend Work (Different Session)
```bash
$ export REPOMAP_SESSION="backend_api_fixes" 
$ repomap-tool explore /project "API response time issues"

🔍 Found 3 exploration contexts:
  • Database Query Optimization [id: db_queries_ghi789] (confidence: 0.93)
  • Caching Layer [id: cache_layer_jkl012] (confidence: 0.87)
  • API Middleware [id: api_middleware_mno345] (confidence: 0.79)
```

### Example 4: Session Management

```bash
$ repomap-tool list-trees --session frontend_refactor
📋 Trees in session 'frontend_refactor':
  • component_perf_abc123 [FOCUSED] - Component Performance (updated 2m ago)
  • state_mgmt_def456 - State Management (created 5m ago)

$ repomap-tool status
📊 Session Status: debug_auth_1704067200
═══════════════════════════════════════

🎯 Current Focus: auth_errors_i9j0k1l2
📅 Session Started: 2024-01-01 09:15:30
🕐 Last Activity: 2024-01-01 10:45:22

🌳 Exploration Trees (3 total):
  1. 🎯 auth_errors_i9j0k1l2 [FOCUSED] - Auth Error Handling
  2. 📋 frontend_auth_a1b2c3d4 - Frontend Auth Flow  
  3. 📋 backend_auth_e5f6g7h8 - Backend Auth Service

💡 Quick Actions:
  repomap-tool map                          # View current focused tree
  repomap-tool focus frontend_auth_a1b2c3d4 # Switch to frontend tree
```

### Example 5: Error Handling

#### When No Entrypoints Found
```bash
$ repomap-tool explore /project "quantum flux capacitor"

⚠️  No high-confidence entrypoints found for intent: "quantum flux capacitor"

💡 Suggestions:
  • Try broader terms: "flux", "capacitor", "quantum"
  • Use semantic search: repomap-tool search "quantum flux"

🔧 Alternative approaches:
  repomap-tool analyze /project               # Get general overview
  repomap-tool search "flux" --fuzzy          # Fuzzy search
```

#### Session Not Found
```bash
$ repomap-tool map --session "nonexistent_session"

❌ Session 'nonexistent_session' not found

💡 Available sessions:
  • debug_auth_1704067200 (active 2h ago)
  • payment_feature (active 5m ago)
  • frontend_refactor (active 1h ago)
```

## Integration with Existing Infrastructure

### Leverages Current Capabilities
- **Semantic Matching:** For entrypoint discovery relevance
- **Fuzzy Matching:** For additional entrypoint candidates
- **Aider RepoMap:** For tree building and dependency analysis
- **Symbol Extraction:** For tree node identification
- **File Processing:** For code snippet extraction

### Extends Current Functionality
- **Structured Exploration:** Adds tree-based navigation
- **Session State:** Adds persistent exploration context
- **Dynamic Focus:** Adds stateful tree manipulation
- **Targeted Output:** Generates focused repomaps from trees

## Definition of Done

### Phase 1 Complete When:
- [ ] Smart entrypoint discovery works with existing semantic/fuzzy matching
- [ ] Tree building creates logical hierarchical structures from entrypoints
- [ ] Tree manipulation (focus, expand, prune) works correctly
- [ ] Session management maintains state across CLI invocations
- [ ] Tree mapping generates focused, useful repomaps
- [ ] CLI provides complete tree exploration workflow
- [ ] External session control works via CLI params and env vars
- [ ] Performance targets met (< 10s for tree operations)
- [ ] Test coverage > 90% for all tree components
- [ ] Documentation complete with examples
- [ ] Integration with existing DockerRepoMap seamless

This phase establishes **tree-based exploration as the core workflow** of the repomap tool, providing the foundational functionality that all other phases will build upon.
