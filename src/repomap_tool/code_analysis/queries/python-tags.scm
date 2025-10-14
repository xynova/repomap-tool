; Enhanced Python tree-sitter queries for RepoMap-Tool
; Comprehensive queries for code analysis with import and call information
; Optimized for detailed code understanding and dependency analysis

; Classes
(class_definition
  name: (identifier) @name.definition.class) @definition.class

; Functions
(function_definition
  name: (identifier) @name.definition.function) @definition.function

; Function calls
(call
  function: [
      (identifier) @name.reference.call
      (attribute
        attribute: (identifier) @name.reference.call)
  ]) @reference.call

; Constants
(module (expression_statement (assignment left: (identifier) @name.definition.constant) @definition.constant))

; ✨ NEW: Import statements
(import_statement
  name: (dotted_name) @name.reference.import) @reference.import

; ✨ NEW: Import-from statements
(import_from_statement
  module_name: (dotted_name)? @name.reference.import.module
  name: (dotted_name) @name.reference.import.name) @reference.import

; ✨ NEW: Aliased imports
(aliased_import
  name: (dotted_name) @name.reference.import
  alias: (identifier) @name.reference.import.alias)

; ✨ NEW: Import aliases (import as)
(import_statement
  name: (dotted_name) @name.reference.import
  alias: (identifier)? @name.reference.import.alias)

; ✨ NEW: Import-from aliases (from module import name as alias)
(import_from_statement
  module_name: (dotted_name)? @name.reference.import.module
  name: (dotted_name) @name.reference.import.name
  alias: (identifier)? @name.reference.import.alias)

; ✨ NEW: Comments (inline and block)
(comment) @comment

; ✨ NEW: Docstrings
(expression_statement
  (string) @docstring)
