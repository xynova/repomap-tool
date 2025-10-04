"""
Unit tests for the OutputManager class.

This module tests the centralized output management functionality,
including display operations, error handling, and formatter integration.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Any, Dict, List, Optional, Type

import click
from rich.console import Console

from repomap_tool.cli.output.manager import (
    OutputManager,
    OutputManagerFactory,
    get_output_manager,
)
from repomap_tool.cli.output.console_manager import ConsoleManager
from repomap_tool.cli.output.formats import OutputConfig, OutputFormat
from repomap_tool.cli.output.protocols import FormatterProtocol, FormatterRegistry
from repomap_tool.models import ProjectInfo, SearchResponse


class MockFormatter(FormatterProtocol):
    """Mock formatter for testing."""

    def __init__(
        self, supports_format: bool = True, return_value: str = "formatted output"
    ):
        self._supports_format = supports_format
        self.return_value = return_value
        self.format_called = False
        self.format_args = None

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        """Mock format method."""
        self.format_called = True
        self.format_args = (data, output_format, config, ctx)
        return self.return_value

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Mock supports_format method."""
        return self._supports_format

    def get_supported_formats(self) -> List[OutputFormat]:
        """Mock get_supported_formats method."""
        return [OutputFormat.TEXT, OutputFormat.JSON] if self._supports_format else []

    def validate_data(self, data: Any) -> bool:
        """Mock validate_data method."""
        return True


class MockFormatterRegistry(FormatterRegistry):
    """Mock formatter registry for testing."""

    def __init__(self):
        self.formatters: List[FormatterProtocol] = []
        self.type_formatters: Dict[Type[Any], List[FormatterProtocol]] = {}

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter."""
        self.formatters.append(formatter)
        if data_type:
            if data_type not in self.type_formatters:
                self.type_formatters[data_type] = []
            self.type_formatters[data_type].append(formatter)

    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format."""
        if data_type in self.type_formatters:
            for formatter in self.type_formatters[data_type]:
                if formatter.supports_format(output_format):
                    return formatter

        # Try all formatters for validation-based matching
        for formatter in self.formatters:
            if hasattr(formatter, "validate_data") and formatter.supports_format(
                output_format
            ):
                return formatter

        return None

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters."""
        return self.formatters.copy()

    def unregister_formatter(self, formatter: FormatterProtocol) -> None:
        """Unregister a formatter."""
        if formatter in self.formatters:
            self.formatters.remove(formatter)


class MockConsoleManager(ConsoleManager):
    """Mock console manager for testing."""

    def __init__(self):
        self.console = Mock()
        self.get_console_called = False
        self.get_console_args = None

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Mock get_console method."""
        self.get_console_called = True
        self.get_console_args = ctx
        return self.console

    def configure_console(
        self, ctx: Optional[click.Context] = None, **kwargs: Any
    ) -> Console:
        """Mock configure_console method."""
        return self.console


class TestOutputManager:
    """Test cases for OutputManager class."""

    def test_init_with_valid_dependencies(self):
        """Test OutputManager initialization with valid dependencies."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        assert manager._console_manager is console_manager
        assert manager._formatter_registry is formatter_registry
        assert manager._enable_logging is False
        assert manager._output_stats["total_outputs"] == 0

    def test_init_without_console_manager_raises_error(self):
        """Test that initialization without console manager raises error."""
        formatter_registry = MockFormatterRegistry()

        with pytest.raises(ValueError, match="ConsoleManager must be injected"):
            OutputManager(console_manager=None, formatter_registry=formatter_registry)

    def test_init_without_formatter_registry_raises_error(self):
        """Test that initialization without formatter registry raises error."""
        console_manager = MockConsoleManager()

        with pytest.raises(ValueError, match="FormatterRegistry must be injected"):
            OutputManager(console_manager=console_manager, formatter_registry=None)

    def test_display_success(self):
        """Test successful data display."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, config)

        assert formatter.format_called
        assert formatter.format_args[0] is data
        assert formatter.format_args[1] == OutputFormat.TEXT
        assert console_manager.get_console_called
        mock_print.assert_called_once_with("formatted output")
        assert manager._output_stats["total_outputs"] == 1
        assert manager._output_stats["text_outputs"] == 1

    def test_display_json_format(self):
        """Test display with JSON format."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.JSON)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, config)

        assert manager._output_stats["json_outputs"] == 1
        assert manager._output_stats["text_outputs"] == 0

    def test_display_no_formatter_found(self):
        """Test display when no formatter is found."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, config)

        # Should fall back to error display
        mock_print.assert_called()
        assert manager._output_stats["errors"] == 1

    def test_display_error(self):
        """Test display_error method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        error = ValueError("Test error")
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display_error(error, config)

        assert formatter.format_called
        assert manager._output_stats["errors"] == 1

    def test_display_success_message(self):
        """Test display_success method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        message = "Operation completed successfully"
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display_success(message, config)

        assert formatter.format_called
        # Check that success data structure was passed
        success_data = formatter.format_args[0]
        assert "success" in success_data
        assert success_data["success"]["message"] == message

    def test_display_progress(self):
        """Test display_progress method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        message = "Processing files..."

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display_progress(message, progress=0.5)

        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Processing files..." in call_args
        assert "50%" in call_args

    def test_validate_format_success(self):
        """Test validate_format with supported format."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        result = manager.validate_format(OutputFormat.TEXT, dict)
        assert result is True

    def test_validate_format_not_supported(self):
        """Test validate_format with unsupported format."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter(supports_format=False)
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        result = manager.validate_format(OutputFormat.TEXT, dict)
        assert result is False

    def test_get_supported_formats(self):
        """Test get_supported_formats method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        supported_formats = manager.get_supported_formats(dict)
        assert OutputFormat.TEXT in supported_formats
        assert OutputFormat.JSON in supported_formats

    def test_get_output_stats(self):
        """Test get_output_stats method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        # Perform some operations
        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print"):
            manager.display(data, config)

        stats = manager.get_output_stats()
        assert stats["total_outputs"] == 1
        assert stats["text_outputs"] == 1
        assert stats["json_outputs"] == 0
        assert stats["errors"] == 0

    def test_reset_stats(self):
        """Test reset_stats method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        formatter = MockFormatter()
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        # Perform some operations
        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print"):
            manager.display(data, config)

        # Reset stats
        manager.reset_stats()

        stats = manager.get_output_stats()
        assert stats["total_outputs"] == 0
        assert stats["text_outputs"] == 0
        assert stats["json_outputs"] == 0
        assert stats["errors"] == 0

    def test_invalid_config_raises_error(self):
        """Test that invalid config raises error."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        data = {"test": "data"}
        invalid_config = "not a config"  # type: ignore

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, invalid_config)  # type: ignore

        # Should handle error gracefully
        mock_print.assert_called()
        assert manager._output_stats["errors"] == 1


class TestOutputManagerFactory:
    """Test cases for OutputManagerFactory class."""

    def test_create_output_manager_with_dependencies(self):
        """Test creating OutputManager with provided dependencies."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        manager = OutputManagerFactory.create_output_manager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        assert isinstance(manager, OutputManager)
        assert manager._console_manager is console_manager
        assert manager._formatter_registry is formatter_registry

    def test_create_output_manager_with_defaults(self):
        """Test creating OutputManager with default dependencies."""
        with (
            patch(
                "repomap_tool.cli.output.console_manager.ConsoleManagerFactory"
            ) as mock_factory,
            patch(
                "repomap_tool.cli.output.manager.get_formatter_registry"
            ) as mock_registry,
        ):

            mock_console_manager = MockConsoleManager()
            mock_formatter_registry = MockFormatterRegistry()
            mock_factory.create_default_manager.return_value = mock_console_manager
            mock_registry.return_value = mock_formatter_registry

            manager = OutputManagerFactory.create_output_manager()

            assert isinstance(manager, OutputManager)
            mock_factory.create_default_manager.assert_called_once()
            mock_registry.assert_called_once()


class TestGlobalOutputManager:
    """Test cases for global output manager functionality."""

    def test_get_output_manager_creates_singleton(self):
        """Test that get_output_manager creates a singleton instance."""
        # Reset the global instance to ensure clean test
        import repomap_tool.cli.output.manager as manager_module

        manager_module._global_output_manager = None

        with patch(
            "repomap_tool.cli.output.manager.OutputManagerFactory.create_output_manager"
        ) as mock_create:
            mock_manager = Mock(spec=OutputManager)
            mock_create.return_value = mock_manager

            # First call
            manager1 = get_output_manager()
            assert manager1 is mock_manager

            # Second call should return same instance
            manager2 = get_output_manager()
            assert manager2 is mock_manager
            assert manager1 is manager2

            # Factory should only be called once
            assert mock_create.call_count == 1


class TestOutputManagerIntegration:
    """Integration tests for OutputManager with real formatters."""

    def test_display_with_real_project_info(self):
        """Test display with real ProjectInfo data."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        # Register a real formatter
        from repomap_tool.cli.output.standard_formatters import ProjectInfoFormatter

        formatter = ProjectInfoFormatter(enable_logging=False)
        formatter_registry.register_formatter(formatter, ProjectInfo)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        # Create real ProjectInfo data
        from datetime import datetime

        project_info = ProjectInfo(
            project_root="/test/project",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={"py": 5, "js": 3, "md": 2},
            identifier_types={"function": 30, "class": 20},
            cache_stats={"hits": 10, "misses": 5},
            last_updated=datetime.now(),
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(project_info, config)

        # Verify output was generated
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "Project Analysis" in output
        assert "Total Files: 10" in output
        assert "Total Identifiers: 50" in output

    def test_display_with_real_search_response(self):
        """Test display with real SearchResponse data."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()

        # Register a real formatter
        from repomap_tool.cli.output.standard_formatters import SearchResponseFormatter

        formatter = SearchResponseFormatter(enable_logging=False)
        formatter_registry.register_formatter(formatter, SearchResponse)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=False,
        )

        # Create real SearchResponse data
        from repomap_tool.models import MatchResult

        search_response = SearchResponse(
            query="test_function",
            match_type="fuzzy",
            threshold=0.7,
            total_results=1,
            search_time_ms=50.0,
            results=[
                MatchResult(
                    identifier="test_function",
                    score=0.95,
                    match_type="fuzzy",
                    strategy="fuzzy",
                    file_path="/test/file.py",
                    line_number=10,
                )
            ],
            performance_metrics={"search_time_ms": 50.0},
        )

        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(search_response, config)

        # Verify output was generated
        mock_print.assert_called_once()
        output = mock_print.call_args[0][0]
        assert "Search Results" in output
        assert "test_function" in output
        assert "95.0%" in output
