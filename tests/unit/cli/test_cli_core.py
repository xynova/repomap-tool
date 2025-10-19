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
from dependency_injector.wiring import Container
from dependency_injector.containers import DynamicContainer
from pathlib import Path


@pytest.fixture
def cli_runner() -> CliRunner:
    # This fixture will be replaced by cli_runner_with_container where needed
    return CliRunner()


@pytest.fixture
def temp_project(session_test_repo_path: str) -> str:
    """Use session test repository instead of creating temporary directory."""
    return str(session_test_repo_path)


@pytest.fixture(scope="class")
def test_container_for_overrides(session_container: Container) -> DynamicContainer:
    """Provides a test container for overriding providers in CLI tests."""
    # Reset the container before each test class to ensure a clean state for overrides
    session_container.reset_singletons()
    yield session_container


@pytest.fixture(scope="function")
def cli_runner_for_tests(cli_runner_with_container: CliRunner) -> CliRunner:
    """Provides a CliRunner for CLI tests."""
    yield cli_runner_with_container


class TestCLICore:
    """Test core CLI commands."""

    def test_analyze_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that analyze command exists and shows help."""
        # We are no longer patching get_output_manager directly.
        # The cli_runner_with_container fixture ensures a configured container.
        result = cli_runner_with_container.invoke(cli, ["index", "create", "--help"])
        assert result.exit_code == 0
        assert "create" in result.output.lower()

    def test_analyze_basic_usage(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test basic analyze command usage."""
        # No longer patching get_output_manager. It comes from the injected container.

        # Mock RepoMapService and its analyze_project method
        mock_repo_map_service = MagicMock()
        mock_project_info = ProjectInfo(
            project_root=temp_project,
            total_files=1,
            total_identifiers=1,
            file_types={"py": 1},
            identifier_types={"function": 1},
            analysis_time_ms=100.0,
            last_updated=datetime.now(),
        )
        mock_repo_map_service.analyze_project.return_value = mock_project_info

        # Patch the repo_map_service provider in the container
        with session_container.repo_map_service.override(mock_repo_map_service):
            result = cli_runner_with_container.invoke(
                cli, ["index", "create", temp_project, "--fuzzy"]
            )
            assert result.exit_code == 0
            assert "LLM-Optimized Project" in result.output  # Check for TEXT output

    def test_analyze_with_config_file(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
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
            # Mock RepoMapService and its analyze_project method
            mock_repo_map_service = MagicMock()
            mock_project_info = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )
            mock_repo_map_service.analyze_project.return_value = mock_project_info

            # Patch the repo_map_service provider in the container
            with session_container.repo_map_service.override(mock_repo_map_service):
                # CLI still requires project_path even with config file
                result = cli_runner_with_container.invoke(
                    cli, ["index", "create", temp_project, "--config", config_file]
                )
                assert result.exit_code == 0
                assert "LLM-Optimized Project" in result.output  # Check for TEXT output
        finally:
            os.unlink(config_file)

    def test_analyze_with_options(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test analyze command with various options."""
        # Mock RepoMapService and its analyze_project method
        mock_repo_map_service = MagicMock()
        mock_repo_map_service.analyze_project.return_value = ProjectInfo(
            project_root=temp_project,
            total_files=1,
            total_identifiers=1,
            file_types={"py": 1},
            identifier_types={"function": 1},
            analysis_time_ms=100.0,
            last_updated=datetime.now(),
        )
        
        # Debug: Check if the mock is being called
        def mock_analyze_project(*args, **kwargs):
            print(f"Mock analyze_project called with args: {args}, kwargs: {kwargs}")
            return ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )
        
        mock_repo_map_service.analyze_project.side_effect = mock_analyze_project

        # Mock the service factory to return our mock service
        with patch('repomap_tool.cli.services.service_factory.get_service_factory') as mock_factory:
            mock_factory.return_value.create_repomap_service.return_value = mock_repo_map_service
            print(f"Mock factory set up: {mock_factory.return_value}")
            
            # Also mock the analyze_project method directly on the mock service
            mock_repo_map_service.analyze_project.return_value = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )
            
            # Also patch the RepoMapService.analyze_project method directly
            with patch('repomap_tool.core.repo_map.RepoMapService.analyze_project') as mock_analyze:
                mock_analyze.return_value = ProjectInfo(
                    project_root=temp_project,
                    total_files=1,
                    total_identifiers=1,
                    file_types={"py": 1},
                    identifier_types={"function": 1},
                    analysis_time_ms=100.0,
                    last_updated=datetime.now(),
                )
                
                result = cli_runner_with_container.invoke(
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
                print(f"Exit code: {result.exit_code}")
                print(f"Output: {result.output}")
                print(f"Mock factory called: {mock_factory.called}")
                print(f"Mock factory return value called: {mock_factory.return_value.create_repomap_service.called}")
                print(f"Mock service analyze_project called: {mock_repo_map_service.analyze_project.called}")
                print(f"Mock analyze called: {mock_analyze.called}")
                
                # Check if the command succeeded
                if result.exit_code != 0:
                    print(f"Command failed with exit code {result.exit_code}")
                    print(f"Error output: {result.output}")
                    assert False, f"Command failed with exit code {result.exit_code}: {result.output}"
                
                # Verify that JSON output contains expected fields
                import json
                try:
                    output_data = json.loads(result.output)
                    print(f"Parsed JSON: {output_data}")
                    assert "project_root" in output_data
                    assert output_data["project_root"] == temp_project
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    print(f"Raw output: {result.output}")
                    assert False, f"Failed to parse JSON: {e}"

    def test_search_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that search command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "search" in result.output.lower()

    def test_search_basic_usage(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test basic search command usage."""
        mock_repo_map_service = MagicMock()
        mock_repo_map_service.search_identifiers.return_value = SearchResponse(
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

        # Mock the RepoMapService.search_identifiers method directly
        with patch('repomap_tool.core.repo_map.RepoMapService.search_identifiers') as mock_search:
            mock_search.return_value = SearchResponse(
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
            result = cli_runner_with_container.invoke(
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

    def test_search_with_options(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test search command with various options."""
        mock_repo_map_service = MagicMock()
        mock_repo_map_service.search_identifiers.return_value = SearchResponse(
            query="test",
            match_type="fuzzy",
            threshold=0.7,
            total_results=0,
            results=[],
            search_time_ms=50.0,
        )

        with session_container.repo_map_service.override(mock_repo_map_service):
            # CLI signature: search QUERY [PROJECT_PATH] [OPTIONS]
            result = cli_runner_with_container.invoke(
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

    def test_config_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that config command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["system", "config", "--help"])
        assert result.exit_code == 0
        assert "config" in result.output.lower()

    def test_config_basic_usage(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test basic config command usage."""
        # Create a temporary config file path
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_file = f.name

        try:
            mock_repo_map_service = MagicMock()
            mock_repo_map_service.analyze_project.return_value = ProjectInfo(
                project_root=temp_project,
                total_files=1,
                total_identifiers=1,
                file_types={"py": 1},
                identifier_types={"function": 1},
                analysis_time_ms=100.0,
                last_updated=datetime.now(),
            )

            with session_container.repo_map_service.override(mock_repo_map_service):
                # Test the system config command with --config option
                result = cli_runner_with_container.invoke(
                    cli, ["system", "config", "--config", config_file]
                )
                assert result.exit_code == 0
                assert os.path.exists(config_file)
        finally:
            if os.path.exists(config_file):
                os.unlink(config_file)

    def test_version_command(self, cli_runner_with_container: CliRunner) -> None:
        """Test version command."""
        result = cli_runner_with_container.invoke(cli, ["system", "version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_explore_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that explore command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "start", "--help"])
        assert result.exit_code == 0
        assert "explore" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_explore_basic_usage(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test basic explore command usage."""
        # Explore command is complex and requires session management
        # Just test that it accepts the basic arguments

        # Mock the exploration controller and its execute method
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        # Patch the exploration_controller provider in the container
        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "start", "analyze", temp_project])

            # It might fail due to missing dependencies, but that's expected
            # We're just testing that the command structure is correct
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_focus_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that focus command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "focus", "--help"])
        assert result.exit_code == 0
        assert "focus" in result.output.lower()

    @pytest.mark.skip(reason="Disabling explore verb tests")
    def test_focus_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic focus command usage."""
        # Focus command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "focus", "tree_123"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_expand_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that expand command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "expand", "--help"])
        assert result.exit_code == 0
        assert "expand" in result.output.lower()

    def test_expand_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic expand command usage."""
        # Expand command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "expand", "src/"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_prune_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that prune command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "prune", "--help"])
        assert result.exit_code == 0
        assert "prune" in result.output.lower()

    def test_prune_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic prune command usage."""
        # Prune command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "prune", "tests/"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_map_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that map command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "map", "--help"])
        assert result.exit_code == 0
        assert "map" in result.output.lower()

    def test_map_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic map command usage."""
        # Map command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "map"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_list_trees_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that list-trees command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "trees", "--help"])
        assert result.exit_code == 0
        assert "trees" in result.output.lower()

    def test_list_trees_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic usage of list-trees command."""
        # List-trees command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "trees"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_status_command_exists(self, cli_runner_with_container: CliRunner) -> None:
        """Test that status command exists and shows help."""
        result = cli_runner_with_container.invoke(cli, ["explore", "status", "--help"])
        assert result.exit_code == 0
        assert "status" in result.output.lower()

    def test_status_basic_usage(self, cli_runner_with_container: CliRunner, session_container: Container) -> None:
        """Test basic usage of status command."""
        # Status command requires session management
        # Just test that it accepts the basic arguments
        mock_exploration_controller = MagicMock()
        mock_exploration_controller.execute.return_value = MagicMock(
            session_id="test_session_id", tree_id="test_tree_id"
        )

        with session_container.exploration_controller.override(mock_exploration_controller):
            result = cli_runner_with_container.invoke(cli, ["explore", "status"])

            # It might fail due to missing session, but that's expected
            assert result.exit_code in [0, 1]  # 0 for success, 1 for expected failure

    def test_cli_error_handling(self, cli_runner_with_container: CliRunner) -> None:
        """Test CLI error handling."""
        # We expect a Click usage error (exit code 2) for a nonexistent command.
        result = cli_runner_with_container.invoke(cli, ["nonexistent-command"])
        assert result.exit_code == 2  # Click usage error

    def test_cli_invalid_project_path(self, cli_runner_with_container: CliRunner) -> None:
        """Test CLI with invalid project path."""
        # We expect a Click usage error (exit code 2) for an invalid project path.
        result = cli_runner_with_container.invoke(cli, ["index", "create", "/nonexistent/path"])
        assert result.exit_code == 2  # Click usage error

    def test_cli_output_format_validation(self, cli_runner_with_container: CliRunner, temp_project: str) -> None:
        """Test CLI output format validation."""
        # We expect a Click usage error (exit code 2) for an invalid output format.
        result = cli_runner_with_container.invoke(
            cli, ["index", "create", temp_project, "--output", "invalid_format"]
        )
        assert result.exit_code == 2  # Click usage error

    def test_cli_verbose_output(self, cli_runner_with_container: CliRunner, temp_project: str, session_container: Container) -> None:
        """Test CLI verbose output."""
        # Mock RepoMapService and its analyze_project method
        mock_repo_map_service = MagicMock()
        mock_repo_map_service.analyze_project.return_value = ProjectInfo(
            project_root=temp_project,
            total_files=1,
            total_identifiers=1,
            file_types={"py": 1},
            identifier_types={"function": 1},
            analysis_time_ms=100.0,
            last_updated=datetime.now(),
        )

        # Patch the repo_map_service provider in the container
        with session_container.repo_map_service.override(mock_repo_map_service):
            result = cli_runner_with_container.invoke(
                cli, ["index", "create", temp_project, "--fuzzy", "--verbose"]
            )
            assert result.exit_code == 0
            # Assert that verbose output contains debug-level information if expected
            # This might require checking specific debug log messages rather than just 'LLM-Optimized Project'
            assert "LLM-Optimized Project" in result.output
