"""
Integration tests for service factory.

This module tests service factory integration with real configuration and DI container.
"""

import pytest
from unittest.mock import Mock, patch
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    DependencyConfig,
)
from repomap_tool.cli.services.service_factory import get_service_factory


class TestServiceFactoryIntegration:
    """Integration tests for service factory."""

    def test_service_factory_integration(self, session_test_repo_path):
        """Test service factory integration with real config."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(
            project_root=str(session_test_repo_path),
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
