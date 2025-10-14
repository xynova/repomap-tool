<!-- 503b5b09-1f04-4138-ba8a-5b22bdc3a238 f4605211-7c48-4073-a9f4-674cb4833e8f -->
# Inspect Density Command Implementation

## Overview
Create `inspect density` command that analyzes code density at file and module levels, showing identifier breakdowns (classes, functions, methods, variables, imports) using TreeSitterParser for accurate cross-language support.

## Phase 1: Core Density Analysis Service

### Create DensityAnalyzer Service
**File**: `src/repomap_tool/code_analysis/density_analyzer.py`

```python
class IdentifierCategory:
    """Categories for identifier classification"""
    CLASSES = "classes"  # class, interface, enum, record, type
    FUNCTIONS = "functions"  # function, def
    METHODS = "methods"  # method, constructor
    VARIABLES = "variables"  # field, property, variable
    IMPORTS = "imports"  # import, require, export
    
class FileDensity:
    """Density metrics for a single file"""
    file_path: str
    total_identifiers: int
    categories: Dict[str, int]  # category -> count
    primary_identifiers: int  # classes + functions + methods
    
class ModuleDensity:
    """Density metrics for a module/package"""
    module_path: str
    total_identifiers: int
    file_count: int
    files: List[FileDensity]  # sorted by density
    categories: Dict[str, int]  # aggregated counts

class DensityAnalyzer:
    def __init__(self, tree_sitter_parser: TreeSitterParser):
        self.parser = tree_sitter_parser
        
    def analyze_file(self, file_path: str) -> FileDensity:
        """Analyze identifier density for a single file"""
        tags = self.parser.parse_file(file_path)
        return self._categorize_tags(tags, file_path)
        
    def analyze_files(self, file_paths: List[str]) -> List[FileDensity]:
        """Analyze multiple files and return sorted by density"""
        
    def analyze_module(self, module_path: str, file_paths: List[str]) -> ModuleDensity:
        """Analyze module density with files sorted by density"""
        
    def _categorize_tag(self, tag_kind: str) -> str:
        """Map tree-sitter tag kind to identifier category"""
        # Map 'class.name', 'name.definition.class' -> CLASSES
        # Map 'function.name', 'name.definition.function' -> FUNCTIONS
        # etc.
```

Key: Use TreeSitterParser.parse_file() which returns tags with detailed `kind` fields for accurate categorization.

## Phase 2: CLI Command Implementation

### Add density subcommand
**File**: `src/repomap_tool/cli/commands/inspect.py`

```python
@inspect.command()
@click.argument("project_path", ...)
@click.option("--scope", type=click.Choice(["file", "module"]), default="file")
@click.option("--limit", "-l", type=int, default=10)
@click.option("--min-identifiers", type=int, default=1)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
@click.pass_context
def density(ctx, project_path, scope, limit, min_identifiers, output):
    """Inspect code density - files/modules with most identifiers by type"""
    # Use DI container to get DensityController
    container = create_container(config_obj)
    density_controller = container.density_controller()
    
    # Execute analysis
    view_model = density_controller.execute(
        scope=scope, 
        limit=limit,
        min_identifiers=min_identifiers
    )
    
    # Display via OutputManager
    output_manager.display(view_model, output_config)
```

## Phase 3: Controller and ViewModel

### Create DensityController
**File**: `src/repomap_tool/cli/controllers/density_controller.py`

```python
class FileDensityViewModel(BaseModel):
    """ViewModel for file density display"""
    file_path: str
    relative_path: str
    total_identifiers: int
    primary_identifiers: int
    categories: Dict[str, int]
    
class ModuleDensityViewModel(BaseModel):
    """ViewModel for module density display"""
    module_path: str
    total_identifiers: int
    file_count: int
    avg_identifiers_per_file: float
    files: List[FileDensityViewModel]  # sorted by density
    categories: Dict[str, int]

class DensityAnalysisViewModel(BaseModel):
    """Top-level ViewModel for density command"""
    scope: str  # "file" or "module"
    results: List[Union[FileDensityViewModel, ModuleDensityViewModel]]
    total_files_analyzed: int
    analysis_summary: Dict[str, Any]

class DensityController(BaseController):
    def __init__(self, density_analyzer: DensityAnalyzer, 
                 file_discovery: FileDiscoveryService):
        self.analyzer = density_analyzer
        self.file_discovery = file_discovery
        
    def execute(self, scope: str, limit: int, 
                min_identifiers: int) -> DensityAnalysisViewModel:
        """Execute density analysis"""
        files = self.file_discovery.discover_files()
        
        if scope == "file":
            return self._analyze_files(files, limit, min_identifiers)
        else:
            return self._analyze_modules(files, limit, min_identifiers)
```

## Phase 4: Output Formatting

### Create density template
**File**: `src/repomap_tool/cli/output/templates/jinja/density_analysis.jinja2`

```jinja2
File Density Analysis

Top {{ results|length }} files by identifier density:

{% for file in results %}
{{ loop.index }}. {{ file.relative_path }} ({{ file.total_identifiers }} identifiers)
   Primary: {{ file.primary_identifiers }}
   ├── Classes: {{ file.categories.classes }}
   ├── Functions: {{ file.categories.functions }}
   └── Methods: {{ file.categories.methods }}
   
   Secondary:
   ├── Variables: {{ file.categories.variables }}
   └── Imports: {{ file.categories.imports }}
{% endfor %}

Module Density Analysis

{% for module in results %}
{{ module.module_path }}/ ({{ module.total_identifiers }} identifiers, {{ module.file_count }} files)
   Avg per file: {{ module.avg_identifiers_per_file }}
   
   Files (by density):
   {% for file in module.files[:5] %}
   ├── {{ file.relative_path }} ({{ file.total_identifiers }})
   {% endfor %}
{% endfor %}
```

### Create DensityFormatter
**File**: `src/repomap_tool/cli/output/controller_formatters.py`

```python
class DensityAnalysisFormatter(TemplateBasedFormatter):
    def supports_format(self, output_format: OutputFormat) -> bool:
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]
        
    def _get_template_name(self) -> str:
        return "density_analysis.jinja2"
```

## Phase 5: DI Container Integration

### Register services
**File**: `src/repomap_tool/core/container.py`

```python
# Add to Container class:
density_analyzer = providers.Factory(
    DensityAnalyzer,
    tree_sitter_parser=tree_sitter_parser,
)

density_controller = providers.Factory(
    DensityController,
    density_analyzer=density_analyzer,
    file_discovery=file_discovery_service,
)
```

## Phase 6: Testing

### Unit tests
**File**: `tests/unit/test_density_analyzer.py`
- Test tag categorization mapping
- Test file density calculation
- Test module aggregation
- Test sorting by density

### Integration tests  
**File**: `tests/integration/test_density_command.py`
- Test CLI command execution
- Test file scope output
- Test module scope output
- Test with real project files

## Key Design Decisions

1. **Use TreeSitterParser directly** - No aider dependency, full tag detail
2. **Separate Primary/Secondary** - Focus on meaningful identifiers (classes, functions)
3. **Module aggregation** - Group by directory, sort files within by density
4. **Cross-language** - Tag kind mapping works for Python, JS, TS, Java, Go, C#
5. **MVC pattern** - Controller returns ViewModel, formatted via templates

## Success Criteria

- Command shows file density with accurate categorization
- Module view shows aggregated stats with files sorted by density
- Works across all supported languages (Python, JS, TS, Java, etc.)
- No aider dependency for this feature
- Output is clear and actionable for refactoring decisions


### To-dos

- [ ] Create DensityAnalyzer service with file and module analysis
- [ ] Add 'inspect density' CLI command with scope option
- [ ] Create DensityController with ViewModels
- [ ] Create Jinja2 templates and formatter
- [ ] Register DensityAnalyzer and Controller in DI container
- [ ] Write unit and integration tests