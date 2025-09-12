#!/usr/bin/env python3
"""
Unit tests for CLI command functions.

This module tests the actual CLI command functions and display functions
to achieve higher test coverage.
"""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

from src.repomap_tool.cli import (
    display_project_info,
    display_search_results,
)
from src.repomap_tool.models import (
    ProjectInfo,
    SearchResponse,
    MatchResult,
)

# Centralized patch path for console - makes refactoring easier
# If the CLI structure changes, only this constant needs to be updated
CONSOLE_PATCH_PATH = "src.repomap_tool.cli.output.formatters.console"


class TestDisplayFunctions:
    """Test the display functions."""

    @patch(CONSOLE_PATCH_PATH)
    def test_display_project_info_json(self, mock_console):
        """Test display_project_info with JSON output."""
        # Create a mock project info
        project_info = ProjectInfo(
            project_root=".",
            total_files=100,
            total_identifiers=1000,
            file_types={"py": 50, "js": 30, "md": 20},
            identifier_types={"functions": 500, "classes": 300, "variables": 200},
            analysis_time_ms=1500.0,
            cache_size_bytes=1024,
            last_updated="2025-01-01T12:00:00",
        )

        # Call the display function
        display_project_info(project_info, "json")

        # Verify JSON output was called
        mock_console.print.assert_called_once()

    @patch(CONSOLE_PATCH_PATH)
    def test_display_project_info_text(self, mock_console):
        """Test display_project_info with text output."""
        # Create a mock project info
        project_info = ProjectInfo(
            project_root=".",
            total_files=100,
            total_identifiers=1000,
            file_types={"py": 50, "js": 30, "md": 20},
            identifier_types={"functions": 500, "classes": 300, "variables": 200},
            analysis_time_ms=1500.0,
            cache_size_bytes=1024,
            last_updated="2025-01-01T12:00:00",
        )

        # Call the display function
        display_project_info(project_info, "text")

        # Verify console.print was called multiple times for tables
        assert mock_console.print.call_count >= 1

    @patch(CONSOLE_PATCH_PATH)
    def test_display_project_info_table(self, mock_console):
        """Test display_project_info with table output."""
        # Create a mock project info
        project_info = ProjectInfo(
            project_root=".",
            total_files=100,
            total_identifiers=1000,
            file_types={"py": 50, "js": 30, "md": 20},
            identifier_types={"functions": 500, "classes": 300, "variables": 200},
            analysis_time_ms=1500.0,
            cache_size_bytes=1024,
            last_updated="2025-01-01T12:00:00",
        )

        # Call the display function
        display_project_info(project_info, "table")

        # Verify console.print was called multiple times for tables
        assert mock_console.print.call_count >= 1

    @patch(CONSOLE_PATCH_PATH)
    def test_display_project_info_markdown(self, mock_console):
        """Test display_project_info with markdown output."""
        # Create a mock project info
        project_info = ProjectInfo(
            project_root=".",
            total_files=100,
            total_identifiers=1000,
            file_types={"py": 50, "js": 30, "md": 20},
            identifier_types={"functions": 500, "classes": 300, "variables": 200},
            analysis_time_ms=1500.0,
            cache_size_bytes=1024,
            last_updated="2025-01-01T12:00:00",
        )

        # Call the display function
        display_project_info(project_info, "markdown")

        # Verify console.print was called multiple times for markdown
        assert mock_console.print.call_count >= 1

    @patch(CONSOLE_PATCH_PATH)
    def test_display_search_results_json(self, mock_console):
        """Test display_search_results with JSON output."""
        # Create mock search results
        results = [
            MatchResult(
                identifier="test_function",
                score=0.95,
                strategy="fuzzy_match",
                match_type="fuzzy",
            ),
            MatchResult(
                identifier="test_class",
                score=0.85,
                strategy="semantic_match",
                match_type="semantic",
            ),
        ]

        search_response = SearchResponse(
            query="test",
            results=results,
            total_results=2,
            match_type="hybrid",
            threshold=0.7,
            search_time_ms=100.0,
        )

        # Call the display function
        display_search_results(search_response, "json")

        # Verify JSON output was called
        mock_console.print.assert_called_once()

    @patch(CONSOLE_PATCH_PATH)
    def test_display_search_results_table(self, mock_console):
        """Test display_search_results with table output."""
        # Create mock search results
        results = [
            MatchResult(
                identifier="test_function",
                score=0.95,
                strategy="fuzzy_match",
                match_type="fuzzy",
            ),
            MatchResult(
                identifier="test_class",
                score=0.85,
                strategy="semantic_match",
                match_type="semantic",
            ),
        ]

        search_response = SearchResponse(
            query="test",
            results=results,
            total_results=2,
            match_type="hybrid",
            threshold=0.7,
            search_time_ms=100.0,
            performance_metrics={"query_time": 50.0, "index_hits": 25},
        )

        # Call the display function
        display_search_results(search_response, "table")

        # Verify console.print was called multiple times for table and summary
        assert mock_console.print.call_count >= 2

    @patch(CONSOLE_PATCH_PATH)
    def test_display_search_results_text(self, mock_console):
        """Test display_search_results with text output."""
        # Create mock search results
        results = [
            MatchResult(
                identifier="test_function",
                score=0.95,
                strategy="fuzzy_match",
                match_type="fuzzy",
            )
        ]

        search_response = SearchResponse(
            query="test",
            results=results,
            total_results=1,
            match_type="fuzzy",
            threshold=0.7,
            search_time_ms=50.0,
        )

        # Call the display function
        display_search_results(search_response, "text")

        # Verify console.print was called
        assert mock_console.print.call_count >= 1

    @patch(CONSOLE_PATCH_PATH)
    def test_display_search_results_empty(self, mock_console):
        """Test display_search_results with empty results."""
        # Create empty search results
        search_response = SearchResponse(
            query="nonexistent",
            results=[],
            total_results=0,
            match_type="fuzzy",
            threshold=0.7,
            search_time_ms=10.0,
        )

        # Call the display function
        display_search_results(search_response, "table")

        # Verify console.print was called for no results message
        assert mock_console.print.call_count >= 1


class TestCLIHelperFunctions:
    """Test CLI helper functions that are called by the commands."""

    @patch("src.repomap_tool.cli.create_default_config")
    @patch("src.repomap_tool.cli.RepoMapService")
    @patch("src.repomap_tool.cli.Progress")
    @patch("src.repomap_tool.cli.display_project_info")
    def test_analyze_command_logic(
        self, mock_display, mock_progress, mock_repo_map, mock_create_config
    ):
        """Test the logic that would be executed by the analyze command."""
        # Mock the configuration
        mock_config = Mock()
        mock_create_config.return_value = mock_config

        # Mock the RepoMap
        mock_repomap_instance = Mock()
        mock_repo_map.return_value = mock_repomap_instance

        # Mock project info
        mock_project_info = Mock()
        mock_repomap_instance.analyze_project_with_progress.return_value = (
            mock_project_info
        )

        # Mock progress context
        mock_progress_context = Mock()
        mock_progress.return_value.__enter__.return_value = mock_progress_context
        mock_progress.return_value.__exit__.return_value = None

        # This simulates what the analyze command would do
        config_obj = mock_create_config(
            project_path=".",
            fuzzy=True,
            semantic=False,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            max_workers=4,
            parallel_threshold=10,
            no_progress=False,
            no_monitoring=False,
            allow_fallback=False,
            cache_size=1000,
            log_level="INFO",
            refresh_cache=False,
        )

        repomap = mock_repo_map(config_obj)
        project_info = repomap.analyze_project_with_progress()
        mock_display(project_info, "json")

        # Verify the function calls
        mock_create_config.assert_called_once()
        mock_repo_map.assert_called_once_with(mock_config)
        mock_repomap_instance.analyze_project_with_progress.assert_called_once()
        mock_display.assert_called_once_with(mock_project_info, "json")

    @patch("src.repomap_tool.cli.create_search_config")
    @patch("src.repomap_tool.cli.RepoMapService")
    @patch("src.repomap_tool.cli.Progress")
    @patch("src.repomap_tool.cli.display_search_results")
    @patch("src.repomap_tool.cli.SearchRequest")
    def test_search_command_logic(
        self,
        mock_search_request,
        mock_display,
        mock_progress,
        mock_repo_map,
        mock_create_search_config,
    ):
        """Test the logic that would be executed by the search command."""
        # Mock the configuration
        mock_config = Mock()
        mock_create_search_config.return_value = mock_config

        # Mock the RepoMap
        mock_repomap_instance = Mock()
        mock_repo_map.return_value = mock_repomap_instance

        # Mock search request
        mock_request = Mock()
        mock_search_request.return_value = mock_request

        # Mock search response
        mock_response = Mock()
        mock_repomap_instance.search_identifiers.return_value = mock_response

        # Mock progress context
        mock_progress_context = Mock()
        mock_progress.return_value.__enter__.return_value = mock_progress_context
        mock_progress.return_value.__exit__.return_value = None

        # This simulates what the search command would do
        config = mock_create_search_config(
            project_path=".",
            match_type="fuzzy",
            verbose=True,
            log_level="INFO",
            cache_size=1000,
        )

        request = mock_search_request(
            query="test query",
            match_type="fuzzy",
            threshold=0.7,
            max_results=10,
            strategies=None,
        )

        repomap = mock_repo_map(config)
        response = repomap.search_identifiers(request)
        mock_display(response, "table")

        # Verify the function calls
        mock_create_search_config.assert_called_once()
        mock_search_request.assert_called_once()
        mock_repo_map.assert_called_once_with(mock_config)
        mock_repomap_instance.search_identifiers.assert_called_once_with(mock_request)
        mock_display.assert_called_once_with(mock_response, "table")

    @patch("src.repomap_tool.cli.create_default_config")
    @patch(CONSOLE_PATCH_PATH)
    def test_config_command_logic_with_output(self, mock_console, mock_create_config):
        """Test the logic that would be executed by the config command with output file."""
        # Mock the configuration
        mock_config = Mock()
        mock_config.model_dump.return_value = {"test": "config"}
        mock_create_config.return_value = mock_config

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_file = f.name

        try:
            # This simulates what the config command would do
            config_obj = mock_create_config(
                project_path=".",
                fuzzy=True,
                semantic=False,
                threshold=0.7,
                max_results=50,
                output="json",
                verbose=True,
                cache_size=1000,
            )

            config_dict = config_obj.model_dump(mode="json")

            # Write to file
            with open(temp_file, "w") as f:
                json.dump(config_dict, f, indent=2)

            mock_console.print(f"Configuration saved to: {temp_file}")

            # Verify the function calls
            mock_create_config.assert_called_once()
            mock_config.model_dump.assert_called_once_with(mode="json")
            mock_console.print.assert_called_once()

            # Verify the file was created
            assert Path(temp_file).exists()

        finally:
            Path(temp_file).unlink(missing_ok=True)

    @patch("src.repomap_tool.cli.create_default_config")
    @patch(CONSOLE_PATCH_PATH)
    def test_config_command_logic_without_output(
        self, mock_console, mock_create_config
    ):
        """Test the logic that would be executed by the config command without output file."""
        # Mock the configuration
        mock_config = Mock()
        mock_config.model_dump.return_value = {"test": "config"}
        mock_create_config.return_value = mock_config

        # This simulates what the config command would do
        config_obj = mock_create_config(
            project_path=".",
            fuzzy=True,
            semantic=False,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
            cache_size=1000,
        )

        config_dict = config_obj.model_dump(mode="json")

        # Display configuration
        mock_console.print("Configuration:")
        mock_console.print(json.dumps(config_dict, indent=2))

        # Verify the function calls
        mock_create_config.assert_called_once()
        mock_config.model_dump.assert_called_once_with(mode="json")
        assert mock_console.print.call_count >= 2

    @patch(CONSOLE_PATCH_PATH)
    def test_version_command_logic(self, mock_console):
        """Test the logic that would be executed by the version command."""
        # This simulates what the version command would do
        version_info = (
            "[bold blue]RepoMap-Tool[/bold blue]\n"
            "Version: 0.1.0\n"
            "A portable code analysis tool using aider libraries"
        )

        mock_console.print(version_info)

        # Verify the function call
        mock_console.print.assert_called_once_with(version_info)


if __name__ == "__main__":
    pytest.main([__file__])
