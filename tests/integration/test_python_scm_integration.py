import pytest
import tree_sitter
from grep_ast.tsl import get_language, get_parser
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.code_analysis.models import CodeTag
from pathlib import Path

@pytest.fixture(scope="function")
def python_parser_and_query():
    language = get_language("python")
    # Directly read the query string to ensure no caching issues
    query_file_path = Path(__file__).parent.parent.parent / "src" / "repomap_tool" / "code_analysis" / "queries" / "python-tags.scm"
    query_string = query_file_path.read_text()
    print(f"DEBUG: Query string loaded: {query_string[:200]}...") # Print first 200 chars for debug
    query = tree_sitter.Query(language, query_string)
    ts_parser = TreeSitterParser()
    return language, query, language, ts_parser

def test_comprehensive_python_patterns(python_parser_and_query, tmp_path):
    parser, query, language, ts_parser = python_parser_and_query
    code = """
# Top-level comment
import os
from sys import argv as my_argv
import asyncio as aio

@my_decorator
async def my_async_function(arg1: int) -> str:
    \"\"\"This is a docstring for an async function.\"\"\"
    variable = "initial_value"
    with open("some_file.txt", "w") as f:
        f.write("hello")

    if arg1 > 0:
        for i in range(arg1):
            print(f"Loop {i}")
    else:
        while arg1 < 0:
            arg1 += 1

    try:
        await aio.sleep(1)
    except asyncio.CancelledError:
        print("Task was cancelled.")
    finally:
        print("Cleanup.")

    lambda_func = lambda x: x * 2
    list_comp = [i for i in range(10)]
    dict_comp = {i: i**2 for i in range(10)}

    return "done"

class MyClass:
    def my_method(self):
        pass

instance = MyClass()
instance.my_method()
"""
    temp_file = tmp_path / "temp_comprehensive.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    print(f"DEBUG: S-expression of code:\n{ts_parser.parse_file_to_sexp(str(temp_file))}") # Print S-expression

    # Convert tags to a simpler structure for assertion
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}") # Debug print

    expected_tags_simplified = [
        ("comment", "# Top-level comment"),
        ("docstring", '"""This is a docstring for an async function."""'),
        ("name.reference.import", "os"),
        ("name.reference.import.module", "sys"),
        ("name.definition.import_alias", "my_argv"),
        ("name.reference.import", "asyncio"),
        ("name.definition.import_alias", "aio"),
        ("name.definition.class", "MyClass"),
        ("name.definition.method", "my_method"),
        ("name.definition.function", "my_async_function"),
        ("keyword.async", "async"),
        ("name.definition.variable", "variable"),
        ("name.definition.variable", "f"),
        ("name.reference.name", "arg1"), # from the if statement
        ("name.reference.name", "range"),
        ("name.reference.name", "i"), # from the for statement
        ("call.name", "print"),
        ("name.reference.name", "i"),
        ("name.reference.name", "arg1"), # from the while statement
        ("name.reference.name", "arg1"),
        ("call.name", "sleep"), # Awaiting a call
        ("name.reference.name", "asyncio"),
        ("name.reference.name", "CancelledError"),
        ("lambda.parameter", "x"),
        ("lambda.body", "x * 2"),
        ("comprehension.iterator", "i"), # List comprehension iterator
        ("comprehension.iterator", "i"), # Dictionary comprehension iterator
        ("comprehension.iterator", "i"), # Generator expression iterator
        ("name.reference.name", "MyClass"),
        ("name.reference.name", "instance"),
        ("call.name", "my_method"),
    ]
    
    # Some tags might be captured multiple times, so we check for presence, not exact count initially
    for expected_kind, expected_name in expected_tags_simplified:
        assert any(tag_kind == expected_kind and tag_name == expected_name for tag_kind, tag_name in actual_tags_simplified), \
            f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"

    # Optional: More rigorous check for unexpected tags if desired
    # For now, focus on ensuring all expected tags are found.
