; TypeScript tree-sitter query for comprehensive code analysis
; Extends JavaScript with TypeScript-specific features

; Type imports
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

; Type-only imports
(import_statement
  import_clause: (type_import
    (named_imports
      (import_specifier
        name: (identifier) @import.type_only
      )
    )
  )
  source: (string) @import.source
) @import.type_only

; Interface imports
(import_statement
  import_clause: (named_imports
    (import_specifier
      name: (identifier) @import.interface
      alias: (identifier) @import.interface_alias
    )
  )
  source: (string) @import.source
) @import.interface

; Interface definitions
(interface_declaration
  name: (identifier) @interface.name
) @interface.declaration

; Type aliases
(type_alias_declaration
  name: (identifier) @type.name
) @type.alias

; Enum definitions
(enum_declaration
  name: (identifier) @enum.name
) @enum.declaration

; Namespace declarations
(namespace_declaration
  name: (identifier) @namespace.name
) @namespace.declaration

; Module declarations
(module_declaration
  name: (string) @module.name
) @module.declaration

; Generic function definitions
(function_declaration
  name: (identifier) @function.name
  type_parameters: (type_parameters) @function.type_params
) @function.generic

; Generic class definitions
(class_declaration
  name: (identifier) @class.name
  type_parameters: (type_parameters) @class.type_params
) @class.generic

; Method definitions with types
(method_definition
  name: (property_identifier) @method.name
  type_parameters: (type_parameters) @method.type_params
) @method.generic

; Property signatures
(property_signature
  name: (property_identifier) @property.name
  type: (type_annotation) @property.type
) @property.signature

; Method signatures
(method_signature
  name: (property_identifier) @method.name
  type_parameters: (type_parameters) @method.type_params
) @method.signature

; Call signatures
(call_signature
  type_parameters: (type_parameters) @call.type_params
) @call.signature

; Index signatures
(index_signature
  type: (type_annotation) @index.type
) @index.signature

; Type assertions
(type_assertion
  type: (type) @assertion.type
  expression: (expression) @assertion.expression
) @assertion.type

; As expressions
(as_expression
  expression: (expression) @as.expression
  type: (type) @as.type
) @as.expression

; Conditional types
(conditional_type
  left: (type) @conditional.left
  right: (type) @conditional.right
) @conditional.type

; Mapped types
(mapped_type_clause
  name: (type_identifier) @mapped.name
  type: (type) @mapped.type
) @mapped.type

; Template literal types
(template_literal_type
  (template_substitution
    type: (type) @template.type
  )
) @template.literal

; Union types
(union_type
  (type) @union.type
) @union.type

; Intersection types
(intersection_type
  (type) @intersection.type
) @intersection.type

; Function type definitions
(function_type
  type_parameters: (type_parameters) @function_type.type_params
) @function_type.definition

; Array types
(array_type
  element: (type) @array.element
) @array.type

; Tuple types
(tuple_type
  (type) @tuple.type
) @tuple.type

; Optional types
(optional_type
  type: (type) @optional.type
) @optional.type

; Rest types
(rest_type
  type: (type) @rest.type
) @rest.type

; Readonly types
(readonly_type
  type: (type) @readonly.type
) @readonly.type

; Keyof types
(keyof_type
  type: (type) @keyof.type
) @keyof.type

; Typeof types
(typeof_type
  expression: (expression) @typeof.expression
) @typeof.type

; Indexed access types
(indexed_access_type
  object: (type) @indexed.object
  index: (type) @indexed.index
) @indexed.access

; Conditional expressions
(conditional_expression
  condition: (expression) @conditional.condition
  consequence: (expression) @conditional.consequence
  alternative: (expression) @conditional.alternative
) @conditional.expression

; Type parameters
(type_parameters
  (type_parameter
    name: (type_identifier) @type_param.name
    constraint: (type) @type_param.constraint
    default: (type) @type_param.default
  )
) @type_param.definition

; Type annotations
(type_annotation
  type: (type) @annotation.type
) @annotation.type

; Parameter types
(formal_parameters
  (required_parameter
    pattern: (identifier) @param.name
    type: (type_annotation) @param.type
  )
) @param.required

(formal_parameters
  (optional_parameter
    pattern: (identifier) @param.name
    type: (type_annotation) @param.type
  )
) @param.optional

; Rest parameters
(formal_parameters
  (rest_parameter
    pattern: (identifier) @param.name
    type: (type_annotation) @param.type
  )
) @param.rest

; Decorators
(decorator
  expression: (call_expression) @decorator.call
) @decorator.expression

; JSDoc comments
(comment) @jsdoc.comment

; Export type statements
(export_statement
  declaration: (type_alias_declaration
    name: (identifier) @export.type
  )
) @export.type

(export_statement
  declaration: (interface_declaration
    name: (identifier) @export.interface
  )
) @export.interface

(export_statement
  declaration: (enum_declaration
    name: (identifier) @export.enum
  )
) @export.enum
