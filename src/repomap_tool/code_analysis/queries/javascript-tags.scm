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
  value: (function_expression)
) @definition.method

; Imports
(import_statement) @reference.import

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

; Named exports: export { a, b }
(export_statement
  (export_clause
    (export_specifier
      name: (identifier) @name.reference.export
    )
  )
)

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
