# Phase 2: Dependency Analysis Implementation

## Overview
**Goal:** Build intelligent dependency graph analysis to understand code relationships, file importance, and impact scope for better repomap generation.

**Duration:** 3-4 weeks  
**Effort:** High  
**Impact:** High  
**Priority:** High (After Phase 1)  
**Depends On:** Phase 1 (Tree-Based Exploration)

## Current State vs Target State

### Current State
- Files analyzed in isolation
- No understanding of import relationships
- No knowledge of function call patterns
- Cannot determine file importance or centrality
- No impact analysis for changes

### Target State
- Complete dependency graph of codebase
- File importance ranking based on connectivity
- Function call graph analysis
- Impact scope analysis for changes
- Intelligent file prioritization based on dependencies

## Technical Architecture

### New Components to Add

```
src/repomap_tool/dependencies/
├── __init__.py
├── import_analyzer.py      # Analyze import statements
├── call_graph_builder.py   # Build function call graphs
├── dependency_graph.py     # Main dependency graph
├── centrality_calculator.py # Calculate file/function importance
├── impact_analyzer.py      # Analyze change impact scope
└── graph_visualizer.py     # Visualize dependency graphs (optional)
```

### Core Classes to Implement

```python
class ImportAnalyzer:
    """Analyzes import statements across all files"""
    
class CallGraphBuilder:
    """Builds function call graphs within and across files"""
    
class DependencyGraph:
    """Main dependency graph representation"""
    
class CentralityCalculator:
    """Calculates importance scores for files and functions"""
    
class ImpactAnalyzer:
    """Analyzes impact scope of potential changes"""
```

## Technical Architecture Overview

### System Flow Diagram
```
Project Files → ImportAnalyzer → DependencyGraph → CentralityCalculator
                                       ↓
CallGraphBuilder → AdvancedDependencyGraph → ImpactAnalyzer
                                       ↓
Phase 1 TreeBuilder → EnhancedTreeBuilder (with dependency intelligence)
                                       ↓
Enhanced Tree Exploration (smarter entrypoints, dependency-aware trees)
```

### Data Flow Architecture

```python
# Input: Project files
project_files = ["/src/auth/handler.py", "/src/auth/validator.py", ...]

# Stage 1: Import Analysis
import_analyzer = ImportAnalyzer()
project_imports = import_analyzer.analyze_project_imports(project_files)
# Output: ProjectImports(file_imports={"/src/auth/handler.py": [Import("validator", "local"), ...]})

# Stage 2: Basic Dependency Graph
dependency_graph = DependencyGraph()
dependency_graph.build_graph(project_files)
# Output: Graph with nodes (files) and edges (import relationships)

# Stage 3: Call Graph Analysis
call_graph_builder = CallGraphBuilder()
call_graph = call_graph_builder.build_call_graph(project_files)
# Output: CallGraph with function-level dependencies

# Stage 4: Advanced Analysis
advanced_graph = AdvancedDependencyGraph()
advanced_graph.integrate_call_graph(call_graph)
centrality_calc = CentralityCalculator(advanced_graph)
centrality_scores = centrality_calc.calculate_composite_importance()
# Output: {"auth/handler.py": 0.9, "auth/validator.py": 0.7, ...}

# Stage 5: Enhanced Phase 1 Integration
enhanced_discoverer = EnhancedEntrypointDiscoverer(repo_map, advanced_graph)
enhanced_entrypoints = enhanced_discoverer.discover_entrypoints(project_path, intent)
# Output: Entrypoints with both semantic scores AND centrality scores

# Stage 6: Impact Analysis
impact_analyzer = ImpactAnalyzer(advanced_graph)
impact_report = impact_analyzer.analyze_change_impact(["auth/handler.py"])
# Output: ImpactReport(affected_files=["auth/validator.py", "api/auth.py"], risk_score=0.8)
```

### Component Integration Map

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Analysis Layer    │    │   Graph Layer       │    │  Enhancement Layer  │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ ImportAnalyzer      │───►│ DependencyGraph     │───►│ EnhancedDiscoverer  │
│ CallGraphBuilder    │───►│ AdvancedDepGraph    │───►│ EnhancedTreeBuilder │
│ Language Parsers    │    │ CentralityCalc      │───►│ ImpactAnalyzer      │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
         ▲                           ▲                           ▲
         │                           │                           │
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│  External Tools     │    │   Phase 1 Classes  │    │   Output Layer      │
├─────────────────────┤    ├─────────────────────┤    ├─────────────────────┤
│ AST Parsers         │    │ EntrypointDiscoverer│    │ Enhanced Trees      │
│ Tree-sitter         │    │ TreeBuilder         │    │ Impact Reports      │
│ Language-specific   │    │ ExplorationTree     │    │ Centrality Rankings │
│                     │    │                     │    │                     │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

### File Structure & Dependencies

```
src/repomap_tool/dependencies/
├── __init__.py                    # Package initialization
├── import_analyzer.py             # Uses: AST, tree-sitter, language parsers
├── call_graph_builder.py          # Uses: import_analyzer, AST parsing
├── dependency_graph.py            # Uses: networkx, import_analyzer
├── centrality_calculator.py       # Uses: networkx algorithms, dependency_graph
├── impact_analyzer.py             # Uses: dependency_graph, centrality_calculator
└── graph_visualizer.py            # Uses: matplotlib/plotly (optional)

# Enhanced files (Phase 1 + Phase 2):
src/repomap_tool/trees/discovery_engine.py  # Enhanced with centrality scoring
src/repomap_tool/trees/tree_builder.py      # Enhanced with dependency intelligence
src/repomap_tool/trees/tree_mapper.py       # Enhanced with impact information

# New dependencies:
pyproject.toml                     # Add: networkx, ast, esprima, tree_sitter
```

### Critical Technical Decisions

1. **Graph Representation**: Use NetworkX for graph algorithms, custom classes for domain logic
2. **Language Support**: Extensible parser architecture for multi-language support
3. **Performance**: Incremental graph updates, aggressive caching, lazy evaluation
4. **Integration**: Enhance Phase 1 classes via inheritance, not replacement
5. **Centrality Algorithms**: Composite scoring using degree, betweenness, and PageRank

## User Experience Examples

### Example 1: Enhanced Entrypoint Discovery

#### Before Phase 2 (Phase 1 Only):
```bash
$ repomap-tool explore /project "authentication bugs"

🔍 Found 3 exploration contexts:
  • Frontend Auth Flow [id: frontend_auth_a1b2c3d4] (confidence: 0.92)
  • Backend Auth Service [id: backend_auth_e5f6g7h8] (confidence: 0.87) 
  • Auth Error Handling [id: auth_errors_i9j0k1l2] (confidence: 0.81)
```

#### After Phase 2 (Enhanced):
```bash
$ repomap-tool explore /project "authentication bugs"

🔍 Found 3 exploration contexts (enhanced with dependency analysis):
  • Backend Auth Service [id: backend_auth_e5f6g7h8] (confidence: 0.87, centrality: 0.95) 🔥
  • Frontend Auth Flow [id: frontend_auth_a1b2c3d4] (confidence: 0.92, centrality: 0.71)
  • Auth Error Handling [id: auth_errors_i9j0k1l2] (confidence: 0.81, centrality: 0.64)

💡 Backend Auth Service promoted to top due to high dependency centrality
   (imported by 12 files, critical for system functioning)
```

### Example 2: Dependency-Enhanced Tree Structure

#### Phase 1 Tree:
```bash
$ repomap-tool map

🌳 Exploration Tree: Backend Auth Service
📍 Root: AuthService

├── AuthService (src/auth/service.py:20)
│   ├── authenticate_user (src/auth/service.py:45)
│   ├── validate_token (src/auth/service.py:78)
│   └── refresh_session (src/auth/service.py:102)
```

#### Phase 2 Enhanced Tree:
```bash
$ repomap-tool map

🌳 Exploration Tree: Backend Auth Service
📍 Root: AuthService (centrality: 0.95, risk: HIGH)

├── AuthService (src/auth/service.py:20)
│   ├── authenticate_user (src/auth/service.py:45) [deps: 3, dependents: 8] ⚠️
│   │   └── 💡 High impact: Changes affect 8 downstream files
│   ├── validate_token (src/auth/service.py:78) [deps: 2, dependents: 12] 🔥  
│   │   └── 💡 Critical: Used by entire API layer
│   └── refresh_session (src/auth/service.py:102) [deps: 1, dependents: 3]

🔗 Dependency Intelligence:
  • Dependencies: TokenValidator, UserRepository, SessionStore
  • Dependents: API controllers (5), Frontend services (3), Background jobs (4)
  • Impact radius: 23 files would be affected by changes
  • Suggested tests: test_auth_service.py, test_api_integration.py, test_user_flows.py
```

### Example 3: Impact Analysis Workflow

```bash
$ repomap-tool impact-analysis /project --files src/auth/service.py

🎯 Impact Analysis Report
═══════════════════════════════════════

📁 Changed File: src/auth/service.py
🎯 Risk Score: 0.85 (HIGH RISK)

📊 Direct Impact:
  • 12 files directly import this module
  • 3 critical API endpoints affected
  • 2 background services affected

📈 Transitive Impact:
  • 23 files in total dependency chain
  • 8 user-facing features potentially affected
  • 3 external integrations at risk

🧪 Recommended Tests:
  Priority 1 (Must Run):
  • tests/unit/test_auth_service.py
  • tests/integration/test_auth_flow.py
  • tests/integration/test_api_auth.py
  
  Priority 2 (Should Run):
  • tests/e2e/test_login_scenarios.py
  • tests/integration/test_background_auth.py

⚠️  Breaking Change Potential:
  • HIGH: authenticate_user() - used by 8 downstream files
  • MEDIUM: validate_token() - public API method
  • LOW: refresh_session() - internal method

💡 Suggestions:
  • Consider feature flags for authenticate_user changes
  • Add deprecation warnings before API changes
  • Review with API team before making breaking changes
```

### Example 4: Dependency Visualization

```bash
$ repomap-tool show-centrality /project --file src/auth/service.py

📊 Centrality Analysis: src/auth/service.py
══════════════════════════════════════════

🎯 Centrality Scores:
  • Degree Centrality: 0.89 (connected to 89% of auth module)
  • Betweenness Centrality: 0.76 (bridges 76% of shortest paths)
  • PageRank Score: 0.92 (very high importance)
  • Composite Score: 0.95 (TOP 5% of codebase)

🔗 Dependency Summary:
  • Imports: 5 files (TokenValidator, UserRepo, SessionStore, CryptoUtils, Logger)
  • Imported by: 12 files (all API controllers, 3 services, 2 background jobs)
  • Dependency depth: 3 levels
  • Stability metric: 0.71 (fairly stable - more incoming than outgoing deps)

🏆 Ranking:
  • #2 most central file in auth module
  • #7 most central file in entire project
  • #3 highest risk for breaking changes
```

### Example 5: Circular Dependency Detection

```bash
$ repomap-tool find-cycles /project

🔄 Circular Dependencies Detected
════════════════════════════════════

⚠️  Found 2 circular dependency cycles:

Cycle 1 (Length: 3):
  src/auth/service.py → src/auth/validator.py → src/auth/exceptions.py → src/auth/service.py
  
  Impact: Medium (affects authentication flow)
  Files involved: 3
  Suggested fix: Move exceptions to separate module

Cycle 2 (Length: 2):  
  src/api/user.py ↔ src/models/user.py
  
  Impact: Low (data access layer)
  Files involved: 2
  Suggested fix: Extract interface or use dependency injection

💡 Recommendations:
  • Break cycles by extracting shared interfaces
  • Consider dependency injection patterns
  • Move common utilities to separate modules
  • Review with architecture team
```

## Quality Standards & Anti-Patterns

### ✅ What Good Looks Like

#### **1. Comprehensive Import Analysis**
```python
# GOOD: Multi-language import parsing
class ImportAnalyzer:
    def analyze_file_imports(self, file_path: str) -> FileImports:
        file_ext = file_path.split('.')[-1]
        parser = self.language_parsers.get(file_ext)
        
        if not parser:
            logger.warning(f"No parser for {file_ext}, skipping {file_path}")
            return FileImports(file_path, [])
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            imports = parser.extract_imports(content)
            resolved_imports = self._resolve_import_paths(imports, file_path)
            
            return FileImports(file_path, resolved_imports)
        except Exception as e:
            logger.error(f"Failed to analyze imports in {file_path}: {e}")
            return FileImports(file_path, [])

# GOOD: Handles complex import resolution
def _resolve_import_paths(self, imports: List[Import], file_path: str) -> List[Import]:
    resolved = []
    for imp in imports:
        try:
            if imp.is_relative:
                resolved_path = self._resolve_relative_import(imp.module, file_path)
            else:
                resolved_path = self._resolve_absolute_import(imp.module)
            
            if resolved_path and os.path.exists(resolved_path):
                imp.resolved_path = resolved_path
                resolved.append(imp)
        except ImportResolutionError:
            # Log but continue - some imports might be external
            continue
    
    return resolved
```

#### **2. Robust Graph Construction**
```python
# GOOD: Incremental graph building with validation
class DependencyGraph:
    def build_graph(self, project_files: List[str]):
        logger.info(f"Building dependency graph for {len(project_files)} files")
        
        # Build in stages with validation
        self._validate_files(project_files)
        self._add_nodes(project_files)
        self._add_edges()
        self._validate_graph_integrity()
        
        logger.info(f"Graph built: {len(self.nodes)} nodes, {len(self.edges)} edges")
    
    def _validate_graph_integrity(self):
        # Check for orphaned nodes
        connected_nodes = set()
        for source, target in self.edges:
            connected_nodes.add(source)
            connected_nodes.add(target)
        
        orphaned = set(self.nodes.keys()) - connected_nodes
        if orphaned:
            logger.warning(f"Found {len(orphaned)} orphaned nodes: {list(orphaned)[:5]}...")
        
        # Check for self-references
        self_refs = [(s, t) for s, t in self.edges if s == t]
        if self_refs:
            logger.warning(f"Found {len(self_refs)} self-references")
```

#### **3. Accurate Centrality Calculation**
```python
# GOOD: Multiple centrality measures with validation
class CentralityCalculator:
    def calculate_composite_importance(self) -> Dict[str, float]:
        # Calculate multiple centrality measures
        degree_scores = self.calculate_degree_centrality()
        betweenness_scores = self.calculate_betweenness_centrality() 
        pagerank_scores = self.calculate_pagerank_centrality()
        
        # Validate scores are reasonable
        self._validate_centrality_scores(degree_scores)
        self._validate_centrality_scores(betweenness_scores) 
        self._validate_centrality_scores(pagerank_scores)
        
        # Weighted combination
        composite_scores = {}
        all_files = set(degree_scores.keys()) | set(betweenness_scores.keys()) | set(pagerank_scores.keys())
        
        for file_path in all_files:
            degree = degree_scores.get(file_path, 0.0)
            betweenness = betweenness_scores.get(file_path, 0.0) 
            pagerank = pagerank_scores.get(file_path, 0.0)
            
            # Weighted average: degree 40%, betweenness 30%, pagerank 30%
            composite = degree * 0.4 + betweenness * 0.3 + pagerank * 0.3
            composite_scores[file_path] = composite
        
        return composite_scores
```

#### **4. Smart Phase 1 Integration**
```python
# GOOD: Enhances Phase 1 without breaking it
class EnhancedEntrypointDiscoverer(EntrypointDiscoverer):
    def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
        # Get base results from Phase 1 (proven to work)
        base_entrypoints = super().discover_entrypoints(project_path, intent)
        
        if not base_entrypoints:
            logger.warning("No base entrypoints found, returning empty list")
            return []
        
        # Add dependency intelligence as enhancement
        try:
            centrality_scores = self.centrality_calc.calculate_composite_importance()
            
            for entrypoint in base_entrypoints:
                file_path = entrypoint.location.split(':')[0]
                centrality = centrality_scores.get(file_path, 0.0)
                
                # Enhance score (don't replace it)
                boost = centrality * 0.3  # 30% boost from centrality
                entrypoint.score = min(1.0, entrypoint.score + boost)
                entrypoint.centrality_score = centrality
                
        except Exception as e:
            logger.error(f"Failed to enhance with centrality: {e}")
            # Fall back to Phase 1 results
            
        return sorted(base_entrypoints, key=lambda x: x.score, reverse=True)
```

### ❌ What NOT Good Looks Like (Anti-Patterns)

#### **1. Lazy Import Analysis (AVOID)**
```python
# BAD: Hardcoded parsing instead of proper language support
def analyze_imports_WRONG(self, file_path: str):
    with open(file_path) as f:
        content = f.read()
    
    imports = []
    # This only works for Python and misses many cases!
    for line in content.split('\n'):
        if line.startswith('import ') or line.startswith('from '):
            imports.append(line.split()[1])  # Brittle parsing!
    
    return imports

# BAD: Doesn't handle different languages
def get_dependencies_WRONG(self, file_path: str):
    if file_path.endswith('.py'):
        return self.python_imports(file_path)
    else:
        return []  # Ignores JS, TS, Java, Go, etc.!
# WHY BAD: No language extensibility, brittle parsing, missing edge cases
```

#### **2. Broken Graph Construction (AVOID)**
```python
# BAD: No validation or error handling
class BadDependencyGraph:
    def build_graph(self, files):
        for file in files:
            imports = get_imports(file)  # Can crash!
            for imp in imports:
                self.add_edge(file, imp)  # No validation!

# BAD: Inefficient graph representation  
def find_cycles_WRONG(self):
    # Brute force - exponential time complexity!
    for node in self.nodes:
        self._check_all_paths(node, node, [])  # Will timeout on large graphs!

# BAD: No caching
def calculate_centrality_WRONG(self):
    # Recalculates everything every time!
    scores = {}
    for file in self.files:
        scores[file] = self._expensive_calculation(file)  # No caching!
    return scores
# WHY BAD: No error handling, poor performance, doesn't scale
```

#### **3. Poor Phase 1 Integration (AVOID)**
```python
# BAD: Replaces Phase 1 instead of enhancing it
class BadEnhancedDiscoverer:
    def discover_entrypoints(self, project_path: str, intent: str):
        # Ignores Phase 1 semantic analysis!
        centrality_scores = self.get_centrality()
        return [file for file, score in centrality_scores.items() if score > 0.5]

# BAD: Breaks existing functionality
class BadTreeBuilder:
    def build_exploration_tree(self, entrypoint):
        # Completely reimplements Phase 1 tree building!
        # Loses all the semantic analysis and tree structure logic
        return DependencyTree(entrypoint)  # Different class hierarchy!
# WHY BAD: Doesn't leverage Phase 1 investment, breaks compatibility
```

#### **4. Performance Anti-Patterns (AVOID)**
```python
# BAD: No incremental updates
def update_graph_WRONG(self, changed_files):
    # Rebuilds entire graph from scratch!
    self.nodes.clear()
    self.edges.clear()
    self.build_graph(self.all_files)  # Expensive!

# BAD: Memory inefficient
class BadGraphStorage:
    def __init__(self):
        # Stores full file contents in memory!
        self.file_contents = {}
        self.call_graph = {}  # Huge nested dictionaries!
        
    def add_file(self, file_path):
        with open(file_path) as f:
            self.file_contents[file_path] = f.read()  # Memory leak!

# BAD: No caching strategy
def get_impact_analysis_WRONG(self, file_path):
    # Recalculates transitive dependencies every time!
    affected = set()
    queue = [file_path]
    while queue:  # BFS without memoization
        current = queue.pop(0)
        for dependent in self.get_dependents(current):  # Expensive query!
            if dependent not in affected:
                affected.add(dependent)
                queue.append(dependent)
    return affected
# WHY BAD: Ignores performance requirements, memory inefficient, no caching
```

### 🚨 Shortcut Prevention Checklist

#### **Before Claiming "Done" - Verify:**

1. **Multi-Language Support**
   - [ ] Import analysis works for Python, JavaScript, TypeScript, Java, Go
   - [ ] Extensible parser architecture for adding new languages
   - [ ] Handles language-specific import patterns correctly
   - [ ] Falls back gracefully for unsupported languages

2. **Graph Accuracy**
   - [ ] Dependency graph accurately represents import relationships
   - [ ] Circular dependency detection finds all cycles
   - [ ] Centrality calculations use proven algorithms (NetworkX)
   - [ ] Graph validation catches orphaned nodes and inconsistencies

3. **Phase 1 Integration**
   - [ ] Enhances existing Phase 1 classes via inheritance
   - [ ] Doesn't break Phase 1 functionality when Phase 2 is disabled
   - [ ] Falls back gracefully when dependency analysis fails
   - [ ] Preserves all Phase 1 semantic analysis capabilities

4. **Performance Standards**
   - [ ] Graph construction < 30 seconds for 1000+ files
   - [ ] Centrality calculation uses efficient algorithms
   - [ ] Incremental updates don't rebuild entire graph
   - [ ] Memory usage scales linearly with project size
   - [ ] Cache hit rate > 80% for repeated analyses

5. **Robustness**
   - [ ] Handles import resolution failures gracefully
   - [ ] Validates graph integrity after construction
   - [ ] Error handling doesn't crash on malformed files
   - [ ] Comprehensive logging for debugging

### 🎯 Acceptance Tests (Must Pass)

```python
# Test 1: Multi-Language Import Analysis
def test_multi_language_import_analysis():
    analyzer = ImportAnalyzer()
    
    # Test Python imports
    python_imports = analyzer.analyze_file_imports("test_files/sample.py")
    assert len(python_imports.imports) > 0
    assert any("import os" in str(imp) for imp in python_imports.imports)
    
    # Test JavaScript imports  
    js_imports = analyzer.analyze_file_imports("test_files/sample.js")
    assert len(js_imports.imports) > 0
    assert any("require(" in str(imp) or "from " in str(imp) for imp in js_imports.imports)

# Test 2: Graph Construction Accuracy
def test_dependency_graph_accuracy():
    graph = DependencyGraph()
    graph.build_graph(["test_files/module_a.py", "test_files/module_b.py"])
    
    # Verify specific known dependencies
    deps_a = graph.get_dependencies("test_files/module_a.py")
    assert "test_files/module_b.py" in deps_a
    
    dependents_b = graph.get_dependents("test_files/module_b.py") 
    assert "test_files/module_a.py" in dependents_b

# Test 3: Centrality Calculation
def test_centrality_calculation():
    calculator = CentralityCalculator(dependency_graph)
    scores = calculator.calculate_composite_importance()
    
    # Scores should be between 0 and 1
    assert all(0 <= score <= 1 for score in scores.values())
    
    # High-centrality files should have higher scores
    central_file = max(scores.items(), key=lambda x: x[1])
    assert central_file[1] > 0.5  # Top file should be clearly central

# Test 4: Phase 1 Enhancement 
def test_phase1_enhancement():
    enhanced_discoverer = EnhancedEntrypointDiscoverer(repo_map, dependency_graph)
    
    # Should find same base entrypoints as Phase 1
    base_entrypoints = EntrypointDiscoverer(repo_map).discover_entrypoints("/project", "auth")
    enhanced_entrypoints = enhanced_discoverer.discover_entrypoints("/project", "auth")
    
    # Same entrypoints found
    base_ids = {ep.identifier for ep in base_entrypoints}
    enhanced_ids = {ep.identifier for ep in enhanced_entrypoints}
    assert base_ids == enhanced_ids
    
    # But enhanced should have centrality scores
    assert all(hasattr(ep, 'centrality_score') for ep in enhanced_entrypoints)

# Test 5: Performance Requirements
def test_performance_requirements():
    large_project_files = generate_test_files(1000)  # 1000 test files
    
    start_time = time.time()
    graph = DependencyGraph()
    graph.build_graph(large_project_files)
    build_time = time.time() - start_time
    
    # Must meet performance target
    assert build_time < 30.0  # 30 second limit
    
    # Centrality calculation should be fast too
    start_time = time.time()
    calculator = CentralityCalculator(graph)
    scores = calculator.calculate_composite_importance()
    calc_time = time.time() - start_time
    
    assert calc_time < 10.0  # 10 second limit for centrality
```

### 🚫 Automatic Failure Conditions

**Implementation FAILS if:**
- Only supports Python imports (not multi-language)
- Uses regex parsing instead of proper AST/language parsers
- Reimplements Phase 1 functionality instead of enhancing it
- No error handling or validation in graph construction
- Doesn't meet performance requirements (> 30s for 1000 files)
- Centrality scores are all 0 or all 1 (calculation error)
- Graph construction crashes on circular dependencies
- No caching or optimization for repeated operations
- Silent failures when import resolution fails

## Implementation Plan

### Week 1: Import Analysis and Basic Graph Structure

#### Day 1-2: Import Analysis Foundation
**Files to Create:**
- `src/repomap_tool/dependencies/__init__.py`
- `src/repomap_tool/dependencies/import_analyzer.py`

**Key Features:**
```python
class ImportAnalyzer:
    def __init__(self):
        self.language_parsers = {
            'python': PythonImportParser(),
            'javascript': JavaScriptImportParser(),
            'typescript': TypeScriptImportParser(),
            'java': JavaImportParser(),
            'go': GoImportParser(),
            # ... more languages
        }
    
    def analyze_file_imports(self, file_path: str) -> FileImports:
        """Analyze all imports in a single file"""
        
    def analyze_project_imports(self, project_files: List[str]) -> ProjectImports:
        """Analyze imports across entire project"""
        
    def resolve_import_paths(self, import_stmt: str, file_path: str) -> str:
        """Resolve relative imports to absolute paths"""
```

**Language-Specific Import Parsers:**
```python
class PythonImportParser:
    def extract_imports(self, file_content: str) -> List[Import]:
        # Handle: import os, from module import func, import package.module as alias
        
class JavaScriptImportParser:
    def extract_imports(self, file_content: str) -> List[Import]:
        # Handle: import { func } from './module', require('module')
        
class TypeScriptImportParser:
    def extract_imports(self, file_content: str) -> List[Import]:
        # Handle TypeScript-specific imports and type imports
```

#### Day 3-4: Basic Dependency Graph
**Files to Create:**
- `src/repomap_tool/dependencies/dependency_graph.py`

**Key Features:**
```python
class DependencyNode:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: List[str] = []
        self.imported_by: List[str] = []
        self.functions: List[str] = []
        self.classes: List[str] = []

class DependencyGraph:
    def __init__(self):
        self.nodes: Dict[str, DependencyNode] = {}
        self.edges: List[Tuple[str, str]] = []  # (source, target)
        self.import_analyzer = ImportAnalyzer()
    
    def build_graph(self, project_files: List[str]):
        """Build complete dependency graph"""
        
    def add_file(self, file_path: str):
        """Add file to dependency graph"""
        
    def add_dependency(self, source: str, target: str):
        """Add dependency edge"""
        
    def get_dependencies(self, file_path: str) -> List[str]:
        """Get files that this file depends on"""
        
    def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on this file"""
        
    def find_cycles(self) -> List[List[str]]:
        """Find circular dependencies"""
```

#### Day 5: File Centrality Calculation
**Files to Create:**
- `src/repomap_tool/dependencies/centrality_calculator.py`

**Key Features:**
```python
class CentralityCalculator:
    def __init__(self, dependency_graph: DependencyGraph):
        self.graph = dependency_graph
    
    def calculate_degree_centrality(self) -> Dict[str, float]:
        """Files with most connections (imports + imported_by)"""
        
    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """Files that are bridges between other files"""
        
    def calculate_pagerank_centrality(self) -> Dict[str, float]:
        """PageRank-style importance scoring"""
        
    def calculate_hub_authority_scores(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """HITS algorithm - hubs (import many) vs authorities (imported by many)"""
        
    def calculate_composite_importance(self) -> Dict[str, float]:
        """Weighted combination of all centrality measures"""
```

### Week 2: Function Call Graph Analysis

#### Day 6-7: Function Call Graph Builder
**Files to Create:**
- `src/repomap_tool/dependencies/call_graph_builder.py`

**Key Features:**
```python
class FunctionCall:
    def __init__(self, caller: str, callee: str, file_path: str, line_number: int):
        self.caller = caller  # calling function
        self.callee = callee  # called function
        self.file_path = file_path
        self.line_number = line_number

class CallGraphBuilder:
    def __init__(self):
        self.language_analyzers = {
            'python': PythonCallAnalyzer(),
            'javascript': JavaScriptCallAnalyzer(),
            # ... more languages
        }
    
    def build_call_graph(self, project_files: List[str]) -> CallGraph:
        """Build function call graph across project"""
        
    def analyze_file_calls(self, file_path: str) -> List[FunctionCall]:
        """Analyze function calls within a file"""
        
    def resolve_cross_file_calls(self, calls: List[FunctionCall]) -> List[FunctionCall]:
        """Resolve calls that cross file boundaries"""
```

**Language-Specific Call Analyzers:**
```python
class PythonCallAnalyzer:
    def extract_calls(self, file_content: str, symbols: List[Symbol]) -> List[FunctionCall]:
        # Use AST to find function calls
        # Match calls to known functions
        
class JavaScriptCallAnalyzer:
    def extract_calls(self, file_content: str, symbols: List[Symbol]) -> List[FunctionCall]:
        # Parse JS/TS to find function calls
```

#### Day 8-9: Advanced Dependency Analysis
**Extend `dependency_graph.py` with:**

```python
class AdvancedDependencyGraph(DependencyGraph):
    def __init__(self):
        super().__init__()
        self.call_graph = None
        self.function_dependencies = {}
    
    def integrate_call_graph(self, call_graph: CallGraph):
        """Integrate function call information"""
        
    def calculate_transitive_dependencies(self, file_path: str) -> Set[str]:
        """Get all files transitively dependent on this file"""
        
    def calculate_dependency_depth(self, file_path: str) -> int:
        """Calculate how deep the dependency chain is"""
        
    def find_dependency_clusters(self) -> List[List[str]]:
        """Find clusters of tightly coupled files"""
        
    def calculate_stability_metric(self, file_path: str) -> float:
        """Calculate how stable a file is (few outgoing dependencies)"""
```

#### Day 10: Impact Analysis
**Files to Create:**
- `src/repomap_tool/dependencies/impact_analyzer.py`

**Key Features:**
```python
class ImpactAnalyzer:
    def __init__(self, dependency_graph: AdvancedDependencyGraph):
        self.graph = dependency_graph
    
    def analyze_change_impact(self, changed_files: List[str]) -> ImpactReport:
        """Analyze potential impact of changes to files"""
        
    def find_affected_files(self, changed_file: str) -> List[str]:
        """Find all files that might be affected by changes"""
        
    def calculate_risk_score(self, file_path: str) -> float:
        """Calculate risk score for changing this file"""
        
    def suggest_test_files(self, changed_files: List[str]) -> List[str]:
        """Suggest which test files should be run"""
        
    def find_breaking_change_potential(self, file_path: str) -> BreakingChangeRisk:
        """Assess potential for breaking changes"""
```

### Week 3: Integration and Optimization

#### Day 11-12: Integration with Tree Exploration (Phase 1)
**Files to Modify:**
- `src/repomap_tool/trees/discovery_engine.py`
- `src/repomap_tool/trees/tree_builder.py`
- `src/repomap_tool/trees/tree_clusters.py`

**Enhanced Entrypoint Discovery:**
```python
class EnhancedEntrypointDiscoverer(EntrypointDiscoverer):
    def __init__(self, repo_map: DockerRepoMap, dependency_graph: AdvancedDependencyGraph):
        super().__init__(repo_map)
        self.dependency_graph = dependency_graph
        self.centrality_calc = CentralityCalculator(dependency_graph)
    
    def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
        """Enhanced entrypoint discovery using dependency intelligence"""
        
        # Get base entrypoints using semantic/fuzzy matching (Phase 1)
        base_entrypoints = super().discover_entrypoints(project_path, intent)
        
        # Enhance with dependency centrality scores
        centrality_scores = self.centrality_calc.calculate_composite_importance()
        
        enhanced_entrypoints = []
        for entrypoint in base_entrypoints:
            # Boost score based on file centrality
            centrality_boost = centrality_scores.get(entrypoint.location, 0.0) * 0.3
            enhanced_score = entrypoint.score + centrality_boost
            
            entrypoint.score = min(1.0, enhanced_score)  # Cap at 1.0
            entrypoint.centrality_score = centrality_scores.get(entrypoint.location, 0.0)
            enhanced_entrypoints.append(entrypoint)
        
        return sorted(enhanced_entrypoints, key=lambda x: x.score, reverse=True)

**Enhanced Tree Building:**
```python
class EnhancedTreeBuilder(TreeBuilder):
    def __init__(self, repo_map: DockerRepoMap, dependency_graph: AdvancedDependencyGraph):
        super().__init__(repo_map)
        self.dependency_graph = dependency_graph
    
    def build_exploration_tree(self, entrypoint: Entrypoint, max_depth: int = 3) -> ExplorationTree:
        """Enhanced tree building using dependency relationships"""
        
        # Build base tree structure (Phase 1)
        tree = super().build_exploration_tree(entrypoint, max_depth)
        
        # Enhance with dependency information
        self._add_dependency_intelligence(tree)
        
        return tree
    
    def _add_dependency_intelligence(self, tree: ExplorationTree):
        """Add dependency-based intelligence to tree structure"""
        if tree.tree_structure:
            self._enhance_node_with_dependencies(tree.tree_structure)
    
    def _enhance_node_with_dependencies(self, node: TreeNode):
        """Enhance tree node with dependency information"""
        file_path = node.location.split(':')[0]
        
        # Add dependency context
        dependencies = self.dependency_graph.get_dependencies(file_path)
        dependents = self.dependency_graph.get_dependents(file_path)
        
        node.structural_info.update({
            'dependencies': dependencies,
            'dependents': dependents,
            'dependency_depth': self.dependency_graph.calculate_dependency_depth(file_path),
            'centrality_score': self.dependency_graph.centrality_scores.get(file_path, 0.0)
        })
        
        # Recursively enhance children
        for child in node.children:
            self._enhance_node_with_dependencies(child)
```

#### Day 13-14: Performance Optimization and Caching
**Focus Areas:**
- Graph construction optimization
- Centrality calculation caching
- Incremental graph updates
- Memory-efficient graph representation

**Caching Strategy:**
```python
class DependencyGraphCache:
    def __init__(self):
        self.graph_cache: Dict[str, AdvancedDependencyGraph] = {}
        self.centrality_cache: Dict[str, Dict[str, float]] = {}
        self.last_modified: Dict[str, datetime] = {}
    
    def get_cached_graph(self, project_path: str) -> Optional[AdvancedDependencyGraph]:
        """Get cached dependency graph if still valid"""
        
    def cache_graph(self, project_path: str, graph: AdvancedDependencyGraph):
        """Cache dependency graph"""
        
    def invalidate_cache(self, project_path: str):
        """Invalidate cache when files change"""
```

### Week 4: Advanced Features and Documentation

#### Day 15-16: Advanced Analysis Features
**Files to Create:**
- `src/repomap_tool/dependencies/graph_visualizer.py` (optional)
- `src/repomap_tool/dependencies/dependency_metrics.py`

**Advanced Metrics:**
```python
class DependencyMetrics:
    def __init__(self, graph: AdvancedDependencyGraph):
        self.graph = graph
    
    def calculate_coupling_metrics(self) -> Dict[str, float]:
        """Calculate afferent/efferent coupling for each file"""
        
    def calculate_cohesion_metrics(self) -> Dict[str, float]:
        """Calculate internal cohesion of modules"""
        
    def identify_hotspots(self) -> List[str]:
        """Identify files that are dependency hotspots"""
        
    def suggest_refactoring_opportunities(self) -> List[RefactoringOpportunity]:
        """Suggest files that might benefit from refactoring"""
```

#### Day 17-18: CLI and API Integration
**CLI Enhancements:**
```bash
# New dependency-related commands
repomap-tool analyze-dependencies /path/to/project
repomap-tool show-centrality /path/to/project --file auth.py
repomap-tool impact-analysis /path/to/project --files auth.py,user.py
repomap-tool find-cycles /path/to/project
repomap-tool dependency-metrics /path/to/project
```

**API Enhancements:**
```python
# New endpoints
POST /dependencies/analyze
POST /dependencies/impact-analysis
GET /dependencies/centrality/{project_id}
GET /dependencies/cycles/{project_id}
GET /dependencies/metrics/{project_id}
```

#### Day 19-21: Testing and Documentation
**Comprehensive Testing:**
- Unit tests for all dependency analysis components
- Integration tests with context awareness
- Performance benchmarks
- Large codebase testing

## Configuration Changes

### New Dependency Config
```python
class DependencyConfig(BaseModel):
    enabled: bool = True
    cache_graphs: bool = True
    max_graph_size: int = 10000  # files
    enable_call_graph: bool = True
    enable_impact_analysis: bool = True
    centrality_algorithms: List[str] = ["degree", "betweenness", "pagerank"]
    
class RepoMapConfig(BaseModel):
    # ... existing fields ...
    dependencies: DependencyConfig = DependencyConfig()
```

## Integration with DockerRepoMap

### Enhanced Core Class
```python
class DockerRepoMap:
    def __init__(self, config: RepoMapConfig):
        # ... existing code ...
        
        # Add dependency analysis
        if config.dependencies.enabled:
            self.dependency_graph = AdvancedDependencyGraph()
            self.impact_analyzer = ImpactAnalyzer(self.dependency_graph)
            self._build_dependency_graph()
    
    def _build_dependency_graph(self):
        """Build dependency graph for the project"""
        project_files = self.get_project_files()
        self.dependency_graph.build_graph(project_files)
    
    def get_dependency_enhanced_trees(
        self, 
        session_id: str,
        intent: str, 
        current_files: List[str] = None
    ) -> List[ExplorationTree]:
        """Generate enhanced exploration trees with dependency intelligence"""
        # Use enhanced entrypoint discovery (Phase 1 + Phase 2)
        enhanced_discoverer = EnhancedEntrypointDiscoverer(self, self.dependency_graph)
        entrypoints = enhanced_discoverer.discover_entrypoints(self.config.project_root, intent)
        
        # Use enhanced tree builder (Phase 1 + Phase 2)
        enhanced_builder = EnhancedTreeBuilder(self, self.dependency_graph)
        trees = []
        for entrypoint in entrypoints:
            tree = enhanced_builder.build_exploration_tree(entrypoint)
            trees.append(tree)
        
        return trees
```

## Success Metrics

### Functional Metrics
- [ ] Dependency graph construction for 1000+ file projects in < 30 seconds
- [ ] Centrality calculation accuracy verified against known graph algorithms
- [ ] Impact analysis identifies 90%+ of actually affected files
- [ ] Memory usage scales linearly with project size
- [ ] Cache hit rate > 80% for repeated analyses

### Quality Metrics
- [ ] Circular dependency detection accuracy > 95%
- [ ] File importance ranking correlates with developer intuition
- [ ] Breaking change risk assessment reduces actual breaking changes
- [ ] Test suggestion accuracy > 70%

## Risk Mitigation

### Technical Risks
- **Large Graph Performance:** Implement incremental updates and caching
- **Memory Usage:** Use efficient graph representations, lazy loading
- **Complex Dependency Resolution:** Start with simple cases, add complexity gradually

### Mitigation Strategies
- Progressive complexity (start with imports, add calls later)
- Extensive caching and optimization
- Configurable feature levels (basic → advanced)
- Performance monitoring and alerts

## Dependencies

### New Dependencies
```toml
# Add to pyproject.toml
networkx = "^3.1"        # Graph algorithms
ast = "^3.8"             # Python AST parsing
esprima = "^4.0"         # JavaScript parsing
tree_sitter = "^0.20"    # Multi-language parsing
```

### External Tools (Optional)
- Language-specific AST parsers
- Graph visualization libraries (for optional features)

## Definition of Done

### Phase 2 Complete When:
- [ ] Dependency graph builds for multi-language projects
- [ ] Import analysis handles all major languages (Python, JS, TS, Java, Go)
- [ ] Function call graph analysis works within and across files
- [ ] Centrality calculations provide meaningful file importance rankings
- [ ] Impact analysis accurately predicts change effects
- [ ] Integration with Phase 1 context awareness works seamlessly
- [ ] Performance meets targets (< 30s for 1000 files)
- [ ] Memory usage is reasonable (< 1GB for large projects)
- [ ] CLI and API provide full dependency analysis features
- [ ] Test coverage > 90%
- [ ] Documentation complete with examples
- [ ] Cache system reduces repeated analysis time by 80%+

This phase will provide the "intelligence" layer that makes repomap generation truly smart about code relationships and importance.

