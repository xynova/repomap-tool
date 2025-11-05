import tree_sitter
from tree_sitter import Language, Parser
import os
import sys
from grep_ast.tsl import get_language, get_parser # Import from grep_ast

# The original code for checking LANGUAGE_SO_PATH is no longer needed
# as grep_ast handles language loading.
# try:
#     PY_LANGUAGE = Language(LANGUAGE_SO_PATH, 'python')
# except Exception as e:
#     print(f"Error loading Python language from {LANGUAGE_SO_PATH}: {e}", file=sys.stderr)
#     sys.exit(1)

try:
    PY_LANGUAGE = get_language('python') # Use grep_ast's get_language
except Exception as e:
    print(f"Error loading Python language: {e}", file=sys.stderr)
    sys.exit(1)

parser = get_parser('python') # Use grep_ast's get_parser
# parser.set_language(PY_LANGUAGE)

code = '''
class MyClass:
    def sync_method(self):
        pass

    async def async_method(self):
        pass

def my_function():
    with open('file.txt', 'r') as f:
        pass
'''

tree = parser.parse(code.encode('utf-8'))

def print_node(node, level=0):
    indent = '  ' * level
    print(f"{indent}{node.type} [start={node.start_point}, end={node.end_point}]")
    for child in node.children:
        print_node(child, level + 1)

print_node(tree.root_node)
