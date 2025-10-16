import pytest
import tree_sitter
from grep_ast.tsl import get_language, get_parser
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.protocols import QueryLoaderProtocol, TagCacheProtocol
from repomap_tool.code_analysis.models import CodeTag
from pathlib import Path
from unittest.mock import Mock
from repomap_tool.code_analysis.query_loader import FileQueryLoader
from repomap_tool.core.logging_service import get_logger, configure_logging
import logging

logger = get_logger(__name__)

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

@pytest.fixture(scope="module")
def python_parser_and_query(tmp_path_factory):
    """Fixture for TreeSitterParser, Python language, and the query file content.

    Dynamically loads the python-tags.scm query file to ensure tests use the latest version
    and avoid caching issues that might hide problems during development.
    """
    # Ensure logging is configured
    configure_logging(level="DEBUG")

    # Create a temporary directory for the project root to ensure absolute paths
    # and to simulate a project structure.
    tmp_path = tmp_path_factory.mktemp("project_root_for_scm_integration")
    project_root = tmp_path.resolve()

    # Initialize a FileQueryLoader for the real .scm files
    query_loader = FileQueryLoader()

    # Initialize a mock cache that adheres to TagCacheProtocol
    # Note: For integration tests, we want to test the full stack,
    # so we'll pass a mock, but it still has to conform to the protocol.
    cache_mock = Mock(spec=TagCacheProtocol)
    cache_mock.get_tags.return_value = None
    cache_mock.set_tags.return_value = None
    cache_mock.invalidate_file.return_value = None
    cache_mock.clear.return_value = None
    cache_mock.get_cache_stats.return_value = {}

    ts_parser = TreeSitterParser(
        project_root=project_root,
        cache=cache_mock, # Use the mock cache here
        query_loader=query_loader,
    )

    language = get_language("python")
    # Directly read the query string to ensure no caching issues
    query_file_path = Path(__file__).parent.parent.parent.parent / "src" / "repomap_tool" / "code_analysis" / "queries" / "python-tags.scm"
    query_string = query_file_path.read_text()
    logger.debug(f"DEBUG: Full query string loaded from SCM:\n{query_string}") # Log full query string for debug
    query = tree_sitter.Query(language, query_string)
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
    \'\'\'This is a docstring for an async function.\'\'\'
    variable = "initial_value"
    with open("some_file.txt", "w") as f:
        f.write("hello")

    if arg1 > 0:
        for i in range(arg1):
            logger.debug(f"Loop {i}")
    else:
        while arg1 < 0:
            arg1 += 1

    try:
        await aio.sleep(1)
    except asyncio.CancelledError:
        logger.debug("Task was cancelled.")
    finally:
        logger.debug("Cleanup.")

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
    logger.debug(f"DEBUG: S-expression of code:\n{ts_parser.parse_file_to_sexp(str(temp_file))}") # Log S-expression

    # Convert tags to a simpler structure for assertion
    actual_tags_simplified = [(tag.kind, tag.name) for tag in tags]
    logger.debug(f"Actual Tags: {actual_tags_simplified}") # Debug log

    expected_tags_simplified = [
        ("comment", "# Top-level comment"),
        ("function.docstring", '\'\'\'This is a docstring for an async function.\'\'\''),
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
        ("name.definition.parameter", "arg1"), # from the if statement
        ("call.name", "range"),
        ("name.reference.name", "i"), # from the for statement
        ("call.name.attribute", "debug"),
        ("name.reference.name", "arg1"), # from the while statement
        ("name.reference.name", "arg1"),
        ("call.name.attribute", "sleep"), # Awaiting a call
        ("name.reference.name", "asyncio"),
        ("name.reference.name", "CancelledError"),
        ("lambda.parameter", "x"),
        ("lambda.body", "x * 2"),
        ("comprehension.iterator", "i"), # List comprehension iterator
        ("comprehension.iterator", "i"), # Dictionary comprehension iterator
        ("comprehension.iterator", "i"), # Generator expression iterator
        ("name.reference.name", "MyClass"),
        ("name.reference.name", "instance"),
        ("call.name.attribute", "my_method"),
    ]

    # Some tags might be captured multiple times, so we check for presence, not exact count initially
    for expected_kind, expected_name in expected_tags_simplified:
        assert any(tag_kind == expected_kind and tag_name == expected_name for tag_kind, tag_name in actual_tags_simplified), \
            f"Missing expected tag: Kind='{expected_kind}', Name='{expected_name}'"

    # Optional: More rigorous check for unexpected tags if desired
    # For now, focus on ensuring all expected tags are found.
