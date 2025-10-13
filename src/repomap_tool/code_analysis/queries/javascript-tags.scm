; JavaScript/TypeScript tree-sitter query for comprehensive code analysis
; Captures imports, exports, function definitions, class definitions, and calls

; ES6 imports
(import_statement
  source: (string) @import.source
) @import.statement

; Import with specifiers
(import_statement
  import_clause: (named_imports
    (import_specifier
      name: (identifier) @import.name
      alias: (identifier) @import.alias
    )
  )
  source: (string) @import.source
) @import.named

; Default imports
(import_statement
  import_clause: (identifier) @import.default
  source: (string) @import.source
) @import.default

; Namespace imports
(import_statement
  import_clause: (namespace_import
    (identifier) @import.namespace
  )
  source: (string) @import.source
) @import.namespace

; Type imports (TypeScript)
(import_statement
  import_clause: (type_import
    (named_imports
      (import_specifier
        name: (identifier) @import.type_name
        alias: (identifier) @import.type_alias
      )
    )
  )
  source: (string) @import.source
) @import.type

; CommonJS requires
(call_expression
  function: (identifier) @require.name
  arguments: (arguments
    (string) @require.source
  )
) @require.statement

; Variable declarations with require
(variable_declaration
  declarator: (variable_declarator
    name: (identifier) @require.var_name
    value: (call_expression
      function: (identifier) @require.name
      arguments: (arguments
        (string) @require.source
      )
    )
  )
) @require.var

; Export statements
(export_statement
  declaration: (function_declaration
    name: (identifier) @export.function
  )
) @export.function

(export_statement
  declaration: (class_declaration
    name: (identifier) @export.class
  )
) @export.class

(export_statement
  declaration: (variable_declaration
    declarator: (variable_declarator
      name: (identifier) @export.variable
    )
  )
) @export.variable

; Named exports
(named_export
  specifiers: (export_specifier
    name: (identifier) @export.name
    alias: (identifier) @export.alias
  )
) @export.named

; Default exports
(export_statement
  default: (identifier) @export.default
) @export.default

; Function definitions
(function_declaration
  name: (identifier) @function.name
) @function.declaration

(function_expression
  name: (identifier) @function.name
) @function.expression

(arrow_function
  parameter: (identifier) @function.param
) @function.arrow

; Method definitions
(method_definition
  name: (property_identifier) @method.name
) @method.definition

; Class definitions
(class_declaration
  name: (identifier) @class.name
) @class.declaration

(class_expression
  name: (identifier) @class.name
) @class.expression

; Interface definitions (TypeScript)
(interface_declaration
  name: (identifier) @interface.name
) @interface.declaration

; Type aliases (TypeScript)
(type_alias_declaration
  name: (identifier) @type.name
) @type.alias

; Enum definitions (TypeScript)
(enum_declaration
  name: (identifier) @enum.name
) @enum.declaration

; Function calls
(call_expression
  function: (identifier) @call.name
) @call.expression

(call_expression
  function: (member_expression
    object: (identifier) @call.object
    property: (property_identifier) @call.method
  )
) @call.method

; Variable declarations
(variable_declaration
  declarator: (variable_declarator
    name: (identifier) @variable.name
  )
) @variable.declaration

; Assignment expressions
(assignment_expression
  left: (identifier) @assignment.name
  right: (expression) @assignment.value
) @assignment.expression

; ✨ NEW: Single-line comments
(comment) @comment

; ✨ NEW: JSDoc comments
(comment) @comment.documentation
