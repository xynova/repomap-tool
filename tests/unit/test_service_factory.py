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

    def _create_test_config(self, temp_dir_path: str):
        """Create a test configuration with a temporary repository path."""
        # Normalize the temporary directory path to resolve symlinks
        normalized_path = Path(temp_dir_path).resolve()
        return RepoMapConfig(
            project_root=str(normalized_path),
            fuzzy_match=FuzzyMatchConfig(),
            semantic_match=SemanticMatchConfig(),
            performance=PerformanceConfig(),
            dependencies=DependencyConfig(),
        )

    def setup_method(self):
        """Set up test fixtures."""
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

    def test_create_repomap_service(self, session_test_repo_path):
        """Test RepoMapService creation with DI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            with patch(
                "repomap_tool.core.container.create_container"
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
                    service = self.factory.create_repomap_service(config)

                    assert service is not None
                    mock_create_container.assert_called_once_with(config)
                    mock_repo_map_service.assert_called_once()

    def test_create_repomap_service_caching(self, session_test_repo_path):
        """Test that RepoMapService is cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            # Use the resolved path from the config object for the expected cache key
            expected_cache_key = f"repomap_{config.project_root}"
            with patch(
                "repomap_tool.core.container.create_container"
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
                    service1 = self.factory.create_repomap_service(config)
                    service2 = self.factory.create_repomap_service(config)

                    # Should be the same instance (cached)
                    assert service1 is service2
                    # Container should only be created once
                    assert mock_create_container.call_count == 1
                    assert expected_cache_key in self.factory._services

    def test_create_entrypoint_discoverer(self, session_test_repo_path):
        """Test EntrypointDiscoverer creation with DI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            # Use the resolved path from the config object for the expected cache key
            expected_cache_key = f"discoverer_{config.project_root}"
            with (
                patch(
                    "repomap_tool.core.container.create_container"
                ) as mock_create_container,
                patch(
                    "repomap_tool.core.repo_map.RepoMapService"
                ) as MockRepoMapService,
                patch(
                    "repomap_tool.code_exploration.discovery_engine.EntrypointDiscoverer"
                ) as MockEntrypointDiscoverer,
            ):
                mock_create_container.return_value.console.return_value = Mock()
                service_factory = ServiceFactory()
                mock_repo_map_service = MockRepoMapService()
                mock_entrypoint_discoverer = MockEntrypointDiscoverer()

                # Create EntrypointDiscoverer
                discoverer = service_factory.create_entrypoint_discoverer(
                    mock_repo_map_service, config
                )

                assert discoverer is not None
                assert expected_cache_key in service_factory._services
                mock_create_container.assert_called_once()

    def test_create_tree_builder(self, session_test_repo_path):
        """Test TreeBuilder creation with DI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            # Use the resolved path from the config object for the expected cache key
            expected_cache_key = f"tree_builder_{config.project_root}"
            with (
                patch(
                    "repomap_tool.core.container.create_container"
                ) as mock_create_container,
                patch(
                    "repomap_tool.core.repo_map.RepoMapService"
                ) as MockRepoMapService,
                patch(
                    "repomap_tool.code_exploration.discovery_engine.EntrypointDiscoverer"
                ) as MockEntrypointDiscoverer,
                patch(
                    "repomap_tool.code_exploration.tree_builder.TreeBuilder"
                ) as MockTreeBuilder,
            ):
                mock_create_container.return_value.console.return_value = Mock()
                service_factory = ServiceFactory()
                mock_repo_map_service = MockRepoMapService()
                mock_entrypoint_discoverer = MockEntrypointDiscoverer()
                mock_tree_builder = MockTreeBuilder()

                # Create TreeBuilder
                tree_builder = service_factory.create_tree_builder(
                    mock_repo_map_service, config
                )

                assert tree_builder is not None
                assert expected_cache_key in service_factory._services
                mock_create_container.assert_called_once()

    def test_create_tree_manager(self, session_test_repo_path):
        """Test TreeManager creation with DI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            # Use the resolved path from the config object for the expected cache key
            expected_cache_key = f"tree_manager_{config.project_root}"
            with (
                patch(
                    "repomap_tool.core.container.create_container"
                ) as mock_create_container,
                patch(
                    "repomap_tool.core.repo_map.RepoMapService"
                ) as MockRepoMapService,
                patch(
                    "repomap_tool.code_exploration.tree_builder.TreeBuilder"
                ) as MockTreeBuilder,
                patch(
                    "repomap_tool.code_exploration.session_manager.SessionManager"
                ) as MockSessionManager,
                patch(
                    "repomap_tool.code_exploration.tree_manager.TreeManager"
                ) as MockTreeManager,
            ):
                mock_create_container.return_value.console.return_value = Mock()
                service_factory = ServiceFactory()
                mock_repo_map_service = MockRepoMapService()
                mock_tree_builder = MockTreeBuilder()
                mock_session_manager = MockSessionManager()
                mock_tree_manager = MockTreeManager()

                # Mock the container.session_manager call
                mock_create_container.return_value.session_manager.return_value = (
                    mock_session_manager
                )

                # Create TreeManager
                tree_manager = service_factory.create_tree_manager(
                    mock_repo_map_service, config
                )

                assert tree_manager is not None
                assert expected_cache_key in service_factory._services
                mock_create_container.assert_called_once()

    def test_get_llm_analyzer(self, session_test_repo_path):
        """Test LLM analyzer creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = self._create_test_config(tmpdir)
            # Use the resolved path from the config object for the expected cache key
            expected_cache_key = f"llm_analyzer_{config.project_root}"
            with (
                patch(
                    "repomap_tool.core.container.create_container"
                ) as mock_create_container,
                patch(
                    "repomap_tool.core.repo_map.RepoMapService"
                ) as MockRepoMapService,
                patch(
                    "repomap_tool.code_analysis.llm_file_analyzer.LLMFileAnalyzer"
                ) as MockLLMFileAnalyzer,
            ):
                mock_create_container.return_value.console.return_value = Mock()
                service_factory = ServiceFactory()
                mock_repo_map_service = MockRepoMapService()
                mock_llm_file_analyzer = MockLLMFileAnalyzer()

                # Mock the container.llm_file_analyzer call
                mock_create_container.return_value.llm_file_analyzer.return_value = (
                    mock_llm_file_analyzer
                )

                # Get LLM analyzer
                llm_analyzer = service_factory.get_llm_analyzer(config)

                assert llm_analyzer is not None
                assert expected_cache_key in service_factory._services
                mock_create_container.assert_called_once()

    def test_clear_cache(self, session_test_repo_path):
        """Test cache clearing functionality."""
        with (
            tempfile.TemporaryDirectory() as tmpdir1,
            tempfile.TemporaryDirectory() as tmpdir2,
        ):
            config1 = self._create_test_config(tmpdir1)
            config2 = self._create_test_config(tmpdir2)

            with patch(
                "repomap_tool.core.container.create_container"
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
                    service1 = self.factory.create_repomap_service(config1)

                    # Clear cache
                    self.factory.clear_cache()

                    # Create service again - should create new instance
                    service2 = self.factory.create_repomap_service(config2)

                    # Should be different instances
                    assert service1 is not service2
                    # Container should be created twice
                    assert mock_create_container.call_count == 2

    def test_clear_cache_specific_project(self, session_test_repo_path):
        """Test clearing cache for specific project."""
        with (
            tempfile.TemporaryDirectory() as tmpdir1,
            tempfile.TemporaryDirectory() as tmpdir2,
        ):
            config1 = self._create_test_config(tmpdir1)
            config2 = self._create_test_config(tmpdir2)
            # Use the resolved path from the config object for the expected cache key
            expected_remaining_key = f"repomap_{config2.project_root}"
            with patch(
                "repomap_tool.core.container.create_container"
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

                    # Create services for two distinct projects
                    service_factory = ServiceFactory()
                    service_factory.create_repomap_service(config1)
                    service_factory.create_repomap_service(config2)

                    assert len(service_factory._services) == 2
                    assert len(service_factory._containers) == 2

                    # Clear cache for specific project
                    service_factory.clear_cache(config1.project_root)

                    assert expected_remaining_key in service_factory._services
                    assert len(service_factory._services) == 1
                    assert len(service_factory._containers) == 1


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
