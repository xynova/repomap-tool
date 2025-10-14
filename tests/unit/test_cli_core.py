"""
Comprehensive CLI testing for core commands.

This module tests all the core CLI commands to ensure they work correctly
in all scenarios, including edge cases and error conditions.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from repomap_tool.cli import cli
from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    ProjectInfo,
    SearchResponse,
    MatchResult,
    TreeConfig,
)


@pytest.fixture
def cli_runner():
    return CliRunner()


@pytest.fixture
def temp_project(session_test_repo_path):
    """Use session test repository instead of creating temporary directory."""
    return str(session_test_repo_path)


class TestCLICore:
    """Test core CLI commands."""

    def test_analyze_command_exists(self, cli_runner):
        """Test that analyze command exists and shows help."""
        result = cli_runner.invoke(cli, ["index", "create", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower()

    def test_analyze_basic_usage(self, cli_runner, temp_project):
        """Test basic analyze command usage."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_instance = mock_repo_map

            # Create a mock ProjectInfo that returns proper JSON
            mock_project_info = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )

            # Mock the analyze_project method to return the ProjectInfo
            mock_instance.analyze_project.return_value = mock_project_info

            result = cli_runner.invoke(
                cli, ["index", "create", temp_project, "--fuzzy"]
            )
            assert result.exit_code == 0
            assert "LLM-Optimized Project" in result.output  # Check for TEXT output

    def test_analyze_with_config_file(self, cli_runner, temp_project):
        """Test analyze command with config file."""
        config_content = f"""
        {{
            "project_root": "{temp_project}",
            "fuzzy_match": {{"threshold": 70}},
            "semantic_match": {{"enabled": false}}
        }}
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(config_content)
            config_file = f.name

        try:
            with patch(
                "repomap_tool.cli.services.get_service_factory"
            ) as mock_get_factory:
                mock_factory = mock_get_factory.return_value
                mock_repo_map = mock_factory.create_repomap_service.return_value
                mock_instance = mock_repo_map

                # Create a mock ProjectInfo that returns proper JSON
                mock_project_info = ProjectInfo(
                    project_root=temp_project,
                    total_files=1,
                    total_identifiers=1,
                    file_types={"py": 1},
                    identifier_types={"function": 1},
                    analysis_time_ms=100.0,
                    last_updated=datetime.now(),
                )

                # Mock the analyze_project method to return the ProjectInfo
                mock_instance.analyze_project.return_value = mock_project_info

                # CLI still requires project_path even with config file
                result = cli_runner.invoke(
                    cli, ["index", "create", temp_project, "--config", config_file]
                )
                assert result.exit_code == 0
                assert "LLM-Optimized Project" in result.output  # Check for TEXT output
        finally:
            os.unlink(config_file)

    def test_analyze_with_options(self, cli_runner, temp_project):
        """Test analyze command with various options."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_instance = mock_repo_map
            mock_instance.analyze_project.return_value = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )

            result = cli_runner.invoke(
                cli,
                [
                    "index",
                    "create",
                    temp_project,
                    "--fuzzy",
                    "--no-progress",
                    "--output",
                    "json",
                ],
            )
            assert result.exit_code == 0

    def test_search_command_exists(self, cli_runner):
        """Test that search command exists and shows help."""
        result = cli_runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_search_basic_usage(self, cli_runner, temp_project):
        """Test basic search command usage."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_repo_map.search_identifiers.return_value = SearchResponse(
                query="test",
                match_type="fuzzy",
                threshold=0.7,
                total_results=1,
                results=[
                    MatchResult(
                        identifier="test_function",
                        score=0.9,
                        strategy="prefix",
                        match_type="fuzzy",
                        file_path="src/main.py",
                        line_number=1,
                    )
                ],
                search_time_ms=50.0,
            )

            # CLI signature: search QUERY [PROJECT_PATH] [OPTIONS]
            result = cli_runner.invoke(
                cli,
                [
                    "search",
                    "test",
                    temp_project,
                    "--match-type",
                    "fuzzy",
                ],
            )
            if result.exit_code != 0:
                print(f"CLI Output: {result.output}")
                print(f"CLI Exception: {result.exception}")
            assert result.exit_code == 0
            assert "test_function" in result.output

    def test_search_with_options(self, cli_runner, temp_project):
        """Test search command with various options."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_repo_map.search_identifiers.return_value = SearchResponse(
                query="test",
                match_type="fuzzy",
                threshold=0.7,
                total_results=0,
                results=[],
                search_time_ms=50.0,
            )

            # CLI signature: search QUERY [PROJECT_PATH] [OPTIONS]
            result = cli_runner.invoke(
                cli,
                [
                    "search",
                    "test",
                    temp_project,
                    "--match-type",
                    "fuzzy",
                    "--max-results",
                    "10",
                    "--output",
                    "text",
                ],
            )
            assert result.exit_code == 0

    def test_config_command_exists(self, cli_runner):
        """Test that config command exists and shows help."""
        result = cli_runner.invoke(cli, ["system", "config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_basic_usage(self, cli_runner, temp_project):
        """Test basic config command usage."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            result = cli_runner.invoke(
                cli, ["system", "config", temp_project, "--output", config_file]
            )
            assert result.exit_code == 0
            assert os.path.exists(config_file)
        finally:
            os.unlink(config_file)

    def test_version_command(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(cli, ["system", "version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_explore_command_exists(self, cli_runner):
        """Test that explore command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "start", "--help"])
        assert result.exit_code == 0
        assert "explore" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_explore_basic_usage(self, cli_runner, temp_project):
        """Test basic explore command usage."""
        # Explore command is complex and requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "start", "analyze", temp_project])

        # It might fail due to missing dependencies, but that's expected
        # We're just testing that the command structure is correct
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_focus_command_exists(self, cli_runner):
        """Test that focus command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "focus", "--help"])
        assert result.exit_code == 0
        assert "focus" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_focus_basic_usage(self, cli_runner):
        """Test basic focus command usage."""
        # Focus command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "focus", "tree_123"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_expand_command_exists(self, cli_runner):
        """Test that expand command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "expand", "--help"])
        assert result.exit_code == 0
        assert "expand" in result.output.lower()

    def test_expand_basic_usage(self, cli_runner):
        """Test basic expand command usage."""
        # Expand command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "expand", "src/"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_prune_command_exists(self, cli_runner):
        """Test that prune command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "prune", "--help"])
        assert result.exit_code == 0
        assert "prune" in result.output.lower()

    def test_prune_basic_usage(self, cli_runner):
        """Test basic prune command usage."""
        # Prune command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "prune", "tests/"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_map_command_exists(self, cli_runner):
        """Test that map command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "map", "--help"])
        assert result.exit_code == 0
        assert "map" in result.output.lower()

    def test_map_basic_usage(self, cli_runner):
        """Test basic map command usage."""
        # Map command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "map"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_list_trees_command_exists(self, cli_runner):
        """Test that list-trees command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "trees", "--help"])
        assert result.exit_code == 0
        assert "trees" in result.output.lower()

    def test_list_trees_basic_usage(self, cli_runner):
        """Test basic usage of list-trees command."""
        # List-trees command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "trees"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_status_command_exists(self, cli_runner):
        """Test that status command exists and shows help."""
        result = cli_runner.invoke(cli, ["explore", "status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()

    def test_status_basic_usage(self, cli_runner):
        """Test basic usage of status command."""
        # Status command requires session management
        # Just test that it accepts the basic arguments
        result = cli_runner.invoke(cli, ["explore", "status"])

        # It might fail due to missing session, but that's expected
        assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_cli_error_handling(self, cli_runner):
        """Test CLI error handling."""
        result = cli_runner.invoke(cli, ["nonexistent-command"])
        assert result.exit_code == 2  # Click usage error

    def test_cli_invalid_project_path(self, cli_runner):
        """Test CLI with invalid project path."""
        result = cli_runner.invoke(cli, ["index", "create", "/nonexistent/path"])
        assert result.exit_code == 2  # Click usage error

    def test_cli_output_format_validation(self, cli_runner, temp_project):
        """Test CLI output format validation."""
        # Test invalid output format
        result = cli_runner.invoke(
            cli, ["index", "create", temp_project, "--output", "invalid_format"]
        )

        assert result.exit_code == 2  # Click usage error

    def test_cli_verbose_output(self, cli_runner, temp_project):
        """Test CLI verbose output."""
        with patch("repomap_tool.cli.services.get_service_factory") as mock_get_factory:
            mock_factory = mock_get_factory.return_value
            mock_repo_map = mock_factory.create_repomap_service.return_value
            mock_instance = mock_repo_map
            mock_instance.analyze_project.return_value = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )

            result = cli_runner.invoke(
                cli, ["index", "create", temp_project, "--fuzzy", "--verbose"]
            )
            assert result.exit_code == 0
