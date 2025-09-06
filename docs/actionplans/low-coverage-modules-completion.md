# Low-Coverage Modules Completion Action Plan

**Priority**: High  
**Timeline**: 3-4 weeks  
**Status**: 🔄 PENDING

## 🎯 **Objective**

Complete implementation of low-coverage modules while ensuring **real functionality delivery** through negative metrics that prevent fake implementations and focus on meaningful feature completion.

## 🚨 **Current State Analysis**

### **Critical Low-Coverage Modules**
- **`llm/context_selector.py`**: 17% coverage (CRITICAL)
- **`llm/critical_line_extractor.py`**: 23% coverage (CRITICAL)
- **`llm/hierarchical_formatter.py`**: 16% coverage (CRITICAL)
- **`llm/output_templates.py`**: 24% coverage (CRITICAL)
- **`llm/signature_enhancer.py`**: 16% coverage (CRITICAL)
- **`llm/token_optimizer.py`**: 19% coverage (CRITICAL)
- **`trees/session_manager.py`**: 27% coverage (HIGH)
- **`trees/tree_builder.py`**: 18% coverage (HIGH)
- **`trees/tree_clusters.py`**: 19% coverage (HIGH)
- **`trees/tree_manager.py`**: 17% coverage (HIGH)
- **`trees/tree_mapper.py`**: 13% coverage (HIGH)

### **Root Cause: Incomplete Implementation**
Low coverage indicates incomplete implementation rather than just missing tests. These modules have stub methods and placeholder logic.

## 🎯 **Success Criteria (Negative Metrics)**

### **❌ What We DON'T Want (Anti-Patterns)**

#### **1. Fake Implementation (AVOID)**
```python
# BAD: Fake implementation that just returns hardcoded values
class ContextSelector:
    def select_context(self, query: str, files: List[str]) -> Context:
        # This is fake - just returns hardcoded response
        return Context(
            selected_lines=["# This is a fake implementation"],
            token_count=10,
            relevance_score=0.8
        )
    
    def calculate_relevance(self, query: str, content: str) -> float:
        # This is fake - just returns random score
        return 0.7  # Always returns same score!
```

#### **2. Placeholder Logic (AVOID)**
```python
# BAD: Placeholder implementation that doesn't do real work
class TreeBuilder:
    def build_tree(self, entrypoint: str) -> Tree:
        # This is placeholder - doesn't actually build trees
        return Tree(
            root=TreeNode(name=entrypoint),
            nodes=[],  # Empty!
            relationships=[]  # Empty!
        )
    
    def expand_node(self, node: TreeNode) -> List[TreeNode]:
        # This is placeholder - doesn't actually expand
        return []  # Always returns empty!
```

#### **3. Mock-Dependent Implementation (AVOID)**
```python
# BAD: Implementation that depends on mocks for testing
class SessionManager:
    def __init__(self):
        self.storage = MockStorage()  # Uses mock in production!
    
    def save_session(self, session: Session) -> bool:
        # This won't work in real usage
        return self.storage.save(session)  # Mock storage!
```

### **✅ What We DO Want (Quality Patterns)**

#### **1. Real Implementation with Actual Logic**
```python
# GOOD: Real implementation with actual business logic
class ContextSelector:
    """Real context selection with actual relevance calculation"""
    
    def __init__(self, max_tokens: int = 4000, min_relevance: float = 0.3):
        self.max_tokens = max_tokens
        self.min_relevance = min_relevance
        self.tokenizer = Tokenizer()
    
    def select_context(self, query: str, files: List[str]) -> Context:
        """Select relevant context from files based on query"""
        if not query or not files:
            return Context.empty()
        
        # Real implementation: analyze each file
        file_scores = []
        for file_path in files:
            try:
                content = self._read_file(file_path)
                relevance = self._calculate_relevance(query, content)
                if relevance >= self.min_relevance:
                    file_scores.append((file_path, content, relevance))
            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                continue
        
        # Sort by relevance
        file_scores.sort(key=lambda x: x[2], reverse=True)
        
        # Select context within token limit
        selected_lines = []
        token_count = 0
        
        for file_path, content, relevance in file_scores:
            lines = content.split('\n')
            for line in lines:
                line_tokens = self.tokenizer.count_tokens(line)
                if token_count + line_tokens > self.max_tokens:
                    break
                selected_lines.append(line)
                token_count += line_tokens
            
            if token_count >= self.max_tokens:
                break
        
        return Context(
            selected_lines=selected_lines,
            token_count=token_count,
            relevance_score=file_scores[0][2] if file_scores else 0.0,
            source_files=[f[0] for f in file_scores[:5]]  # Top 5 files
        )
    
    def _calculate_relevance(self, query: str, content: str) -> float:
        """Calculate relevance score using TF-IDF and semantic similarity"""
        # Real implementation: use actual algorithms
        query_terms = set(query.lower().split())
        content_terms = set(content.lower().split())
        
        # Calculate term frequency
        term_freq = {}
        for term in content_terms:
            term_freq[term] = content.lower().count(term)
        
        # Calculate relevance score
        relevance = 0.0
        for term in query_terms:
            if term in term_freq:
                # TF-IDF-like scoring
                tf = term_freq[term] / len(content_terms)
                idf = math.log(len(content_terms) / (term_freq[term] + 1))
                relevance += tf * idf
        
        # Normalize score
        return min(relevance / len(query_terms), 1.0)
```

#### **2. Complete Business Logic Implementation**
```python
# GOOD: Complete implementation with all business logic
class TreeBuilder:
    """Real tree building with actual graph construction"""
    
    def __init__(self, max_depth: int = 10, max_nodes: int = 1000):
        self.max_depth = max_depth
        self.max_nodes = max_nodes
        self.parser = CodeParser()
        self.analyzer = DependencyAnalyzer()
    
    def build_tree(self, entrypoint: str) -> Tree:
        """Build exploration tree from entrypoint"""
        if not entrypoint or not os.path.exists(entrypoint):
            return Tree.empty()
        
        # Real implementation: build actual tree
        root = TreeNode(
            name=os.path.basename(entrypoint),
            path=entrypoint,
            node_type=self._determine_node_type(entrypoint),
            children=[],
            metadata=self._extract_metadata(entrypoint)
        )
        
        # Build tree recursively
        self._build_tree_recursive(root, 0)
        
        # Calculate tree statistics
        stats = self._calculate_tree_statistics(root)
        
        return Tree(
            root=root,
            nodes=self._collect_all_nodes(root),
            relationships=self._extract_relationships(root),
            statistics=stats,
            depth=self._calculate_depth(root),
            node_count=len(self._collect_all_nodes(root))
        )
    
    def _build_tree_recursive(self, node: TreeNode, depth: int) -> None:
        """Recursively build tree nodes"""
        if depth >= self.max_depth:
            return
        
        if len(self._collect_all_nodes(node)) >= self.max_nodes:
            return
        
        # Real implementation: analyze dependencies
        dependencies = self.analyzer.analyze_dependencies(node.path)
        
        for dep in dependencies:
            if dep.is_relevant and dep.path != node.path:
                child = TreeNode(
                    name=os.path.basename(dep.path),
                    path=dep.path,
                    node_type=dep.type,
                    children=[],
                    metadata=dep.metadata,
                    parent=node
                )
                
                node.children.append(child)
                
                # Recursively build children
                self._build_tree_recursive(child, depth + 1)
    
    def expand_node(self, node: TreeNode) -> List[TreeNode]:
        """Expand a specific node with its dependencies"""
        if not node or not os.path.exists(node.path):
            return []
        
        # Real implementation: analyze and expand
        dependencies = self.analyzer.analyze_dependencies(node.path)
        new_nodes = []
        
        for dep in dependencies:
            if dep.is_relevant and dep.path != node.path:
                # Check if node already exists
                if not self._node_exists_in_tree(node, dep.path):
                    new_node = TreeNode(
                        name=os.path.basename(dep.path),
                        path=dep.path,
                        node_type=dep.type,
                        children=[],
                        metadata=dep.metadata,
                        parent=node
                    )
                    new_nodes.append(new_node)
        
        return new_nodes
```

#### **3. Production-Ready Implementation**
```python
# GOOD: Production-ready implementation with proper error handling
class SessionManager:
    """Real session management with actual persistence"""
    
    def __init__(self, session_dir: str = ".repomap_sessions"):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
        self.active_sessions = {}
        self.lock = threading.Lock()
    
    def save_session(self, session: Session) -> bool:
        """Save session to disk with proper error handling"""
        try:
            with self.lock:
                # Real implementation: actual file I/O
                session_file = self.session_dir / f"{session.id}.json"
                
                # Serialize session data
                session_data = {
                    "id": session.id,
                    "project_path": session.project_path,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "exploration_trees": [
                        {
                            "name": tree.name,
                            "root_path": tree.root_path,
                            "nodes": self._serialize_nodes(tree.nodes),
                            "statistics": tree.statistics
                        }
                        for tree in session.exploration_trees
                    ],
                    "metadata": session.metadata
                }
                
                # Write to file with atomic operation
                temp_file = session_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                
                # Atomic rename
                temp_file.rename(session_file)
                
                # Update active sessions
                self.active_sessions[session.id] = session
                
                return True
                
        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session from disk with proper error handling"""
        try:
            with self.lock:
                # Check active sessions first
                if session_id in self.active_sessions:
                    return self.active_sessions[session_id]
                
                # Real implementation: actual file I/O
                session_file = self.session_dir / f"{session_id}.json"
                
                if not session_file.exists():
                    return None
                
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                # Deserialize session
                session = Session(
                    id=session_data["id"],
                    project_path=session_data["project_path"],
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    last_accessed=datetime.fromisoformat(session_data["last_accessed"]),
                    exploration_trees=[
                        self._deserialize_tree(tree_data)
                        for tree_data in session_data["exploration_trees"]
                    ],
                    metadata=session_data["metadata"]
                )
                
                # Update active sessions
                self.active_sessions[session_id] = session
                
                return session
                
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
```

## 📋 **Detailed Action Items**

### **Phase 1: LLM Modules Completion (Week 1-2)**

#### **1.1 Context Selector Implementation**
**Target**: Complete `llm/context_selector.py` (17% → 80% coverage)

**Current Issues**:
```python
# Current incomplete implementation
class ContextSelector:
    def select_context(self, query: str, files: List[str]) -> Context:
        # TODO: Implement real context selection
        return Context.empty()
    
    def calculate_relevance(self, query: str, content: str) -> float:
        # TODO: Implement relevance calculation
        return 0.5
```

**Completion Plan**:
- [ ] Implement real TF-IDF relevance calculation
- [ ] Implement token counting and limit handling
- [ ] Implement file content analysis
- [ ] Implement context ranking and selection
- [ ] Implement error handling for file operations
- [ ] Implement caching for performance

**Negative Metrics**:
- ❌ **NO** hardcoded return values
- ❌ **NO** placeholder TODO comments
- ❌ **NO** mock dependencies in production code
- ❌ **NO** methods that always return the same value

**Success Criteria**:
- ✅ **At least 5** real business logic methods
- ✅ **At least 3** error handling scenarios
- ✅ **At least 2** performance optimization features
- ✅ **At least 1** caching mechanism

#### **1.2 Critical Line Extractor Implementation**
**Target**: Complete `llm/critical_line_extractor.py` (23% → 80% coverage)

**Completion Plan**:
- [ ] Implement real code parsing and analysis
- [ ] Implement critical line identification algorithms
- [ ] Implement context-aware line extraction
- [ ] Implement syntax highlighting and formatting
- [ ] Implement error handling for malformed code
- [ ] Implement performance optimization for large files

**Negative Metrics**:
- ❌ **NO** simple line counting without analysis
- ❌ **NO** hardcoded line selection
- ❌ **NO** mock file parsing
- ❌ **NO** placeholder extraction logic

**Success Criteria**:
- ✅ **At least 4** real extraction algorithms
- ✅ **At least 3** code analysis features
- ✅ **At least 2** error handling scenarios
- ✅ **At least 1** performance optimization

### **Phase 2: Trees Modules Completion (Week 3-4)**

#### **2.1 Tree Builder Implementation**
**Target**: Complete `trees/tree_builder.py` (18% → 80% coverage)

**Completion Plan**:
- [ ] Implement real dependency analysis
- [ ] Implement tree construction algorithms
- [ ] Implement node expansion logic
- [ ] Implement tree statistics calculation
- [ ] Implement error handling for circular dependencies
- [ ] Implement performance optimization for large trees

**Negative Metrics**:
- ❌ **NO** empty tree structures
- ❌ **NO** hardcoded node relationships
- ❌ **NO** mock dependency analysis
- ❌ **NO** placeholder tree building

**Success Criteria**:
- ✅ **At least 5** real tree building methods
- ✅ **At least 3** dependency analysis features
- ✅ **At least 2** error handling scenarios
- ✅ **At least 1** performance optimization

#### **2.2 Session Manager Implementation**
**Target**: Complete `trees/session_manager.py` (27% → 80% coverage)

**Completion Plan**:
- [ ] Implement real file I/O operations
- [ ] Implement session serialization/deserialization
- [ ] Implement session persistence and loading
- [ ] Implement session cleanup and management
- [ ] Implement error handling for file operations
- [ ] Implement concurrent access handling

**Negative Metrics**:
- ❌ **NO** mock file operations
- ❌ **NO** in-memory only sessions
- ❌ **NO** placeholder persistence logic
- ❌ **NO** hardcoded session data

**Success Criteria**:
- ✅ **At least 4** real persistence methods
- ✅ **At least 3** error handling scenarios
- ✅ **At least 2** concurrent access features
- ✅ **At least 1** cleanup mechanism

## 🚨 **Anti-Cheating Measures**

### **1. Implementation Completeness Validation**
```python
# REQUIRED: Check that implementations are complete
class ImplementationCompletenessValidator:
    """Validates that implementations are complete and not fake"""
    
    def validate_implementation(self, module_path: str) -> ValidationResult:
        """Validate implementation completeness"""
        
        # 1. Check for TODO comments
        todo_count = self._count_todo_comments(module_path)
        if todo_count > 0:
            return ValidationResult.error(f"Found {todo_count} TODO comments")
        
        # 2. Check for hardcoded return values
        hardcoded_returns = self._count_hardcoded_returns(module_path)
        if hardcoded_returns > 2:  # Allow some constants
            return ValidationResult.error(f"Found {hardcoded_returns} hardcoded returns")
        
        # 3. Check for mock dependencies
        mock_dependencies = self._count_mock_dependencies(module_path)
        if mock_dependencies > 0:
            return ValidationResult.error(f"Found {mock_dependencies} mock dependencies")
        
        # 4. Check for placeholder logic
        placeholder_logic = self._count_placeholder_logic(module_path)
        if placeholder_logic > 0:
            return ValidationResult.error(f"Found {placeholder_logic} placeholder logic")
        
        return ValidationResult.success()
```

### **2. Business Logic Validation**
```python
# REQUIRED: Check that business logic is real
class BusinessLogicValidator:
    """Validates that business logic is real and not fake"""
    
    def validate_business_logic(self, module_path: str) -> ValidationResult:
        """Validate business logic implementation"""
        
        # 1. Check for algorithm complexity
        complexity_score = self._calculate_algorithm_complexity(module_path)
        if complexity_score < 0.3:  # Too simple, likely fake
            return ValidationResult.error(f"Algorithm complexity too low: {complexity_score}")
        
        # 2. Check for real data processing
        data_processing = self._count_data_processing_operations(module_path)
        if data_processing < 3:  # Should have real data processing
            return ValidationResult.error(f"Insufficient data processing: {data_processing}")
        
        # 3. Check for error handling
        error_handling = self._count_error_handling(module_path)
        if error_handling < 2:  # Should have error handling
            return ValidationResult.error(f"Insufficient error handling: {error_handling}")
        
        return ValidationResult.success()
```

### **3. Production Readiness Validation**
```python
# REQUIRED: Check that implementation is production-ready
class ProductionReadinessValidator:
    """Validates that implementation is production-ready"""
    
    def validate_production_readiness(self, module_path: str) -> ValidationResult:
        """Validate production readiness"""
        
        # 1. Check for proper error handling
        error_handling_coverage = self._calculate_error_handling_coverage(module_path)
        if error_handling_coverage < 0.7:  # 70% coverage
            return ValidationResult.error(f"Low error handling coverage: {error_handling_coverage}")
        
        # 2. Check for performance considerations
        performance_features = self._count_performance_features(module_path)
        if performance_features < 1:  # Should have performance features
            return ValidationResult.error(f"No performance features: {performance_features}")
        
        # 3. Check for logging
        logging_coverage = self._calculate_logging_coverage(module_path)
        if logging_coverage < 0.5:  # 50% coverage
            return ValidationResult.error(f"Low logging coverage: {logging_coverage}")
        
        return ValidationResult.success()
```

## 📊 **Success Metrics (Negative Approach)**

### **Coverage Targets**
- **llm/context_selector.py**: 80%+ (up from 17%)
- **llm/critical_line_extractor.py**: 80%+ (up from 23%)
- **llm/hierarchical_formatter.py**: 80%+ (up from 16%)
- **llm/output_templates.py**: 80%+ (up from 24%)
- **llm/signature_enhancer.py**: 80%+ (up from 16%)
- **llm/token_optimizer.py**: 80%+ (up from 19%)
- **trees/session_manager.py**: 80%+ (up from 27%)
- **trees/tree_builder.py**: 80%+ (up from 18%)
- **trees/tree_clusters.py**: 80%+ (up from 19%)
- **trees/tree_manager.py**: 80%+ (up from 17%)
- **trees/tree_mapper.py**: 80%+ (up from 13%)

### **Implementation Quality**
- **TODO comments**: 0 (down from 20+)
- **Hardcoded returns**: ≤2 per module (down from 5+)
- **Mock dependencies**: 0 (down from 3+)
- **Placeholder logic**: 0 (down from 10+)

### **Business Logic Completeness**
- **Real algorithms**: ≥15 (up from 3)
- **Error handling**: ≥20 (up from 5)
- **Performance features**: ≥8 (up from 1)
- **Data processing**: ≥25 (up from 8)

### **Anti-Cheating Validation**
- **No fake implementations**
- **No placeholder logic**
- **No mock dependencies in production**
- **No hardcoded business logic**

## 🎯 **Deliverables**

1. **Week 1-2**: LLM modules completion with real implementations
2. **Week 3-4**: Trees modules completion with real implementations
3. **Final**: Implementation completeness report with quality metrics

## 🚨 **Failure Conditions**

This action plan **FAILS** if:
- Implementations are still fake or placeholder
- Business logic is not real
- Error handling is insufficient
- Performance considerations are missing
- Production readiness is not achieved

## 📝 **Next Steps**

1. **Audit current implementations** to identify incomplete code
2. **Create implementation templates** for common patterns
3. **Set up completeness validation** to prevent regression
4. **Begin Phase 1** with LLM modules completion
5. **Weekly implementation reviews** to ensure quality standards
