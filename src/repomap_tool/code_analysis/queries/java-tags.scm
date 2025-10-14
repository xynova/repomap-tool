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
    name: (identifier) @type_param.name
    extends: (type_bound) @type_param.bound
  )
) @type_param.definition

; Type arguments
(type_arguments
  (type) @type_arg.type
) @type_arg.usage

; Generic types
(generic_type
  type: (type_identifier) @generic.type
  type_arguments: (type_arguments) @generic.type_args
) @generic.usage

; Array types
(array_type
  element: (type) @array.element
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
  method: (identifier) @method_ref.method
) @method_ref.expression

; Try-catch-finally blocks
(try_statement
  body: (block) @try.body
  catch_clause: (catch_clause) @try.catch
  finally_clause: (finally_clause) @try.finally
) @try.statement

; Throw statements
(throw_statement
  expression: (expression) @throw.expression
) @throw.statement

; Assert statements
(assert_statement
  condition: (expression) @assert.condition
  detail: (expression) @assert.detail
) @assert.statement

; Synchronized statements
(synchronized_statement
  expression: (expression) @synchronized.expression
  body: (block) @synchronized.body
) @synchronized.statement

; Switch expressions
(switch_expression
  condition: (expression) @switch.condition
  case: (switch_rule) @switch.case
) @switch.expression

; Pattern matching (Java 17+)
(instanceof_expression
  left: (expression) @instanceof.expression
  right: (type) @instanceof.type
) @instanceof.expression

; Record declarations (Java 14+)
(record_declaration
  name: (identifier) @record.name
  type_parameters: (type_parameters) @record.type_params
) @record.declaration

; Sealed classes (Java 17+)
(class_declaration
  modifiers: (modifiers
    (modifier) @class.sealed
  )
  name: (identifier) @class.name
) @class.sealed

; Text blocks (Java 15+)
(text_block) @text.block

; Var declarations (Java 10+)
(local_variable_declaration
  type: (var) @var.type
  declarator: (variable_declarator
    name: (identifier) @var.name
  )
) @var.declaration

; Enhanced for loops
(enhanced_for_statement
  variable: (identifier) @for.variable
  iterable: (expression) @for.iterable
  body: (block) @for.body
) @for.enhanced

; Traditional for loops
(for_statement
  init: (expression) @for.init
  condition: (expression) @for.condition
  update: (expression) @for.update
  body: (block) @for.body
) @for.traditional

; While loops
(while_statement
  condition: (expression) @while.condition
  body: (block) @while.body
) @while.statement

; Do-while loops
(do_statement
  body: (block) @do.body
  condition: (expression) @do.condition
) @do.statement

; If statements
(if_statement
  condition: (expression) @if.condition
  consequence: (block) @if.consequence
  alternative: (else_clause) @if.alternative
) @if.statement

; Return statements
(return_statement
  expression: (expression) @return.expression
) @return.statement

; Break statements
(break_statement
  label: (identifier) @break.label
) @break.statement

; Continue statements
(continue_statement
  label: (identifier) @continue.label
) @continue.statement

; Assignment expressions
(assignment_expression
  left: (expression) @assignment.left
  right: (expression) @assignment.right
) @assignment.expression

; Binary expressions
(binary_expression
  left: (expression) @binary.left
  operator: (binary_operator) @binary.operator
  right: (expression) @binary.right
) @binary.expression

; Unary expressions
(unary_expression
  operator: (unary_operator) @unary.operator
  operand: (expression) @unary.operand
) @unary.expression

; Ternary expressions
(ternary_expression
  condition: (expression) @ternary.condition
  consequence: (expression) @ternary.consequence
  alternative: (expression) @ternary.alternative
) @ternary.expression

; Parenthesized expressions
(parenthesized_expression
  expression: (expression) @paren.expression
) @paren.expression

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
  type: (type) @class.type
) @class.literal

; ✨ NEW: Comments (single-line and block)
(comment) @comment

; ✨ NEW: Javadoc comments
(comment) @comment.documentation
