; Capture comments
(comment) @comment

; Capture docstrings (string literals as immediate children of definitions or modules)
(expression_statement
  (string) @module.docstring
)
(function_definition
  body: (block
    (expression_statement (string) @function.docstring)
  )
)
(class_definition
  body: (block
    (expression_statement (string) @class.docstring)
  )
)

; Capture direct imports like `import os`
(import_statement
  (dotted_name (identifier) @name.reference.import))

; Capture the module name in `from sys import ...`
(import_from_statement
  module_name: (dotted_name (identifier) @name.reference.import.module))

; Capture the module name in `from ..another_module import ...`
(import_from_statement
  module_name: (relative_import
    (dotted_name (identifier) @name.reference.import.module)
  )
)

; Capture relative import prefixes like `.` or `..`
(import_from_statement
  module_name: (relative_import (import_prefix) @import.relative_prefix))

; Capture individual imported names like `local_module` or `some_func` directly from the import list
(import_from_statement
  (dotted_name (identifier) @name.reference.import) @reference.import.item
)

; Capture aliased imports like `argv as my_argv`
(aliased_import
  name: (dotted_name (identifier) @name.reference.import)
  alias: (identifier) @name.definition.import_alias)

; Capture class definitions
(class_definition
  name: (identifier) @name.definition.class
)

; Capture regular function definitions
(function_definition
  name: (identifier) @name.definition.function
)

; Capture async function definitions
(function_definition
  "async" @keyword.async
  name: (identifier) @name.definition.async_function
)

; Capture method definitions within a class
(class_definition
  body: (block
    (function_definition
      name: (identifier) @name.definition.method
    )
  )
)

; Capture simple parameters (e.g., 'a')
(function_definition
  parameters: (parameters
    (identifier) @name.definition.parameter
  )
)

; Capture typed parameters (e.g., 'b: str', 'name: str')
(typed_parameter
  (identifier) @name.definition.parameter
  ":"
  type: (type)
)

; Capture default parameters (e.g., 'c=True', 'age=0')
(default_parameter
  name: (identifier) @name.definition.parameter
)

; Capture list splat patterns (e.g., '*args')
(list_splat_pattern
  (identifier) @name.definition.parameter.splat
)

; Capture dictionary splat patterns (e.g., '**kwargs')
(dictionary_splat_pattern
  (identifier) @name.definition.parameter.splat
)

; Capture function calls (basic, non-method calls)
(call
  function: (identifier) @call.name
)

; Capture simple variable assignments
(assignment
  left: (identifier) @name.definition.variable
)

; Capture calls to attributes (e.g., logger.debug)
(call
  function: (attribute
    attribute: (identifier) @call.name.attribute
  )
)

; Capture loop variables in for statements
(for_statement
  left: (identifier) @name.definition.variable
)

; Capture variable definition in a 'with' statement (e.g., 'with open() as f:')
(with_item
  (as_pattern
    alias: (as_pattern_target (identifier) @name.definition.variable)
  )
)

; Capture identifiers in expressions as general references
(expression
  (identifier) @name.reference.name
)

; Capture comprehension iterators (e.g., 'i' in '[i for i in range(10)]')
(for_in_clause
  left: (identifier) @comprehension.iterator
)

; Capture lambda parameters
(lambda
  parameters: (lambda_parameters
    (identifier) @lambda.parameter
  )
)

; Capture lambda body
(lambda
  body: (expression) @lambda.body
)
