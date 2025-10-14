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
from repomap_tool.core.container import create_container
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser

# Disable cache for all tests to avoid database locks
os.environ["REPOMAP_DISABLE_CACHE"] = "1"


@pytest.fixture(scope="session")
def session_test_repo_path():
    """Path to the comprehensive test fixture repository."""
    return Path(__file__).parent / "fixtures" / "test-repo"


@pytest.fixture(scope="session")
def session_config():
    """Base RepoMapConfig for all tests."""
    test_repo_path = Path(__file__).parent / "fixtures" / "test-repo"
    return RepoMapConfig(
        project_root=str(test_repo_path),
        verbose=False,
        fuzzy_match=FuzzyMatchConfig(),
        semantic_match=SemanticMatchConfig(),
        performance=PerformanceConfig(),
        dependencies=DependencyConfig(),
    )


@pytest.fixture(scope="session")
def session_tree_sitter_parser():
    """Single TreeSitter parser shared across all tests."""
    return TreeSitterParser()


@pytest.fixture(scope="session")
def session_parsed_files(session_test_repo_path, session_tree_sitter_parser):
    """Pre-parse all test files once per session."""
    parsed_data = {}

    # Supported file extensions
    supported_extensions = {".py", ".ts", ".js", ".java", ".go"}

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
def session_import_data(session_test_repo_path, session_container):
    """Pre-analyze all imports once per session."""
    analyzer = session_container.import_analyzer()

    # Analyze project imports
    project_imports = analyzer.analyze_project_imports(str(session_test_repo_path))
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
    from dependency_injector import providers

    # Create container without cache
    container = Container()
    container.config.from_dict(session_config.model_dump())

    # Override tag_cache to be None
    container.tag_cache.override(None)

    return container


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
    parallel_extractor = session_container.parallel_tag_extractor()
    fuzzy_matcher = session_container.fuzzy_matcher()
    dependency_graph = session_container.dependency_graph()
    centrality_calculator = session_container.centrality_calculator()
    spellchecker_service = session_container.spellchecker_service()

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
        parallel_extractor=parallel_extractor,
        fuzzy_matcher=fuzzy_matcher,
        semantic_matcher=semantic_matcher,
        embedding_matcher=None,
        hybrid_matcher=hybrid_matcher,
        dependency_graph=dependency_graph,
        impact_analyzer=impact_analyzer,
        centrality_calculator=centrality_calculator,
        spellchecker_service=spellchecker_service,
    )
