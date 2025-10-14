; Go tree-sitter query for comprehensive code analysis
; Captures imports, package declarations, function definitions, struct definitions, and calls

; Package declarations
(package_declaration
  (package_identifier) @package.name
) @package.declaration

; Import declarations
(import_declaration
  (import_spec_list
    (import_spec
      path: (string_literal) @import.path
      name: (package_identifier) @import.alias
    )
  )
) @import.statement

; Single import
(import_declaration
  (import_spec
    path: (string_literal) @import.path
  )
) @import.single

; Grouped imports
(import_declaration
  "("
  (import_spec_list
    (import_spec
      path: (string_literal) @import.path
      name: (package_identifier) @import.alias
    )
  )
  ")"
) @import.grouped

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
) @func.literal

; Variable declarations
(var_declaration
  (var_spec
    name: (identifier) @var.name
    type: (type_identifier) @var.type
    value: (expression) @var.value
  )
) @var.declaration

; Short variable declarations
(short_var_declaration
  left: (expression_list) @short.left
  right: (expression_list) @short.right
) @short.declaration

; Type declarations
(type_declaration
  (type_spec
    name: (type_identifier) @type.name
    type: (type) @type.definition
  )
) @type.declaration

; Struct declarations
(struct_declaration
  name: (type_identifier) @struct.name
  fields: (field_declaration_list) @struct.fields
) @struct.declaration

; Interface declarations
(interface_declaration
  name: (type_identifier) @interface.name
  methods: (method_spec_list) @interface.methods
) @interface.declaration

; Field declarations
(field_declaration
  name: (field_identifier) @field.name
  type: (type) @field.type
  tag: (raw_string_literal) @field.tag
) @field.declaration

; Method specifications
(method_spec
  name: (field_identifier) @method_spec.name
  parameters: (parameter_list) @method_spec.params
  result: (type) @method_spec.result
) @method_spec.definition

; Function calls
(call_expression
  function: (identifier) @call.function
  arguments: (argument_list) @call.args
) @call.expression

; Method calls
(call_expression
  function: (selector_expression
    operand: (expression) @call.object
    field: (field_identifier) @call.method
  )
  arguments: (argument_list) @call.args
) @call.method

; Built-in function calls
(call_expression
  function: (builtin) @call.builtin
  arguments: (argument_list) @call.args
) @call.builtin

; Type assertions
(type_assertion
  expression: (expression) @assert.expression
  type: (type) @assert.type
) @assert.type

; Type switches
(type_switch_statement
  expression: (expression) @switch.expression
  cases: (type_case_list) @switch.cases
) @switch.type

; Type cases
(type_case
  type: (type) @case.type
  body: (block) @case.body
) @case.type

; Regular cases
(expression_case
  expression: (expression) @case.expression
  body: (block) @case.body
) @case.expression

; Default cases
(default_case
  body: (block) @case.default
) @case.default

; Select statements
(select_statement
  cases: (communication_case_list) @select.cases
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
  channel: (expression) @send.channel
  value: (expression) @send.value
) @send.statement

; Receive statements
(receive_statement
  channel: (expression) @receive.channel
  left: (expression) @receive.left
) @receive.statement

; Go statements
(go_statement
  expression: (expression) @go.expression
) @go.statement

; Defer statements
(defer_statement
  expression: (expression) @defer.expression
) @defer.statement

; If statements
(if_statement
  condition: (expression) @if.condition
  consequence: (block) @if.consequence
  alternative: (else_clause) @if.alternative
) @if.statement

; For statements
(for_statement
  init: (expression) @for.init
  condition: (expression) @for.condition
  update: (expression) @for.update
  body: (block) @for.body
) @for.statement

; For range statements
(for_statement
  left: (expression_list) @for.left
  right: (expression) @for.right
  body: (block) @for.body
) @for.range

; Switch statements
(switch_statement
  expression: (expression) @switch.expression
  cases: (expression_case_list) @switch.cases
) @switch.statement

; Return statements
(return_statement
  expression: (expression) @return.expression
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

; Index expressions
(index_expression
  operand: (expression) @index.operand
  index: (expression) @index.index
) @index.expression

; Slice expressions
(slice_expression
  operand: (expression) @slice.operand
  start: (expression) @slice.start
  end: (expression) @slice.end
) @slice.expression

; Selector expressions
(selector_expression
  operand: (expression) @selector.operand
  field: (field_identifier) @selector.field
) @selector.expression

; Composite literals
(composite_literal
  type: (type) @composite.type
  elements: (element_list) @composite.elements
) @composite.literal

; Keyed elements
(keyed_element
  key: (expression) @element.key
  value: (expression) @element.value
) @element.keyed

; Unkeyed elements
(unkeyed_element
  value: (expression) @element.value
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
  value: (type) @channel.value
) @channel.type

; Pointer types
(pointer_type
  base: (type) @pointer.base
) @pointer.type

; Array types
(array_type
  length: (expression) @array.length
  element: (type) @array.element
) @array.type

; Slice types
(slice_type
  element: (type) @slice.element
) @slice.type

; Map types
(map_type
  key: (type) @map.key
  value: (type) @map.value
) @map.type

; Function types
(function_type
  parameters: (parameter_list) @func_type.params
  result: (type) @func_type.result
) @func_type.definition

; Interface types
(interface_type
  methods: (method_spec_list) @interface_type.methods
) @interface_type.definition

; Struct types
(struct_type
  fields: (field_declaration_list) @struct_type.fields
) @struct_type.definition

; Type assertions
(type_assertion
  expression: (expression) @assert.expression
  type: (type) @assert.type
) @assert.type

; Type switches
(type_switch_statement
  expression: (expression) @switch.expression
  cases: (type_case_list) @switch.cases
) @switch.type

; Type cases
(type_case
  type: (type) @case.type
  body: (block) @case.body
) @case.type

; Regular cases
(expression_case
  expression: (expression) @case.expression
  body: (block) @case.body
) @case.expression

; Default cases
(default_case
  body: (block) @case.default
) @case.default

; Select statements
(select_statement
  cases: (communication_case_list) @select.cases
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
  channel: (expression) @send.channel
  value: (expression) @send.value
) @send.statement

; Receive statements
(receive_statement
  channel: (expression) @receive.channel
  left: (expression) @receive.left
) @receive.statement

; Go statements
(go_statement
  expression: (expression) @go.expression
) @go.statement

; Defer statements
(defer_statement
  expression: (expression) @defer.expression
) @defer.statement

; ✨ NEW: Comments (single-line and block)
(comment) @comment

; ✨ NEW: Documentation comments
(comment) @comment.documentation
