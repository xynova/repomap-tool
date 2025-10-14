# Tree-Sitter Query Files

This directory contains custom tree-sitter query files (.scm) that extend default queries to capture additional code elements for RepoMap-Tool.

## Why Custom Queries?

Default query files are optimized for LLM context and filter out many code elements like imports and detailed function calls. Our custom queries capture these elements while maintaining compatibility with standard approaches.

## Query Loading Priority

1. **Custom queries** (this directory) - `src/repomap_tool/code_analysis/queries/*.scm`
2. **Standard queries** (fallback) - `.venv/.../tree-sitter-language-pack/*.scm`

## File Structure

- `python-tags.scm` - Enhanced Python queries with imports, calls, definitions
- `javascript-tags.scm` - Enhanced JavaScript queries (future)
- `typescript-tags.scm` - Enhanced TypeScript queries (future)

## Query Syntax

Tree-sitter queries use S-expression syntax to match AST nodes:

```scheme
; Match class definitions
(class_definition
  name: (identifier) @name.definition.class) @definition.class

; Match import statements
(import_statement
  name: (dotted_name) @name.reference.import) @reference.import
```

## Tag Naming Convention

- `@name.definition.*` - Definitions (classes, functions, variables)
- `@name.reference.*` - References (calls, imports, usage)
- `@definition.*` - Node-level definition tags
- `@reference.*` - Node-level reference tags

## Adding New Languages

1. Create `{language}-tags.scm` file
2. Include all standard queries for that language
3. Add custom queries for imports, calls, etc.
4. Test with TreeSitterParser

## Examples

### Python Import Queries

```scheme
; Standard imports: import os
(import_statement
  name: (dotted_name) @name.reference.import) @reference.import

; From imports: from os import path
(import_from_statement
  module_name: (dotted_name)? @name.reference.import.module
  name: (dotted_name) @name.reference.import.name) @reference.import

; Aliased imports: import os as operating_system
(import_statement
  name: (dotted_name) @name.reference.import
  alias: (identifier)? @name.reference.import.alias)
```

## Testing

Query files are automatically loaded by `TreeSitterParser`. Test with:

```python
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser

parser = TreeSitterParser()
tags = parser.parse_file("test.py")
print(f"Found {len(tags)} tags")
```
