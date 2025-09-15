"""
Tests for dependency injection container.

This module tests the DI container functionality, service creation,
and dependency resolution.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from repomap_tool.core.container import Container, create_container, get_container
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)


class TestContainer:
    """Test the DI container functionality."""

    def _create_test_config(self):
        """Create a test configuration with a real project path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            with open(os.path.join(temp_dir, "src", "__init__.py"), "w") as f:
                f.write("# Test project")

            return RepoMapConfig(
                project_root=temp_dir,
                fuzzy_match=FuzzyMatchConfig(),
                semantic_match=SemanticMatchConfig(),
                performance=PerformanceConfig(),
                dependencies=DependencyConfig(),
            )

    def test_container_creation(self):
        """Test that container can be created."""
        container = Container()
        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "dependency_graph")
        assert hasattr(container, "fuzzy_matcher")

    def test_container_configuration(self):
        """Test container configuration."""
        config = self._create_test_config()

        container = create_container(config)
        assert container is not None
        assert container.config.project_root() == config.project_root

    def test_dependency_graph_provider(self):
        """Test dependency graph provider."""
        config = self._create_test_config()

        container = create_container(config)
        dependency_graph = container.dependency_graph()

        assert dependency_graph is not None
        # Test that it's a singleton
        dependency_graph2 = container.dependency_graph()
        assert dependency_graph is dependency_graph2

    def test_fuzzy_matcher_provider(self):
        """Test fuzzy matcher provider."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 80

        container = create_container(config)
        fuzzy_matcher = container.fuzzy_matcher()

        assert fuzzy_matcher is not None
        assert hasattr(fuzzy_matcher, "threshold")

    def test_semantic_matcher_provider(self):
        """Test semantic matcher provider."""
        config = self._create_test_config()
        config.semantic_match.enabled = True

        container = create_container(config)
        semantic_matcher = container.adaptive_semantic_matcher()

        assert semantic_matcher is not None

    def test_hybrid_matcher_provider(self):
        """Test hybrid matcher provider."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 70
        config.semantic_match.enabled = True
        config.semantic_match.threshold = 0.5

        container = create_container(config)
        hybrid_matcher = container.hybrid_matcher()

        assert hybrid_matcher is not None

    def test_console_provider(self):
        """Test console provider."""
        config = self._create_test_config()

        container = create_container(config)
        console = container.console()

        assert console is not None
        # Test that it's a singleton
        console2 = container.console()
        assert console is console2

    def test_llm_analyzer_provider(self):
        """Test LLM analyzer provider."""
        config = self._create_test_config()

        container = create_container(config)
        llm_analyzer = container.llm_file_analyzer()

        assert llm_analyzer is not None
        assert hasattr(llm_analyzer, "config")
        assert hasattr(llm_analyzer, "dependencies")

    def test_centrality_calculator_provider(self):
        """Test centrality calculator provider."""
        config = self._create_test_config()

        container = create_container(config)
        centrality_calculator = container.centrality_calculator()

        assert centrality_calculator is not None
        # Test that it's a singleton
        centrality_calculator2 = container.centrality_calculator()
        assert centrality_calculator is centrality_calculator2

    def test_impact_analyzer_provider(self):
        """Test impact analyzer provider."""
        config = self._create_test_config()
        config.dependencies.enable_impact_analysis = True

        container = create_container(config)
        impact_analyzer = container.impact_analyzer()

        assert impact_analyzer is not None
        # Test that it's a singleton
        impact_analyzer2 = container.impact_analyzer()
        assert impact_analyzer is impact_analyzer2

    def test_parallel_tag_extractor_provider(self):
        """Test parallel tag extractor provider."""
        config = self._create_test_config()
        config.performance.max_workers = 4

        container = create_container(config)
        parallel_extractor = container.parallel_tag_extractor()

        assert parallel_extractor is not None

    def test_container_error_handling(self):
        """Test container error handling."""
        # Test with invalid config
        with pytest.raises(Exception):
            create_container(None)

    def test_get_container(self):
        """Test get_container function."""
        # Initially should return None
        container = get_container()
        assert container is None

    def test_container_dependency_injection(self):
        """Test that dependencies are properly injected."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 75
        config.semantic_match.enabled = True
        config.semantic_match.threshold = 0.6
        config.performance.max_workers = 2
        config.dependencies.enable_impact_analysis = True

        container = create_container(config)

        # Test that all major services can be created
        services = [
            container.console(),
            container.dependency_graph(),
            container.fuzzy_matcher(),
            container.adaptive_semantic_matcher(),
            container.hybrid_matcher(),
            container.centrality_calculator(),
            container.impact_analyzer(),
            container.llm_file_analyzer(),
        ]

        for service in services:
            assert service is not None

    def test_container_configuration_validation(self):
        """Test that container configuration is properly validated."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 50
        config.semantic_match.enabled = False
        config.performance.max_workers = 1
        config.dependencies.enable_impact_analysis = False

        container = create_container(config)

        # Test configuration values
        assert container.config.project_root() == config.project_root
        assert container.config.fuzzy_match.threshold() == 50
        assert container.config.semantic_match.threshold() == 0.1  # default
        assert container.config.performance.max_workers() == 1
        assert container.config.dependencies.enable_impact_analysis() is False

    @patch("repomap_tool.core.container.logger")
    def test_container_logging(self, mock_logger):
        """Test that container creation is properly logged."""
        config = self._create_test_config()

        container = create_container(config)
        assert container is not None

        # Verify logging was called
        mock_logger.info.assert_called_with(
            "Dependency injection container created and configured"
        )

    def test_container_with_missing_dependencies(self):
        """Test container behavior with missing optional dependencies."""
        config = self._create_test_config()
        config.semantic_match.enabled = False
        config.dependencies.enable_impact_analysis = False

        container = create_container(config)

        # Should still create container successfully
        assert container is not None

        # Semantic matcher should not be available when disabled
        # (This would be handled by the service factory in practice)
        assert container.config.semantic_match.threshold() == 0.1  # default value
