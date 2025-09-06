# Large Files Refactoring Action Plan

**Priority**: High  
**Timeline**: 2-3 weeks  
**Status**: 🔄 PENDING

## 🎯 **Objective**

Break down large files into focused, maintainable modules while ensuring **real architectural improvements** through negative metrics that prevent superficial refactoring and focus on meaningful separation of concerns.

## 🚨 **Current State Analysis**

### **Problem Files**
- **`cli.py`**: 1,832 lines (CRITICAL - should be <300 lines)
- **`core/repo_map.py`**: 815 lines (HIGH - should be <200 lines)
- **`dependencies/advanced_dependency_graph.py`**: 611 lines (MEDIUM - should be <300 lines)
- **`llm/signature_enhancer.py`**: 564 lines (MEDIUM - should be <300 lines)
- **`llm/critical_line_extractor.py`**: 603 lines (MEDIUM - should be <300 lines)

### **Root Cause: Monolithic Design**
Large files contain multiple responsibilities, making them hard to test, maintain, and extend.

## 🎯 **Success Criteria (Negative Metrics)**

### **❌ What We DON'T Want (Anti-Patterns)**

#### **1. Superficial Refactoring (AVOID)**
```python
# BAD: Just moving code around without real separation
# Before: cli.py (1832 lines)
# After: cli.py (200 lines) + cli_helpers.py (1632 lines)
# This doesn't improve architecture, just moves the problem!

# BAD: Creating modules that are still tightly coupled
class CLIMain:
    def __init__(self):
        self.helpers = CLIHelpers()  # Still monolithic
        self.utils = CLIUtils()      # Still monolithic
        self.display = CLIDisplay()  # Still monolithic
```

#### **2. Artificial Separation (AVOID)**
```python
# BAD: Separating by arbitrary criteria (e.g., line count)
# cli_commands_1.py, cli_commands_2.py, cli_commands_3.py
# This creates confusion and doesn't improve maintainability

# BAD: Creating modules with no clear responsibility
class CLIMiscellaneous:
    """Contains random CLI functions that don't fit elsewhere"""
    def handle_random_case_1(self): pass
    def handle_random_case_2(self): pass
    def handle_random_case_3(self): pass
```

#### **3. Over-Abstraction (AVOID)**
```python
# BAD: Creating too many layers of abstraction
class CLICommandFactory:
    def create_command(self, type):
        return CLICommandBuilder().with_type(type).build()

class CLICommandBuilder:
    def with_type(self, type):
        return CLICommandValidator().validate_type(type)

class CLICommandValidator:
    def validate_type(self, type):
        return CLICommandExecutor().execute_type(type)
# This makes simple operations complex!
```

### **✅ What We DO Want (Quality Patterns)**

#### **1. Domain-Driven Separation**
```python
# GOOD: Separating by business domain and responsibility
# cli/commands/analyze.py - Analysis-related commands
class AnalyzeCommand:
    """Handles all analysis-related CLI commands"""
    def __init__(self, analyzer: ProjectAnalyzer, formatter: OutputFormatter):
        self.analyzer = analyzer
        self.formatter = formatter
    
    def execute_analyze(self, args):
        """Execute project analysis with proper error handling"""
        try:
            result = self.analyzer.analyze_project(args.project_path)
            return self.formatter.format_analysis_result(result)
        except AnalysisError as e:
            return self.formatter.format_error(e)

# cli/commands/search.py - Search-related commands  
class SearchCommand:
    """Handles all search-related CLI commands"""
    def __init__(self, search_engine: SearchEngine, formatter: OutputFormatter):
        self.search_engine = search_engine
        self.formatter = formatter
    
    def execute_search(self, args):
        """Execute search with proper error handling"""
        try:
            result = self.search_engine.search(args.query, args.options)
            return self.formatter.format_search_result(result)
        except SearchError as e:
            return self.formatter.format_error(e)
```

#### **2. Single Responsibility Principle**
```python
# GOOD: Each module has one clear responsibility
# cli/output/formatters.py - Only handles output formatting
class OutputFormatter:
    """Handles all output formatting logic"""
    def format_analysis_result(self, result: AnalysisResult) -> str:
        """Format analysis results for display"""
        if result.format == "json":
            return self._format_json(result)
        elif result.format == "table":
            return self._format_table(result)
        else:
            return self._format_text(result)
    
    def format_error(self, error: Exception) -> str:
        """Format error messages consistently"""
        return f"Error: {error.message}\nDetails: {error.details}"

# cli/output/validators.py - Only handles input validation
class InputValidator:
    """Handles all input validation logic"""
    def validate_project_path(self, path: str) -> ValidationResult:
        """Validate project path input"""
        if not path:
            return ValidationResult.error("Project path is required")
        if not os.path.exists(path):
            return ValidationResult.error("Project path does not exist")
        return ValidationResult.success()
```

#### **3. Dependency Injection**
```python
# GOOD: Dependencies are injected, not created internally
class CLIMain:
    """Main CLI orchestrator with injected dependencies"""
    def __init__(
        self,
        analyze_command: AnalyzeCommand,
        search_command: SearchCommand,
        config_command: ConfigCommand,
        output_formatter: OutputFormatter,
        input_validator: InputValidator
    ):
        self.analyze_command = analyze_command
        self.search_command = search_command
        self.config_command = config_command
        self.output_formatter = output_formatter
        self.input_validator = input_validator
    
    def run(self, args):
        """Main CLI entry point"""
        # Validate inputs
        validation = self.input_validator.validate_all(args)
        if not validation.is_valid:
            return self.output_formatter.format_error(validation.error)
        
        # Route to appropriate command
        if args.command == "analyze":
            return self.analyze_command.execute_analyze(args)
        elif args.command == "search":
            return self.search_command.execute_search(args)
        # etc.
```

## 📋 **Detailed Action Items**

### **Phase 1: CLI Refactoring (Week 1)**

#### **1.1 Analyze Current CLI Structure**
**Target**: Break down 1,832-line `cli.py` into focused modules

**Current Analysis**:
```python
# Current cli.py contains:
# - Command definitions (analyze, search, config, etc.)
# - Output formatting (JSON, table, text)
# - Input validation
# - Error handling
# - Configuration loading
# - Progress display
# - Help text generation
```

**Refactoring Plan**:
```
cli/
├── __init__.py
├── main.py                    # Main CLI entry point (<100 lines)
├── commands/
│   ├── __init__.py
│   ├── analyze.py            # Analysis commands (<200 lines)
│   ├── search.py             # Search commands (<200 lines)
│   ├── config.py             # Configuration commands (<150 lines)
│   ├── explore.py            # Tree exploration commands (<200 lines)
│   └── dependencies.py       # Dependency analysis commands (<200 lines)
├── output/
│   ├── __init__.py
│   ├── formatters.py         # Output formatting (<300 lines)
│   ├── validators.py         # Input validation (<200 lines)
│   └── progress.py           # Progress display (<150 lines)
├── config/
│   ├── __init__.py
│   ├── loader.py             # Configuration loading (<150 lines)
│   └── validator.py          # Configuration validation (<100 lines)
└── utils/
    ├── __init__.py
    ├── error_handler.py      # Error handling (<100 lines)
    └── help_generator.py     # Help text generation (<150 lines)
```

**Negative Metrics**:
- ❌ **NO** modules larger than 300 lines
- ❌ **NO** modules with more than 3 responsibilities
- ❌ **NO** modules that import from more than 5 other modules
- ❌ **NO** circular dependencies between modules

**Success Criteria**:
- ✅ **At least 8** focused modules (not just 2-3 large ones)
- ✅ **At least 5** modules with single responsibility
- ✅ **At least 3** modules that can be tested independently
- ✅ **At least 2** modules that can be reused in other contexts

#### **1.2 Core RepoMap Refactoring**
**Target**: Break down 815-line `core/repo_map.py` into focused modules

**Current Analysis**:
```python
# Current repo_map.py contains:
# - Project scanning and file discovery
# - Identifier extraction and analysis
# - Search coordination
# - Cache management
# - Performance monitoring
# - Error handling and recovery
```

**Refactoring Plan**:
```
core/
├── __init__.py
├── repo_map.py               # Main orchestrator (<100 lines)
├── project_scanner.py        # File discovery and filtering (<200 lines)
├── identifier_extractor.py   # Identifier extraction (<200 lines)
├── search_coordinator.py     # Search coordination (<150 lines)
├── cache_manager.py          # Cache management (existing, <200 lines)
├── performance_monitor.py    # Performance monitoring (<150 lines)
└── error_recovery.py         # Error handling and recovery (<100 lines)
```

**Negative Metrics**:
- ❌ **NO** modules that handle both file operations and business logic
- ❌ **NO** modules that mix caching with core functionality
- ❌ **NO** modules that handle both input and output processing

**Success Criteria**:
- ✅ **At least 6** focused modules
- ✅ **At least 4** modules that can be tested in isolation
- ✅ **At least 3** modules that can be replaced with different implementations
- ✅ **At least 2** modules that can be used independently

### **Phase 2: Dependencies Module Refactoring (Week 2)**

#### **2.1 Advanced Dependency Graph Refactoring**
**Target**: Break down 611-line `dependencies/advanced_dependency_graph.py`

**Refactoring Plan**:
```
dependencies/
├── __init__.py
├── advanced_dependency_graph.py  # Main orchestrator (<150 lines)
├── graph_builder.py              # Graph construction (<200 lines)
├── cycle_detector.py             # Cycle detection algorithms (<150 lines)
├── centrality_calculator.py      # Centrality calculations (existing, <300 lines)
├── impact_analyzer.py            # Impact analysis (existing, <300 lines)
└── graph_visualizer.py           # Graph visualization (<200 lines)
```

**Negative Metrics**:
- ❌ **NO** modules that mix graph construction with analysis
- ❌ **NO** modules that handle both algorithms and data structures
- ❌ **NO** modules that mix visualization with computation

**Success Criteria**:
- ✅ **At least 5** focused modules
- ✅ **At least 3** modules that can be tested independently
- ✅ **At least 2** modules that can be optimized separately
- ✅ **At least 1** module that can be replaced with different algorithms

### **Phase 3: LLM Module Refactoring (Week 3)**

#### **3.1 Signature Enhancer Refactoring**
**Target**: Break down 564-line `llm/signature_enhancer.py`

**Refactoring Plan**:
```
llm/
├── __init__.py
├── signature_enhancer.py     # Main orchestrator (<150 lines)
├── signature_parser.py       # Signature parsing (<200 lines)
├── signature_analyzer.py     # Signature analysis (<200 lines)
├── signature_formatter.py    # Signature formatting (<150 lines)
└── signature_validator.py    # Signature validation (<100 lines)
```

**Negative Metrics**:
- ❌ **NO** modules that mix parsing with formatting
- ❌ **NO** modules that handle both validation and analysis
- ❌ **NO** modules that mix different types of signature processing

**Success Criteria**:
- ✅ **At least 4** focused modules
- ✅ **At least 3** modules that can be tested independently
- ✅ **At least 2** modules that can be reused for different signature types
- ✅ **At least 1** module that can be replaced with different algorithms

## 🚨 **Anti-Cheating Measures**

### **1. Responsibility Validation**
```python
# REQUIRED: Each module must have clear responsibility
class ModuleResponsibilityValidator:
    """Validates that modules have single responsibility"""
    
    def validate_module(self, module_path: str) -> ValidationResult:
        """Validate module has single responsibility"""
        
        # 1. Check method count (should be <20 for focused modules)
        method_count = self._count_methods(module_path)
        if method_count > 20:
            return ValidationResult.error(f"Too many methods: {method_count}")
        
        # 2. Check import count (should be <10 for focused modules)
        import_count = self._count_imports(module_path)
        if import_count > 10:
            return ValidationResult.error(f"Too many imports: {import_count}")
        
        # 3. Check responsibility keywords
        responsibilities = self._extract_responsibilities(module_path)
        if len(responsibilities) > 1:
            return ValidationResult.error(f"Multiple responsibilities: {responsibilities}")
        
        return ValidationResult.success()
```

### **2. Coupling Validation**
```python
# REQUIRED: Check for proper decoupling
class CouplingValidator:
    """Validates that modules are properly decoupled"""
    
    def validate_coupling(self, module_path: str) -> ValidationResult:
        """Validate module coupling"""
        
        # 1. Check for circular dependencies
        if self._has_circular_dependencies(module_path):
            return ValidationResult.error("Circular dependencies detected")
        
        # 2. Check for tight coupling
        coupling_score = self._calculate_coupling_score(module_path)
        if coupling_score > 0.7:  # High coupling
            return ValidationResult.error(f"High coupling score: {coupling_score}")
        
        # 3. Check for proper abstraction
        if not self._has_proper_abstraction(module_path):
            return ValidationResult.error("Missing proper abstraction")
        
        return ValidationResult.success()
```

### **3. Testability Validation**
```python
# REQUIRED: Each module must be independently testable
class TestabilityValidator:
    """Validates that modules can be tested independently"""
    
    def validate_testability(self, module_path: str) -> ValidationResult:
        """Validate module testability"""
        
        # 1. Check for dependency injection
        if not self._uses_dependency_injection(module_path):
            return ValidationResult.error("Missing dependency injection")
        
        # 2. Check for proper interfaces
        if not self._has_proper_interfaces(module_path):
            return ValidationResult.error("Missing proper interfaces")
        
        # 3. Check for testable methods
        testable_methods = self._count_testable_methods(module_path)
        total_methods = self._count_total_methods(module_path)
        if testable_methods / total_methods < 0.8:  # 80% testable
            return ValidationResult.error(f"Low testability: {testable_methods}/{total_methods}")
        
        return ValidationResult.success()
```

## 📊 **Success Metrics (Negative Approach)**

### **Size Targets**
- **cli.py**: <300 lines (down from 1,832)
- **core/repo_map.py**: <200 lines (down from 815)
- **dependencies/advanced_dependency_graph.py**: <300 lines (down from 611)
- **llm/signature_enhancer.py**: <300 lines (down from 564)
- **llm/critical_line_extractor.py**: <300 lines (down from 603)

### **Quality Metrics**
- **Module count**: ≥15 focused modules (up from 5 large ones)
- **Single responsibility**: ≥80% of modules
- **Independent testability**: ≥90% of modules
- **Reusability**: ≥60% of modules can be reused
- **Coupling score**: ≤0.3 (low coupling)

### **Anti-Cheating Validation**
- **No modules larger than 300 lines**
- **No modules with more than 3 responsibilities**
- **No circular dependencies**
- **No modules that can't be tested independently**
- **No modules that can't be reused**

## 🎯 **Deliverables**

1. **Week 1**: CLI refactoring with 8+ focused modules
2. **Week 2**: Core and Dependencies refactoring with 10+ focused modules
3. **Week 3**: LLM refactoring with 5+ focused modules
4. **Final**: Architecture review with coupling analysis

## 🚨 **Failure Conditions**

This action plan **FAILS** if:
- Files are just split by line count without real separation
- Modules still have multiple responsibilities
- Modules can't be tested independently
- Circular dependencies are introduced
- Coupling increases instead of decreases

## 📝 **Next Steps**

1. **Analyze current file responsibilities** to identify separation points
2. **Create module responsibility matrix** to ensure proper separation
3. **Set up coupling analysis tools** to measure architectural quality
4. **Begin Phase 1** with CLI refactoring
5. **Weekly architecture reviews** to ensure quality standards
