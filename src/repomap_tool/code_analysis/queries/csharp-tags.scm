; C# tree-sitter query for comprehensive code analysis
; Captures using directives, namespace declarations, class definitions, method definitions, and calls

; Using directives
(using_directive
  (identifier) @using.name
) @using.directive

; Using static directives
(using_static_directive
  (identifier) @using.static
) @using.static

; Using alias directives
(using_alias_directive
  alias: (identifier) @using.alias
  name: (identifier) @using.name
) @using.alias

; Global using directives
(global_using_directive
  (identifier) @using.global
) @using.global

; Namespace declarations
(namespace_declaration
  name: (qualified_name) @namespace.name
  body: (declaration_list) @namespace.body
) @namespace.declaration

; File-scoped namespace declarations
(file_scoped_namespace_declaration
  name: (qualified_name) @namespace.name
  body: (declaration_list) @namespace.body
) @namespace.file_scoped

; Class declarations
(class_declaration
  name: (identifier) @class.name
  type_parameter_list: (type_parameter_list) @class.type_params
  base_list: (base_list) @class.base
) @class.declaration

; Interface declarations
(interface_declaration
  name: (identifier) @interface.name
  type_parameter_list: (type_parameter_list) @interface.type_params
  base_list: (base_list) @interface.base
) @interface.declaration

; Struct declarations
(struct_declaration
  name: (identifier) @struct.name
  type_parameter_list: (type_parameter_list) @struct.type_params
  base_list: (base_list) @struct.base
) @struct.declaration

; Enum declarations
(enum_declaration
  name: (identifier) @enum.name
  base_list: (base_list) @enum.base
) @enum.declaration

; Delegate declarations
(delegate_declaration
  name: (identifier) @delegate.name
  type_parameter_list: (type_parameter_list) @delegate.type_params
  parameters: (parameter_list) @delegate.params
  return_type: (type) @delegate.return
) @delegate.declaration

; Method declarations
(method_declaration
  name: (identifier) @method.name
  type_parameter_list: (type_parameter_list) @method.type_params
  parameters: (parameter_list) @method.params
  return_type: (type) @method.return
) @method.declaration

; Constructor declarations
(constructor_declaration
  name: (identifier) @constructor.name
  parameters: (parameter_list) @constructor.params
) @constructor.declaration

; Destructor declarations
(destructor_declaration
  name: (identifier) @destructor.name
) @destructor.declaration

; Property declarations
(property_declaration
  name: (identifier) @property.name
  type: (type) @property.type
) @property.declaration

; Indexer declarations
(indexer_declaration
  parameters: (bracketed_parameter_list) @indexer.params
  type: (type) @indexer.type
) @indexer.declaration

; Event declarations
(event_declaration
  name: (identifier) @event.name
  type: (type) @event.type
) @event.declaration

; Field declarations
(field_declaration
  declarator: (variable_declarator
    name: (identifier) @field.name
  )
  type: (type) @field.type
) @field.declaration

; Local variable declarations
(local_declaration_statement
  declarator: (variable_declarator
    name: (identifier) @variable.name
  )
  type: (type) @variable.type
) @variable.declaration

; Method invocations
(invocation_expression
  function: (identifier) @call.method
  arguments: (argument_list) @call.args
) @call.method

; Method invocations with object
(invocation_expression
  function: (member_access_expression
    object: (expression) @call.object
    name: (identifier) @call.method
  )
  arguments: (argument_list) @call.args
) @call.object_method

; Constructor invocations
(object_creation_expression
  type: (type) @call.constructor
  arguments: (argument_list) @call.args
) @call.constructor

; Array creation expressions
(array_creation_expression
  type: (array_type) @array.type
  initializer: (array_initializer) @array.initializer
) @array.creation

; Collection expressions
(collection_expression
  elements: (expression_list) @collection.elements
) @collection.expression

; Base expressions
(base_expression) @base.expression

; This expressions
(this_expression) @this.expression

; Attribute lists
(attribute_list
  (attribute
    name: (identifier) @attribute.name
    argument_list: (attribute_argument_list) @attribute.args
  )
) @attribute.usage

; Generic attributes
(attribute
  name: (generic_name
    name: (identifier) @attribute.name
    type_argument_list: (type_argument_list) @attribute.type_args
  )
) @attribute.generic

; Type parameters
(type_parameter_list
  (type_parameter
    name: (identifier) @type_param.name
    constraints: (type_parameter_constraints) @type_param.constraints
  )
) @type_param.definition

; Type arguments
(type_argument_list
  (type) @type_arg.type
) @type_arg.usage

; Generic types
(generic_name
  name: (identifier) @generic.name
  type_argument_list: (type_argument_list) @generic.type_args
) @generic.usage

; Array types
(array_type
  element: (type) @array.element
  rank_specifiers: (array_rank_specifier) @array.rank
) @array.type

; Pointer types
(pointer_type
  base: (type) @pointer.base
) @pointer.type

; Nullable types
(nullable_type
  base: (type) @nullable.base
) @nullable.type

; Tuple types
(tuple_type
  elements: (tuple_element_list) @tuple.elements
) @tuple.type

; Tuple elements
(tuple_element
  type: (type) @tuple_element.type
  identifier: (identifier) @tuple_element.name
) @tuple_element.definition

; Function pointer types
(function_pointer_type
  calling_convention: (calling_convention) @func_ptr.calling_convention
  parameters: (function_pointer_parameter_list) @func_ptr.params
  return_type: (type) @func_ptr.return
) @func_ptr.type

; Lambda expressions
(lambda_expression
  parameters: (parameter_list) @lambda.params
  body: (expression) @lambda.body
) @lambda.expression

; Parenthesized lambda expressions
(parenthesized_lambda_expression
  parameters: (parameter_list) @lambda.params
  body: (block) @lambda.body
) @lambda.parenthesized

; Anonymous object creation
(anonymous_object_creation_expression
  initializer: (object_initializer) @anonymous.initializer
) @anonymous.creation

; Object initializers
(object_initializer
  (assignment_expression
    left: (identifier) @init.property
    right: (expression) @init.value
  )
) @init.assignment

; Collection initializers
(collection_initializer
  (expression) @collection.element
) @collection.initializer

; Try-catch-finally blocks
(try_statement
  body: (block) @try.body
  catch_clause: (catch_clause) @try.catch
  finally_clause: (finally_clause) @try.finally
) @try.statement

; Catch clauses
(catch_clause
  declaration: (catch_declaration
    type: (type) @catch.type
    identifier: (identifier) @catch.name
  )
  body: (block) @catch.body
) @catch.clause

; Finally clauses
(finally_clause
  body: (block) @finally.body
) @finally.clause

; Throw statements
(throw_statement
  expression: (expression) @throw.expression
) @throw.statement

; Using statements
(using_statement
  declaration: (local_declaration_statement) @using.declaration
  body: (block) @using.body
) @using.statement

; Using expressions
(using_expression
  expression: (expression) @using.expression
  body: (block) @using.body
) @using.expression

; Lock statements
(lock_statement
  expression: (expression) @lock.expression
  body: (block) @lock.body
) @lock.statement

; Fixed statements
(fixed_statement
  declaration: (variable_declaration) @fixed.declaration
  body: (block) @fixed.body
) @fixed.statement

; Checked statements
(checked_statement
  body: (block) @checked.body
) @checked.statement

; Unchecked statements
(unchecked_statement
  body: (block) @unchecked.body
) @unchecked.statement

; Unsafe statements
(unsafe_statement
  body: (block) @unsafe.body
) @unsafe.statement

; Switch expressions
(switch_expression
  governing_expression: (expression) @switch.expression
  arms: (switch_expression_arm_list) @switch.arms
) @switch.expression

; Switch expression arms
(switch_expression_arm
  pattern: (pattern) @switch_arm.pattern
  when_clause: (when_clause) @switch_arm.when
  expression: (expression) @switch_arm.expression
) @switch_arm.definition

; Switch statements
(switch_statement
  expression: (expression) @switch.expression
  body: (block) @switch.body
) @switch.statement

; Switch sections
(switch_section
  labels: (switch_label_list) @switch_section.labels
  statements: (statement_list) @switch_section.statements
) @switch_section.definition

; Case labels
(case_switch_label
  value: (expression) @case.value
) @case.label

; Default labels
(default_switch_label) @default.label

; Pattern matching
(is_pattern_expression
  expression: (expression) @pattern.expression
  pattern: (pattern) @pattern.pattern
) @pattern.is

; Declaration patterns
(declaration_pattern
  type: (type) @pattern.type
  designation: (variable_designation) @pattern.designation
) @pattern.declaration

; Constant patterns
(constant_pattern
  value: (expression) @pattern.value
) @pattern.constant

; Var patterns
(var_pattern
  designation: (variable_designation) @pattern.designation
) @pattern.var

; Discard patterns
(discard_pattern) @pattern.discard

; Parenthesized patterns
(parenthesized_pattern
  pattern: (pattern) @pattern.inner
) @pattern.parenthesized

; Type patterns
(type_pattern
  type: (type) @pattern.type
) @pattern.type

; Relational patterns
(relational_pattern
  operator: (relational_operator) @pattern.operator
  expression: (expression) @pattern.expression
) @pattern.relational

; Logical patterns
(logical_pattern
  left: (pattern) @pattern.left
  operator: (logical_operator) @pattern.operator
  right: (pattern) @pattern.right
) @pattern.logical

; List patterns
(list_pattern
  elements: (pattern_list) @pattern.elements
) @pattern.list

; Slice patterns
(slice_pattern
  start: (pattern) @pattern.start
  end: (pattern) @pattern.end
) @pattern.slice

; Conditional expressions
(conditional_expression
  condition: (expression) @conditional.condition
  consequence: (expression) @conditional.consequence
  alternative: (expression) @conditional.alternative
) @conditional.expression

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

; Assignment expressions
(assignment_expression
  left: (expression) @assignment.left
  right: (expression) @assignment.right
) @assignment.expression

; Compound assignment expressions
(compound_assignment_expression
  left: (expression) @assignment.left
  operator: (compound_assignment_operator) @assignment.operator
  right: (expression) @assignment.right
) @assignment.compound

; Postfix unary expressions
(postfix_unary_expression
  operand: (expression) @postfix.operand
  operator: (postfix_unary_operator) @postfix.operator
) @postfix.expression

; Prefix unary expressions
(prefix_unary_expression
  operator: (prefix_unary_operator) @prefix.operator
  operand: (expression) @prefix.operand
) @prefix.expression

; Cast expressions
(cast_expression
  type: (type) @cast.type
  value: (expression) @cast.value
) @cast.expression

; As expressions
(as_expression
  expression: (expression) @as.expression
  type: (type) @as.type
) @as.expression

; Is expressions
(is_expression
  expression: (expression) @is.expression
  type: (type) @is.type
) @is.expression

; Parenthesized expressions
(parenthesized_expression
  expression: (expression) @paren.expression
) @paren.expression

; Element access expressions
(element_access_expression
  expression: (expression) @element.expression
  argument_list: (bracketed_argument_list) @element.args
) @element.access

; Member access expressions
(member_access_expression
  expression: (expression) @member.expression
  name: (identifier) @member.name
) @member.access

; Conditional access expressions
(conditional_access_expression
  expression: (expression) @conditional.expression
  when_not_null: (expression) @conditional.when_not_null
) @conditional.access

; String literals
(string_literal) @string.literal

; Interpolated strings
(interpolated_string_expression
  (interpolated_string_text) @interpolated.text
  (interpolation
    expression: (expression) @interpolated.expression
  )
) @interpolated.string

; Character literals
(character_literal) @char.literal

; Integer literals
(integer_literal) @int.literal

; Real literals
(real_literal) @real.literal

; Boolean literals
(boolean_literal) @bool.literal

; Null literals
(null_literal) @null.literal

; Type identifiers
(type_identifier) @type.identifier

; Qualified names
(qualified_name
  left: (identifier) @qualified.left
  right: (identifier) @qualified.right
) @qualified.name

; Generic names
(generic_name
  name: (identifier) @generic.name
  type_argument_list: (type_argument_list) @generic.type_args
) @generic.name

; Predefined types
(predefined_type) @predefined.type

; Void types
(void_keyword) @void.type

; Var types
(var) @var.type

; Ref types
(ref_type
  type: (type) @ref.type
) @ref.type

; Out types
(out_type
  type: (type) @out.type
) @out.type

; In types
(in_type
  type: (type) @in.type
) @in.type

; Readonly types
(readonly_type
  type: (type) @readonly.type
) @readonly.type

; Const types
(const_type
  type: (type) @const.type
) @const.type

; Volatile types
(volatile_type
  type: (type) @volatile.type
) @volatile.type

; Unsafe types
(unsafe_type
  type: (type) @unsafe.type
) @unsafe.type

; Stackalloc expressions
(stackalloc_expression
  type: (type) @stackalloc.type
  initializer: (array_initializer) @stackalloc.initializer
) @stackalloc.expression

; Sizeof expressions
(sizeof_expression
  type: (type) @sizeof.type
) @sizeof.expression

; Typeof expressions
(typeof_expression
  type: (type) @typeof.type
) @typeof.expression

; Nameof expressions
(nameof_expression
  expression: (expression) @nameof.expression
) @nameof.expression

; Default expressions
(default_expression
  type: (type) @default.type
) @default.expression

; Make ref expressions
(make_ref_expression
  expression: (expression) @make_ref.expression
) @make_ref.expression

; Ref value expressions
(ref_value_expression
  expression: (expression) @ref_value.expression
) @ref_value.expression

; Ref type expressions
(ref_type_expression
  expression: (expression) @ref_type.expression
) @ref_type.expression

; With expressions
(with_expression
  expression: (expression) @with.expression
  initializer: (object_initializer) @with.initializer
) @with.expression

; Range expressions
(range_expression
  left: (expression) @range.left
  right: (expression) @range.right
) @range.expression

; Index expressions
(index_expression
  expression: (expression) @index.expression
  argument_list: (bracketed_argument_list) @index.args
) @index.expression

; Conditional expressions
(conditional_expression
  condition: (expression) @conditional.condition
  consequence: (expression) @conditional.consequence
  alternative: (expression) @conditional.alternative
) @conditional.expression

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

; Assignment expressions
(assignment_expression
  left: (expression) @assignment.left
  right: (expression) @assignment.right
) @assignment.expression

; Compound assignment expressions
(compound_assignment_expression
  left: (expression) @assignment.left
  operator: (compound_assignment_operator) @assignment.operator
  right: (expression) @assignment.right
) @assignment.compound

; Postfix unary expressions
(postfix_unary_expression
  operand: (expression) @postfix.operand
  operator: (postfix_unary_operator) @postfix.operator
) @postfix.expression

; Prefix unary expressions
(prefix_unary_expression
  operator: (prefix_unary_operator) @prefix.operator
  operand: (expression) @prefix.operand
) @prefix.expression

; Cast expressions
(cast_expression
  type: (type) @cast.type
  value: (expression) @cast.value
) @cast.expression

; As expressions
(as_expression
  expression: (expression) @as.expression
  type: (type) @as.type
) @as.expression

; Is expressions
(is_expression
  expression: (expression) @is.expression
  type: (type) @is.type
) @is.expression

; Parenthesized expressions
(parenthesized_expression
  expression: (expression) @paren.expression
) @paren.expression

; Element access expressions
(element_access_expression
  expression: (expression) @element.expression
  argument_list: (bracketed_argument_list) @element.args
) @element.access

; Member access expressions
(member_access_expression
  expression: (expression) @member.expression
  name: (identifier) @member.name
) @member.access

; Conditional access expressions
(conditional_access_expression
  expression: (expression) @conditional.expression
  when_not_null: (expression) @conditional.when_not_null
) @conditional.access
