"""
Tests for dependency injection container.

This module tests the DI container functionality, service creation,
and dependency resolution.
"""

import logging
import os
import tempfile

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch
from typing import cast

import pytest
from dependency_injector import containers, providers
from rich.console import Console

from repomap_tool.cli.output.console_manager import (
    ConsoleManagerProtocol,
    ConsoleProvider,
    DefaultConsoleManager,
)
from repomap_tool.cli.output.templates.engine import TemplateEngine
from repomap_tool.cli.output.templates.registry import DefaultTemplateRegistry
from repomap_tool.cli.output.standard_formatters import FormatterRegistry
from repomap_tool.cli.output.manager import OutputManager
from repomap_tool.core.container import Container, create_container, get_container
from repomap_tool.core.cache_manager import CacheManager
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.code_analysis.query_loader import FileQueryLoader
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer
from repomap_tool.code_analysis.call_graph_builder import CallGraphBuilder


from repomap_tool.models import (
    DependencyConfig,
    EmbeddingConfig,
    FuzzyMatchConfig,
    PerformanceConfig,
    RepoMapConfig,
    SemanticMatchConfig,
)


class TestContainer:
    """Test the DI container functionality."""

    def _create_test_config(self) -> RepoMapConfig:
        """Create a test configuration with a real project path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            with open(os.path.join(temp_dir, "src", "__init__.py"), "w") as f:
                f.write("# Test project")

            return RepoMapConfig(
                project_root=Path(temp_dir),
                fuzzy_match=FuzzyMatchConfig(),
                semantic_match=SemanticMatchConfig(),
                performance=PerformanceConfig(),
                dependencies=DependencyConfig(),
            )

    def test_container_creation(self) -> None:
        """Test that container can be created."""
        container = Container()
        assert container is not None
        assert hasattr(container, "config")
        assert hasattr(container, "dependency_graph")
        assert hasattr(container, "fuzzy_matcher")

    def test_repo_map_config_provider(self) -> None:
        """Test that RepoMapConfig is correctly provided and is a singleton."""
        config_obj = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config_obj)
        repo_map_config = container.config()
        assert repo_map_config == config_obj
        assert repo_map_config is container.config()

    def test_console_provider(self) -> None:
        """Test that ConsoleProvider and console are correctly provided."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        # Ensure the console manager is a singleton
        assert container.console_manager() is container.console_manager()

        # Ensure get_console returns a Console instance (RichConsoleFactory always returns a new Console)
        console1 = container.console()
        console2 = container.console()
        assert isinstance(console1, Console)
        assert isinstance(console2, Console)
        assert console1 is not console2  # Expect new console instances

    def test_console_manager_provider(self) -> None:
        """Test that ConsoleManager is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        console_manager = container.console_manager()
        assert isinstance(console_manager, DefaultConsoleManager)
        assert console_manager is container.console_manager()

    def test_logger_provider(self) -> None:
        """Test that a logger is correctly provided."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        logger = container.logger("test_logger")
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_cache_manager_provider(self) -> None:
        """Test that CacheManager is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        cache_manager = container.cache_manager()
        assert cache_manager is not None
        assert isinstance(cache_manager, CacheManager)
        assert cache_manager is container.cache_manager()

    def test_tree_sitter_tag_cache_provider(self) -> None:
        """Test that TreeSitterTagCache is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        tag_cache = container.tag_cache()
        assert tag_cache is not None
        assert isinstance(tag_cache, TreeSitterTagCache)
        assert tag_cache is container.tag_cache()

    def test_file_query_loader_provider(self) -> None:
        """Test that FileQueryLoader is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        query_loader = container.query_loader()
        assert query_loader is not None
        assert isinstance(query_loader, FileQueryLoader)
        assert query_loader is container.query_loader()

    def test_tree_sitter_parser_provider(self) -> None:
        """Test that TreeSitterParser is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        tree_sitter_parser = container.tree_sitter_parser()
        assert tree_sitter_parser is not None
        assert isinstance(tree_sitter_parser, TreeSitterParser)
        assert tree_sitter_parser is container.tree_sitter_parser()

    def test_import_analyzer_provider(self) -> None:
        """Test that ImportAnalyzer is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        import_analyzer = container.import_analyzer()
        assert import_analyzer is not None
        assert isinstance(import_analyzer, ImportAnalyzer)
        assert import_analyzer is container.import_analyzer()

    def test_call_graph_builder_provider(self) -> None:
        """Test that CallGraphBuilder is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        call_graph_builder = container.call_graph_builder()
        assert call_graph_builder is not None
        assert isinstance(call_graph_builder, CallGraphBuilder)
        assert call_graph_builder is container.call_graph_builder()

    def test_default_console_manager_provider(self) -> None:
        """Test that DefaultConsoleManager is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        console_manager = container.console_manager()
        assert isinstance(console_manager, DefaultConsoleManager)
        assert console_manager is container.console_manager()

    def test_default_template_registry_provider(self) -> None:
        """Test that DefaultTemplateRegistry is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        template_registry = container.template_registry()
        assert isinstance(template_registry, DefaultTemplateRegistry)
        assert template_registry is container.template_registry()

    def test_template_engine_provider(self) -> None:
        """Test that TemplateEngine is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        template_engine = container.template_engine()
        assert isinstance(template_engine, TemplateEngine)
        assert template_engine is container.template_engine()

    def test_formatter_registry_provider(self) -> None:
        """Test that FormatterRegistry is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        formatter_registry = container.formatter_registry()
        assert isinstance(formatter_registry, FormatterRegistry)
        assert formatter_registry is container.formatter_registry()

    def test_output_manager_provider(self) -> None:
        """Test that OutputManager is correctly provided and is a singleton."""
        config = RepoMapConfig(
            project_root=Path("/tmp/test_project"), cache_dir=Path("/tmp/cache")
        )
        container = create_container(config)
        output_manager = container.output_manager()
        assert isinstance(output_manager, OutputManager)
        assert output_manager is container.output_manager()

    def test_container_configuration(self) -> None:
        """Test container configuration."""
        config = self._create_test_config()

        container = create_container(config)
        assert container is not None
        assert str(container.config.project_root()) == str(config.project_root)

    def test_dependency_graph_provider(self) -> None:
        """Test dependency graph provider."""
        config = self._create_test_config()

        container = create_container(config)
        dependency_graph = container.dependency_graph()

        assert dependency_graph is not None
        # Test that it's a singleton
        dependency_graph2 = container.dependency_graph()
        assert dependency_graph is dependency_graph2

    def test_fuzzy_matcher_provider(self) -> None:
        """Test fuzzy matcher provider."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 80

        container = create_container(config)
        fuzzy_matcher = container.fuzzy_matcher()

        assert fuzzy_matcher is not None
        assert hasattr(fuzzy_matcher, "threshold")

    def test_semantic_matcher_provider(self) -> None:
        """Test semantic matcher provider."""
        config = self._create_test_config()
        config.semantic_match.enabled = True

        container = create_container(config)
        semantic_matcher = container.adaptive_semantic_matcher()

        assert semantic_matcher is not None

    def test_hybrid_matcher_provider(self) -> None:
        """Test hybrid matcher provider."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 70
        config.semantic_match.enabled = True
        config.semantic_match.threshold = 0.5

        container = create_container(config)
        hybrid_matcher = container.hybrid_matcher()

        assert hybrid_matcher is not None

    def test_centrality_calculator_provider(self) -> None:
        """Test centrality calculator provider."""
        config = self._create_test_config()

        container = create_container(config)
        centrality_calculator = container.centrality_calculator()

        assert centrality_calculator is not None
        # Test that it's a singleton
        centrality_calculator2 = container.centrality_calculator()
        assert centrality_calculator is centrality_calculator2

    def test_impact_analyzer_provider(self) -> None:
        """Test impact analyzer provider."""
        config = self._create_test_config()
        config.dependencies.enable_impact_analysis = True

        container = create_container(config)
        impact_analyzer = container.impact_analyzer()

        assert impact_analyzer is not None
        # Test that it's a singleton
        impact_analyzer2 = container.impact_analyzer()
        assert impact_analyzer is impact_analyzer2

    def test_container_error_handling(self) -> None:
        """Test container error handling."""
        # Test with invalid config
        with pytest.raises(Exception):
            # Provide a valid, but potentially problematic, config for error handling test
            invalid_config = RepoMapConfig(project_root=Path("/nonexistent"), cache_dir=Path("/tmp/cache"))
            create_container(invalid_config) # This should still be a valid call

    def test_get_container(self) -> None:
        """Test get_container function."""
        # Initially should return None
        container = get_container()
        assert container is None

    def test_container_dependency_injection(self) -> None:
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
        ]

        for service in services:
            assert service is not None

    def test_container_configuration_validation(self) -> None:
        """Test that container configuration is properly validated."""
        config = self._create_test_config()
        config.fuzzy_match.threshold = 50
        config.semantic_match.enabled = False
        config.performance.max_workers = 1
        config.dependencies.enable_impact_analysis = False

        container = create_container(config)

        # Test configuration values
        assert str(container.config.project_root()) == str(config.project_root)
        assert container.config.fuzzy_match.threshold() == 50
        assert container.config.semantic_match.threshold() == 0.1  # default
        assert container.config.performance.max_workers() == 1
        assert container.config.dependencies.enable_impact_analysis() is False

    @patch("repomap_tool.core.container.logger")
    def test_container_logging(self, mock_logger: Mock) -> None:
        """Test that container creation is properly logged."""
        config = self._create_test_config()

        container = create_container(config)
        assert container is not None

        # Verify logging was called (changed to debug level)
        mock_logger.debug.assert_called_with(
            "Dependency injection container created and configured"
        )

    def test_container_with_missing_dependencies(self) -> None:
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
