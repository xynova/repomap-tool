import pytest
import tree_sitter
from grep_ast.tsl import get_language, get_parser
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.code_analysis.models import CodeTag
from pathlib import Path
from typing import List, Tuple
from unittest.mock import Mock
from repomap_tool.protocols import QueryLoaderProtocol, TagCacheProtocol
from tree_sitter import Parser, QueryCursor


@pytest.fixture
def mock_cache():
    """A mock cache object for testing purposes."""
    mock = Mock(spec=TagCacheProtocol)
    mock.get_tags.return_value = None
    mock.set_tags.return_value = None
    mock.invalidate_file.return_value = None
    mock.clear.return_value = None
    mock.get_cache_stats.return_value = {}
    return mock


@pytest.fixture
def mock_query_loader():
    """A mock QueryLoader that can return specific query strings for testing."""
    mock = Mock(spec=QueryLoaderProtocol)
    # By default, it returns None, so tests must set side_effect or return_value
    mock.load_query.return_value = None
    return mock


def test_import_statements(tmp_path, mock_cache: Mock, mock_query_loader: Mock):
    language = get_language("python")
    import_query_string = """
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
"""
    mock_query_loader.load_query.return_value = import_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    # query = tree_sitter.Query(language, import_query_string)

    code = """
import os
from sys import argv as my_argv
import asyncio as aio
from collections import defaultdict as dd
from . import local_module
from ..another_module import some_func
"""
    temp_file = tmp_path / "temp_imports.py"
    temp_file.write_text(code)

    # Directly use the query object with ts_parser to get tags
    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")

    expected_tags_simplified = [
        ("name.reference.import", "os"),
        ("name.reference.import.module", "sys"),
        ("name.definition.import_alias", "my_argv"),
        ("name.reference.import", "asyncio"),
        ("name.definition.import_alias", "aio"),
        ("name.reference.import.module", "collections"),
        ("name.definition.import_alias", "dd"),
        ("import.relative_prefix", "."),
        ("name.reference.import", "local_module"),
        ("import.relative_prefix", ".."),
        ("name.reference.import.module", "another_module"),
        ("name.reference.import", "some_func"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_class_and_function_definitions(
    tmp_path, mock_cache: Mock, mock_query_loader: Mock
):
    # ts_parser = TreeSitterParser()
    language = get_language("python")
    class_func_query_string = """
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
"""
    mock_query_loader.load_query.return_value = class_func_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    # query = tree_sitter.Query(language, class_func_query_string)

    code = """
class MyClass:
    def __init__(self):
        pass

def my_function(arg):
    pass

async def my_async_function():
    pass

class AnotherClass:
    async def my_async_method(self):
        pass

@decorator
def decorated_function():
    pass

@another_decorator
class DecoratedClass:
    pass
"""
    temp_file = tmp_path / "temp_class_func.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")

    expected_tags_simplified = [
        ("name.definition.class", "MyClass"),
        ("name.definition.method", "__init__"),
        ("name.definition.function", "my_function"),
        ("name.definition.async_function", "my_async_function"),
        ("name.definition.class", "AnotherClass"),
        ("name.definition.async_method", "my_async_method"),
        ("name.definition.function", "decorated_function"),
        ("name.definition.class", "DecoratedClass"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_calls_and_references(tmp_path, mock_cache: Mock, mock_query_loader: Mock):
    language = get_language("python")
    calls_refs_query_string = """
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
(identifier) @reference.name
"""
    mock_query_loader.load_query.return_value = calls_refs_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    # query = tree_sitter.Query(language, calls_refs_query_string)

    code = """
import math

def my_function():
    return "hello"

class MyClass:
    def my_method(self):
        return 1

value = my_function()
result = MyClass().my_method()
x = 10
y = x + value
math.sqrt(y)
"""
    temp_file = tmp_path / "temp_calls_refs.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")

    expected_tags_simplified = [
        ("reference.name", "math"),
        ("call.name", "my_function"),
        ("reference.name", "my_function"),
        ("reference.name", "MyClass"),
        ("call.name", "my_method"),
        ("reference.name", "my_method"),
        ("reference.name", "value"),
        ("reference.name", "x"),
        ("reference.name", "y"),
        ("call.name", "sqrt"),
        ("reference.name", "math"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_assignments_and_parameters(
    tmp_path, mock_cache: Mock, mock_query_loader: Mock
):
    language = get_language("python")
    assign_params_query_string = """
; Capture assigned variables (left-hand side of assignment)
(assignment
  left: (identifier) @name.definition.variable
)
"""
    mock_query_loader.load_query.return_value = assign_params_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    # query = tree_sitter.Query(language, assign_params_query_string)

    code = """
x = 10
y: int = 20
z = "hello"

def func(a, b: str, c=True, *, d, **kwargs):
    local_var = a + b
    return local_var

class MyClass:
    def __init__(self, name: str, age=0, *args, **attrs):
        pass
"""
    temp_file = tmp_path / "temp_assign_params.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")

    expected_tags_simplified = [
        ("name.definition.variable", "x"),
        ("name.definition.variable", "y"),
        ("name.definition.variable", "z"),
        ("name.definition.variable", "local_var"),
        # "self.name" and "self.age" are not simple identifiers in assignments,
        # they are attribute assignments and require a different query pattern.
        # Removing them for this iteration to focus on basic assignments.
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_advanced_constructs(tmp_path, mock_cache: Mock, mock_query_loader: Mock):
    language = get_language("python")
    advanced_query_string = """
; Capture lambda functions
(lambda
  parameters: (lambda_parameters (identifier) @lambda.parameter)?
  body: (expression) @lambda.body
)

; Capture list comprehensions
(list_comprehension
  (for_in_clause
    (identifier) @comprehension.iterator
  )
)

; Capture dictionary comprehensions
(dictionary_comprehension
  (for_in_clause
    (identifier) @comprehension.iterator
  )
)

; Capture generator expressions
(generator_expression
  (for_in_clause
    (identifier) @comprehension.iterator
  )
)
"""
    mock_query_loader.load_query.return_value = advanced_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    # query = tree_sitter.Query(language, advanced_query_string)

    code = """
def process_data(data):
    # Lambda function
    square = lambda x: x * x
    add = lambda a, b: a + b

    # List comprehension
    squares = [x*x for x in data if x > 0]

    # Dictionary comprehension
    cubes_dict = {x: x*x*x for x in data if x < 10}

    # Generator expression
    gen_exp = (x for x in data if x % 2 == 0)

    return square(add(1, 2))
"""
    temp_file = tmp_path / "temp_advanced.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")

    expected_tags_simplified = [
        ("lambda.parameter", "x"),
        ("lambda.body", "x * x"),
        ("lambda.parameter", "a"),
        ("lambda.parameter", "b"),
        ("lambda.body", "a + b"),
        ("comprehension.iterator", "x"),
        ("comprehension.iterator", "x"),
        ("comprehension.iterator", "x"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_with_statement_variable_capture(
    tmp_path, mock_cache: Mock, mock_query_loader: Mock
):
    language = get_language("python")
    with_query_string = """
; Capture variable definition in a 'with' statement (e.g., 'with open() as f:')
(with_item
  (as_pattern
    alias: (as_pattern_target (identifier) @name.definition.variable)
  )
)
"""
    mock_query_loader.load_query.return_value = with_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )

    code = """
with open("file.txt", "r") as f:
    pass
with MyContext() as ctx, another_resource as res:
    pass
"""
    temp_file = tmp_path / "temp_with.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")
    print(
        f"DEBUG: S-expression of code:\n{ts_parser.parse_file_to_sexp(str(temp_file))}"
    )

    expected_tags_simplified = [
        ("name.definition.variable", "f"),
        ("name.definition.variable", "ctx"),
        ("name.definition.variable", "res"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"


def test_function_parameter_capture(
    tmp_path, mock_cache: Mock, mock_query_loader: Mock
):
    language = get_language("python")
    param_query_string = """
; Capture simple parameters (e.g., 'a')
(function_definition
  parameters: (parameters
    (identifier) @name.definition.parameter
  )
)

; Capture typed parameters (e.g., 'b: str')
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
"""
    mock_query_loader.load_query.return_value = param_query_string
    ts_parser = TreeSitterParser(
        project_root=tmp_path.resolve(),
        cache=mock_cache,
        query_loader=mock_query_loader,
    )

    code = """
def func(a, b: str, c=True, *, d, **kwargs):
    pass

class MyClass:
    def __init__(self, name: str, age=0, *args, **attrs):
        pass
"""
    temp_file = tmp_path / "temp_params.py"
    temp_file.write_text(code)

    tags = ts_parser.get_tags(str(temp_file))
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    print(f"Actual Tags: {actual_tags_simplified}")
    print(
        f"DEBUG: S-expression of code:\n{ts_parser.parse_file_to_sexp(str(temp_file))}"
    )

    expected_tags_simplified = [
        ("name.definition.parameter", "a"),
        ("name.definition.parameter", "b"),
        ("name.definition.parameter", "c"),
        ("name.definition.parameter", "d"),
        ("name.definition.parameter.splat", "kwargs"),
        ("name.definition.parameter", "self"),
        ("name.definition.parameter", "name"),
        ("name.definition.parameter", "age"),
        ("name.definition.parameter.splat", "args"),
        ("name.definition.parameter.splat", "attrs"),
    ]

    for expected_kind, expected_name in expected_tags_simplified:
        assert any(
            tag_kind == expected_kind and tag_name == expected_name
            for tag_kind, tag_name in actual_tags_simplified
        ), f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"
