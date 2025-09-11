# Phase 1B: Collaborative Context Awareness Enhancement - CANCELLED

## Overview
**Goal:** Add collaborative context awareness as an enhancement layer on top of Phase 1 tree exploration, allowing LLMs to semantically augment exploration points for richer understanding.

**Duration:** 1-2 weeks  
**Effort:** Low-Medium  
**Impact:** Medium  
**Priority:** CANCELLED - Unrealistic and Over-engineered  
**Status:** ❌ CANCELLED (January 2025)

## 🚨 **CANCELLATION REASON**

This action plan was cancelled because it was **unrealistic and over-engineered**:

### **Why It Was Cancelled:**
- **Over-complexity**: Required sophisticated AI/ML features beyond scope
- **Unclear ROI**: Benefits were speculative, not proven
- **Scope creep**: Beyond essential repomap functionality
- **Current tool is already effective**: Dependency analysis and centrality scoring already provide intelligent prioritization

### **Alternative Approach:**
Focus on **practical improvements** that build on existing solid foundation:
- Performance optimization (current priority)
- Architecture cleanup
- Simple real-time features

## Current State vs Target State

### Current State (After Phase 1)
- Tree-based exploration with structural understanding
- Session management and tree manipulation
- Tree mapping generates focused repomaps
- No LLM semantic enhancement of exploration points

### Target State (Phase 1B Enhancement)
- **Collaborative Discovery:** LLM adds semantic layer to tree exploration
- **Exploration Point Augmentation:** LLM enriches tree nodes with understanding
- **Context-Enhanced Mapping:** Maps include both structure and semantic insights
- **Guided Expansion:** LLM insights suggest intelligent tree expansions
- **Semantic Memory:** LLM augmentations persist across sessions

## Technical Architecture

### New Components to Add

```
src/repomap_tool/context/
├── __init__.py
├── augmentation_points.py      # Identify tree nodes for LLM augmentation
├── semantic_layer.py           # Handle LLM semantic augmentations
├── context_mapper.py           # Generate context-enhanced maps
└── expansion_guide.py          # LLM-guided expansion suggestions
```

### Core Classes to Implement

```python
class AugmentationPointIdentifier:
    """Identifies tree nodes ready for LLM semantic enhancement"""
    
class SemanticAugmentation:
    """Stores LLM's semantic understanding of tree nodes"""
    
class ContextEnhancedMapper:
    """Generates maps with both tree structure and LLM insights"""
    
class ExpansionGuide:
    """Provides LLM-guided expansion suggestions based on augmentations"""
```

## Implementation Plan

### Week 1: Collaborative Discovery Infrastructure

#### Day 1-2: Session Management & Discovery Engine
**Files to Create:**
- `src/repomap_tool/collaborative/__init__.py`
- `src/repomap_tool/collaborative/session_manager.py`
- `src/repomap_tool/collaborative/discovery_engine.py`

**Session Management (External Control):**
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
        
    def get_or_create_session(self, session_id: str, project_path: str) -> Session:
        """Get existing session or create new one"""
        session = self.session_store.load_session(session_id)
        if not session:
            session = Session(session_id, project_path)
        return session

class CollaborativeDiscovery:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        
    def discover_exploration_trees(self, project_path: str, intent: str) -> List[ExplorationTree]:
        """Discover multiple contextual trees for LLM to choose from"""
        # Smart entrypoint discovery
        entrypoints = self._discover_entrypoints_by_intent(intent, project_path)
        
        # Cluster entrypoints into logical trees
        tree_clusters = self._cluster_entrypoints_by_context(entrypoints)
        
        # Build exploration trees with augmentation points
        exploration_trees = []
        for cluster in tree_clusters:
            tree = self._build_exploration_tree(cluster)
            exploration_trees.append(tree)
            
        return exploration_trees
```

**Smart Entrypoint Discovery:**
```python
class EntrypointDiscoverer:
    def __init__(self):
        self.context_patterns = self._load_context_patterns()
        
    def discover_by_intent(self, intent: str, project_path: str) -> List[Entrypoint]:
        """Find entrypoints relevant to intent using existing semantic/fuzzy matching"""
        # Use existing semantic matcher for intent analysis
        intent_concepts = self._extract_concepts(intent)
        
        # Find functions/classes that match intent semantically
        all_symbols = self.repo_map.get_tags()
        relevant_symbols = []
        
        for symbol in all_symbols:
            # Use existing semantic matching infrastructure
            similarity = self.semantic_matcher.calculate_similarity(intent, symbol)
            if similarity > 0.6:
                relevant_symbols.append((symbol, similarity))
        
        # Group into entrypoints by context (frontend, backend, infrastructure)
        return self._group_into_contexts(relevant_symbols)
```

#### Day 3-4: Exploration Points & Tree Building
**Files to Create:**
- `src/repomap_tool/collaborative/exploration_points.py`
- `src/repomap_tool/collaborative/tree_builder.py`

**Exploration Points for LLM Augmentation:**
```python
class ExplorationPoint:
    """Represents a code point ready for LLM semantic enrichment"""
    def __init__(self, identifier: str, location: str):
        self.identifier = identifier  # function/class name
        self.location = location      # file:line
        self.structural_context: Dict = {}  # dependencies, calls, complexity
        self.llm_augmentation: Optional[SemanticAugmentation] = None
        self.augmentation_prompts: List[str] = []
        self.ready_for_augmentation: bool = True
        
class ExplorationTree:
    """A tree of exploration points for collaborative discovery"""
    def __init__(self, tree_id: str, context_name: str):
        self.tree_id = tree_id           # Auto-generated attention token
        self.context_name = context_name # "Frontend Auth Flow"
        self.entrypoints: List[ExplorationPoint] = []
        self.tree_structure: Dict = {}   # Hierarchical structure
        self.confidence: float = 0.0     # How well this matches intent
        self.layer_type: str = ""        # frontend, backend, infrastructure
        self.augmentation_status: str = "ready"  # ready, partial, complete

class TreeBuilder:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        
    def build_exploration_tree(self, entrypoint: Entrypoint, max_depth: int = 3) -> ExplorationTree:
        """Build tree from entrypoint with exploration points"""
        tree = ExplorationTree(
            tree_id=f"{entrypoint.context}_{uuid4().hex[:8]}",
            context_name=entrypoint.context_name
        )
        
        # Build tree structure using existing dependency analysis
        tree_structure = self._build_tree_structure(entrypoint, max_depth)
        
        # Convert tree nodes to exploration points
        exploration_points = self._create_exploration_points(tree_structure)
        
        tree.entrypoints = exploration_points
        tree.tree_structure = tree_structure
        
        return tree
```

#### Day 5: Semantic Augmentation System
**Files to Create:**
- `src/repomap_tool/collaborative/semantic_augmentation.py`

**LLM Semantic Augmentation:**
```python
class SemanticAugmentation:
    """Stores LLM's semantic understanding of exploration points"""
    def __init__(self):
        self.point_id: str = ""           # authenticate_user, verify_password, etc.
        self.llm_description: str = ""    # LLM's semantic understanding
        self.context_tags: List[str] = [] # ["security_critical", "error_prone"]
        self.suggested_expansions: List[str] = []  # Areas LLM thinks should be explored
        self.risk_assessment: str = ""    # LLM's risk analysis
        self.relationships: List[str] = [] # LLM-identified relationships
        self.confidence: float = 1.0      # LLM augmentation has high confidence
        self.timestamp: datetime = datetime.now()

class AugmentationManager:
    def __init__(self):
        self.session_manager = SessionManager()
        
    def add_augmentation(
        self, 
        session_id: str, 
        tree_id: str, 
        point_id: str, 
        augmentation: SemanticAugmentation
    ):
        """Add LLM semantic augmentation to exploration point"""
        session = self.session_manager.get_session(session_id)
        if session and tree_id in session.exploration_trees:
            tree = session.exploration_trees[tree_id]
            
            # Find exploration point and add augmentation
            for point in tree.entrypoints:
                if point.identifier == point_id:
                    point.llm_augmentation = augmentation
                    break
                    
            # Update tree augmentation status
            self._update_tree_augmentation_status(tree)
            self.session_manager.persist_session(session)
    
    def get_augmentation_prompts(self, exploration_point: ExplorationPoint) -> List[str]:
        """Generate prompts to help LLM augment exploration points"""
        return [
            f"What does {exploration_point.identifier} do in this context?",
            "What are the potential issues or risks here?",
            "How does this relate to other parts of the system?",
            "What would you want to explore deeper here?",
            "What security, performance, or reliability concerns exist?"
        ]
```

### Week 2: Collaborative Mapping and LLM Integration

#### Day 6-7: Collaborative Mapper
**Files to Create:**
- `src/repomap_tool/collaborative/collaborative_mapper.py`

**LLM-Enhanced Mapping:**
```python
class CollaborativeMapper:
    def __init__(self, repo_map: DockerRepoMap):
        self.repo_map = repo_map
        self.session_manager = SessionManager()
        self.augmentation_manager = AugmentationManager()
        
    def generate_exploration_tree_map(
        self, 
        session_id: str, 
        tree_id: str,
        include_augmentations: bool = True
    ) -> str:
        """Generate map for exploration tree with LLM augmentations"""
        
        session = self.session_manager.get_session(session_id)
        if not session or tree_id not in session.exploration_trees:
            return "❌ Tree not found"
            
        tree = session.exploration_trees[tree_id]
        
        # Generate base structural map
        base_map = self._generate_structural_map(tree)
        
        if include_augmentations:
            # Enhance with LLM semantic augmentations
            augmented_map = self._inject_llm_augmentations(base_map, tree)
            
            # Add LLM-guided expansion suggestions
            expansion_suggestions = self._generate_llm_guided_suggestions(tree)
            
            return f"{augmented_map}\n\n{expansion_suggestions}"
        
        return base_map
    
    def show_exploration_points(self, session_id: str, tree_id: str) -> str:
        """Show exploration points ready for LLM augmentation"""
        session = self.session_manager.get_session(session_id)
        tree = session.exploration_trees[tree_id]
        
        output = f"📍 Exploration Points for: {tree.context_name}\n\n"
        
        for point in tree.entrypoints:
            output += f"Point: {point.identifier}\n"
            output += f"Location: {point.location}\n"
            output += f"Status: {'✅ Augmented' if point.llm_augmentation else '⏳ Ready for augmentation'}\n"
            
            if not point.llm_augmentation:
                prompts = self.augmentation_manager.get_augmentation_prompts(point)
                output += "🤖 Augmentation prompts:\n"
                for i, prompt in enumerate(prompts, 1):
                    output += f"  {i}. {prompt}\n"
                output += f"\n💬 Use: repomap-tool augment {tree_id} --point \"{point.identifier}\" --semantic \"Your description\"\n"
            
            output += "\n"
            
        return output
```

#### Day 8-9: CLI Integration with Collaborative Discovery
**Files to Modify:**
- `src/repomap_tool/core/repo_map.py`
- `src/repomap_tool/cli.py`

**Enhanced DockerRepoMap:**
```python
class DockerRepoMap:
    def __init__(self, config: RepoMapConfig):
        # ... existing code ...
        
        # Add collaborative discovery
        if config.collaborative.enabled:
            from ..collaborative import CollaborativeDiscovery, CollaborativeMapper
            self.collaborative_discovery = CollaborativeDiscovery(self)
            self.collaborative_mapper = CollaborativeMapper(self)
            self.session_manager = SessionManager()
        else:
            self.collaborative_discovery = None

    def explore_with_collaboration(
        self, 
        project_path: str, 
        intent: str,
        session_id: Optional[str] = None
    ) -> List[ExplorationTree]:
        """Collaborative exploration: tool finds structure, LLM adds semantics"""
        if not self.collaborative_discovery:
            raise ValueError("Collaborative discovery not enabled")
            
        # Get or create session
        session_id = self.session_manager.get_session_id(session_id)
        session = self.session_manager.get_or_create_session(session_id, project_path)
        
        # Discover exploration trees
        exploration_trees = self.collaborative_discovery.discover_exploration_trees(
            project_path, intent
        )
        
        # Store trees in session
        for tree in exploration_trees:
            session.exploration_trees[tree.tree_id] = tree
            
        self.session_manager.persist_session(session)
        
        return exploration_trees
```

**New CLI Commands:**
```python
@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.argument("intent", type=str)
@click.option("--session", "-s", help="Session ID (or use REPOMAP_SESSION env var)")
def explore(project_path: str, intent: str, session: Optional[str]):
    """Collaborative exploration: discover structural trees for LLM augmentation"""
    
    session_id = session or os.environ.get('REPOMAP_SESSION')
    if not session_id:
        session_id = f"explore_{int(time.time())}"
        console.print(f"💡 No session specified, using: {session_id}")
        console.print(f"Set REPOMAP_SESSION={session_id} for subsequent commands")
    
    config = create_default_config(project_path)
    repo_map = DockerRepoMap(config)
    
    trees = repo_map.explore_with_collaboration(project_path, intent, session_id)
    
    console.print(f"🔍 Found {len(trees)} exploration contexts:")
    for tree in trees:
        console.print(f"  • {tree.context_name} [token: {tree.tree_id}] (confidence: {tree.confidence:.2f})")
        console.print(f"    {len(tree.entrypoints)} exploration points ready for augmentation")
    
    console.print(f"\n💡 Next steps:")
    console.print(f"  1. Show exploration points: repomap-tool show-points <tree_id>")
    console.print(f"  2. Focus on a tree: repomap-tool focus <tree_id>")
    console.print(f"  3. Augment points: repomap-tool augment <tree_id> --point <point> --semantic \"description\"")
```

#### Day 10: Complete CLI Command Set
**Complete Collaborative CLI Commands:**
```bash
# Core collaborative discovery
repomap-tool explore /project "intent description" [--session session_id]

# Show exploration points ready for LLM augmentation  
repomap-tool show-points <tree_id> [--session session_id]

# LLM adds semantic understanding to exploration points
repomap-tool augment <tree_id> --point <point_id> --semantic "LLM description" [--session session_id]

# Focus on specific exploration tree (stateful within session)
repomap-tool focus <tree_id> [--session session_id]

# Generate map with LLM augmentations
repomap-tool map [tree_id] [--session session_id] [--include-augmentations]

# LLM-guided expansion based on augmentations
repomap-tool expand <expansion_area> [--session session_id]

# Session management (external control)
repomap-tool status [--session session_id]  # Show current session status
repomap-tool list-trees [--session session_id]  # List exploration trees in session
```

**Example Collaborative Workflow:**
```bash
# 1. Set session (via environment variable)
export REPOMAP_SESSION="debug_auth_$(date +%s)"

# 2. Collaborative discovery
repomap-tool explore /project "authentication bugs"
# Output: Found 3 trees: auth_frontend_a1b2, auth_backend_c3d4, auth_errors_e5f6

# 3. Show exploration points for LLM augmentation
repomap-tool show-points auth_errors_e5f6
# Output: Shows structural context + augmentation prompts

# 4. LLM augments exploration points with semantic understanding
repomap-tool augment auth_errors_e5f6 --point "authenticate_user" \
  --semantic "Primary auth entry point. Handles credential validation, account lockouts, and database errors. Critical path for login bugs."

# 5. Focus on augmented tree
repomap-tool focus auth_errors_e5f6

# 6. Generate enhanced map with LLM insights
repomap-tool map
# Output: Structural map + LLM semantic understanding + guided expansion suggestions

# 7. LLM-guided expansion
repomap-tool expand "password_validation"  # Based on LLM's augmentation insights
```

### Week 3: Testing, Optimization, and Documentation

#### Day 11-12: Comprehensive Testing
**Files to Create:**
- `tests/unit/test_collaborative_discovery.py`
- `tests/unit/test_exploration_points.py`
- `tests/unit/test_semantic_augmentation.py`
- `tests/unit/test_session_manager.py`
- `tests/integration/test_collaborative_workflow.py`

**Test Coverage:**
- **Collaborative Discovery:** Entrypoint discovery, tree clustering, exploration point generation
- **Session Management:** External session control, state persistence, multi-session isolation
- **Semantic Augmentation:** LLM augmentation storage, retrieval, and integration
- **Tree Building:** Structural tree creation, exploration point identification
- **CLI Integration:** All collaborative commands, session parameter handling
- **Performance Impact:** Overhead of collaborative features vs baseline

#### Day 13-14: Performance Optimization
**Focus Areas:**
- Caching intent analysis results
- Optimizing relevance calculations
- Memory management for context history
- Response time optimization

#### Day 15: Documentation and Examples
**Files to Create:**
- `docs/CONTEXT_AWARENESS_GUIDE.md`
- `examples/context/context_aware_examples.sh`
- `examples/context/intent_patterns.json`

## API Changes

### New CLI Options
```bash
--enable-context         # Enable context awareness
--context-message TEXT   # Provide context message
--context-files LIST     # Specify current working files
--intent TYPE           # Manually specify intent
--max-context-history N  # Limit context history size
```

### New API Endpoints
```python
POST /repo-map/context-aware
{
    "project_path": "/path/to/project",
    "message": "I need to fix the authentication bug",
    "current_files": ["auth.py", "user.py"],
    "max_tokens": 1024
}

POST /context/analyze
{
    "message": "I'm working on user authentication"
}

GET /context/history/{project_id}
```

## Configuration Changes

### New Config Options
```python
class ContextConfig(BaseModel):
    enabled: bool = True
    max_history_size: int = 100
    intent_confidence_threshold: float = 0.7
    relevance_threshold: float = 0.5
    cache_intent_analysis: bool = True

class RepoMapConfig(BaseModel):
    # ... existing fields ...
    context: ContextConfig = ContextConfig()
```

## Success Metrics

### Functional Metrics
- [ ] Intent extraction accuracy > 85%
- [ ] Context-aware file ranking shows relevant files in top 5
- [ ] Response time increase < 20% over baseline
- [ ] Memory usage increase < 100MB

### User Experience Metrics
- [ ] Developers can find relevant code 3x faster
- [ ] Reduced need to manually specify files
- [ ] Improved relevance of suggested code
- [ ] Positive feedback on context awareness features

## Testing Strategy

### Unit Tests
```python
def test_intent_extraction():
    analyzer = IntentAnalyzer()
    
    # Test authentication intent
    result = analyzer.extract_intent("I need to fix the login bug")
    assert result.primary_intent == "authentication"
    assert "debugging" in result.action_types
    
def test_context_management():
    manager = ContextManager()
    
    # Test context updates
    manager.update_context("Working on auth", ["auth.py"])
    assert "authentication" in manager.current_context.focus_areas
```

### Integration Tests
```python
def test_context_aware_mapping():
    # Test full context-aware workflow
    mapper = ContextAwareMapper(repo_map)
    
    result = mapper.generate_context_aware_map(
        "I need to add password validation"
    )
    
    # Should prioritize auth-related files
    assert "auth.py" in result[:500]  # Should appear early
    assert "utils.py" not in result[:500]  # Should not be prioritized
```

## Migration Strategy

### Backward Compatibility
- All existing APIs continue to work
- Context awareness is opt-in via flags
- Fallback to existing behavior when context features disabled

### Gradual Rollout
1. **Week 1:** Core infrastructure (no user-facing changes)
2. **Week 2:** Optional CLI flags for testing
3. **Week 3:** Full integration with documentation

## Risk Mitigation

### Technical Risks
- **Performance Impact:** Implement caching and optimization
- **Accuracy Issues:** Start with conservative thresholds, tune based on feedback
- **Integration Complexity:** Thorough testing and gradual rollout

### Mitigation Strategies
- Feature flags for easy disable
- Comprehensive test coverage
- Performance monitoring
- User feedback collection

## Dependencies

### New Dependencies
```toml
# Add to pyproject.toml
nltk = "^3.8"           # For text processing
scikit-learn = "^1.3"   # For relevance scoring
```

### Internal Dependencies
- Existing DockerRepoMap infrastructure
- Current file scanning and symbol extraction
- Configuration management system

## Definition of Done

### Phase 1 Complete When:
- [ ] Intent analysis extracts correct intent 85%+ of the time
- [ ] Context manager maintains conversation state
- [ ] Relevance ranking prioritizes relevant files
- [ ] CLI integration provides context-aware commands
- [ ] API endpoints support context-aware mapping
- [ ] Performance impact < 20% increase
- [ ] Test coverage > 90%
- [ ] Documentation complete
- [ ] Examples demonstrate functionality

This foundation will enable the next phases (dependency analysis, LLM optimization) to build on a solid context-aware base.

