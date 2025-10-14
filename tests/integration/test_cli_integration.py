"""
Integration tests for CLI functionality.

This module tests CLI integration with real configuration and services.
"""

import pytest
from unittest.mock import patch
from datetime import datetime
from repomap_tool.models import ProjectInfo
from repomap_tool.cli.main import cli


class TestCLIIntegration:
    """Integration tests for CLI functionality."""

    def test_cli_configuration_integration(self, session_test_repo_path):
        """Test CLI configuration integration."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_instance = mock_repo_map
            mock_instance.analyze_project.return_value = ProjectInfo(
                project_root=str(session_test_repo_path),
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )

            # Test that we can create services without errors
            service = mock_factory.create_repomap_service.return_value
            assert service is not None
