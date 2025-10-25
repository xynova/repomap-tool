"""
Session-scoped fixtures for unit tests.

This module provides shared fixtures that are loaded once per test session,
dramatically improving test performance by avoiding repeated parsing and
analysis of the same codebase.
"""

import os
import pytest
from pathlib import Path
from typing import Dict, List, Any, Set
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from tree_sitter import Language
import grep_ast.tsl as tsl
from grep_ast.tsl import get_language  # Import get_language
import click
from click.testing import CliRunner
from unittest.mock import patch
import io

# Cache is now enabled for tests - database locking issues have been resolved
# os.environ["REPOMAP_DISABLE_CACHE"] = "1"

# This makes tests run faster - otherwise it tries to re-parse the grammar files constantly
# and can take 5-10 seconds for each test. With pre-compiled, it's < 1 second.
# BUILD_DIR = Path("build")
# BUILD_DIR.mkdir(exist_ok=True)
# LANGUAGE_LIB_PATH = BUILD_DIR / "languages.so"

# # Build the languages library once per session (NOT SUPPORTED IN THIS VERSION OF TREE-SITTER)
# if not LANGUAGE_LIB_PATH.exists():
#     Language.build_library(
#         str(LANGUAGE_LIB_PATH),
#         [
#             "tmp/tree-sitter-python",
#             "tmp/tree-sitter-javascript",
#             "tmp/tree-sitter-go",
#             "tmp/tree-sitter-java",
#             "tmp/tree-sitter-typescript/typescript", # TypeScript has a nested grammar
#             "tmp/tree-sitter-c-sharp",
#         ],
#     )

# Load individual languages using grep_ast.tsl.get_language
LANGUAGE_PYTHON = get_language("python")
LANGUAGE_JAVASCRIPT = get_language("javascript")
LANGUAGE_GO = get_language("go")
LANGUAGE_JAVA = get_language("java")
LANGUAGE_TYPESCRIPT = get_language("typescript")
LANGUAGE_CSHARP = get_language("csharp")  # C# uses 'csharp' name


@pytest.fixture(scope="session")
def session_test_repo_path():
    """Path to the comprehensive test fixture repository."""
    return Path(__file__).parent / "fixtures" / "test-repo"


@pytest.fixture(scope="session")
def session_config(session_test_repo_path):
    """Base RepoMapConfig for all tests."""
    return RepoMapConfig(
        project_root=str(session_test_repo_path),
        verbose=False,
        fuzzy_match=FuzzyMatchConfig(),
        semantic_match=SemanticMatchConfig(),
        performance=PerformanceConfig(),
        dependencies=DependencyConfig(),
    )


@pytest.fixture(scope="session")
def session_tree_sitter_parser(session_test_repo_path) -> TreeSitterParser:
    """Provides a TreeSitterParser instance for the entire test session."""
    from repomap_tool.protocols import TagCacheProtocol, QueryLoaderProtocol
    from repomap_tool.code_analysis.query_loader import (
        FileQueryLoader,
    )  # Use real query loader
    from repomap_tool.core.tag_cache import TreeSitterTagCache  # Use real tag cache

    # Setup a temporary directory for the cache
    # Use TemporaryDirectory for proper cleanup
    import tempfile

    temp_cache_dir = tempfile.TemporaryDirectory()
    cache_path = Path(temp_cache_dir.name)

    mock_cache = TreeSitterTagCache(cache_dir=cache_path)  # Use real cache
    mock_query_loader = FileQueryLoader()  # Use real query loader

    # Ensure project_root is a Path object for the parser
    # Use the session_test_repo_path for the parser's project_root
    parser = TreeSitterParser(
        project_root=session_test_repo_path,
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    yield parser
    # Cleanup the temporary directory after the session
    temp_cache_dir.cleanup()


@pytest.fixture(scope="function")
def get_tree_sitter_parser_function_fixture(session_test_repo_path) -> TreeSitterParser:
    """Provides a TreeSitterParser instance for each test function."""
    from repomap_tool.protocols import TagCacheProtocol, QueryLoaderProtocol
    from repomap_tool.code_analysis.query_loader import (
        FileQueryLoader,
    )  # Use real query loader
    from repomap_tool.core.tag_cache import TreeSitterTagCache  # Use real tag cache

    # Setup a temporary directory for the cache
    import tempfile

    temp_cache_dir = tempfile.TemporaryDirectory()
    cache_path = Path(temp_cache_dir.name)

    mock_cache = TreeSitterTagCache(cache_dir=cache_path)  # Use real cache
    mock_query_loader = FileQueryLoader()  # Use real query loader

    # Ensure project_root is a Path object for the parser
    # Use the session_test_repo_path for the parser's project_root
    parser = TreeSitterParser(
        project_root=session_test_repo_path,
        cache=mock_cache,
        query_loader=mock_query_loader,
    )
    yield parser
    # Cleanup the temporary directory after the function
    temp_cache_dir.cleanup()


@pytest.fixture(scope="session")
def session_parsed_files(session_test_repo_path, session_tree_sitter_parser):
    """Pre-parse all test files once per session."""
    parsed_data = {}

    # Supported file extensions
    supported_extensions = {".py", ".ts", ".js", ".java", ".go", ".cs"}

    for file_path in session_test_repo_path.rglob("*"):
        if file_path.is_file() and file_path.suffix in supported_extensions:
            try:
                tags = session_tree_sitter_parser.get_tags(str(file_path))
                parsed_data[str(file_path)] = tags
            except Exception as e:
                # Log but don't fail - some files might not be parseable
                print(f"Warning: Could not parse {file_path}: {e}")
                parsed_data[str(file_path)] = []

    return parsed_data


@pytest.fixture(scope="session")
def session_identifiers(session_parsed_files):
    """Extract all identifiers from parsed files."""
    identifiers = set()

    for file_path, tags in session_parsed_files.items():
        for tag in tags:
            if hasattr(tag, "name") and tag.name:
                identifiers.add(tag.name)

    return identifiers


@pytest.fixture(scope="session")
def session_import_data(session_container, session_test_repo_path):
    """Pre-analyze all imports once per session."""
    analyzer = session_container.import_analyzer()

    # Analyze project imports - use the resolved absolute path
    project_imports = analyzer.analyze_project_imports(
        str(session_test_repo_path.resolve())
    )
    return project_imports


@pytest.fixture(scope="session")
def session_dependency_graph(session_import_data, session_container):
    """Pre-build dependency graph once per session."""
    graph = session_container.dependency_graph()

    # Build graph with pre-analyzed imports
    graph.build_graph(session_import_data)
    return graph


@pytest.fixture(scope="session")
def session_container(session_config):
    """Pre-created DI container for session."""
    # Create a custom container that doesn't use cache to avoid database locks
    from repomap_tool.core.container import Container
    from repomap_tool.core.container_config import configure_container
    from dependency_injector import providers

    # Create container without cache
    container = Container()
    container.config.from_dict(session_config.model_dump())

    # Configure the container with formatters
    configure_container(container, session_config)

    # Removed: Override tag_cache to be None
    # container.tag_cache.override(None)

    return container


@pytest.fixture(scope="session")
def cli_runner_with_container(session_container):
    """Provides a Click CliRunner with a pre-configured session_container injected."""
    from repomap_tool.cli.main import cli
    from repomap_tool.cli.output.console_manager import DefaultConsoleManager
    from repomap_tool.cli.utils.console import ConsoleProvider
    from repomap_tool.cli.utils.console import RichConsoleFactory as _RichConsoleFactory
    from rich.console import Console
    import logging

    runner = CliRunner()

    # Create an isolated console stream for tests to avoid interleaving with logging
    buffer = io.StringIO()

    class BufferConsoleFactory(_RichConsoleFactory):
        def create_console(self, no_color: bool = False) -> Console:  # type: ignore[override]
            return Console(
                file=buffer,  # isolate stdout output to in-memory buffer
                stderr=False,
                force_terminal=False,
                color_system=None,
                no_color=no_color,
                soft_wrap=False,
            )

    # Override console_manager in the DI container to use the isolated buffer
    provider = ConsoleProvider(factory=BufferConsoleFactory(), no_color=True)
    isolated_manager = DefaultConsoleManager(provider=provider, enable_logging=False)
    session_container.console_manager.override(lambda: isolated_manager)

    # Also redirect logging to the isolated buffer to prevent logging from corrupting JSON output
    # This prevents "I/O operation on closed file" errors when pytest tears down logging handlers
    logging_handler = logging.StreamHandler(buffer)
    logging_handler.setLevel(logging.DEBUG)

    # Store original handlers to restore later
    original_handlers = logging.getLogger().handlers[:]

    # Clear existing handlers and add our isolated handler
    logging.getLogger().handlers.clear()
    logging.getLogger().addHandler(logging_handler)

    # Patch the cli.__call__ method to ensure our container is always used
    # when CliRunner.invoke calls cli.
    def mock_cli_call(*args, **kwargs):
        ctx = click.Context(cli, obj={})
        ctx.obj["container"] = session_container
        ctx.obj["no_color"] = True  # Disable color for consistent test output

        # Retrieve the console manager from the injected container and configure it.
        # This mimics the behavior in src/repomap_tool/cli/main.py
        console_manager_instance = ctx.obj["container"].console_manager()
        console_manager_instance.configure(no_color=ctx.obj.get("no_color", False))

        result = cli.invoke(ctx, args, **kwargs)
        # Attach captured console output to result for tests that need to parse it
        try:
            result.captured_output = buffer.getvalue()  # type: ignore[attr-defined]
        except Exception:
            pass
        return result

    with patch("repomap_tool.cli.main.cli.__call__", new=mock_cli_call):
        try:
            yield runner
        finally:
            # Reset override to avoid leaking across sessions
            try:
                session_container.console_manager.reset_override()
            except Exception:
                pass

            # Restore original logging handlers
            try:
                logging.getLogger().handlers.clear()
                logging.getLogger().handlers.extend(original_handlers)
            except Exception:
                pass


# Isolated fixtures for cache testing
@pytest.fixture
def isolated_tree_sitter_parser():
    """Function-scoped TreeSitter parser for cache isolation tests."""
    return TreeSitterParser()


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "cache_isolation: mark test as requiring cache isolation"
    )


# Utility functions for tests
def get_test_file_path(session_test_repo_path: Path, filename: str) -> str:
    """Get absolute path to a test file."""
    return str(session_test_repo_path / filename)


def get_parsed_file_tags(session_parsed_files: Dict[str, List], filename: str) -> List:
    """Get parsed tags for a specific test file."""
    for file_path, tags in session_parsed_files.items():
        if file_path.endswith(filename):
            return tags
    return []


def get_identifiers_from_file(
    session_parsed_files: Dict[str, List], filename: str
) -> Set[str]:
    """Get identifiers from a specific test file."""
    tags = get_parsed_file_tags(session_parsed_files, filename)
    identifiers = set()
    for tag in tags:
        if hasattr(tag, "name") and tag.name:
            identifiers.add(tag.name)
    return identifiers


def create_repomap_service_from_session_container(session_container, config):
    """Helper function to create RepoMapService using session container.

    This replicates the service factory pattern but uses the session container
    to avoid database locks and improve test performance.
    """
    # Get all dependencies from session container (same as service factory)
    console = session_container.console()
    fuzzy_matcher = session_container.fuzzy_matcher()
    dependency_graph = session_container.dependency_graph()
    centrality_calculator = session_container.centrality_calculator()
    spellchecker_service = session_container.spellchecker_service()
    tree_sitter_parser = session_container.tree_sitter_parser()
    tag_cache = session_container.tag_cache()
    file_discovery_service = session_container.file_discovery_service()

    # Create semantic matchers if enabled (same as service factory)
    semantic_matcher = None
    hybrid_matcher = None
    if config.semantic_match.enabled:
        semantic_matcher = session_container.adaptive_semantic_matcher()
        hybrid_matcher = session_container.hybrid_matcher()

    # Create impact analyzer if enabled
    impact_analyzer = None
    if config.dependencies.enable_impact_analysis:
        impact_analyzer = session_container.impact_analyzer()

    # Create RepoMapService with injected dependencies
    from repomap_tool.core.repo_map import RepoMapService

    return RepoMapService(
        config=config,
        console=console,
        fuzzy_matcher=fuzzy_matcher,
        semantic_matcher=semantic_matcher,
        embedding_matcher=None,
        hybrid_matcher=hybrid_matcher,
        dependency_graph=dependency_graph,
        impact_analyzer=impact_analyzer,
        centrality_calculator=centrality_calculator,
        spellchecker_service=spellchecker_service,
        tree_sitter_parser=tree_sitter_parser,
        tag_cache=tag_cache,
        file_discovery_service=file_discovery_service,
    )
