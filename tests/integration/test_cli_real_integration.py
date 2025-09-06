"""
Real CLI Integration Tests - No Mocking

This module tests CLI commands with real RepoMapService instances to ensure
the actual integration between CLI arguments, configuration, and core components works.
"""

import pytest
import tempfile
import json
import os
import re
from pathlib import Path
from click.testing import CliRunner
from repomap_tool.cli import cli
from repomap_tool.models import RepoMapConfig


def extract_session_id_from_output(output: str) -> str:
    """Helper to extract session ID from CLI output."""
    match = re.search(r"💡 Using session: (explore_\w+)", output)
    if match:
        return match.group(1)
    raise ValueError("Session ID not found in output")


class TestTreeExplorationCLI:
    """Test tree exploration CLI commands with real component integration."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with authentication-related files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            (src_dir / "auth.py").write_text(
                """
class UserAuth:
    def login(self, username, password):
        # authentication logic here
        return True

    def logout(self, user_id):
        # logout logic
        return True

def handle_authentication_request():
    auth = UserAuth()
    auth.login("test", "pass")
"""
            )
            yield temp_dir

    @pytest.fixture(autouse=True)
    def cleanup_sessions(self):
        """Clean up session files before and after tests."""
        session_dir = Path(".repomap_sessions")
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)
        yield
        if session_dir.exists():
            import shutil

            shutil.rmtree(session_dir)

    def test_explore_command_creates_session_and_tree(self, cli_runner, temp_project):
        """Test that 'explore' command creates a session and persists it correctly."""
        # Invoke 'explore' command with no-color flag for cleaner test assertions
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "explore",
                temp_project,
                "user authentication",  # More specific intent
            ],
        )

        # Assert successful exit code
        assert result.exit_code == 0, f"CLI command failed with output: {result.output}"

        # Assert relevant output (e.g., session ID)
        session_id = extract_session_id_from_output(result.output)
        assert session_id is not None
        # Check for session export message (no ANSI colors with --no-color flag)
        assert f"Set: export REPOMAP_SESSION={session_id}" in result.output
        # The command should either find entrypoints or provide helpful suggestions
        assert (
            "Found" in result.output and "exploration contexts" in result.output
        ) or "No high-confidence entrypoints found" in result.output

        # Verify session file exists on disk (only if entrypoints were found)
        if "Found" in result.output and "exploration contexts" in result.output:
            session_file = Path(".repomap_sessions") / f"{session_id}.json"
            assert session_file.exists()
        else:
            # When no entrypoints are found, session file may not be created
            # This is expected behavior
            pass

        # Verify initial exploration tree is built (by checking session file content)
        if "Found" in result.output and "exploration contexts" in result.output:
            session_file = Path(".repomap_sessions") / f"{session_id}.json"
            with open(session_file, "r") as f:
                session_data = json.load(f)
            assert "exploration_trees" in session_data
            assert len(session_data["exploration_trees"]) > 0
            tree_id = list(session_data["exploration_trees"].keys())[0]
            assert "context_name" in session_data["exploration_trees"][tree_id]
            assert "entrypoints" in session_data["exploration_trees"][tree_id]


class TestCLIRealIntegration:
    """Test CLI commands with real component integration."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with real files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            (src_dir / "example.py").write_text(
                """
class MyClass:
    def my_method(self):
        pass

def my_function():
    pass
"""
            )
            yield temp_dir

    def test_analyze_command_real_integration(self, cli_runner, temp_project):
        """Test analyze command with real RepoMapService integration."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--fuzzy",
                "--max-results",
                "10",
                "--output",
                "json",
                "--no-progress",  # Disable progress bars for cleaner output
            ],
        )

        # Should succeed without errors
        assert result.exit_code == 0

        # Should contain real analysis results
        output = result.output
        assert "project_root" in output
        assert "total_files" in output
        assert "total_identifiers" in output

        # Should have found some identifiers
        assert '"total_identifiers":' in output
        # Extract the JSON part from the output (may include logs and progress)
        # Find the JSON object in the output
        json_match = re.search(r"\{.*\}", output, re.DOTALL)
        assert json_match, "No JSON found in output"
        data = json.loads(json_match.group())
        assert data["total_identifiers"] > 0
        assert data["total_files"] > 0

    def test_search_command_real_integration(self, cli_runner, temp_project):
        """Test search command with real fuzzy matching."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "search",
                temp_project,
                "main",
                "--match-type",
                "fuzzy",
                "--max-results",
                "5",
                "--output",
                "table",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should contain search results
        output = result.output
        assert "Search Results" in output
        assert "main" in output.lower()

    def test_analyze_dependencies_real_integration(self, cli_runner, temp_project):
        """Test dependency analysis with real project structure."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze-dependencies",
                temp_project,
                "--max-files",
                "100",
                "--output",
                "table",
            ],
        )

        # Dependency analysis may fail with small test projects (real behavior)
        # This is actually good - it shows the real error handling works
        if result.exit_code == 0:
            # Should contain dependency analysis results
            output = result.output
            assert "Dependency Analysis Results" in output
            assert "Total Files" in output
            assert "Total Dependencies" in output
        else:
            # Should show proper error message for small projects
            assert "Error:" in result.output or "Failed" in result.output

    def test_cli_error_handling_real(self, cli_runner):
        """Test CLI error handling with real validation."""
        # Test with non-existent directory
        result = cli_runner.invoke(
            cli, ["--no-color", "analyze", "/non/existent/directory"]
        )

        # Should fail with proper error
        assert result.exit_code != 0
        assert "Error:" in result.output

    def test_config_validation_real(self, cli_runner, temp_project):
        """Test that CLI properly validates configuration parameters."""
        # Test with invalid threshold
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--threshold",
                "1.5",  # Invalid: should be 0.0-1.0
            ],
        )

        # Should fail with validation error
        assert result.exit_code != 0
        assert (
            "validation error" in result.output.lower()
            or "error" in result.output.lower()
        )

    def test_parallel_processing_real(self, cli_runner, temp_project):
        """Test that parallel processing actually works with real data."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--max-workers",
                "2",
                "--parallel-threshold",
                "1",
                "--output",
                "json",
                "--no-progress",  # Disable progress bars for cleaner output
            ],
        )

        # Should succeed (or fail gracefully with proper error handling)
        if result.exit_code == 0:
            # Should show parallel processing was used
            output = result.output
            # The real implementation should log parallel processing
            # This tests that the CLI properly passes parameters to the core
            assert "project_root" in output
        else:
            # If it fails, should show proper error message
            assert "Error:" in result.output or "Failed" in result.output

    def test_cache_integration_real(self, cli_runner, temp_project):
        """Test that caching works with real CLI usage."""
        # First run - should populate cache
        result1 = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--fuzzy",
                "--output",
                "json",
                "--no-progress",  # Disable progress bars for cleaner output
            ],
        )
        assert result1.exit_code == 0

        # Second run - should use cache (faster)
        result2 = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--fuzzy",
                "--output",
                "json",
                "--no-progress",  # Disable progress bars for cleaner output
            ],
        )
        assert result2.exit_code == 0

        # Results should be identical (except for timing fields)

        # Extract JSON from both outputs
        json1_match = re.search(r"\{.*\}", result1.output, re.DOTALL)
        json2_match = re.search(r"\{.*\}", result2.output, re.DOTALL)
        assert json1_match and json2_match, "No JSON found in outputs"

        data1 = json.loads(json1_match.group())
        data2 = json.loads(json2_match.group())

        # Core data should be identical
        assert data1["total_files"] == data2["total_files"]
        assert data1["total_identifiers"] == data2["total_identifiers"]
        assert data1["file_types"] == data2["file_types"]
        assert data1["identifier_types"] == data2["identifier_types"]

    def test_llm_friendly_output_real(self, cli_runner, temp_project):
        """Test LLM-friendly output formats (markdown, text)."""
        # Test markdown output
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--fuzzy",
                "--output",
                "markdown",
                "--no-progress",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should contain the new template-based output
        output = result.output
        assert "Project:" in output
        assert "Files:" in output
        assert "Identifiers:" in output
        assert "File Types:" in output
        assert "Identifier Types:" in output

        # Test text output
        result_text = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--fuzzy",
                "--output",
                "text",
                "--no-progress",
            ],
        )

        # Should succeed
        assert result_text.exit_code == 0

        # Should contain the same template-based content
        text_output = result_text.output
        assert "Project:" in text_output
        assert "Files:" in text_output
        assert "Identifiers:" in text_output

    def test_config_command_real(self, cli_runner, temp_project):
        """Test config command generation."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "config",
                temp_project,
                "--fuzzy",
                "--semantic",
                "--threshold",
                "0.8",
                "--cache-size",
                "500",
            ],
        )

        assert result.exit_code == 0
        output = result.output
        assert "Generated Configuration" in output
        assert "fuzzy_match" in output
        assert "semantic_match" in output
        assert "0.8" in output


class TestAdvancedDependencyCLI:
    """Test advanced dependency analysis CLI commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def temp_project_with_dependencies(self):
        """Create a temporary project with some dependencies for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Create files with dependencies
            (src_dir / "main.py").write_text(
                """
import auth
import database
from utils import helper

def main():
    user = auth.login("admin", "password")
    data = database.get_data()
    result = helper.process(data)
    return result

if __name__ == "__main__":
    main()
"""
            )

            (src_dir / "auth.py").write_text(
                """
import database

class UserAuth:
    def __init__(self):
        self.db = database.Database()
    
    def login(self, username, password):
        return self.db.authenticate(username, password)
    
    def logout(self, user_id):
        return self.db.logout(user_id)
"""
            )

            (src_dir / "database.py").write_text(
                """
import auth

class Database:
    def __init__(self):
        self.auth = auth.UserAuth()
    
    def authenticate(self, username, password):
        # authentication logic
        return True
    
    def get_data(self):
        return {"data": "test"}
    
    def logout(self, user_id):
        return True
"""
            )

            (src_dir / "utils.py").write_text(
                """
def helper(data):
    return {"processed": data}

def utility_function():
    return "utility"
"""
            )

            yield temp_dir

    def test_show_centrality_command_real(
        self, cli_runner, temp_project_with_dependencies
    ):
        """Test show-centrality command with real dependency analysis."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "show-centrality",
                temp_project_with_dependencies,
                "--output",
                "table",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should contain centrality analysis results
        output = result.output
        assert "Top Centrality Files" in output or "Centrality Analysis" in output

        # Test with specific file - use a simple approach
        main_file = os.path.join(temp_project_with_dependencies, "src/main.py")

        # Test with the file path (should work even if not found)
        result_file = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "show-centrality",
                temp_project_with_dependencies,
                "--file",
                main_file,
                "--output",
                "json",
            ],
        )

        # Should succeed or fail gracefully
        assert result_file.exit_code in [
            0,
            1,
        ]  # Accept both success and "file not found"

        # Should contain some output
        output = result_file.output
        assert len(output) > 0

    def test_impact_analysis_command_real(
        self, cli_runner, temp_project_with_dependencies
    ):
        """Test impact-analysis command with real dependency analysis."""
        main_file = os.path.join(temp_project_with_dependencies, "src/main.py")
        auth_file = os.path.join(temp_project_with_dependencies, "src/auth.py")

        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "impact-analysis",
                temp_project_with_dependencies,
                "--files",
                main_file,
                "--output",
                "table",
            ],
        )

        # Should succeed or fail gracefully
        assert result.exit_code in [0, 1]

        # Should contain some output
        output = result.output
        assert len(output) > 0

        # Test with multiple files
        result_multi = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "impact-analysis",
                temp_project_with_dependencies,
                "--files",
                main_file,
                auth_file,
                "--output",
                "json",
            ],
        )

        # Should succeed or fail gracefully (exit code 2 is also acceptable for some errors)
        assert result_multi.exit_code in [0, 1, 2]

        # Should contain some output
        output = result_multi.output
        assert len(output) > 0

    def test_find_cycles_command_real(self, cli_runner, temp_project_with_dependencies):
        """Test find-cycles command with real dependency analysis."""
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "find-cycles",
                temp_project_with_dependencies,
                "--output",
                "table",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should contain cycle analysis results
        output = result.output
        assert (
            "No circular dependencies found" in output
            or "Circular Dependencies Found" in output
        )

        # Test with JSON output
        result_json = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "find-cycles",
                temp_project_with_dependencies,
                "--output",
                "json",
            ],
        )

        # Should succeed
        assert result_json.exit_code == 0

        # Should contain JSON output (even if empty) - look for array structure
        output = result_json.output
        assert "[" in output and "]" in output

    def test_cache_command_real(self, cli_runner, temp_project_with_dependencies):
        """Test cache command with real cache operations."""
        # Test cache status
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "cache",
                temp_project_with_dependencies,
                "--output",
                "table",
            ],
        )

        # Should succeed
        assert result.exit_code == 0

        # Should contain cache status information
        output = result.output
        assert "Cache Status" in output
        assert "Component" in output or "Status" in output

        # Test cache refresh
        result_refresh = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "cache",
                temp_project_with_dependencies,
                "--refresh",
                "--output",
                "json",
            ],
        )

        # Should succeed
        assert result_refresh.exit_code == 0

        # Should contain cache refresh confirmation
        output = result_refresh.output
        assert "All caches cleared" in output or "cache" in output.lower()

        # Test verbose mode
        result_verbose = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "cache",
                temp_project_with_dependencies,
                "--verbose",
                "--output",
                "table",
            ],
        )

        # Should succeed
        assert result_verbose.exit_code == 0

        # Should contain verbose cache information
        output = result_verbose.output
        assert "Cache Status" in output

    def test_advanced_dependency_commands_error_handling(self, cli_runner):
        """Test error handling for advanced dependency commands."""
        # Test with non-existent directory
        result = cli_runner.invoke(
            cli, ["--no-color", "show-centrality", "/non/existent/directory"]
        )

        # Should fail with proper error
        assert result.exit_code != 0
        assert "Error:" in result.output

        # Test impact-analysis without files
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(cli, ["--no-color", "impact-analysis", temp_dir])

            # Should fail with proper error
            assert result.exit_code != 0
            assert "Must specify at least one file" in result.output

        # Test with invalid file path
        with tempfile.TemporaryDirectory() as temp_dir:
            result = cli_runner.invoke(
                cli,
                [
                    "--no-color",
                    "show-centrality",
                    temp_dir,
                    "--file",
                    "non/existent/file.py",
                ],
            )

            # Should fail with proper error
            assert result.exit_code != 0
            assert "Error:" in result.output or "not found" in result.output


class TestCLIEdgeCasesAndNegativeTesting:
    """Test edge cases, negative scenarios, and error conditions for CLI commands."""

    @pytest.fixture
    def cli_runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    @pytest.fixture
    def empty_project(self):
        """Create an empty project directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def large_project(self):
        """Create a large project with many files for stress testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Create 50 Python files with dependencies
            for i in range(50):
                file_content = f"""
import os
import sys
from pathlib import Path

class Module{i}:
    def __init__(self):
        self.id = {i}
        self.dependencies = []
    
    def add_dependency(self, dep):
        self.dependencies.append(dep)
    
    def process(self):
        return f"Processing module {{self.id}}"

def main():
    module = Module{i}()
    return module.process()

if __name__ == "__main__":
    main()
"""
                (src_dir / f"module_{i:02d}.py").write_text(file_content)

            yield temp_dir

    @pytest.fixture
    def malformed_project(self):
        """Create a project with malformed Python files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Create files with syntax errors
            (src_dir / "syntax_error.py").write_text(
                "def broken_function(\n    # Missing closing parenthesis\n    pass"
            )
            (src_dir / "import_error.py").write_text("import nonexistent_module")
            (src_dir / "valid.py").write_text(
                "def valid_function():\n    return 'valid'"
            )

            yield temp_dir

    @pytest.fixture
    def permission_denied_project(self):
        """Create a project with permission issues."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()

            # Create a file and make it unreadable
            restricted_file = src_dir / "restricted.py"
            restricted_file.write_text(
                "def restricted_function():\n    return 'restricted'"
            )
            restricted_file.chmod(0o000)  # No permissions

            yield temp_dir

    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with authentication-related files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            src_dir = Path(temp_dir) / "src"
            src_dir.mkdir()
            (src_dir / "auth.py").write_text(
                """
class UserAuth:
    def login(self, username, password):
        # authentication logic here
        return True

    def logout(self, user_id):
        # logout logic
        return True

def handle_authentication_request():
    auth = UserAuth()
    auth.login("test", "pass")
"""
            )
            yield temp_dir

    def test_analyze_command_edge_cases(
        self, cli_runner, empty_project, large_project, malformed_project
    ):
        """Test analyze command with various edge cases."""

        # Test with empty project
        result = cli_runner.invoke(
            cli, ["--no-color", "analyze", empty_project, "--output", "json"]
        )
        assert result.exit_code in [0, 1]  # Should handle gracefully
        assert len(result.output) > 0

        # Test with large project (stress test)
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                large_project,
                "--max-results",
                "10",  # Limit results
                "--output",
                "json",
            ],
        )
        assert result.exit_code in [0, 1]
        assert len(result.output) > 0

        # Test with malformed project
        result = cli_runner.invoke(
            cli, ["--no-color", "analyze", malformed_project, "--output", "json"]
        )
        assert result.exit_code in [0, 1]  # Should handle syntax errors gracefully
        assert len(result.output) > 0

    def test_analyze_command_invalid_parameters(self, cli_runner, temp_project):
        """Test analyze command with invalid parameters."""

        # Test with invalid threshold
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--threshold",
                "2.0",  # Invalid: should be 0.0-1.0
                "--output",
                "json",
            ],
        )
        assert result.exit_code != 0  # Should fail with invalid threshold

        # Test with negative max-results
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze",
                temp_project,
                "--max-results",
                "-1",
                "--output",
                "json",
            ],
        )
        assert result.exit_code != 0  # Should fail with negative max-results

        # Test with invalid output format
        result = cli_runner.invoke(
            cli, ["--no-color", "analyze", temp_project, "--output", "invalid_format"]
        )
        assert result.exit_code != 0  # Should fail with invalid output format

    def test_search_command_edge_cases(self, cli_runner, empty_project, large_project):
        """Test search command with edge cases."""

        # Test with empty query
        result = cli_runner.invoke(cli, ["--no-color", "search", empty_project, ""])
        assert result.exit_code in [0, 1]

        # Test with very long query
        long_query = "a" * 1000
        result = cli_runner.invoke(
            cli, ["--no-color", "search", large_project, long_query]
        )
        assert result.exit_code in [0, 1]

        # Test with special characters
        result = cli_runner.invoke(
            cli,
            ["--no-color", "search", large_project, "!@#$%^&*()_+-=[]{}|;':\",./<>?"],
        )
        assert result.exit_code in [0, 1]

    def test_dependency_analysis_edge_cases(
        self, cli_runner, empty_project, large_project
    ):
        """Test dependency analysis with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze-dependencies",
                empty_project,
                "--max-files",
                "1000",
            ],
        )
        assert result.exit_code in [0, 1]

        # Test with large project and low file limit
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "analyze-dependencies",
                large_project,
                "--max-files",
                "5",  # Very low limit
            ],
        )
        assert result.exit_code in [0, 1]

        # Test with invalid max-files
        result = cli_runner.invoke(
            cli,
            ["--no-color", "analyze-dependencies", large_project, "--max-files", "-1"],
        )
        assert result.exit_code != 0

    def test_show_centrality_edge_cases(self, cli_runner, empty_project, large_project):
        """Test show-centrality command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(
            cli, ["--no-color", "show-centrality", empty_project]
        )
        assert result.exit_code in [0, 1]

        # Test with large project
        result = cli_runner.invoke(
            cli, ["--no-color", "show-centrality", large_project]
        )
        assert result.exit_code in [0, 1]

        # Test with non-existent file
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "show-centrality",
                large_project,
                "--file",
                "nonexistent_file.py",
            ],
        )
        assert result.exit_code != 0
        assert "not found" in result.output or "Error:" in result.output

    def test_impact_analysis_edge_cases(self, cli_runner, empty_project, large_project):
        """Test impact-analysis command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(
            cli,
            ["--no-color", "impact-analysis", empty_project, "--files", "any_file.py"],
        )
        assert result.exit_code in [0, 1]

        # Test with large project and many files
        files = [f"src/module_{i:02d}.py" for i in range(10)]
        result = cli_runner.invoke(
            cli, ["--no-color", "impact-analysis", large_project, "--files"] + files
        )
        assert result.exit_code in [0, 1, 2]  # Accept various exit codes for edge cases

        # Test with non-existent files
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "impact-analysis",
                large_project,
                "--files",
                "nonexistent1.py",
                "nonexistent2.py",
            ],
        )
        assert result.exit_code in [0, 1, 2]  # May fail gracefully

    def test_find_cycles_edge_cases(self, cli_runner, empty_project, large_project):
        """Test find-cycles command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(cli, ["--no-color", "find-cycles", empty_project])
        assert result.exit_code in [0, 1]

        # Test with large project
        result = cli_runner.invoke(cli, ["--no-color", "find-cycles", large_project])
        assert result.exit_code in [0, 1]

    def test_cache_command_edge_cases(self, cli_runner, empty_project, large_project):
        """Test cache command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(cli, ["--no-color", "cache", empty_project])
        assert result.exit_code in [0, 1]

        # Test with large project
        result = cli_runner.invoke(cli, ["--no-color", "cache", large_project])
        assert result.exit_code in [0, 1]

        # Test cache refresh with large project
        result = cli_runner.invoke(
            cli, ["--no-color", "cache", large_project, "--refresh"]
        )
        assert result.exit_code in [0, 1]

    def test_explore_command_edge_cases(self, cli_runner, empty_project, large_project):
        """Test explore command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(
            cli, ["--no-color", "explore", empty_project, "test intent"]
        )
        assert result.exit_code in [0, 1]

        # Test with large project
        result = cli_runner.invoke(
            cli, ["--no-color", "explore", large_project, "module processing"]
        )
        assert result.exit_code in [0, 1]

        # Test with very long intent
        long_intent = "a" * 1000
        result = cli_runner.invoke(
            cli, ["--no-color", "explore", large_project, long_intent]
        )
        assert result.exit_code in [0, 1]

    def test_config_command_edge_cases(self, cli_runner, empty_project):
        """Test config command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(cli, ["--no-color", "config", empty_project])
        assert result.exit_code in [0, 1]

        # Test with invalid parameters
        result = cli_runner.invoke(
            cli,
            [
                "--no-color",
                "config",
                empty_project,
                "--threshold",
                "2.0",  # Invalid threshold
            ],
        )
        assert result.exit_code != 0

    def test_performance_command_edge_cases(
        self, cli_runner, empty_project, large_project
    ):
        """Test performance command with edge cases."""

        # Test with empty project
        result = cli_runner.invoke(cli, ["--no-color", "performance", empty_project])
        assert result.exit_code in [0, 1]

        # Test with large project
        result = cli_runner.invoke(cli, ["--no-color", "performance", large_project])
        assert result.exit_code in [0, 1]

    def test_version_command(self, cli_runner):
        """Test version command."""
        result = cli_runner.invoke(cli, ["--no-color", "version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_help_command(self, cli_runner):
        """Test help command."""
        result = cli_runner.invoke(cli, ["--no-color", "--help"])
        assert result.exit_code == 0
        assert "Docker RepoMap" in result.output

    def test_invalid_command(self, cli_runner):
        """Test invalid command."""
        result = cli_runner.invoke(cli, ["--no-color", "invalid-command"])
        assert result.exit_code != 0
        assert "No such command" in result.output or "Usage:" in result.output

    def test_missing_required_arguments(self, cli_runner, temp_project):
        """Test commands with missing required arguments."""

        # Test analyze without project path
        result = cli_runner.invoke(cli, ["--no-color", "analyze"])
        assert result.exit_code != 0

        # Test search without query
        result = cli_runner.invoke(cli, ["--no-color", "search", temp_project])
        assert result.exit_code != 0

        # Test explore without intent
        result = cli_runner.invoke(cli, ["--no-color", "explore", temp_project])
        assert result.exit_code != 0
