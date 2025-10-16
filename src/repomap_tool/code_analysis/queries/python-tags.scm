; Capture comments
(comment) @comment

; Capture docstrings (string literals as immediate children of definitions or modules)
(expression_statement
  (string) @docstring
)
(function_definition
  body: (block
    (expression_statement (string) @docstring)
  )
)
(class_definition
  body: (block
    (expression_statement (string) @docstring)
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

; Capture async method definitions within a class
(class_definition
  body: (block
    (function_definition
      "async" @keyword.async
      name: (identifier) @name.definition.async_method
    )
  )
)

; Capture assigned variables (left-hand side of assignment)
(assignment
  left: (identifier) @name.definition.variable
)

; Capture variables from 'with ... as' statements
(with_item
  value: (as_pattern
    alias: (as_pattern_target
      (identifier) @name.definition.variable
    )
  )
)

; Capture function calls
(call
  function: (identifier) @call.name
)

; Capture method calls (attribute access followed by call)
(call
  function: (attribute
    attribute: (identifier) @call.name
  )
)

; Capture variable references
(identifier) @name.reference.name

; Capture lambda function parameters
(lambda_parameters
  (identifier) @lambda.parameter
)

; Capture lambda function body
(lambda
  body: (expression) @lambda.body
)

; Capture comprehension iterators
(for_in_clause
  left: (identifier) @comprehension.iterator
)
