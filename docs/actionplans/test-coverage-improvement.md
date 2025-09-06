# Test Coverage Improvement Action Plan

**Priority**: High  
**Timeline**: 2-3 weeks  
**Status**: 🔄 PENDING

## 🎯 **Objective**

Increase test coverage from 53% to 70%+ while ensuring **real quality improvements** through negative metrics that prevent cheating and focus on non-trivial, non-happy-path scenarios.

## 🚨 **Current State Analysis**

### **Coverage Gaps by Module**
- **llm/ modules**: 16-24% coverage (CRITICAL)
- **trees/ modules**: 13-27% coverage (CRITICAL) 
- **dependencies/ modules**: 38-66% coverage (HIGH)
- **core/ modules**: 51-100% coverage (MIXED)

### **Root Cause: Over-Mocking Problem**
Current tests often mock core functionality, providing false confidence. We need **real integration testing** with actual code paths.

## 🎯 **Success Criteria (Negative Metrics)**

### **❌ What We DON'T Want (Anti-Patterns)**

#### **1. Fake Coverage (AVOID)**
```python
# BAD: Mocking everything to achieve coverage
@patch('repomap_tool.core.repo_map.DockerRepoMap')
@patch('repomap_tool.matchers.fuzzy_matcher.FuzzyMatcher')
def test_search_function_mocked_everything(mock_repo, mock_matcher):
    # This gives 100% coverage but tests nothing real!
    mock_repo.return_value.search.return_value = [{"fake": "result"}]
    result = search_function("test")
    assert result == [{"fake": "result"}]
```

#### **2. Happy-Path Only Testing (AVOID)**
```python
# BAD: Only testing the easy cases
def test_analyze_file_success():
    # Only tests when everything works perfectly
    result = analyze_file("simple_file.py")
    assert result.success == True
```

#### **3. Trivial Test Cases (AVOID)**
```python
# BAD: Testing obvious functionality
def test_get_cache_size():
    cache = CacheManager()
    assert cache.get_size() == 0  # Too trivial!
```

### **✅ What We DO Want (Quality Patterns)**

#### **1. Real Integration Testing**
```python
# GOOD: Testing actual functionality with real data
def test_llm_context_selector_with_real_codebase():
    """Test context selection with actual Python files"""
    selector = ContextSelector()
    
    # Use real project files, not mocks
    test_files = [
        "src/repomap_tool/core/repo_map.py",
        "src/repomap_tool/matchers/fuzzy_matcher.py"
    ]
    
    # Test with real file content
    context = selector.select_context("search functionality", test_files)
    
    # Verify real behavior, not mocked responses
    assert len(context.selected_lines) > 0
    assert any("search" in line.lower() for line in context.selected_lines)
    assert context.token_count < context.max_tokens
```

#### **2. Comprehensive Error Scenario Testing**
```python
# GOOD: Testing failure modes and edge cases
def test_tree_builder_with_corrupted_files():
    """Test tree building with various file corruption scenarios"""
    builder = TreeBuilder()
    
    # Test with corrupted files
    corrupted_scenarios = [
        "file_with_syntax_errors.py",
        "file_with_encoding_issues.py", 
        "file_with_circular_imports.py",
        "file_with_missing_dependencies.py"
    ]
    
    for scenario in corrupted_scenarios:
        # Should handle gracefully, not crash
        result = builder.build_tree(scenario)
        assert result is not None
        assert result.error_count > 0  # Should detect errors
        assert result.partial_tree is not None  # Should provide partial results
```

#### **3. Non-Trivial Business Logic Testing**
```python
# GOOD: Testing complex algorithms and edge cases
def test_dependency_graph_cycle_detection_complex():
    """Test cycle detection with complex dependency patterns"""
    graph = AdvancedDependencyGraph()
    
    # Build complex dependency chain
    files = {
        "auth.py": ["user.py", "permissions.py"],
        "user.py": ["database.py", "auth.py"],  # Creates cycle
        "permissions.py": ["auth.py"],  # Another cycle
        "database.py": ["models.py"]
    }
    
    for file, deps in files.items():
        graph.add_file(file, deps)
    
    # Test complex cycle detection
    cycles = graph.find_cycles()
    assert len(cycles) >= 2  # Should find multiple cycles
    assert any("auth.py" in cycle for cycle in cycles)
    
    # Test impact analysis
    impact = graph.analyze_change_impact("auth.py")
    assert impact.affected_files >= 3  # Should affect multiple files
    assert impact.risk_score > 0.7  # High risk due to cycles
```

## 📋 **Detailed Action Items**

### **Phase 1: LLM Module Testing (Week 1)**

#### **1.1 Context Selector Testing**
**Target**: Increase from 17% to 70% coverage

**Real Test Scenarios**:
- [ ] Test with actual Python files (not mocked)
- [ ] Test token limit handling with large files
- [ ] Test context selection with malformed code
- [ ] Test with files containing special characters/Unicode
- [ ] Test performance with 1000+ line files

**Negative Metrics**:
- ❌ **NO** tests that mock `ContextSelector.select_context()`
- ❌ **NO** tests with hardcoded responses
- ❌ **NO** tests that only verify return types

**Success Criteria**:
- ✅ **At least 5** tests with real file content
- ✅ **At least 3** tests with error conditions
- ✅ **At least 2** tests with performance constraints

#### **1.2 Critical Line Extractor Testing**
**Target**: Increase from 23% to 70% coverage

**Real Test Scenarios**:
- [ ] Test extraction from actual code with complex logic
- [ ] Test with files containing multiple function definitions
- [ ] Test with files containing class hierarchies
- [ ] Test with files containing decorators and annotations
- [ ] Test with files containing async/await patterns

**Negative Metrics**:
- ❌ **NO** tests that mock file reading
- ❌ **NO** tests with simplified code samples
- ❌ **NO** tests that only check line counts

**Success Criteria**:
- ✅ **At least 4** tests with real Python files
- ✅ **At least 3** tests with complex code structures
- ✅ **At least 2** tests with edge cases (empty files, single-line files)

### **Phase 2: Trees Module Testing (Week 2)**

#### **2.1 Tree Builder Testing**
**Target**: Increase from 18% to 70% coverage

**Real Test Scenarios**:
- [ ] Test building trees from actual project structure
- [ ] Test with projects containing symlinks
- [ ] Test with projects containing binary files
- [ ] Test with projects containing deeply nested directories
- [ ] Test with projects containing circular dependencies

**Negative Metrics**:
- ❌ **NO** tests that mock file system operations
- ❌ **NO** tests with artificial directory structures
- ❌ **NO** tests that only verify tree structure without content

**Success Criteria**:
- ✅ **At least 3** tests with real project structures
- ✅ **At least 2** tests with error conditions
- ✅ **At least 2** tests with performance constraints

#### **2.2 Session Manager Testing**
**Target**: Increase from 27% to 70% coverage

**Real Test Scenarios**:
- [ ] Test session persistence with actual file I/O
- [ ] Test session loading with corrupted session files
- [ ] Test session management with concurrent access
- [ ] Test session cleanup with large session data
- [ ] Test session migration between versions

**Negative Metrics**:
- ❌ **NO** tests that mock file I/O operations
- ❌ **NO** tests with in-memory only sessions
- ❌ **NO** tests that only verify session creation

**Success Criteria**:
- ✅ **At least 3** tests with real file persistence
- ✅ **At least 2** tests with error recovery
- ✅ **At least 2** tests with concurrent access scenarios

### **Phase 3: Dependencies Module Testing (Week 3)**

#### **3.1 Advanced Dependency Graph Testing**
**Target**: Increase from 55% to 70% coverage

**Real Test Scenarios**:
- [ ] Test with actual Python import statements
- [ ] Test with complex dependency chains (10+ levels)
- [ ] Test with circular dependency detection
- [ ] Test with missing dependency handling
- [ ] Test with dynamic import scenarios

**Negative Metrics**:
- ❌ **NO** tests that mock import analysis
- ❌ **NO** tests with simplified dependency graphs
- ❌ **NO** tests that only verify graph structure

**Success Criteria**:
- ✅ **At least 4** tests with real import analysis
- ✅ **At least 3** tests with complex dependency scenarios
- ✅ **At least 2** tests with error conditions

## 🚨 **Anti-Cheating Measures**

### **1. Coverage Quality Gates**
```python
# REQUIRED: Each test must include these checks
def test_quality_gate():
    """Template for quality test validation"""
    
    # 1. Must test real functionality, not mocks
    assert not any("mock" in str(type(obj)) for obj in locals().values())
    
    # 2. Must test error conditions
    try:
        result = function_under_test(invalid_input)
        assert result.error_handled == True
    except Exception:
        pass  # Expected for error testing
    
    # 3. Must test non-trivial scenarios
    assert len(test_data) > 5  # Not just trivial cases
    assert any(complex_condition for item in test_data)
```

### **2. Integration Test Requirements**
- **At least 30%** of new tests must be integration tests
- **At least 20%** of new tests must test error conditions
- **At least 15%** of new tests must test performance constraints
- **At least 10%** of new tests must test edge cases

### **3. Code Review Checklist**
- [ ] Does this test use real data/files?
- [ ] Does this test cover error conditions?
- [ ] Does this test verify actual behavior, not just return types?
- [ ] Does this test add meaningful coverage to uncovered code paths?
- [ ] Does this test prevent regression of real bugs?

## 📊 **Success Metrics (Negative Approach)**

### **Coverage Targets**
- **Overall coverage**: 70%+ (up from 53%)
- **llm/ modules**: 70%+ (up from 16-24%)
- **trees/ modules**: 70%+ (up from 13-27%)
- **dependencies/ modules**: 70%+ (up from 38-66%)

### **Quality Metrics**
- **Integration test ratio**: ≥30% of new tests
- **Error condition coverage**: ≥20% of new tests
- **Real data usage**: ≥80% of new tests
- **Mock usage**: ≤20% of new tests (only for external dependencies)

### **Anti-Cheating Validation**
- **No tests that only mock core functionality**
- **No tests that only verify return types**
- **No tests with hardcoded responses**
- **No tests that skip error conditions**

## 🎯 **Deliverables**

1. **Week 1**: LLM module tests with 70%+ coverage
2. **Week 2**: Trees module tests with 70%+ coverage  
3. **Week 3**: Dependencies module tests with 70%+ coverage
4. **Final**: Overall coverage report with quality metrics

## 🚨 **Failure Conditions**

This action plan **FAILS** if:
- Coverage increases but tests are mostly mocked
- Tests only cover happy paths
- Tests don't use real data/files
- Integration test ratio is below 30%
- Error condition coverage is below 20%

## 📝 **Next Steps**

1. **Review current test patterns** to identify over-mocking
2. **Create test templates** with quality gates
3. **Set up coverage tracking** with quality metrics
4. **Begin Phase 1** with LLM module testing
5. **Weekly reviews** to ensure quality standards
