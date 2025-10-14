# Inspect Density Command Implementation Plan

## Overview
Implement `inspect density` command to show files and modules with most identifiers, broken down by type (classes, functions, methods, variables, imports) using TreeSitterParser for detailed cross-language analysis.

## Implementation Checklist

- [ ] Phase 1: Create DensityAnalyzer service with file and module analysis
- [ ] Phase 2: Add 'inspect density' CLI command with scope option  
- [ ] Phase 3: Create DensityController with ViewModels
- [ ] Phase 4: Create Jinja2 templates and formatter
- [ ] Phase 5: Register DensityAnalyzer and Controller in DI container
- [ ] Phase 6: Write unit and integration tests

## Phase 1: Core Density Analysis Service

### File: `src/repomap_tool/code_analysis/density_analyzer.py`

Complete implementation with:
- `IdentifierCategory` class with constants
- `FileDensity` dataclass with file metrics
- `ModuleDensity` dataclass with module metrics and files sorted by density
- `DensityAnalyzer` class with comprehensive tag kind mapping
- Cross-language support (Python, JS/TS, Java, Go, C#)
- Proper error handling and logging

**Tag Kind Mapping Strategy:**
```python
TAG_KIND_MAPPING = {
    # Python: name.definition.class, name.definition.function
    # JavaScript: class.name, function.name, method.name
    # Java: class.name, method.name, field.name
    # All mapped to: CLASSES, FUNCTIONS, METHODS, VARIABLES, IMPORTS
}
```

## Phase 2: CLI Command

### File: `src/repomap_tool/cli/commands/inspect.py`

Add `density` subcommand to existing `inspect` group:
```python
@inspect.command()
@click.argument("project_path", type=click.Path(exists=True))
@click.option("--scope", type=click.Choice(["file", "module"]), default="file")
@click.option("--limit", "-l", type=int, default=10)
@click.option("--min-identifiers", type=int, default=1)
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text")
def density(ctx, project_path, scope, limit, min_identifiers, output):
    """Show files/modules with most identifiers by type"""
```

## Phase 3: Controller and ViewModels

### File: `src/repomap_tool/cli/controllers/density_controller.py`

Create:
- `FileDensityViewModel` - for file-level display
- `ModuleDensityViewModel` - for module-level display with files sorted by density
- `DensityAnalysisViewModel` - top-level result
- `DensityController` - orchestrates analysis and builds ViewModels

## Phase 4: Output Formatting

### File: `src/repomap_tool/cli/output/templates/jinja/density_analysis.jinja2`

Template showing:
- File scope: List files sorted by density with category breakdown
- Module scope: List modules with aggregated stats, files within sorted by density
- Primary identifiers (classes, functions, methods) highlighted
- Secondary identifiers (variables, imports) shown separately

### File: `src/repomap_tool/cli/output/controller_formatters.py`

Add `DensityAnalysisFormatter` class

## Phase 5: DI Container

### File: `src/repomap_tool/core/container.py`

Register:
```python
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

### File: `tests/unit/test_density_analyzer.py`
- Test tag categorization for different languages
- Test file density calculation
- Test module aggregation with files sorted correctly
- Test sorting by density

### File: `tests/integration/test_density_command.py`
- Test CLI command with real files
- Test both file and module scopes
- Test output formats (text, json)
- Verify cross-language support

## Key Design Decisions

1. **TreeSitterParser only** - No aider dependency, use parse_file() directly
2. **Cross-language mapping** - Comprehensive tag kind mapping for all supported languages
3. **Module files sorted by density** - Within each module, files ordered by identifier count descending
4. **Primary vs Secondary** - Highlight meaningful identifiers (classes, functions, methods)
5. **MVC pattern** - Controller orchestrates, ViewModels structure data, templates format
6. **Proper DI** - All dependencies injected via container

## Success Criteria

- ✅ Command shows accurate file density with categorization
- ✅ Module view aggregates correctly with files sorted by density
- ✅ Works for Python, JavaScript, TypeScript, Java, Go, C#
- ✅ No aider dependency for this feature
- ✅ Output is clear and actionable
- ✅ All tests pass
- ✅ Follows existing architectural patterns

