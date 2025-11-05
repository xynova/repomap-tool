import os
from collections import defaultdict as ddict
import tree_sitter
from grep_ast.tsl import get_language, get_parser

def print_ast(node, indent=0):
    indent_str = "  " * indent
    print(f"{indent_str}{node.type}: {node.text.decode('utf-8').strip()}")
    for child in node.children:
        print_ast(child, indent + 1)

python_code = """
import os
from collections import defaultdict as ddict

class MyClass:
    def my_method(self, arg1, arg2):
        x = 10
        y = self.my_method_call(x)
        return x + y

def my_function(param1):
    z = param1 + 5
    return z

my_global_var = "hello"
"""

# Get Python language and parser
python_language = get_language("python")
python_parser = get_parser("python")

# Parse the code
tree = python_parser.parse(bytes(python_code, "utf-8"))

# Print the AST
print("\n--- Python AST ---")
print_ast(tree.root_node)

# Test with a simple query
query_string = """
(import_statement
  (dotted_name) @import.module
)
(import_from_statement
  module_name: (dotted_name) @import.module
  (aliased_import
    name: (dotted_name) @import.name
    alias: (identifier) @import.alias
  )?
  (dotted_name) @import.name
)
(class_definition
  name: (identifier) @class.name
)
(function_definition
  name: (identifier) @function.name
)
"""

query = tree_sitter.Query(python_language, query_string)
query_cursor = tree_sitter.QueryCursor(query)
captures = query_cursor.captures(tree.root_node)

print("\n--- Query Captures ---")
if captures:
    if isinstance(captures, dict):
        for tag_kind, nodes in captures.items():
            print(f"Tag Kind: {tag_kind}")
            for node in nodes:
                print(f"  Node: {node.type}: {node.text.decode('utf-8').strip()}")
    else:
        print(f"Unexpected captures type: {type(captures)}. Expected dict.")
else:
    print("No captures found.")
