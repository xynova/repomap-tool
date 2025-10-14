"""
Integration tests for edge cases in integration scenarios.

This module tests full workflow integration with various edge cases.
"""

import pytest
from repomap_tool.models import RepoMapConfig, SearchRequest


class TestIntegrationEdgeCases:
    """Test edge cases in integration scenarios."""

    def test_full_workflow_with_edge_cases(
        self, session_container, session_test_repo_path
    ):
        """Test full workflow with various edge cases."""
        # Use session test repository instead of creating temporary directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))
        from tests.conftest import create_repomap_service_from_session_container

        repomap = create_repomap_service_from_session_container(
            session_container, config
        )

        # Act
        project_info = repomap.analyze_project()

        # Assert - Should handle edge cases gracefully
        assert isinstance(project_info.total_files, int)
        assert isinstance(project_info.total_identifiers, int)

        # Test search with edge cases
        search_request = SearchRequest(query="test", match_type="fuzzy", max_results=5)
        search_response = repomap.search_identifiers(search_request)

        # Assert - Should handle search with edge cases gracefully
        assert isinstance(search_response.total_results, int)

    def test_integration_edge_cases_break_system(
        self, session_container, session_test_repo_path
    ):
        """Integration edge cases can break the entire system."""
        # Arrange - Use session test repository instead of temp directory
        config = RepoMapConfig(project_root=str(session_test_repo_path))
        from tests.conftest import create_repomap_service_from_session_container

        repomap = create_repomap_service_from_session_container(
            session_container, config
        )

        # Act & Assert - Should handle integration edge cases gracefully
        # Use a more focused test that doesn't run full project analysis
        try:
            # Test basic service creation and configuration
            assert repomap.config is not None
            assert repomap.fuzzy_matcher is not None

            # Test a simple search without full project analysis
            search_request = SearchRequest(
                query="test", match_type="fuzzy", max_results=5
            )
            # This will use the pre-built session identifiers instead of analyzing the whole project
            search_response = repomap.search_identifiers(search_request)
            assert isinstance(search_response.total_results, int)
        except Exception as e:
            pytest.fail(f"Integration edge cases broke the system: {e}")
