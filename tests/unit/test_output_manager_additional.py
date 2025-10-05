"""
Additional tests for the OutputManager class.

This module provides additional test coverage for the OutputManager to ensure
all functionality is properly tested with real scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from repomap_tool.cli.output.manager import (
    OutputManager,
    OutputManagerFactory,
    get_output_manager,
)
from repomap_tool.cli.output.formats import OutputFormat, OutputConfig
from repomap_tool.cli.output.console_manager import ConsoleManager
from repomap_tool.cli.output.standard_formatters import FormatterRegistry
from repomap_tool.models import ProjectInfo, SearchResponse, MatchResult


class TestOutputManagerAdditional:
    """Additional test cases for the OutputManager class."""

    def test_display_with_real_project_info(self):
        """Test displaying real ProjectInfo data."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted ProjectInfo"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        project_info = ProjectInfo(
            project_root="/test/project",
            total_files=10,
            total_identifiers=50,
            file_types={"py": 8, "js": 2},
            identifier_types={"function": 30, "class": 20},
            analysis_time_ms=150.0,
            last_updated=datetime.now(),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        manager.display(project_info, config)

        # Verify formatter was called
        mock_formatter_registry.get_formatter.assert_called_once()
        mock_formatter.format.assert_called_once()

    def test_display_with_real_search_response(self):
        """Test displaying real SearchResponse data."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted SearchResponse"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        match_result = MatchResult(
            identifier="test_function",
            score=0.95,
            match_type="fuzzy",
            line_number=42,
            file_path="/test/file.py",
            strategy="fuzzy",
        )

        search_response = SearchResponse(
            query="test",
            match_type="fuzzy",
            threshold=0.7,
            total_results=1,
            search_time_ms=25.0,
            results=[match_result],
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        manager.display(search_response, config)

        # Verify formatter was called
        mock_formatter_registry.get_formatter.assert_called_once()
        mock_formatter.format.assert_called_once()

    def test_display_with_different_formats(self):
        """Test displaying data in different output formats."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted data"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        data = {"test": "data"}

        # Test TEXT format
        config_text = OutputConfig(format=OutputFormat.TEXT)
        manager.display(data, config_text)

        # Test JSON format
        config_json = OutputConfig(format=OutputFormat.JSON)
        manager.display(data, config_json)

        # Verify formatter was called for both formats
        assert mock_formatter_registry.get_formatter.call_count == 2
        assert mock_formatter.format.call_count == 2

    def test_display_error_with_different_exceptions(self):
        """Test displaying different types of exceptions."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        # Test with ValueError
        value_error = ValueError("Invalid value provided")
        manager.display_error(value_error, config)

        # Test with RuntimeError
        runtime_error = RuntimeError("Runtime issue occurred")
        manager.display_error(runtime_error, config)

        # Test with generic Exception
        generic_error = Exception("Generic error")
        manager.display_error(generic_error, config)

        # Verify console was called for each error
        assert mock_console.print.call_count == 3

    def test_display_success_with_different_messages(self):
        """Test displaying different types of success messages."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        # Test with string message
        manager.display_success("Operation completed successfully", config)

        # Test with message containing emojis
        manager.display_success("✅ Task completed! 🎉", config)

        # Test with multiline message
        manager.display_success("Line 1\nLine 2\nLine 3", config)

        # Verify console was called for each message
        assert mock_console.print.call_count == 3

    def test_display_progress_with_different_stages(self):
        """Test displaying progress messages for different stages."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        # Simulate a multi-stage process
        stages = [
            "Initializing...",
            "Loading data...",
            "Processing files...",
            "Generating report...",
            "Finalizing...",
        ]

        for stage in stages:
            manager.display_progress(stage, progress=None)

        # Verify console was called for each stage
        assert mock_console.print.call_count == len(stages)

    def test_validate_format_with_different_data_types(self):
        """Test format validation with different data types."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.supports_format.return_value = True

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        # Test with different data types
        data_types = [
            str,
            int,
            float,
            bool,
            list,
            dict,
            ProjectInfo,
            SearchResponse,
        ]

        for data_type in data_types:
            result = manager.validate_format(OutputFormat.TEXT, data_type)
            assert result is True

    def test_validate_format_with_unsupported_format(self):
        """Test format validation with unsupported format."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)

        # Simulate no formatter found
        mock_formatter_registry.get_formatter.return_value = None

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        result = manager.validate_format(OutputFormat.TEXT, str)
        assert result is False

    def test_get_supported_formats_with_data_type(self):
        """Test getting supported formats for a specific data type."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.get_supported_formats.return_value = [
            OutputFormat.TEXT,
            OutputFormat.JSON,
        ]

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        supported_formats = manager.get_supported_formats(str)

        # Should return formats from the formatter
        assert OutputFormat.TEXT in supported_formats
        assert OutputFormat.JSON in supported_formats

    def test_get_output_stats(self):
        """Test getting output statistics."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted data"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        config = OutputConfig(format=OutputFormat.TEXT)
        data = {"test": "data"}

        # Perform various operations to generate stats
        manager.display(data, config)
        manager.display_success("Success message", config)
        manager.display_progress("Progress message")
        manager.display_error(ValueError("Test error"), config)

        stats = manager.get_output_stats()

        # Verify stats are tracked correctly
        assert "total_outputs" in stats
        assert (
            stats["total_outputs"] == 3
        )  # display, success, progress (error doesn't count as output)

    def test_reset_stats(self):
        """Test resetting output statistics."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted data"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        config = OutputConfig(format=OutputFormat.TEXT)
        data = {"test": "data"}

        # Generate some stats
        manager.display(data, config)
        manager.display_success("Success", config)

        # Verify stats exist
        stats_before = manager.get_output_stats()
        assert stats_before["total_outputs"] > 0

        # Reset stats
        manager.reset_stats()

        # Verify stats are reset
        stats_after = manager.get_output_stats()
        assert stats_after["total_outputs"] == 0

    def test_display_with_click_context(self):
        """Test display with Click context provided."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)
        mock_formatter = Mock()

        mock_formatter_registry.get_formatter.return_value = mock_formatter
        mock_formatter.format.return_value = "Formatted data"

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
        )

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)
        mock_ctx = Mock()

        manager.display(data, config, ctx=mock_ctx)

        # Verify formatter was called with context
        mock_formatter.format.assert_called_once_with(
            data, OutputFormat.TEXT, config, mock_ctx
        )

    def test_display_error_with_click_context(self):
        """Test error display with Click context provided."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)
        error = ValueError("Test error")
        mock_ctx = Mock()

        manager.display_error(error, config, ctx=mock_ctx)

        # Verify console manager was called with context
        mock_console_manager.get_console.assert_called_once_with(mock_ctx)

    def test_display_success_with_click_context(self):
        """Test success display with Click context provided."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)
        mock_ctx = Mock()

        manager.display_success("Success message", config, ctx=mock_ctx)

        # Verify console manager was called with context
        mock_console_manager.get_console.assert_called_once_with(mock_ctx)

    def test_display_progress_with_click_context(self):
        """Test progress display with Click context provided."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock()
        mock_console_manager.get_console.return_value = mock_console

        manager = OutputManager(
            console_manager=mock_console_manager,
            formatter_registry=Mock(spec=FormatterRegistry),
        )

        config = OutputConfig(format=OutputFormat.TEXT)
        mock_ctx = Mock()

        manager.display_progress("Progress message", ctx=mock_ctx)

        # Verify console manager was called with context
        mock_console_manager.get_console.assert_called_once_with(mock_ctx)


class TestOutputManagerFactoryAdditional:
    """Additional test cases for the OutputManagerFactory class."""

    def test_create_output_manager_with_all_parameters(self):
        """Test creating output manager with all parameters provided."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_formatter_registry = Mock(spec=FormatterRegistry)

        manager = OutputManagerFactory.create_output_manager(
            console_manager=mock_console_manager,
            formatter_registry=mock_formatter_registry,
            enable_logging=True,
        )

        assert isinstance(manager, OutputManager)
        assert manager._console_manager == mock_console_manager
        assert manager._formatter_registry == mock_formatter_registry
        assert manager._enable_logging is True

    def test_create_output_manager_with_partial_parameters(self):
        """Test creating output manager with partial parameters."""
        mock_console_manager = Mock(spec=ConsoleManager)

        manager = OutputManagerFactory.create_output_manager(
            console_manager=mock_console_manager,
            enable_logging=False,
        )

        assert isinstance(manager, OutputManager)
        assert manager._console_manager == mock_console_manager
        assert manager._enable_logging is False
        # Formatter registry should be created automatically
        assert manager._formatter_registry is not None

    def test_create_output_manager_with_no_parameters(self):
        """Test creating output manager with no parameters."""
        manager = OutputManagerFactory.create_output_manager()

        assert isinstance(manager, OutputManager)
        # All dependencies should be created automatically
        assert manager._console_manager is not None
        assert manager._formatter_registry is not None
        assert manager._enable_logging is True  # Default value


class TestGlobalOutputManagerAdditional:
    """Additional test cases for global output manager functionality."""

    def test_get_output_manager_multiple_calls(self):
        """Test that multiple calls to get_output_manager return the same instance."""
        # Reset the global instance to ensure clean test
        import repomap_tool.cli.output.manager as manager_module

        manager_module._global_output_manager = None

        # First call
        manager1 = get_output_manager()

        # Second call
        manager2 = get_output_manager()

        # Should be the same instance
        assert manager1 is manager2
        assert isinstance(manager1, OutputManager)
        assert isinstance(manager2, OutputManager)

    def test_get_output_manager_with_different_imports(self):
        """Test that get_output_manager works consistently across different imports."""
        # Reset the global instance
        import repomap_tool.cli.output.manager as manager_module

        manager_module._global_output_manager = None

        # Import from different paths
        from repomap_tool.cli.output.manager import get_output_manager as get_manager_1
        from repomap_tool.cli.output import get_output_manager as get_manager_2

        manager1 = get_manager_1()
        manager2 = get_manager_2()

        # Should be the same instance
        assert manager1 is manager2
