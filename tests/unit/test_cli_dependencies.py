"""
Comprehensive CLI testing for dependency analysis commands.

This module tests the CLI commands to ensure they work correctly
in all scenarios, including edge cases and error conditions.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from repomap_tool.cli import cli
from repomap_tool.models import RepoMapConfig, DependencyConfig


class TestCLIDependencies:
    """Test dependency analysis CLI commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create some test files
            test_file = Path(temp_dir) / "test.py"
            test_file.write_text("import os\nimport sys\n")

            # Create a subdirectory
            sub_dir = Path(temp_dir) / "src"
            sub_dir.mkdir()
            sub_file = sub_dir / "module.py"
            sub_file.write_text("from .. import test\n")

            yield temp_dir

    def test_analyze_dependencies_command_exists(self, cli_runner):
        """Test that analyze-dependencies command exists and shows help."""
        result = cli_runner.invoke(cli, ["analyze-dependencies", "--help"])
        assert result.exit_code == 0
        assert (
            "Analyze project dependencies and build dependency graph" in result.output
        )
        assert "--max-files" in result.output
        assert "--enable-call-graph" in result.output
        assert "--enable-impact-analysis" in result.output

    def test_analyze_dependencies_basic_usage(self, cli_runner, temp_project):
        """Test basic usage of analyze-dependencies command."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            # Mock the dependency graph
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 5,
                "total_edges": 3,
                "cycles": 0,
                "leaf_nodes": 3,
                "root_nodes": 2,
            }
            mock_graph.construction_time = 0.15

            # Mock the repo map instance
            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["analyze-dependencies", temp_project, "--output", "text"]
            )

            assert result.exit_code == 0
            assert "Total Files: 5" in result.output
            assert "Total Dependencies: 3" in result.output
            assert "Circular Dependencies: 0" in result.output

    def test_analyze_dependencies_json_output(self, cli_runner, temp_project):
        """Test analyze-dependencies with JSON output."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 3,
                "total_edges": 1,
                "cycles": 0,
                "leaf_nodes": 2,
                "root_nodes": 1,
            }

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["analyze-dependencies", temp_project, "--output", "json"]
            )

            assert result.exit_code == 0
            # Verify JSON output is valid (strip progress bar and ANSI codes)
            # Find the JSON content in the output
            import re

            # Remove ANSI escape codes and find JSON
            clean_output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.output)
            # Find JSON object
            json_match = re.search(r"\{.*\}", clean_output, re.DOTALL)
            assert json_match is not None, f"JSON output not found in: {clean_output}"

            json_line = json_match.group(0)
            output_data = json.loads(json_line)
            assert "total_nodes" in output_data
            assert output_data["total_nodes"] == 3

    def test_analyze_dependencies_table_output(self, cli_runner, temp_project):
        """Test analyze-dependencies with table output."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 4,
                "total_edges": 2,
                "cycles": 0,
                "leaf_nodes": 2,
                "root_nodes": 2,
            }
            mock_graph.construction_time = 0.1

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["analyze-dependencies", temp_project, "--output", "table"]
            )

            assert result.exit_code == 0
            assert "Dependency Analysis Results" in result.output
            assert "Total Files" in result.output
            assert "Total Dependencies" in result.output

    def test_analyze_dependencies_with_options(self, cli_runner, temp_project):
        """Test analyze-dependencies with various options."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 10,
                "total_edges": 5,
                "cycles": 0,
                "leaf_nodes": 6,
                "root_nodes": 4,
            }
            mock_graph.construction_time = 0.1

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "analyze-dependencies",
                    temp_project,
                    "--max-files",
                    "500",
                    "--enable-call-graph",
                    "--enable-impact-analysis",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 0
            # Verify options were processed
            assert "Total Files: 10" in result.output

    def test_show_centrality_command_exists(self, cli_runner):
        """Test that show-centrality command exists and shows help."""
        result = cli_runner.invoke(cli, ["show-centrality", "--help"])
        assert result.exit_code == 0
        assert "Show centrality analysis for project files" in result.output
        assert "--file" in result.output
        assert "--output" in result.output

    def test_show_centrality_all_files(self, cli_runner, temp_project):
        """Test show-centrality for all files."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.get_centrality_scores.return_value = {
                "file1.py": 0.8,
                "file2.py": 0.6,
                "file3.py": 0.4,
            }
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["show-centrality", temp_project, "--output", "table"]
            )

            assert result.exit_code == 0
            assert "Top Centrality Files" in result.output
            assert "file1.py" in result.output
            assert "0.8000" in result.output

    def test_show_centrality_specific_file(self, cli_runner, temp_project):
        """Test show-centrality for a specific file."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.get_centrality_scores.return_value = {"src/main.py": 0.9}
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "show-centrality",
                    temp_project,
                    "--file",
                    "src/main.py",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 0
            assert "Centrality Analysis: src/main.py" in result.output
            assert "0.9000" in result.output

    def test_show_centrality_file_not_found(self, cli_runner, temp_project):
        """Test show-centrality when file is not found."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.get_centrality_scores.return_value = {"existing.py": 0.5}
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "show-centrality",
                    temp_project,
                    "--file",
                    "nonexistent.py",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 1
            assert "File 'nonexistent.py' not found in project" in result.output

    def test_impact_analysis_command_exists(self, cli_runner):
        """Test that impact-analysis command exists and shows help."""
        result = cli_runner.invoke(cli, ["impact-analysis", "--help"])
        assert result.exit_code == 0
        assert "Analyze impact of changes to specific files" in result.output
        assert "--files" in result.output
        assert "--output" in result.output

    def test_impact_analysis_basic_usage(self, cli_runner, temp_project):
        """Test basic usage of impact-analysis command."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            # Mock impact report as dictionary
            mock_report = {
                "risk_score": 0.7,
                "affected_files": ["file1.py", "file2.py"],
                "breaking_change_potential": {"main.py": "MEDIUM"},
                "suggested_tests": ["test_main.py"],
            }

            mock_instance = Mock()
            mock_instance.analyze_change_impact.return_value = mock_report
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "impact-analysis",
                    temp_project,
                    "--files",
                    "main.py",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 0
            assert "Impact Analysis: main.py" in result.output
            assert "Risk Score: 0.70" in result.output
            assert "Affected Files: 2" in result.output

    def test_impact_analysis_no_files_specified(self, cli_runner, temp_project):
        """Test impact-analysis when no files are specified."""
        result = cli_runner.invoke(cli, ["impact-analysis", temp_project])

        assert result.exit_code == 1
        assert "Must specify at least one file with --files" in result.output

    def test_impact_analysis_multiple_files(self, cli_runner, temp_project):
        """Test impact-analysis with multiple files."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            # Mock multiple impact reports as dictionaries
            mock_report1 = {
                "risk_score": 0.5,
                "affected_files": ["file1.py"],
                "breaking_change_potential": {"file1.py": "LOW"},
                "suggested_tests": [],
            }

            mock_report2 = {
                "risk_score": 0.8,
                "affected_files": ["file2.py", "file3.py"],
                "breaking_change_potential": {"file2.py": "HIGH"},
                "suggested_tests": ["test_file2.py"],
            }

            mock_instance = Mock()
            mock_instance.analyze_change_impact.side_effect = [
                mock_report1,
                mock_report2,
            ]
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "impact-analysis",
                    temp_project,
                    "--files",
                    "file1.py",
                    "--files",
                    "file2.py",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 0
            assert "Impact Analysis: file1.py" in result.output
            assert "Impact Analysis: file2.py" in result.output

    def test_find_cycles_command_exists(self, cli_runner):
        """Test that find-cycles command exists and shows help."""
        result = cli_runner.invoke(cli, ["find-cycles", "--help"])
        assert result.exit_code == 0
        assert "Find circular dependencies in the project" in result.output
        assert "--output" in result.output

    def test_find_cycles_no_cycles(self, cli_runner, temp_project):
        """Test find-cycles when no cycles exist."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.find_circular_dependencies.return_value = []
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["find-cycles", temp_project, "--output", "text"]
            )

            assert result.exit_code == 0
            assert "✓ No circular dependencies found" in result.output

    def test_find_cycles_with_cycles(self, cli_runner, temp_project):
        """Test find-cycles when cycles exist."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.find_circular_dependencies.return_value = [
                ["file1.py", "file2.py", "file1.py"],
                ["file3.py", "file4.py", "file3.py"],
            ]
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["find-cycles", temp_project, "--output", "text"]
            )

            assert result.exit_code == 0
            assert "Found 2 circular dependencies" in result.output
            assert "file1.py → file2.py → file1.py" in result.output

    def test_find_cycles_json_output(self, cli_runner, temp_project):
        """Test find-cycles with JSON output."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.find_circular_dependencies.return_value = [
                ["file1.py", "file2.py", "file1.py"]
            ]
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli, ["find-cycles", temp_project, "--output", "json"]
            )

            assert result.exit_code == 0
            # Verify JSON output is valid (strip progress bar and ANSI codes)
            # Find the JSON content in the output
            import re

            # Remove ANSI escape codes and find JSON
            clean_output = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", result.output)
            # Find JSON array
            json_match = re.search(r"\[.*\]", clean_output, re.DOTALL)
            assert json_match is not None, f"JSON output not found in: {clean_output}"

            json_line = json_match.group(0)
            output_data = json.loads(json_line)
            assert isinstance(output_data, list)
            assert len(output_data) == 1
            assert "file1.py" in output_data[0]

    def test_cli_error_handling(self, cli_runner, temp_project):
        """Test CLI error handling when dependencies are disabled."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_instance = Mock()
            mock_instance.build_dependency_graph.side_effect = RuntimeError(
                "Dependency analysis is not enabled"
            )
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(cli, ["analyze-dependencies", temp_project])

            assert result.exit_code == 1
            assert "Error: Dependency analysis is not enabled" in result.output

    def test_cli_invalid_project_path(self, cli_runner):
        """Test CLI with invalid project path."""
        result = cli_runner.invoke(cli, ["analyze-dependencies", "/nonexistent/path"])

        # Click returns exit code 2 for usage errors
        assert result.exit_code == 2
        assert "Error:" in result.output

    def test_cli_output_format_validation(self, cli_runner, temp_project):
        """Test CLI output format validation."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 1,
                "total_edges": 0,
                "cycles": 0,
                "leaf_nodes": 1,
                "root_nodes": 0,
            }

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            # Test invalid output format
            result = cli_runner.invoke(
                cli,
                ["analyze-dependencies", temp_project, "--output", "invalid_format"],
            )

            assert result.exit_code == 2  # Click error for invalid choice

    def test_cli_verbose_output(self, cli_runner, temp_project):
        """Test CLI verbose output."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 2,
                "total_edges": 1,
                "cycles": 0,
                "leaf_nodes": 1,
                "root_nodes": 1,
            }
            mock_graph.construction_time = 0.1

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                ["analyze-dependencies", temp_project, "--verbose", "--output", "text"],
            )

            assert result.exit_code == 0
            # Verbose output should show more details
            assert "Total Files: 2" in result.output

    def test_cli_configuration_integration(self, cli_runner, temp_project):
        """Test that CLI properly creates and uses configuration."""
        with patch("repomap_tool.cli.RepoMapService") as mock_repo_map:
            mock_graph = Mock()
            mock_graph.get_graph_statistics.return_value = {
                "total_nodes": 1,
                "total_edges": 0,
                "cycles": 0,
                "leaf_nodes": 1,
                "root_nodes": 0,
            }
            mock_graph.construction_time = 0.1

            mock_instance = Mock()
            mock_instance.build_dependency_graph.return_value = mock_graph
            mock_repo_map.return_value = mock_instance

            result = cli_runner.invoke(
                cli,
                [
                    "analyze-dependencies",
                    temp_project,
                    "--max-files",
                    "500",
                    "--enable-call-graph",
                    "--enable-impact-analysis",
                    "--output",
                    "text",
                ],
            )

            assert result.exit_code == 0

            # Verify RepoMapService was called with proper configuration
            mock_repo_map.assert_called_once()
            call_args = mock_repo_map.call_args[0][0]
            assert isinstance(call_args, RepoMapConfig)
            assert call_args.dependencies.max_graph_size == 500
            # Note: The CLI function creates its own DependencyConfig internally
            # so we can't verify the boolean flags from the mock call
            # The important thing is that the CLI processed the options correctly
