; Tree-sitter query for JavaScript to extract definitions and references

; Class Definitions
(class_declaration
  name: (identifier) @name.definition.class
) @definition.class

; Function Definitions
(function_declaration
  name: (identifier) @name.definition.function
) @definition.function

; Arrow Function Expressions (when assigned to a variable)
(variable_declarator
  name: (identifier) @name.definition.function
  value: (arrow_function)
) @definition.function

; Method Definitions (inside classes or object literals)
(method_definition
  name: (property_identifier) @name.definition.method
) @definition.method

(pair
  key: (property_identifier) @name.definition.method
  value: (function)
) @definition.method

; Imports
(import_statement
  (import_clause
    (named_imports
      (import_specifier
        name: (identifier) @name.reference.import
      )
    )
  )
) @reference.import

(import_statement
  (import_clause
    (namespace_import
      name: (identifier) @name.reference.import
    )
  )
) @reference.import

(import_statement
  (import_clause
    (identifier) @name.reference.import
  )
) @reference.import

; Exports
(export_statement
  declaration: (function_declaration
    name: (identifier) @name.definition.export
  )
) @definition.export

(export_statement
  declaration: (class_declaration
    name: (identifier) @name.definition.export
  )
) @definition.export

(export_statement
  declaration: (variable_declaration
    (variable_declarator
      name: (identifier) @name.definition.export
    )
  )
) @definition.export

(export_statement
  (named_exports
    (export_specifier
      name: (identifier) @name.reference.export
    )
  )
) @reference.export

; Variable Declarations
(variable_declarator
  name: (identifier) @name.definition.variable
) @definition.variable

; Function Calls
(call_expression
  function: (identifier) @name.call
) @call.function

(call_expression
  function: (member_expression
    property: (property_identifier) @name.call
  )
) @call.function

; General Identifiers (references to variables, etc.)
(identifier) @name.reference.identifier

; Comments
(comment) @comment
