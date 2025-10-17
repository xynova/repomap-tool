import pytest
import tree_sitter
from grep_ast.tsl import get_language, get_parser
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.code_analysis.models import CodeTag
from pathlib import Path

@pytest.fixture(scope="module")
def python_parser_and_query(session_tree_sitter_parser):
    language = get_language("python")
    parser = get_parser("python")
    # Use the injected TreeSitterParser fixture
    ts_parser = session_tree_sitter_parser
    query_string = ts_parser.query_loader.load_query("python")
    query = tree_sitter.Query(language, query_string)
    return parser, query, language, ts_parser

class TestPythonQueries:
    def test_class_definition(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
class MyClass:
    pass
"""
        # Create a temporary file for the code snippet
        temp_file = tmp_path / "temp_class.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        expected_tags = [
            CodeTag(name="MyClass", kind="name.definition.class", line=2, column=6, file=str(temp_file), end_line=2, end_column=13)
        ]

        # Filter out other tags if present (e.g., block.function)
        actual_class_tags = [tag for tag in tags if tag.kind == "name.definition.class" and tag.name == "MyClass"]
        
        assert len(actual_class_tags) == 1
        assert actual_class_tags[0].name == "MyClass"
        assert actual_class_tags[0].kind == "name.definition.class"
        # We can't assert on line/column precisely without knowing the query,
        # but we can check if it's roughly correct.
        assert actual_class_tags[0].line == 2
        assert actual_class_tags[0].column == 6

    def test_function_definition(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
def my_function(arg):
    return arg
"""
        temp_file = tmp_path / "temp_function.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        actual_function_tags = [tag for tag in tags if tag.kind == "name.definition.function" and tag.name == "my_function"]

        assert len(actual_function_tags) == 1
        assert actual_function_tags[0].name == "my_function"
        assert actual_function_tags[0].kind == "name.definition.function"
        assert actual_function_tags[0].line == 2
        assert actual_function_tags[0].column == 4

    def test_method_definition(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
class AnotherClass:
    def a_method(self):
        pass
"""
        temp_file = tmp_path / "temp_method.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        actual_method_tags = [tag for tag in tags if tag.kind == "name.definition.method" and tag.name == "a_method"]

        assert len(actual_method_tags) == 1
        assert actual_method_tags[0].name == "a_method"
        assert actual_method_tags[0].kind in ["name.definition.method", "name.definition.function"]
        assert actual_method_tags[0].line == 3
        assert actual_method_tags[0].column == 8

    def test_import_statement(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
import os
"""
        temp_file = tmp_path / "temp_import.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        actual_import_tags = [tag for tag in tags if tag.kind == "name.reference.import" and tag.name == "os"]

        assert len(actual_import_tags) == 1
        assert actual_import_tags[0].name == "os"
        assert actual_import_tags[0].kind == "name.reference.import"
        assert actual_import_tags[0].line == 2
        assert actual_import_tags[0].column == 7

    def test_import_from_statement(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
from collections import defaultdict as ddict
"""
        temp_file = tmp_path / "temp_import_from.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        module_tags = [tag for tag in tags if tag.kind == "name.reference.import.module" and tag.name == "collections"]
        name_tags = [tag for tag in tags if tag.kind == "name.reference.import" and tag.name == "defaultdict"]
        alias_tags = [tag for tag in tags if tag.kind == "name.definition.import_alias" and tag.name == "ddict"]

        assert len(module_tags) == 1
        assert module_tags[0].name == "collections"
        assert module_tags[0].kind == "name.reference.import.module"
        assert module_tags[0].line == 2
        assert module_tags[0].column == 5

        assert len(name_tags) == 1
        assert name_tags[0].name == "defaultdict"
        assert name_tags[0].kind == "name.reference.import"
        assert name_tags[0].line == 2
        assert name_tags[0].column == 24 # Corrected column
        
        assert len(alias_tags) == 1
        assert alias_tags[0].name == "ddict"
        assert alias_tags[0].kind == "name.definition.import_alias"
        assert alias_tags[0].line == 2
        assert alias_tags[0].column == 39

    def test_function_call(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
def foo():
    bar(1, 2)
    obj.method()
"""
        temp_file = tmp_path / "temp_function_call.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        # Filter for function call tags explicitly
        function_call_tags = [tag for tag in tags if tag.kind == "call.name"]
        method_call_tags = [tag for tag in tags if tag.kind == "call.name.attribute"]

        assert len(function_call_tags) == 1
        assert function_call_tags[0].name == "bar"
        assert function_call_tags[0].kind == "call.name"
        assert function_call_tags[0].line == 3
        assert function_call_tags[0].column == 4

        assert len(method_call_tags) == 1
        assert method_call_tags[0].name == "method"
        assert method_call_tags[0].kind == "call.name.attribute"
        assert method_call_tags[0].line == 4
        assert method_call_tags[0].column == 8

    def test_variable_definition(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
my_var = 10
another_var: int = 20
"""
        temp_file = tmp_path / "temp_variable_definition.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        variable_tags = [tag for tag in tags if tag.kind == "name.definition.variable"]

        assert len(variable_tags) == 2
        assert any(tag.name == "my_var" for tag in variable_tags)
        assert any(tag.name == "another_var" for tag in variable_tags)
        assert all(tag.kind == "name.definition.variable" for tag in variable_tags)
        assert variable_tags[0].name == "my_var"
        assert variable_tags[0].kind == "name.definition.variable"
        assert variable_tags[0].line == 2
        assert variable_tags[0].column == 0
        assert variable_tags[1].name == "another_var"
        assert variable_tags[1].kind == "name.definition.variable"
        assert variable_tags[1].line == 3
        assert variable_tags[1].column == 0

    def test_comment(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
# This is a comment
"""
        temp_file = tmp_path / "temp_comment.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        comment_tags = [tag for tag in tags if tag.kind == "comment"]

        assert len(comment_tags) == 1
        assert comment_tags[0].name == "# This is a comment"
        assert comment_tags[0].kind == "comment"
        assert comment_tags[0].line == 2

    def test_variable_definition_in_for_loop(self, python_parser_and_query, tmp_path):
        parser, query, language, ts_parser = python_parser_and_query
        code = """
for i in range(10):
    pass
"""
        temp_file = tmp_path / "temp_for_loop.py"
        temp_file.write_text(code)

        tags = ts_parser.get_tags(str(temp_file))

        variable_tags = [tag for tag in tags if tag.kind == "name.definition.variable" and tag.name == "i"]

        assert len(variable_tags) == 1
        assert variable_tags[0].name == "i"
        assert variable_tags[0].kind == "name.definition.variable"
        assert variable_tags[0].line == 2
