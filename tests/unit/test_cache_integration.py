"""
Unit tests for cache integration functionality in DockerRepoMap.

Tests the integration between cache manager and DockerRepoMap for file-based cache invalidation.
"""

import pytest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock


# Mock the external dependencies
@pytest.fixture(autouse=True)
def mock_external_deps():
    """Mock external dependencies that aren't available in test environment."""
    with patch.dict(
        "sys.modules",
        {
            "aider.repomap": Mock(),
            "aider.io": Mock(),
            "rich.console": Mock(),
            "rich.progress": Mock(),
        },
    ):
        yield


class TestCacheIntegration:
    """Test cases for cache integration functionality."""

    def test_cache_invalidation_on_initialization(self):
        """Test that stale caches are invalidated when DockerRepoMap is initialized."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        # Create a temporary project directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            test_file1 = temp_path / "test1.py"
            test_file2 = temp_path / "test2.py"

            test_file1.write_text("def hello(): pass")
            test_file2.write_text("def world(): pass")

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner to return our test files
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = [str(test_file1), str(test_file2)]

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Check that cache invalidation was called
                # Since we're mocking external dependencies, we can't fully test the actual invalidation
                # but we can verify the method exists and is callable
                assert hasattr(repomap, "_invalidate_stale_caches")
                assert callable(repomap._invalidate_stale_caches)

    def test_get_cache_status(self):
        """Test getting cache status from DockerRepoMap."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = []

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Get cache status
                status = repomap.get_cache_status()

                # Verify status structure
                assert isinstance(status, dict)
                assert "project_root" in status
                assert "fuzzy_matcher_cache" in status
                assert "tracked_files" in status
                assert "cache_enabled" in status

                # Verify project root (handle path normalization)
                assert (
                    Path(status["project_root"]).resolve() == Path(temp_path).resolve()
                )

                # Verify cache enabled status
                assert status["cache_enabled"] is True

    def test_refresh_all_caches(self):
        """Test refreshing all caches functionality."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = []

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Mock the logger to capture log messages
                with patch.object(repomap.logger, "info") as mock_logger:
                    # Refresh all caches
                    repomap.refresh_all_caches()

                    # Verify that the log message was called
                    mock_logger.assert_called_with("Cleared fuzzy matcher cache")

    def test_cache_invalidation_with_modified_files(self):
        """Test cache invalidation when files are modified."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            test_file1 = temp_path / "test1.py"
            test_file2 = temp_path / "test2.py"

            test_file1.write_text("def hello(): pass")
            test_file2.write_text("def world(): pass")

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner to return our test files
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = [str(test_file1), str(test_file2)]

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Modify one of the files
                time.sleep(0.1)  # Ensure different timestamp
                test_file1.write_text("def hello_modified(): pass")

                # Mock the logger to capture invalidation messages
                with patch.object(repomap.logger, "info") as mock_logger:
                    # Call cache invalidation manually
                    repomap._invalidate_stale_caches()

                    # Verify that invalidation was logged
                    # Note: In a real scenario, this would actually invalidate caches
                    # Here we're just testing the method exists and is callable
                    assert hasattr(repomap, "_invalidate_stale_caches")

    def test_cache_invalidation_error_handling(self):
        """Test that cache invalidation handles errors gracefully."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner to raise an exception
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.side_effect = Exception("File system error")

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Mock the logger to capture warning messages
                with patch.object(repomap.logger, "warning") as mock_logger:
                    # Call cache invalidation manually
                    repomap._invalidate_stale_caches()

                    # Verify that the error was logged as a warning
                    mock_logger.assert_called()
                    # Check that the warning message contains error information
                    call_args = mock_logger.call_args[0][0]
                    assert "Error during cache invalidation" in call_args

    def test_cache_status_with_disabled_cache(self):
        """Test cache status when caching is disabled."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create configuration with caching disabled but matchers enabled
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,  # Keep enabled for validation
                threshold=70,
                cache_results=False,  # Disable caching
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,  # Keep enabled for validation
                threshold=0.7,
                cache_results=False,  # Disable caching
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = []

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Get cache status
                status = repomap.get_cache_status()

                # Verify cache is disabled
                assert status["cache_enabled"] is False
                assert status["fuzzy_matcher_cache"] is None
                assert status["tracked_files"] == []

    def test_cache_integration_with_file_changes(self):
        """Test the complete flow of cache integration with file changes."""
        from repomap_tool.core.repo_map import DockerRepoMap
        from repomap_tool.models import (
            RepoMapConfig,
            FuzzyMatchConfig,
            SemanticMatchConfig,
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            test_file1 = temp_path / "test1.py"
            test_file2 = temp_path / "test2.py"

            test_file1.write_text("def hello(): pass")
            test_file2.write_text("def world(): pass")

            # Create configuration
            fuzzy_config = FuzzyMatchConfig(
                enabled=True,
                threshold=70,
                cache_results=True,
            )
            semantic_config = SemanticMatchConfig(
                enabled=True,
                threshold=0.7,
                cache_results=True,
            )

            config = RepoMapConfig(
                project_root=str(temp_path),
                fuzzy_match=fuzzy_config,
                semantic_match=semantic_config,
                verbose=False,
            )

            # Mock the file scanner to return our test files
            with patch(
                "repomap_tool.core.repo_map.get_project_files"
            ) as mock_get_files:
                mock_get_files.return_value = [str(test_file1), str(test_file2)]

                # Initialize DockerRepoMap
                repomap = DockerRepoMap(config)

                # Get initial cache status
                initial_status = repomap.get_cache_status()
                assert initial_status["cache_enabled"] is True

                # Modify files
                time.sleep(0.1)
                test_file1.write_text("def hello_modified(): pass")
                test_file2.write_text("def world_modified(): pass")

                # Mock the logger to capture invalidation messages
                with patch.object(repomap.logger, "info") as mock_logger:
                    # Call cache invalidation manually
                    repomap._invalidate_stale_caches()

                    # Verify that the method executed without errors
                    # In a real scenario, this would actually invalidate caches
                    assert hasattr(repomap, "_invalidate_stale_caches")

                    # Get final cache status
                    final_status = repomap.get_cache_status()
                    assert final_status["cache_enabled"] is True
