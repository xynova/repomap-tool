"""
Unit tests for CLI cache command functionality.

Tests the cache command that shows cache status and allows cache refresh.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner


# Mock the external dependencies
@pytest.fixture(autouse=True)
def mock_external_deps():
    """Mock external dependencies that aren't available in test environment."""
    with patch.dict(
        "sys.modules",
        {
            "rich.console": Mock(),
            "rich.table": Mock(),
            "rich.panel": Mock(),
            "rich.progress": Mock(),
        },
    ):
        yield


class TestCLICacheCommand:
    """Test cases for CLI cache command functionality."""

    def test_cache_command_help(self):
        """Test that the cache command shows help information."""
        from repomap_tool.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["cache", "--help"])

        assert result.exit_code == 0
        assert "Show cache status and optionally refresh caches" in result.output
        assert "--refresh" in result.output
        assert "--output" in result.output
        assert "--verbose" in result.output

    def test_cache_command_basic_usage(self):
        """Test basic cache command usage."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file to make the directory valid
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap to avoid external dependencies
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                # Mock the instance
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": {
                        "cache_size": 5,
                        "max_size": 1000,
                        "hit_rate_percent": 85.5,
                        "tracked_files": 3,
                    },
                    "tracked_files": ["test1.py", "test2.py", "test3.py"],
                    "cache_enabled": True,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command
                result = runner.invoke(cli, ["cache", str(temp_path)])

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify that DockerRepoMap was called with correct config
                mock_docker_repomap.assert_called_once()
                call_args = mock_docker_repomap.call_args[0][0]
                # Handle path normalization for comparison
                assert (
                    Path(call_args.project_root).resolve() == Path(temp_path).resolve()
                )
                assert call_args.fuzzy_match.enabled is True
                assert call_args.fuzzy_match.cache_results is True

    def test_cache_command_with_refresh(self):
        """Test cache command with refresh flag."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": None,
                    "tracked_files": [],
                    "cache_enabled": False,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command with refresh
                result = runner.invoke(cli, ["cache", str(temp_path), "--refresh"])

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify that refresh_all_caches was called
                mock_instance.refresh_all_caches.assert_called_once()

    def test_cache_command_json_output(self):
        """Test cache command with JSON output format."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": {
                        "cache_size": 10,
                        "max_size": 1000,
                        "hit_rate_percent": 90.0,
                        "tracked_files": 5,
                    },
                    "tracked_files": [
                        "file1.py",
                        "file2.py",
                        "file3.py",
                        "file4.py",
                        "file5.py",
                    ],
                    "cache_enabled": True,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command with JSON output
                result = runner.invoke(
                    cli, ["cache", str(temp_path), "--output", "json"]
                )

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify JSON output (should contain the cache status data)
                assert "project_root" in result.output
                assert "fuzzy_matcher_cache" in result.output
                assert "tracked_files" in result.output
                assert "cache_enabled" in result.output

    def test_cache_command_verbose_output(self):
        """Test cache command with verbose flag."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": {
                        "cache_size": 3,
                        "max_size": 1000,
                        "hit_rate_percent": 75.0,
                        "tracked_files": 2,
                    },
                    "tracked_files": ["main.py", "utils.py"],
                    "cache_enabled": True,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command with verbose flag
                result = runner.invoke(cli, ["cache", str(temp_path), "--verbose"])

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify that tracked files are shown in verbose mode
                # The output should contain the file names
                assert "main.py" in result.output
                assert "utils.py" in result.output

    def test_cache_command_error_handling(self):
        """Test cache command error handling."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap to raise an exception
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_docker_repomap.side_effect = Exception("Configuration error")

                # Run the cache command
                result = runner.invoke(cli, ["cache", str(temp_path)])

                # Verify the command failed with error
                assert result.exit_code == 1
                assert "Error:" in result.output

    def test_cache_command_invalid_project_path(self):
        """Test cache command with invalid project path."""
        from repomap_tool.cli import cli

        runner = CliRunner()

        # Run the cache command with non-existent path
        result = runner.invoke(cli, ["cache", "/nonexistent/path"])

        # Verify the command failed
        assert result.exit_code != 0

    def test_cache_command_cache_disabled(self):
        """Test cache command when caching is disabled."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": None,
                    "tracked_files": [],
                    "cache_enabled": False,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command
                result = runner.invoke(cli, ["cache", str(temp_path)])

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify that disabled cache is shown correctly
                assert "✗ Disabled" in result.output or "No cache" in result.output

    def test_cache_command_complex_cache_status(self):
        """Test cache command with complex cache status data."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap with complex cache data
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": {
                        "cache_size": 150,
                        "max_size": 1000,
                        "hit_rate_percent": 92.3,
                        "tracked_files": 25,
                        "hits": 1200,
                        "misses": 100,
                        "evictions": 5,
                        "expirations": 2,
                        "invalidations": 8,
                    },
                    "tracked_files": [f"file{i}.py" for i in range(25)],
                    "cache_enabled": True,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command
                result = runner.invoke(cli, ["cache", str(temp_path)])

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify that complex cache data is displayed
                assert "150/1000" in result.output  # cache size
                assert "92.3%" in result.output  # hit rate
                assert "25" in result.output  # tracked files

    def test_cache_command_table_output_format(self):
        """Test cache command table output format."""
        from repomap_tool.cli import cli

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file
            test_file = temp_path / "test.py"
            test_file.write_text("def test(): pass")

            runner = CliRunner()

            # Mock the DockerRepoMap
            with patch("repomap_tool.cli.DockerRepoMap") as mock_docker_repomap:
                mock_instance = Mock()
                mock_instance.get_cache_status.return_value = {
                    "project_root": str(temp_path),
                    "fuzzy_matcher_cache": {
                        "cache_size": 5,
                        "max_size": 1000,
                        "hit_rate_percent": 80.0,
                        "tracked_files": 3,
                    },
                    "tracked_files": ["src/main.py", "src/utils.py", "tests/test.py"],
                    "cache_enabled": True,
                }
                mock_docker_repomap.return_value = mock_instance

                # Run the cache command with table output (default)
                result = runner.invoke(
                    cli, ["cache", str(temp_path), "--output", "table"]
                )

                # Verify the command executed successfully
                assert result.exit_code == 0

                # Verify table structure elements
                assert "Component" in result.output
                assert "Status" in result.output
                assert "Details" in result.output
                assert "Cache System" in result.output
                assert "Fuzzy Matcher" in result.output
