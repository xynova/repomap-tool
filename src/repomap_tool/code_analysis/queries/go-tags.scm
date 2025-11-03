; Go tree-sitter query for comprehensive code analysis
; Captures imports, package declarations, function definitions, struct definitions, and calls

; Package declarations
(package_clause
  (package_identifier) @package.name
)

; Import declarations
(import_declaration
  (import_spec_list
    (import_spec
      path: [(interpreted_string_literal) (raw_string_literal)] @import.path
      name: (package_identifier) @import.alias
    )
  )
)

; Single import
(import_declaration
  (import_spec
    path: [(interpreted_string_literal) (raw_string_literal)] @import.path
  )
)

; Grouped imports
(import_declaration
  "("
  (import_spec_list
    (import_spec
      path: [(interpreted_string_literal) (raw_string_literal)] @import.path
      name: (package_identifier) @import.alias
    )
  )
  ")"
)

; Function declarations
(function_declaration
  name: (identifier) @function.name
  parameters: (parameter_list) @function.params
) @function.declaration

; Method declarations
(method_declaration
  receiver: (parameter_list) @method.receiver
  name: (field_identifier) @method.name
  parameters: (parameter_list) @method.params
) @method.declaration

; Function literals
(func_literal
  parameters: (parameter_list) @func.params
  body: (block) @func.body
)

; Variable declarations
(var_declaration
  (var_spec
    name: (identifier) @var.name
    value: (_expression) @var.value
  )
)

; Short variable declarations
(short_var_declaration
  left: (expression_list) @short.left
  right: (expression_list) @short.right
) @short.declaration

; Type declarations
(type_declaration
  (type_spec
    name: (type_identifier) @type.name
  )
)

; Struct declarations (via type_declaration)
(type_declaration
  (type_spec
    name: (type_identifier) @struct.name
    (struct_type
      (field_declaration_list) @struct.fields
    )
  )
)

; Interface declarations (via type_declaration)
(type_declaration
  (type_spec
    name: (type_identifier) @interface.name
  )
)

; Field declarations
(field_declaration
  name: (field_identifier) @field.name
  tag: (raw_string_literal) @field.tag
)

; Method specifications (disabled - causes query compilation errors)
; (method_spec
;   name: (field_identifier) @method_spec.name
;   parameters: (parameter_list) @method_spec.params
; )

; Function calls
(call_expression
  function: (identifier) @call.function
  arguments: (argument_list) @call.args
)

; Method calls
(call_expression
  function: (selector_expression
    operand: (_expression) @call.object
    field: (field_identifier) @call.method
  )
  arguments: (argument_list) @call.args
) @call.method

; Built-in function calls
(call_expression
  function: (_) @call.builtin
  arguments: (argument_list) @call.args
)

; Type assertions
(type_assertion_expression
  operand: (_expression) @assert.expression
) @assert.type

; Type switches
(type_switch_statement
) @switch.type

; Type cases
(type_case
  body: (block) @case.body
) @case.type

; Regular cases
(expression_case
  body: (block) @case.body
) @case.expression

; Default cases
(default_case
  body: (block) @case.default
) @case.default

; Select statements
(select_statement
) @select.statement

; Communication cases
(communication_case
  communication: (send_statement) @comm.send
  body: (block) @comm.body
) @comm.send_case

(communication_case
  communication: (receive_statement) @comm.receive
  body: (block) @comm.body
) @comm.receive_case

; Send statements
(send_statement
  channel: (_expression) @send.channel
  value: (_expression) @send.value
) @send.statement

; Receive statements
(receive_statement
  channel: (_expression) @receive.channel
  left: (_expression) @receive.left
) @receive.statement

; Go statements
(go_statement
) @go.statement

; Defer statements
(defer_statement
) @defer.statement

; If statements
(if_statement
  condition: (_expression) @if.condition
  consequence: (block) @if.consequence
  alternative: (else_clause) @if.alternative
) @if.statement

; For statements
(for_statement
  init: (_expression) @for.init
  condition: (_expression) @for.condition
  update: (_expression) @for.update
  body: (block) @for.body
) @for.statement

; For range statements
(for_statement
  left: (expression_list) @for.left
  right: (_expression) @for.right
  body: (block) @for.body
) @for.range

; Switch statements
(switch_statement
) @switch.statement

; Return statements
(return_statement
) @return.statement

; Break statements
(break_statement
  label: (label_name) @break.label
) @break.statement

; Continue statements
(continue_statement
  label: (label_name) @continue.label
) @continue.statement

; Goto statements
(goto_statement
  label: (label_name) @goto.label
) @goto.statement

; Label statements
(labeled_statement
  label: (label_name) @label.name
  statement: (statement) @label.statement
) @label.statement

; Assignment expressions
(assignment_expression
  left: (_expression) @assignment.left
  right: (_expression) @assignment.right
) @assignment.expression

; Binary expressions
(binary_expression
  left: (_expression) @binary.left
  operator: (binary_operator) @binary.operator
  right: (_expression) @binary.right
) @binary.expression

; Unary expressions
(unary_expression
  operator: (unary_operator) @unary.operator
  operand: (_expression) @unary.operand
) @unary.expression

; Ternary expressions
(ternary_expression
  condition: (_expression) @ternary.condition
  consequence: (_expression) @ternary.consequence
  alternative: (_expression) @ternary.alternative
) @ternary.expression

; Parenthesized expressions
(parenthesized_expression
) @paren.expression

; Index expressions
(index_expression
  operand: (_expression) @index.operand
  index: (_expression) @index.index
) @index.expression

; Slice expressions
(slice_expression
  operand: (_expression) @slice.operand
  start: (_expression) @slice.start
  end: (_expression) @slice.end
) @slice.expression

; Selector expressions
(selector_expression
  operand: (_expression) @selector.operand
  field: (field_identifier) @selector.field
) @selector.expression

; Composite literals
(composite_literal
  elements: (element_list) @composite.elements
)

; Keyed elements
(keyed_element
  key: (_expression) @element.key
  value: (_expression) @element.value
) @element.keyed

; Unkeyed elements
(unkeyed_element
  value: (_expression) @element.value
) @element.unkeyed

; String literals
(string_literal) @string.literal

; Raw string literals
(raw_string_literal) @string.raw

; Rune literals
(rune_literal) @rune.literal

; Integer literals
(int_literal) @int.literal

; Float literals
(float_literal) @float.literal

; Imaginary literals
(imaginary_literal) @imaginary.literal

; Boolean literals
(boolean_literal) @bool.literal

; Nil literal
(nil) @nil.literal

; Type identifiers
(type_identifier) @type.identifier

; Package identifiers
(package_identifier) @package.identifier

; Field identifiers
(field_identifier) @field.identifier

; Label names
(label_name) @label.name

; Built-in types
(builtin) @builtin.type

; Built-in functions
(builtin) @builtin.function

; Channel types
(channel_type
  direction: (channel_direction) @channel.direction
) @channel.type

; Pointer types
(pointer_type
) @pointer.type

; Array types
(array_type
  length: (_expression) @array.length
) @array.type

; Slice types
(slice_type
) @slice.type

; Map types
(map_type
) @map.type

; Function types
(function_type
  parameters: (parameter_list) @func_type.params
  result: (_simple_type) @func_type.result
)

; Interface types
(interface_type) @interface_type.definition

; Struct types
(struct_type
  fields: (field_declaration_list) @struct_type.fields
) @struct_type.definition

; Type assertions
(type_assertion_expression
  operand: (_expression) @assert.expression
) @assert.type

; Type switches
(type_switch_statement
) @switch.type

; Type cases
(type_case
  body: (block) @case.body
) @case.type

; Regular cases
(expression_case
  body: (block) @case.body
) @case.expression

; Default cases
(default_case
  body: (block) @case.default
) @case.default

; Select statements
(select_statement
) @select.statement

; Communication cases
(communication_case
  communication: (send_statement) @comm.send
  body: (block) @comm.body
) @comm.send_case

(communication_case
  communication: (receive_statement) @comm.receive
  body: (block) @comm.body
) @comm.receive_case

; Send statements
(send_statement
  channel: (_expression) @send.channel
  value: (_expression) @send.value
) @send.statement

; Receive statements
(receive_statement
  channel: (_expression) @receive.channel
  left: (_expression) @receive.left
) @receive.statement

; Go statements
(go_statement
) @go.statement

; Defer statements
(defer_statement
) @defer.statement

; ✨ NEW: Comments (single-line and block)
(comment) @comment

; ✨ NEW: Documentation comments
(comment) @comment.documentation
