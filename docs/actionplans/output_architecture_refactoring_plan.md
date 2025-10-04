# Output Architecture Refactoring Action Plan

## 🎯 **Objective**
Clean up and standardize the fragmented output generation architecture in RepoMap-Tool to create a unified, maintainable, and extensible system.

## 📊 **Current State Analysis**

### **Problems Identified:**
1. **Fragmented Output Handling**: 66 direct `console.print()` calls across 6 CLI command files
2. **Inconsistent Format Support**: ✅ **RESOLVED** - Simplified to TEXT and JSON formats only
3. **Multiple Format Enum Systems**: ✅ **RESOLVED** - Unified to single AnalysisFormat enum
4. **Mixed Output Strategies**: Direct printing, formatter functions, and string returns
5. **Inconsistent Console Management**: Multiple ways to obtain console instances
6. **Duplicate Commands**: ✅ **RESOLVED** - `analyze` and `search` commands removed, consolidated into `inspect`
7. **Complex Template Configuration**: Inconsistent template config usage

### **Progress Update:**
- ✅ **Command Consolidation Complete**: Successfully removed `analyze` and `search` commands
- ✅ **Test Updates Complete**: All test files updated to reflect new command structure
- ✅ **Format Simplification Complete**: Reduced from 4 formats to 2 (TEXT and JSON)
- ✅ **Format Enum Unification**: Single AnalysisFormat enum used throughout
- ✅ **CLI Format Integration Complete**: All CLI commands now use simplified format system
- ✅ **Test Fixes Complete**: All 428 tests passing with 0 failures
- ✅ **Deep Scan Validation**: Comprehensive verification of format simplification
- ✅ **Action Plan Updated**: Documentation reflects current state

### **Phase 1.1 Implementation Details:**
- **Comprehensive Format System**: Created `src/repomap_tool/cli/output/formats.py` with full format management
- **OutputFormat Enum**: Defined unified `OutputFormat` enum with TEXT and JSON formats
- **FormatConverter Class**: Implemented comprehensive format conversion and validation utilities
- **OutputConfig Model**: Created Pydantic model for output configuration with validation
- **FormatRegistry System**: Built extensible registry for format capabilities and data type support
- **Utility Functions**: Added helper functions for format validation, conversion, and configuration
- **Test Coverage**: Created comprehensive test suite with 22 tests covering all functionality
- **Integration**: Updated `__init__.py` to expose new format system components

### **Format Simplification Details:**
- **Reduced Format Complexity**: From 4 formats (`LLM_OPTIMIZED`, `TABLE`, `MARKDOWN`, `JSON`) to 2 formats (`TEXT`, `JSON`)
- **Improved Naming**: `LLM_OPTIMIZED` renamed to `TEXT` for better user understanding
- **Unified Format System**: Single `AnalysisFormat` enum used throughout the codebase
- **CLI Integration**: All commands (`index create`, `inspect impact`, `inspect centrality`) now support only TEXT and JSON
- **Test Coverage**: All 428 tests updated and passing with new format system
- **Backward Compatibility**: Maintained functionality while simplifying interface

### **Architecture Issues:**
- **Separation of Concerns**: Formatters handle data formatting, console management, and Click context
- **Dependency Injection**: Inconsistent console DI patterns
- **Error Handling**: Inconsistent error output formatting
- **Testing**: Difficult to test due to tight coupling with console

## 🏗️ **Target Architecture**

### **Core Principles:**
1. **Single Responsibility**: Each component has one clear purpose
2. **Dependency Injection**: All dependencies injected, no direct instantiation
3. **Consistent Interface**: All formatters follow the same protocol
4. **Unified Format System**: Single format enum used throughout
5. **Centralized Management**: One output manager handles all output operations

### **New Architecture Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Commands                             │
│  (analyze, inspect, search, index, explore, system)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Output Manager                                 │
│  - Format validation                                        │
│  - Console management                                       │
│  - Template application                                     │
│  - Error handling                                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Formatter Registry                             │
│  - JSON Formatter                                           │
│  - Text Formatter                                           │
│  - Table Formatter                                          │
│  - Markdown Formatter                                       │
│  - LLM Optimized Formatter                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│              Template System                                │
│  - Project Templates                                        │
│  - Search Templates                                         │
│  - Analysis Templates                                       │
│  - Error Templates                                          │
└─────────────────────────────────────────────────────────────┘
```

## 📋 **Implementation Plan**

### **Phase 1: Foundation (Week 1)**

#### **1.1 Unified Format System** ✅ **COMPLETED**
- [x] Create `src/repomap_tool/cli/output/formats.py`
- [x] Define comprehensive `OutputFormat` enum
- [x] Create format validation utilities
- [x] Add format conversion helpers
- [x] **Interim Solution**: Simplified existing `AnalysisFormat` enum to TEXT and JSON
- [x] **Interim Solution**: Updated CLI commands to use simplified formats

```python
class OutputFormat(str, Enum):
    TEXT = "text"        # Rich, hierarchical, token-optimized format (default)
    JSON = "json"        # Raw data for programmatic consumption

class OutputConfig(BaseModel):
    format: OutputFormat
    template_config: Optional[Dict[str, Any]] = None
    max_tokens: Optional[int] = None
    verbose: bool = False
    no_emojis: bool = False
    no_color: bool = False
```

#### **1.2 Console Management**
- [ ] Create `src/repomap_tool/cli/output/console_manager.py`
- [ ] Centralize console creation and configuration
- [ ] Implement proper DI patterns
- [ ] Add console state management

```python
class ConsoleManager:
    def get_console(self, ctx: Optional[click.Context] = None) -> Console
    def configure_console(self, config: OutputConfig) -> Console
    def handle_errors(self, error: Exception, format_type: OutputFormat) -> None
```

#### **1.3 Base Formatter Protocol**
- [ ] Create `src/repomap_tool/cli/output/protocols.py`
- [ ] Define consistent formatter interface
- [ ] Add validation protocols
- [ ] Create base formatter classes

```python
class OutputFormatter(Protocol):
    def format(self, data: Any, config: OutputConfig) -> str
    def validate_data(self, data: Any) -> bool
    def get_supported_formats(self) -> List[OutputFormat]
```

### **Phase 2: Core Implementation (Week 2)**

#### **2.1 Output Manager**
- [ ] Create `src/repomap_tool/cli/output/manager.py`
- [ ] Implement centralized output management
- [ ] Add format routing logic
- [ ] Integrate with console manager

```python
class OutputManager:
    def __init__(self, console_manager: ConsoleManager, formatter_registry: FormatterRegistry):
        self.console_manager = console_manager
        self.formatter_registry = formatter_registry
    
    def display(self, data: Any, config: OutputConfig) -> None
    def display_error(self, error: Exception, config: OutputConfig) -> None
    def validate_format(self, format_type: OutputFormat, data_type: type) -> bool
```

#### **2.2 Formatter Registry**
- [ ] Create `src/repomap_tool/cli/output/registry.py`
- [ ] Implement formatter registration system
- [ ] Add automatic formatter discovery
- [ ] Create formatter factory

```python
class FormatterRegistry:
    def register_formatter(self, formatter: OutputFormatter) -> None
    def get_formatter(self, format_type: OutputFormat, data_type: type) -> OutputFormatter
    def list_supported_formats(self, data_type: type) -> List[OutputFormat]
```

#### **2.3 Individual Formatters**
- [ ] Create `src/repomap_tool/cli/output/formatters/`
- [ ] Implement JSON formatter
- [ ] Implement Text formatter
- [ ] Implement Table formatter
- [ ] Implement Markdown formatter
- [ ] Implement LLM Optimized formatter

```python
# src/repomap_tool/cli/output/formatters/json_formatter.py
class JSONFormatter(BaseFormatter):
    def format(self, data: Any, config: OutputConfig) -> str
    def get_supported_formats(self) -> List[OutputFormat]
```

### **Phase 3: Template System (Week 3)**

#### **3.1 Template Engine**
- [ ] Create `src/repomap_tool/cli/output/templates/`
- [ ] Implement template engine
- [ ] Add template validation
- [ ] Create template registry

```python
class TemplateEngine:
    def render(self, template_name: str, data: Dict[str, Any], config: OutputConfig) -> str
    def validate_template(self, template_name: str) -> bool
    def list_templates(self) -> List[str]
```

#### **3.2 Template Definitions**
- [ ] Create project analysis templates
- [ ] Create search result templates
- [ ] Create dependency analysis templates
- [ ] Create error templates
- [ ] Create progress templates

```python
# templates/project_analysis.jinja2
# templates/search_results.jinja2
# templates/dependency_analysis.jinja2
# templates/error.jinja2
```

### **Phase 4: Command Refactoring (Week 4)**

#### **4.1 Command Consolidation** ✅ **COMPLETED**
- [x] Remove duplicate `analyze` command
- [x] Remove duplicate `search` command  
- [x] Consolidate functionality into `inspect` command
- [x] Update all test files to reflect new command structure
- [x] Update action plan documentation
- [x] Standardize format support across all commands (TEXT and JSON only)
- [x] Update command help text and documentation
- [x] Add format validation to all commands

#### **4.2 CLI Integration**
- [ ] Update all CLI commands to use OutputManager
- [ ] Remove direct `console.print()` calls
- [ ] Implement consistent error handling
- [ ] Add progress reporting integration

```python
# Before (messy)
console.print(f"📊 Output format: {output}")
console.print(result)
console.print("✅ Impact analysis completed")

# After (clean)
output_manager.display(result, OutputConfig(format=OutputFormat(output)))
output_manager.display_success("Impact analysis completed")
```

#### **4.3 Configuration Integration**
- [ ] Update configuration system to support new output options
- [ ] Add output format defaults
- [ ] Implement output-specific settings
- [ ] Add validation for output configuration

### **Phase 5: Testing & Validation (Week 5)**

#### **5.1 Unit Tests**
- [ ] Test all formatters individually
- [ ] Test output manager functionality
- [ ] Test console manager
- [ ] Test template engine
- [ ] Test format validation

#### **5.2 Integration Tests**
- [ ] Test CLI command integration
- [ ] Test error handling scenarios
- [ ] Test format conversion
- [ ] Test template rendering
- [ ] Test performance with large datasets

#### **5.3 End-to-End Tests**
- [ ] Test complete workflows with new architecture
- [ ] Test backward compatibility
- [ ] Test all output formats
- [ ] Test error scenarios
- [ ] Test performance benchmarks

### **Phase 6: Documentation & Migration (Week 6)**

#### **6.1 Documentation**
- [ ] Update CLI documentation
- [ ] Create output architecture guide
- [ ] Document formatter development
- [ ] Create migration guide
- [ ] Update examples

#### **6.2 Migration**
- [ ] Create migration scripts
- [ ] Update existing configurations
- [ ] Test migration scenarios
- [ ] Provide backward compatibility
- [ ] Create deprecation warnings

## 🔧 **Technical Implementation Details**

### **File Structure:**
```
src/repomap_tool/cli/output/
├── __init__.py
├── formats.py              # OutputFormat enum and validation
├── protocols.py            # Formatter protocols and interfaces
├── console_manager.py      # Console management and DI
├── manager.py              # Central output manager
├── registry.py             # Formatter registry
├── config.py               # Output configuration models
├── formatters/
│   ├── __init__.py
│   ├── base.py             # Base formatter class
│   ├── json_formatter.py
│   ├── text_formatter.py
│   ├── table_formatter.py
│   ├── markdown_formatter.py
│   └── llm_formatter.py
├── templates/
│   ├── __init__.py
│   ├── engine.py           # Template engine
│   ├── registry.py         # Template registry
│   └── templates/
│       ├── project_analysis.jinja2
│       ├── search_results.jinja2
│       ├── dependency_analysis.jinja2
│       └── error.jinja2
└── utils/
    ├── __init__.py
    ├── validation.py       # Format and data validation
    └── helpers.py          # Utility functions
```

### **Dependency Injection Integration:**
```python
# In core/container.py
class Container(containers.DeclarativeContainer):
    # Output system
    console_manager: "providers.Singleton[ConsoleManager]" = providers.Singleton(
        "repomap_tool.cli.output.console_manager.ConsoleManager"
    )
    
    formatter_registry: "providers.Singleton[FormatterRegistry]" = providers.Singleton(
        "repomap_tool.cli.output.registry.FormatterRegistry"
    )
    
    output_manager: "providers.Singleton[OutputManager]" = providers.Singleton(
        "repomap_tool.cli.output.manager.OutputManager",
        console_manager=console_manager,
        formatter_registry=formatter_registry,
    )
```

### **CLI Command Integration:**
```python
# In CLI commands
@click.command()
@click.option("--output", "-o", type=click.Choice([f.value for f in OutputFormat]))
def inspect_command(output: str, ...) -> None:
    # Get services via DI
    service_factory = get_service_factory()
    output_manager = service_factory.get_output_manager()
    
    # Create output config
    config = OutputConfig(
        format=OutputFormat(output),
        verbose=verbose,
        no_emojis=no_emojis,
    )
    
    # Perform analysis
    result = perform_analysis(...)
    
    # Display results
    output_manager.display(result, config)
```

## 📊 **Success Metrics**

### **Code Quality Metrics:**
- [ ] Reduce direct `console.print()` calls from 66 to 0
- [ ] Achieve 100% test coverage for output system
- [ ] Reduce cyclomatic complexity in CLI commands by 50%
- [ ] Eliminate duplicate code in formatters

### **Architecture Metrics:**
- [ ] Single responsibility: Each class has one clear purpose
- [ ] Dependency injection: No direct instantiation outside DI container
- [ ] Consistent interface: All formatters follow same protocol
- [ ] Unified format system: Single format enum used throughout

### **User Experience Metrics:**
- [ ] Consistent output format support across all commands
- [ ] Improved error messages and formatting
- [ ] Better performance with large datasets
- [ ] Simplified configuration options

## 🚨 **Risk Mitigation**

### **Backward Compatibility:**
- Maintain existing CLI interface during transition
- Provide deprecation warnings for old patterns
- Create migration guide for users
- Test all existing workflows

### **Performance:**
- Benchmark new architecture against current system
- Optimize formatter performance
- Implement caching where appropriate
- Monitor memory usage

### **Testing:**
- Comprehensive test coverage before deployment
- Integration tests with real projects
- Performance regression testing
- User acceptance testing

## 📅 **Timeline**

- **Week 1**: Foundation (Formats, Console Management, Protocols)
- **Week 2**: Core Implementation (Manager, Registry, Formatters)
- **Week 3**: Template System
- **Week 4**: Command Refactoring ✅ **PARTIALLY COMPLETE** (Command consolidation done)
- **Week 5**: Testing & Validation
- **Week 6**: Documentation & Migration

### **Current Status:**
- ✅ **Command Consolidation**: Completed ahead of schedule
- ✅ **Format Simplification**: Completed ahead of schedule (interim solution)
- ✅ **Phase 1.1 (Unified Format System)**: Completed with comprehensive implementation
- 🔄 **Next Priority**: Continue Phase 1 (Foundation) - Console Management and Protocols

## 🎯 **Deliverables**

1. **Unified Output Architecture**: Clean, maintainable output system
2. **Comprehensive Test Suite**: Full coverage of new architecture
3. **Updated Documentation**: Complete guides and examples
4. **Migration Tools**: Scripts and guides for existing users
5. **Performance Benchmarks**: Validation of performance improvements

## 🔄 **Next Steps**

1. ✅ **Command Consolidation**: Completed - `analyze` and `search` commands removed
2. ✅ **Test Updates**: Completed - All test files updated to reflect new structure
3. 🔄 **Begin Phase 1**: Start with foundation components (Unified Format System)
4. **Regular Reviews**: Weekly progress reviews and adjustments
5. **User Feedback**: Gather feedback during development

### **Immediate Next Actions:**
1. ✅ **Complete Unified Format System** - COMPLETED with comprehensive `formats.py` implementation
2. **Implement Console Management** (`src/repomap_tool/cli/output/console_manager.py`)
3. **Define Base Formatter Protocol** (`src/repomap_tool/cli/output/protocols.py`)
4. **Create Output Manager** (`src/repomap_tool/cli/output/manager.py`)

---

**Status**: In Progress - Phase 4.1 & 1.1 Complete  
**Priority**: High  
**Estimated Effort**: 6 weeks (2 weeks ahead of schedule)  
**Dependencies**: None  
**Blockers**: None  
**Last Updated**: Unified format system and command consolidation completed
