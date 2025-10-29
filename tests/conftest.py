"""
Session-scoped fixtures for unit tests.

This module provides shared fixtures that are loaded once per test session,
dramatically improving test performance by avoiding repeated parsing and
analysis of the same codebase.
"""

import os
import signal
import sys
import atexit
import time
import pytest
from pathlib import Path
from typing import Dict, List, Any, Set, Generator, Optional, Union
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


# Worker-isolated logging setup to prevent I/O operation on closed file errors
def setup_worker_isolated_logging() -> None:
    """Set up logging isolation for pytest workers to prevent stream conflicts."""
    try:
        import logging
        import threading

        # Get worker ID for unique log files
        worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")

        # Create worker-specific log handler
        log_file = f"/tmp/pytest_worker_{worker_id}_{os.getpid()}.log"

        # Remove all existing handlers to prevent conflicts
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            try:
                root_logger.removeHandler(handler)
                handler.close()
            except Exception:
                # Ignore errors when closing handlers
                pass

        # Create file handler for this worker
        try:
            file_handler = logging.FileHandler(log_file, mode="w")
            file_handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(formatter)

            # Add handler to root logger
            root_logger.addHandler(file_handler)
            root_logger.setLevel(logging.DEBUG)
        except Exception:
            # If file logging fails, continue without it
            pass

        # Also disable console logging to prevent stdout conflicts
        try:
            console_handler = logging.StreamHandler(
                sys.stderr
            )  # Use stderr instead of stdout
            console_handler.setLevel(logging.WARNING)  # Only show warnings and errors
            console_handler.setFormatter(
                logging.Formatter("%(levelname)s: %(message)s")
            )
            root_logger.addHandler(console_handler)
        except Exception:
            # If console logging fails, continue without it
            pass

    except Exception:
        # If logging setup fails completely, continue without it
        pass


# Enhanced signal handling for pytest-xdist worker cleanup
def cleanup_pytest_workers() -> None:
    """Clean up pytest worker processes on termination."""
    try:
        import subprocess

        # Use logging instead of print to avoid stdout conflicts
        try:
            import logging

            logger = logging.getLogger(__name__)
            logger.info("🧹 Starting cleanup of pytest workers...")
        except Exception:
            # If logging fails, use print as fallback
            print("🧹 Starting cleanup of pytest workers...")

        # Find and terminate pytest worker processes
        try:
            result = subprocess.run(
                ["pgrep", "-f", "pytest.*worker"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = [int(pid) for pid in result.stdout.strip().split("\n") if pid]
                try:
                    logger.info(f"🔍 Found {len(pids)} worker processes: {pids}")
                except Exception:
                    print(f"🔍 Found {len(pids)} worker processes: {pids}")

                for pid in pids:
                    try:
                        try:
                            logger.info(f"💀 Terminating worker process {pid}...")
                        except Exception:
                            print(f"💀 Terminating worker process {pid}...")

                        # Try SIGTERM first
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.1)
                        # Force kill if still running
                        try:
                            os.kill(pid, 0)  # Check if process still exists
                            # Process still exists, force kill it
                            try:
                                logger.info(f"💀 Force killing worker process {pid}...")
                            except Exception:
                                print(f"💀 Force killing worker process {pid}...")
                            os.kill(pid, signal.SIGKILL)
                        except (OSError, ProcessLookupError):
                            # Process already dead, continue
                            pass
                    except (OSError, ProcessLookupError):
                        pass
            else:
                try:
                    logger.info("✅ No worker processes found")
                except Exception:
                    print("✅ No worker processes found")
        except subprocess.TimeoutExpired:
            # If pgrep times out, continue with cleanup
            pass
        except Exception:
            # If pgrep fails, continue with cleanup
            pass

        # Also clean up any remaining pytest processes
        try:
            result = subprocess.run(
                ["pgrep", "-f", "python.*pytest"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = [int(pid) for pid in result.stdout.strip().split("\n") if pid]
                current_pid = os.getpid()
                pytest_pids = [pid for pid in pids if pid != current_pid]
                if pytest_pids:
                    try:
                        logger.info(
                            f"🔍 Found {len(pytest_pids)} pytest processes: {pytest_pids}"
                        )
                    except Exception:
                        print(
                            f"🔍 Found {len(pytest_pids)} pytest processes: {pytest_pids}"
                        )

                    for pid in pytest_pids:
                        try:
                            try:
                                logger.info(f"💀 Terminating pytest process {pid}...")
                            except Exception:
                                print(f"💀 Terminating pytest process {pid}...")

                            # Try SIGTERM first
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.1)  # Give it a moment to terminate
                            # Force kill if still running
                            try:
                                os.kill(pid, 0)  # Check if process still exists
                                # Process still exists, force kill it
                                try:
                                    logger.info(
                                        f"💀 Force killing pytest process {pid}..."
                                    )
                                except Exception:
                                    print(f"💀 Force killing pytest process {pid}...")
                                os.kill(pid, signal.SIGKILL)
                            except (OSError, ProcessLookupError):
                                # Process already dead, continue
                                pass
                        except (OSError, ProcessLookupError):
                            pass
                else:
                    try:
                        logger.info("✅ No other pytest processes found")
                    except Exception:
                        print("✅ No other pytest processes found")
            else:
                try:
                    logger.info("✅ No pytest processes found")
                except Exception:
                    print("✅ No pytest processes found")
        except subprocess.TimeoutExpired:
            # If pgrep times out, continue
            pass
        except Exception:
            # If pgrep fails, continue
            pass

    except Exception:
        pass  # Ignore all errors during cleanup


def signal_handler(signum: int, frame: Any) -> None:
    """Handle interrupt signals and clean up workers."""
    try:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"🛑 Received signal {signum}, cleaning up worker processes...")
        cleanup_pytest_workers()
    except Exception:
        # Ignore logging errors during cleanup
        pass

    # Use SIGKILL for more aggressive termination
    try:
        os.kill(os.getpid(), signal.SIGKILL)
    except Exception:
        # If SIGKILL fails, just exit
        sys.exit(1)


# Set up worker-isolated logging first
setup_worker_isolated_logging()

# Register signal handlers for graceful termination
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)
atexit.register(cleanup_pytest_workers)

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
def session_test_repo_path() -> Path:
    """Path to the comprehensive test fixture repository."""
    return Path(__file__).parent / "fixtures" / "test-repo"


@pytest.fixture(scope="session")
def session_config(session_test_repo_path: Path) -> RepoMapConfig:
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
def session_tree_sitter_parser(
    session_test_repo_path: Path,
) -> Generator[TreeSitterParser, None, None]:
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
def get_tree_sitter_parser_function_fixture(
    session_test_repo_path: Path,
) -> Generator[TreeSitterParser, None, None]:
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
def session_parsed_files(
    session_test_repo_path: Path, session_tree_sitter_parser: TreeSitterParser
) -> Dict[str, List[Any]]:
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
def session_identifiers(session_parsed_files: Dict[str, List[Any]]) -> Set[str]:
    """Extract all identifiers from parsed files."""
    identifiers = set()

    for file_path, tags in session_parsed_files.items():
        for tag in tags:
            if hasattr(tag, "name") and tag.name:
                identifiers.add(tag.name)

    return identifiers


@pytest.fixture(scope="session")
def session_import_data(session_container: Any, session_test_repo_path: Path) -> Any:
    """Pre-analyze all imports once per session."""
    analyzer = session_container.import_analyzer()

    # Analyze project imports - use the resolved absolute path
    project_imports = analyzer.analyze_project_imports(
        str(session_test_repo_path.resolve())
    )
    return project_imports


@pytest.fixture(scope="session")
def session_dependency_graph(session_import_data: Any, session_container: Any) -> Any:
    """Pre-build dependency graph once per session."""
    graph = session_container.dependency_graph()

    # Build graph with pre-analyzed imports
    graph.build_graph(session_import_data)
    return graph


@pytest.fixture(scope="session")
def session_container(session_config: RepoMapConfig) -> Any:
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
def cli_runner_with_container(
    session_container: Any,
) -> Generator[CliRunner, None, None]:
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
        def create_console(self, no_color: bool = False) -> Console:
            # Use ConsoleProvider to avoid direct instantiation
            from repomap_tool.cli.utils.console import ConsoleProvider

            provider = ConsoleProvider()
            return provider.create_console(
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

    # Use the worker-isolated logging instead of buffer logging
    # The setup_worker_isolated_logging() function already handles this
    # No need to modify logging handlers here since they're already isolated per worker

    # Patch the cli.__call__ method to ensure our container is always used
    # when CliRunner.invoke calls cli.
    def mock_cli_call(*args: Any, **kwargs: Any) -> Any:
        ctx = click.Context(cli, obj={})
        ctx.obj["container"] = session_container
        ctx.obj["no_color"] = True  # Disable color for consistent test output

        # Retrieve the console manager from the injected container and configure it.
        # This mimics the behavior in src/repomap_tool/cli/main.py
        console_manager_instance = ctx.obj["container"].console_manager()
        console_manager_instance.configure(no_color=ctx.obj.get("no_color", False))

        result = cli.invoke(ctx)
        # Attach captured console output to result for tests that need to parse it
        try:
            result.captured_output = buffer.getvalue()
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

            # No need to restore logging handlers since we're using worker-isolated logging


# Isolated fixtures for cache testing
@pytest.fixture
def isolated_tree_sitter_parser() -> TreeSitterParser:
    """Function-scoped TreeSitter parser for cache isolation tests."""
    # Create a minimal TreeSitterParser for testing
    from repomap_tool.core.tag_cache import TreeSitterTagCache
    from repomap_tool.code_analysis.query_loader import FileQueryLoader
    import tempfile

    temp_cache_dir = tempfile.TemporaryDirectory()
    cache_path = Path(temp_cache_dir.name)

    cache = TreeSitterTagCache(cache_dir=cache_path)
    query_loader = FileQueryLoader()

    return TreeSitterParser(
        project_root=Path.cwd(),
        cache=cache,
        query_loader=query_loader,
    )


# Test markers
def pytest_configure(config: Any) -> None:
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


def create_repomap_service_from_session_container(
    session_container: Any, config: RepoMapConfig
) -> Any:
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
