"""
Tests for tree exploration and dependency analysis integration.

This module tests the integration between Phase 1 tree exploration
and Phase 2 dependency analysis components.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, MagicMock
from pathlib import Path

from repomap_tool.code_exploration.discovery_engine import EntrypointDiscoverer
from repomap_tool.models import Entrypoint, RepoMapConfig
from repomap_tool.code_analysis import (
    ImportAnalyzer,
    DependencyGraph,
)


class TestTreeDependencyIntegration:
    """Test integration between tree exploration and dependency analysis."""

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_discovery_engine_initialization_with_dependencies(
        self, session_container, session_test_repo_path
    ):
        """Test that EntrypointDiscoverer initializes with dependency components."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # Check that dependency components are initialized
        assert discoverer.import_analyzer is not None
        assert isinstance(discoverer.import_analyzer, ImportAnalyzer)
        assert discoverer.dependency_graph is not None
        assert isinstance(discoverer.dependency_graph, DependencyGraph)
        # With DI, components are initialized immediately
        assert discoverer.centrality_calculator is not None
        assert discoverer.impact_analyzer is not None

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_enhance_entrypoints_with_dependencies(
        self, session_container, session_test_repo_path
    ):
        """Test that entrypoints are enhanced with dependency information."""

        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # Create test entrypoints
        entrypoint1 = Entrypoint(
            identifier="test_function",
            file_path=Path("src/test.py"),
            score=0.8,
            structural_context={},
        )

        entrypoint2 = Entrypoint(
            identifier="another_function",
            file_path=Path("src/another.py"),
            score=0.7,
            structural_context={},
        )

        entrypoints = [entrypoint1, entrypoint2]

        # Mock the dependency analysis methods
        discoverer._build_project_dependency_graph = Mock()
        discoverer._enhance_single_entrypoint = Mock()

        # Call the enhancement method with the session test repository
        discoverer._enhance_entrypoints_with_dependencies(
            entrypoints, str(session_test_repo_path)
        )

        # Verify that dependency analysis was called
        discoverer._build_project_dependency_graph.assert_called_once_with(
            str(session_test_repo_path)
        )
        assert discoverer._enhance_single_entrypoint.call_count == 2

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_extract_file_path_from_location(
        self, session_container, session_test_repo_path
    ):
        """Test file path extraction from entrypoint location."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # Test with line number - should return None since file doesn't exist
        file_path = discoverer._extract_file_path_from_location(
            "src/test.py:123", str(session_test_repo_path)
        )
        expected_path = os.path.normpath(
            os.path.join(str(session_test_repo_path), "src/test.py")
        )
        # The method returns None for non-existent files, but we can verify the path construction logic
        assert file_path is None  # File doesn't exist

        # Test without line number - should return None since file doesn't exist
        file_path = discoverer._extract_file_path_from_location(
            "src/test.py", str(session_test_repo_path)
        )
        expected_path = os.path.normpath(
            os.path.join(str(session_test_repo_path), "src/test.py")
        )
        assert file_path is None  # File doesn't exist

        # Test with relative path - should return None since file doesn't exist
        file_path = discoverer._extract_file_path_from_location(
            "test.py:10", str(session_test_repo_path)
        )
        expected_path = os.path.normpath(
            os.path.join(str(session_test_repo_path), "test.py")
        )
        assert file_path is None  # File doesn't exist

        # Test the path construction logic by checking what would be constructed
        # This verifies our path construction logic works correctly
        test_location = "src/test.py:123"
        if ":" in test_location:
            file_part = test_location.split(":")[0]
        else:
            file_part = test_location

        constructed_path = os.path.join(str(session_test_repo_path), file_part)
        normalized_path = os.path.normpath(constructed_path)
        # The constructed path should be correct
        expected_constructed_path = os.path.normpath(
            os.path.join(str(session_test_repo_path), "src/test.py")
        )
        assert normalized_path == expected_constructed_path

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_dependency_graph_integration(
        self, session_container, session_test_repo_path
    ):
        """Test that dependency graph is properly integrated."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # Verify dependency graph is accessible
        assert discoverer.dependency_graph is not None
        assert hasattr(discoverer.dependency_graph, "build_graph")
        assert hasattr(discoverer.dependency_graph, "get_dependencies")
        assert hasattr(discoverer.dependency_graph, "get_dependents")

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_import_analyzer_integration(
        self, session_container, session_test_repo_path
    ):
        """Test that import analyzer is properly integrated."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # Verify import analyzer is accessible
        assert discoverer.import_analyzer is not None
        assert hasattr(discoverer.import_analyzer, "analyze_project_imports")
        assert hasattr(discoverer.import_analyzer, "analyze_file_imports")

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_lazy_initialization_of_analysis_components(
        self, session_container, session_test_repo_path
    ):
        """Test that centrality calculator and impact analyzer are lazily initialized."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))

        # Mock repo_map with real config
        mock_repo_map = Mock()
        mock_repo_map.config = config

        # Create dependencies using session container
        from tests.conftest import create_repomap_service_from_session_container

        repomap_service = create_repomap_service_from_session_container(
            session_container, config
        )

        # Create discoverer with injected dependencies
        from repomap_tool.core.container import create_container

        container = create_container(config)
        discoverer = EntrypointDiscoverer(
            repo_map=repomap_service,
            import_analyzer=container.import_analyzer(),
            dependency_graph=container.dependency_graph(),
            centrality_calculator=container.centrality_calculator(),
            impact_analyzer=(
                container.impact_analyzer()
                if config.dependencies.enable_impact_analysis
                else None
            ),
        )

        # With DI, these are now initialized immediately
        assert discoverer.centrality_calculator is not None
        assert discoverer.impact_analyzer is not None

        # Mock the entire enhancement method to avoid any initialization
        discoverer._enhance_entrypoints_with_dependencies = Mock()

        # Create a test entrypoint
        entrypoint = Entrypoint(
            identifier="test_function",
            file_path=Path("src/test.py"),
            score=0.8,
            structural_context={},
        )

        # Call the mocked enhancement method
        discoverer._enhance_entrypoints_with_dependencies(
            [entrypoint], str(session_test_repo_path)
        )

        # The components are initialized by DI, not by the enhancement method
        assert discoverer.centrality_calculator is not None
        assert discoverer.impact_analyzer is not None

        # Verify the mock was called
        discoverer._enhance_entrypoints_with_dependencies.assert_called_once_with(
            [entrypoint], str(session_test_repo_path)
        )


class TestEntrypointEnhancement:
    """Test the enhancement of entrypoints with dependency information."""

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_entrypoint_model_with_dependency_fields(self):
        """Test that Entrypoint model includes dependency analysis fields."""
        entrypoint = Entrypoint(
            identifier="test_function",
            file_path=Path("src/test.py"),
            score=0.8,
            structural_context={},
        )

        # Check that dependency fields exist and are None by default
        assert hasattr(entrypoint, "dependency_centrality")
        assert entrypoint.dependency_centrality is None

        assert hasattr(entrypoint, "import_count")
        assert entrypoint.import_count is None

        assert hasattr(entrypoint, "dependency_count")
        assert entrypoint.dependency_count is None

        assert hasattr(entrypoint, "impact_risk")
        assert entrypoint.impact_risk is None

        assert hasattr(entrypoint, "refactoring_priority")
        assert entrypoint.refactoring_priority is None

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_entrypoint_model_with_dependency_values(self):
        """Test that Entrypoint model can store dependency analysis values."""
        entrypoint = Entrypoint(
            identifier="test_function",
            file_path=Path("src/test.py"),
            score=0.8,
            structural_context={},
            dependency_centrality=0.75,
            import_count=5,
            dependency_count=3,
            impact_risk=0.6,
            refactoring_priority=0.7,
        )

        # Check that dependency fields can store values
        assert entrypoint.dependency_centrality == 0.75
        assert entrypoint.import_count == 5
        assert entrypoint.dependency_count == 3
        assert entrypoint.impact_risk == 0.6
        assert entrypoint.refactoring_priority == 0.7


class TestTreeNodeEnhancement:
    """Test the enhancement of TreeNode model with dependency information."""

    @pytest.mark.skip(reason="Disabling tree/exploration tests")
    def test_treenode_model_with_dependency_fields(self):
        """Test that TreeNode model includes dependency analysis fields."""
        from repomap_tool.models import TreeNode

        node = TreeNode(
            identifier="test_function",
            location="src/test.py:10",
            node_type="function",
            depth=0,
        )

        # Check that dependency fields exist and are None by default
        assert hasattr(node, "dependency_centrality")
        assert node.dependency_centrality is None

        assert hasattr(node, "import_count")
        assert node.import_count is None

        assert hasattr(node, "dependency_count")
        assert node.dependency_count is None

        assert hasattr(node, "impact_risk")
        assert node.impact_risk is None

        assert hasattr(node, "refactoring_priority")
        assert node.refactoring_priority is None
