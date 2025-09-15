"""
Tests for service factory with dependency injection.

This module tests the service factory functionality, service creation,
and dependency injection patterns.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from repomap_tool.cli.services.service_factory import (
    ServiceFactory,
    get_service_factory,
    clear_service_cache,
)
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)


class TestServiceFactory:
    """Test the service factory functionality."""

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

    def setup_method(self):
        """Set up test fixtures."""
        self.config = self._create_test_config()
        self.factory = ServiceFactory()

    def teardown_method(self):
        """Clean up after tests."""
        self.factory.clear_cache()

    def test_service_factory_creation(self):
        """Test that service factory can be created."""
        factory = ServiceFactory()
        assert factory is not None
        assert hasattr(factory, "_containers")
        assert hasattr(factory, "_services")

    def test_create_repomap_service(self):
        """Test RepoMapService creation with DI."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            # Mock the container and its providers
            mock_container = Mock()
            mock_container.console.return_value = Mock()
            mock_container.parallel_tag_extractor.return_value = Mock()
            mock_container.fuzzy_matcher.return_value = Mock()
            mock_container.adaptive_semantic_matcher.return_value = Mock()
            mock_container.hybrid_matcher.return_value = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.cli.services.service_factory.RepoMapService"
            ) as mock_repo_map_service:
                mock_service = Mock()
                mock_repo_map_service.return_value = mock_service

                # Test service creation
                service = self.factory.create_repomap_service(self.config)

                assert service is not None
                mock_create_container.assert_called_once_with(self.config)
                mock_repo_map_service.assert_called_once()

    def test_create_repomap_service_caching(self):
        """Test that RepoMapService is cached."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.console.return_value = Mock()
            mock_container.parallel_tag_extractor.return_value = Mock()
            mock_container.fuzzy_matcher.return_value = Mock()
            mock_container.adaptive_semantic_matcher.return_value = Mock()
            mock_container.hybrid_matcher.return_value = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_service = Mock()
                mock_repo_map_service.return_value = mock_service

                # Create service twice
                service1 = self.factory.create_repomap_service(self.config)
                service2 = self.factory.create_repomap_service(self.config)

                # Should be the same instance (cached)
                assert service1 is service2
                # Container should only be created once
                assert mock_create_container.call_count == 1

    def test_create_entrypoint_discoverer(self):
        """Test EntrypointDiscoverer creation with DI."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.import_analyzer.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_repo_map = Mock()
                mock_repo_map_service.return_value = mock_repo_map

                with patch(
                    "repomap_tool.cli.services.service_factory.EntrypointDiscoverer"
                ) as mock_discoverer:
                    mock_discoverer_instance = Mock()
                    mock_discoverer.return_value = mock_discoverer_instance

                    # Create RepoMapService first
                    repo_map = self.factory.create_repomap_service(self.config)

                    # Create EntrypointDiscoverer
                    discoverer = self.factory.create_entrypoint_discoverer(
                        repo_map, self.config
                    )

                    assert discoverer is not None
                    mock_discoverer.assert_called_once()

    def test_create_tree_builder(self):
        """Test TreeBuilder creation with DI."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.console.return_value = Mock()
            mock_container.parallel_tag_extractor.return_value = Mock()
            mock_container.fuzzy_matcher.return_value = Mock()
            mock_container.adaptive_semantic_matcher.return_value = Mock()
            mock_container.hybrid_matcher.return_value = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()
            mock_container.import_analyzer.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_repo_map = Mock()
                mock_repo_map_service.return_value = mock_repo_map

                with patch(
                    "repomap_tool.cli.services.service_factory.TreeBuilder"
                ) as mock_tree_builder:
                    mock_tree_builder_instance = Mock()
                    mock_tree_builder.return_value = mock_tree_builder_instance

                    # Create RepoMapService first
                    repo_map = self.factory.create_repomap_service(self.config)

                    # Create TreeBuilder
                    tree_builder = self.factory.create_tree_builder(
                        repo_map, self.config
                    )

                    assert tree_builder is not None
                    mock_tree_builder.assert_called_once()

    def test_create_tree_manager(self):
        """Test TreeManager creation with DI."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.console.return_value = Mock()
            mock_container.parallel_tag_extractor.return_value = Mock()
            mock_container.fuzzy_matcher.return_value = Mock()
            mock_container.adaptive_semantic_matcher.return_value = Mock()
            mock_container.hybrid_matcher.return_value = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()
            mock_container.import_analyzer.return_value = Mock()
            mock_container.session_manager.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_repo_map = Mock()
                mock_repo_map_service.return_value = mock_repo_map

                with patch(
                    "repomap_tool.cli.services.service_factory.TreeManager"
                ) as mock_tree_manager:
                    mock_tree_manager_instance = Mock()
                    mock_tree_manager.return_value = mock_tree_manager_instance

                    # Create RepoMapService first
                    repo_map = self.factory.create_repomap_service(self.config)

                    # Create TreeManager
                    tree_manager = self.factory.create_tree_manager(
                        repo_map, self.config
                    )

                    assert tree_manager is not None
                    mock_tree_manager.assert_called_once()

    def test_get_llm_analyzer(self):
        """Test LLM analyzer creation."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.llm_file_analyzer.return_value = Mock()

            mock_create_container.return_value = mock_container

            # Get LLM analyzer
            llm_analyzer = self.factory.get_llm_analyzer(self.config)

            assert llm_analyzer is not None
            mock_create_container.assert_called_once_with(self.config)
            mock_container.llm_file_analyzer.assert_called_once()

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        with patch(
            "repomap_tool.cli.services.service_factory.create_container"
        ) as mock_create_container:
            mock_container = Mock()
            mock_container.console.return_value = Mock()
            mock_container.parallel_tag_extractor.return_value = Mock()
            mock_container.fuzzy_matcher.return_value = Mock()
            mock_container.adaptive_semantic_matcher.return_value = Mock()
            mock_container.hybrid_matcher.return_value = Mock()
            mock_container.dependency_graph.return_value = Mock()
            mock_container.impact_analyzer.return_value = Mock()
            mock_container.centrality_calculator.return_value = Mock()

            mock_create_container.return_value = mock_container

            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_service = Mock()
                mock_repo_map_service.return_value = mock_service

                # Create a service
                service1 = self.factory.create_repomap_service(self.config)

                # Clear cache
                self.factory.clear_cache()

                # Create service again - should create new instance
                service2 = self.factory.create_repomap_service(self.config)

                # Should be different instances
                assert service1 is not service2
                # Container should be created twice
                assert mock_create_container.call_count == 2

    def test_clear_cache_specific_project(self):
        """Test clearing cache for specific project."""
        # Create two different configs with different project roots
        with tempfile.TemporaryDirectory() as temp_dir1:
            with tempfile.TemporaryDirectory() as temp_dir2:
                # Create project structures
                for temp_dir in [temp_dir1, temp_dir2]:
                    os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
                    with open(os.path.join(temp_dir, "src", "__init__.py"), "w") as f:
                        f.write("# Test project")

                config1 = RepoMapConfig(project_root=temp_dir1)
                config2 = RepoMapConfig(project_root=temp_dir2)

                with patch(
                    "repomap_tool.cli.services.service_factory.create_container"
                ) as mock_create_container:
                    mock_container = Mock()
                    mock_container.console.return_value = Mock()
                    mock_container.parallel_tag_extractor.return_value = Mock()
                    mock_container.fuzzy_matcher.return_value = Mock()
                    mock_container.adaptive_semantic_matcher.return_value = Mock()
                    mock_container.hybrid_matcher.return_value = Mock()
                    mock_container.dependency_graph.return_value = Mock()
                    mock_container.impact_analyzer.return_value = Mock()
                    mock_container.centrality_calculator.return_value = Mock()

                    mock_create_container.return_value = mock_container

                    with patch(
                        "repomap_tool.core.repo_map.RepoMapService"
                    ) as mock_repo_map_service:
                        mock_service = Mock()
                        mock_repo_map_service.return_value = mock_service

                        # Create services for both projects
                        service1 = self.factory.create_repomap_service(config1)
                        service2 = self.factory.create_repomap_service(config2)

                        # Clear cache for project1 only
                        self.factory.clear_cache(temp_dir1)

                        # Create service for project1 again - should create new instance
                        service1_new = self.factory.create_repomap_service(config1)

                        # Create service for project2 again - should use cached instance
                        service2_cached = self.factory.create_repomap_service(config2)

                        # Project1 should be different (new instance)
                        assert service1 is not service1_new
                        # Project2 should be same (cached)
                        assert service2 is service2_cached


class TestServiceFactoryGlobal:
    """Test global service factory functions."""

    def teardown_method(self):
        """Clean up after tests."""
        clear_service_cache()

    def test_get_service_factory(self):
        """Test get_service_factory function."""
        factory1 = get_service_factory()
        factory2 = get_service_factory()

        # Should return the same instance (singleton)
        assert factory1 is factory2

    def test_clear_service_cache(self):
        """Test clear_service_cache function."""
        factory = get_service_factory()

        # Clear cache should work
        clear_service_cache()

        # Should not raise any exceptions
        assert True

    def test_service_factory_integration(self):
        """Test service factory integration with real config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a simple project structure
            os.makedirs(os.path.join(temp_dir, "src"), exist_ok=True)
            with open(os.path.join(temp_dir, "src", "__init__.py"), "w") as f:
                f.write("# Test project")

            config = RepoMapConfig(
                project_root=temp_dir,
                fuzzy_match=FuzzyMatchConfig(threshold=80),
                semantic_match=SemanticMatchConfig(enabled=True, threshold=0.7),
                performance=PerformanceConfig(max_workers=4),
                dependencies=DependencyConfig(enable_impact_analysis=True),
            )

            factory = get_service_factory()

            # Test that we can create services without errors
            # (This will use real DI container, so we need to mock the actual service creation)
            with patch(
                "repomap_tool.core.repo_map.RepoMapService"
            ) as mock_repo_map_service:
                mock_service = Mock()
                mock_repo_map_service.return_value = mock_service

                service = factory.create_repomap_service(config)
                assert service is not None
