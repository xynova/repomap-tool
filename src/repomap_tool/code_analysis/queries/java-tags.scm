; Java tree-sitter query for comprehensive code analysis
; Captures imports, package declarations, class definitions, method definitions, and calls

; Package declarations
(package_declaration
  (scoped_identifier) @package.name
) @package.declaration

; Import statements
(import_declaration
  (scoped_identifier) @import.name
) @import.statement

; Static imports
(import_declaration
  "static" @import.static
  (scoped_identifier) @import.name
) @import.static

; Wildcard imports
(import_declaration
  (scoped_identifier) @import.package
  "*" @import.wildcard
) @import.wildcard

; Class declarations
(class_declaration
  name: (identifier) @class.name
  type_parameters: (type_parameters) @class.type_params
) @class.declaration

; Interface declarations
(interface_declaration
  name: (identifier) @interface.name
  type_parameters: (type_parameters) @interface.type_params
) @interface.declaration

; Enum declarations
(enum_declaration
  name: (identifier) @enum.name
) @enum.declaration

; Annotation type declarations
(annotation_type_declaration
  name: (identifier) @annotation.name
) @annotation.declaration

; Method declarations
(method_declaration
  name: (identifier) @method.name
  type_parameters: (type_parameters) @method.type_params
) @method.declaration

; Constructor declarations
(constructor_declaration
  name: (identifier) @constructor.name
) @constructor.declaration

; Field declarations
(field_declaration
  declarator: (variable_declarator
    name: (identifier) @field.name
  )
) @field.declaration

; Local variable declarations
(local_variable_declaration
  declarator: (variable_declarator
    name: (identifier) @variable.name
  )
) @variable.declaration

; Method invocations
(method_invocation
  name: (identifier) @call.method
) @call.method

(method_invocation
  object: (identifier) @call.object
  name: (identifier) @call.method
) @call.object_method

; Constructor invocations
(object_creation_expression
  type: (type_identifier) @call.constructor
) @call.constructor

; Super method calls
(super) @call.super

; This expressions
(this) @call.this

; Annotations
(annotation
  name: (identifier) @annotation.name
) @annotation.usage

; Type parameters
(type_parameters
  (type_parameter
    name: (type_identifier) @type_param.name
    constraint: (type_bound) @type_param.bound
  )
)

; Type arguments
(type_arguments
  (_type) @type_arg.type
)

; Generic types
(generic_type
  type: (type_identifier) @generic.type
  type_arguments: (type_arguments) @generic.type_args
) @generic.usage

; Array types
(array_type
  element: (_type) @array.element
) @array.type

; Primitive types
(integral_type) @primitive.integral
(floating_point_type) @primitive.floating
(boolean_type) @primitive.boolean
(void_type) @primitive.void

; Reference types
(type_identifier) @type.identifier
(scoped_identifier) @type.scoped

; Lambda expressions
(lambda_expression
  parameters: (formal_parameters) @lambda.params
  body: (expression) @lambda.body
) @lambda.expression

; Method references
(method_reference
  object: (identifier) @method_ref.object
  name: (identifier) @method_ref.method
)

; Try-catch-finally blocks
(try_statement
  body: (block) @try.body
  (catch_clause) @try.catch
  (finally_clause) @try.finally
)

; Throw statements
(throw_statement
  (expression) @throw.expression
)

; Assert statements
(assert_statement
  (expression) @assert.condition
  (expression) @assert.detail
)

; Synchronized statements
(synchronized_statement
  (expression) @synchronized.expression
  body: (block) @synchronized.body
)

; Switch expressions
(switch_expression
  condition: (parenthesized_expression) @switch.condition
  body: (switch_block) @switch.body
)

; Pattern matching (Java 17+)
(instanceof_expression
  left: (expression) @instanceof.expression
  right: (_type) @instanceof.type
)

; Record declarations (Java 14+)
(record_declaration
  name: (identifier) @record.name
  type_parameters: (type_parameters) @record.type_params
) @record.declaration

; Sealed classes (Java 17+) - modifiers are children, not fields
(class_declaration
  name: (identifier) @class.name
)

; Text blocks (Java 15+) - handled by string literal patterns

; Var declarations (Java 10+)
(local_variable_declaration
  declarator: (variable_declarator
    name: (identifier) @var.name
  )
) @var.declaration

; Enhanced for loops
(enhanced_for_statement
  (identifier) @for.variable
  body: (block) @for.body
)

; Traditional for loops
(for_statement
  body: (block) @for.body
) @for.traditional

; While loops
(while_statement
  body: (block) @while.body
) @while.statement

; Do-while loops
(do_statement
  body: (block) @do.body
) @do.statement

; If statements
(if_statement
  consequence: (block) @if.consequence
) @if.statement

; Return statements
(return_statement
) @return.statement

; Break statements
(break_statement
) @break.statement

; Continue statements
(continue_statement
) @continue.statement

; Assignment expressions
(assignment_expression
  left: (expression) @assignment.left
  right: (expression) @assignment.right
) @assignment.expression

; Binary expressions
(binary_expression
  left: (expression) @binary.left
  right: (expression) @binary.right
) @binary.expression

; Unary expressions
(unary_expression
  operand: (expression) @unary.operand
) @unary.expression

; Ternary expressions
(ternary_expression
  (expression) @ternary.consequence
  (expression) @ternary.alternative
)

; Parenthesized expressions
(parenthesized_expression
  (expression) @paren.expression
)

; Array access
(array_access
  array: (expression) @array.array
  index: (expression) @array.index
) @array.access

; Member access
(field_access
  object: (expression) @field.object
  field: (identifier) @field.field
) @field.access

; Method chaining
(method_invocation
  object: (method_invocation) @chain.method
  name: (identifier) @chain.name
) @chain.method

; String literals
(string_literal) @string.literal

; Character literals
(character_literal) @char.literal

; Integer literals
(integer_literal) @int.literal

; Floating point literals
(floating_point_literal) @float.literal

; Boolean literals
(boolean_literal) @bool.literal

; Null literal
(null_literal) @null.literal

; Class literals
(class_literal
  type: (_type) @class.type
)

; ✨ NEW: Comments (single-line and block)
(comment) @comment

; ✨ NEW: Javadoc comments
(comment) @comment.documentation
