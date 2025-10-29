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

from repomap_tool.cli.output.manager import OutputManager
from repomap_tool.protocols import (
    FormatterProtocol,
    FormatterRegistryProtocol,
    ConsoleManagerProtocol,
    TemplateRegistryProtocol,
)  # Updated imports
from repomap_tool.cli.output.templates.engine import (
    TemplateEngine as ConcreteTemplateEngine,
)  # Import concrete for mocks
from repomap_tool.cli.output.templates.registry import (
    DefaultTemplateRegistry,
)  # Import concrete for mocks
from repomap_tool.models import (
    ProjectInfo,
    SearchResponse,
    OutputConfig,
    OutputFormat,
    ErrorResponse,
    SuccessResponse,
)  # Ensure OutputConfig and OutputFormat are imported from models


class MockFormatter(FormatterProtocol):
    """Mock formatter for testing."""

    def __init__(
        self,
        supports_format: bool = True,
        return_value: str = "formatted output",
        data_type: Type[Any] = Any,
        # Accept these for compatibility with BaseFormatter, but don't use them
        console_manager: Optional[ConsoleManagerProtocol] = None,
        template_engine: Optional[ConcreteTemplateEngine] = None,
        template_registry: Optional[TemplateRegistryProtocol] = None,
        enable_logging: bool = True,
    ):
        self._supports_format = supports_format
        self.return_value = return_value
        self.format_called = False
        self.format_args = None
        self._data_type = data_type

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
        return isinstance(data, self._data_type)

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return self._data_type


class MockFormatterRegistry(FormatterRegistryProtocol):
    """Mock formatter registry for testing."""

    def __init__(
        self,
        template_engine: ConcreteTemplateEngine = Mock(spec=ConcreteTemplateEngine),
        template_registry: TemplateRegistryProtocol = Mock(
            spec=DefaultTemplateRegistry
        ),
        console_manager: ConsoleManagerProtocol = Mock(spec=ConsoleManagerProtocol),
    ):
        self._formatters: List[FormatterProtocol] = []
        self._type_formatters: Dict[Type[Any], List[FormatterProtocol]] = {}
        self._template_engine = template_engine
        self._template_registry = template_registry
        self._console_manager = console_manager

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter."""
        self._formatters.append(formatter)
        if data_type:
            if data_type not in self._type_formatters:
                self._type_formatters[data_type] = []
            self._type_formatters[data_type].append(formatter)

    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format."""
        # Try specific type formatters first
        if data_type in self._type_formatters:
            for formatter in self._type_formatters[data_type]:
                if formatter.supports_format(output_format):
                    return formatter

        # Try all formatters for validation-based matching
        for formatter in self._formatters:
            if (
                hasattr(formatter, "validate_data")
                and formatter.validate_data(data_type)
                and formatter.supports_format(output_format)
            ):
                return formatter

        return None

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters."""
        return self._formatters.copy()

    def unregister_formatter(self, formatter: FormatterProtocol) -> None:
        """Unregister a formatter."""
        if formatter in self._formatters:
            self._formatters.remove(formatter)


class MockConsoleManager(ConsoleManagerProtocol):
    """Mock console manager for testing."""

    def __init__(self, enable_logging: bool = True):
        self.console = Mock(spec=Console)
        self.get_console_called = False
        self.get_console_args = None
        self.log_operations = []
        self.enable_logging = enable_logging
        self.logger = Mock() if enable_logging else None

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Mock get_console method."""
        self.get_console_called = True
        self.get_console_args = ctx
        return self.console

    def configure(self, no_color: bool = False) -> None:
        """Mock configure method."""
        self.console.no_color = no_color
        self.log_operation("configure", {"no_color": no_color})

    def log_operation(self, operation: str, context: Dict[str, Any]) -> None:
        """Mock log_operation method."""
        self.log_operations.append((operation, context))
        if self.enable_logging and self.logger:
            self.logger.debug(f"Mock console operation: {operation} {context}")

    def get_usage_stats(self) -> Dict[str, Any]:
        """Mock get_usage_stats method."""
        stats: Dict[str, Any] = {}
        for op, _ in self.log_operations:
            stats[op] = stats.get(op, 0) + 1
        return stats

    def reset_usage_stats(self) -> None:
        """Mock reset_usage_stats method."""
        self.log_operations = []


class TestOutputManager:
    """Test cases for OutputManager class."""

    def test_init_with_valid_dependencies(self):
        """Test OutputManager initialization with valid dependencies."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        template_engine = Mock(spec=ConcreteTemplateEngine)
        template_registry = Mock(spec=TemplateRegistryProtocol)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=template_engine,
            template_registry=template_registry,
            enable_logging=False,
        )

        assert manager.console_manager is console_manager
        assert manager.formatter_registry is formatter_registry
        assert manager.template_engine is template_engine
        assert manager.template_registry is template_registry
        assert manager.enable_logging is False
        assert manager._output_stats["total_outputs"] == 0

    def test_init_without_console_manager_raises_error(self):
        """Test that initialization without console manager raises error."""
        formatter_registry = MockFormatterRegistry()
        template_engine = Mock(spec=ConcreteTemplateEngine)
        template_registry = Mock(spec=TemplateRegistryProtocol)

        with pytest.raises(ValueError, match="ConsoleManager must be injected"):
            OutputManager(
                console_manager=None,
                formatter_registry=formatter_registry,
                template_engine=template_engine,
                template_registry=template_registry,
            )

    def test_init_without_formatter_registry_raises_error(self):
        """Test that initialization without formatter registry raises error."""
        console_manager = MockConsoleManager()
        template_engine = Mock(spec=ConcreteTemplateEngine)
        template_registry = Mock(spec=TemplateRegistryProtocol)

        with pytest.raises(ValueError, match="FormatterRegistry must be injected"):
            OutputManager(
                console_manager=console_manager,
                formatter_registry=None,
                template_engine=template_engine,
                template_registry=template_registry,
            )

    def test_init_without_template_engine_raises_error(self):
        """Test that initialization without template engine raises error."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        template_registry = Mock(spec=TemplateRegistryProtocol)

        with pytest.raises(ValueError, match="TemplateEngine must be injected"):
            OutputManager(
                console_manager=console_manager,
                formatter_registry=formatter_registry,
                template_engine=None,
                template_registry=template_registry,
            )

    def test_init_without_template_registry_raises_error(self):
        """Test that initialization without template registry raises error."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry()
        template_engine = Mock(spec=ConcreteTemplateEngine)

        with pytest.raises(ValueError, match="TemplateRegistry must be injected"):
            OutputManager(
                console_manager=console_manager,
                formatter_registry=formatter_registry,
                template_engine=template_engine,
                template_registry=None,
            )

    def test_display_success(self):
        """Test successful data display."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)  # Specify data_type for formatter
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
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
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)  # Specify data_type for formatter
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
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
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        data = {"test": "data"}
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, config)

        # Should log an error and display a fallback message.
        mock_print.assert_called()
        assert manager._output_stats["errors"] == 1

    def test_display_error(self):
        """Test display_error method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(
            data_type=ErrorResponse
        )  # ErrorResponseFormatter is typically used for this
        formatter_registry.register_formatter(formatter, ErrorResponse)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        error = ValueError("Test error")
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display_error(error, config)

        assert formatter.format_called  # The generic dict formatter will be called
        assert manager._output_stats["errors"] == 1

    def test_display_success_message(self):
        """Test display_success method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(
            data_type=SuccessResponse
        )  # SuccessResponseFormatter is typically used for this
        formatter_registry.register_formatter(formatter, SuccessResponse)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        message = "Operation completed successfully"
        config = OutputConfig(format=OutputFormat.TEXT)

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display_success(message, config)

        assert formatter.format_called
        # Check that SuccessResponse object was passed
        success_response = formatter.format_args[0]
        assert isinstance(success_response, SuccessResponse)
        assert success_response.message == message
        assert success_response.status_code == 200

    def test_display_progress(self):
        """Test display_progress method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
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
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)  # Specify data_type for formatter
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        result = manager.validate_format(OutputFormat.TEXT, dict)
        assert result is True

    def test_validate_format_not_supported(self):
        """Test validate_format with unsupported format."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(supports_format=False, data_type=dict)
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        result = manager.validate_format(OutputFormat.TEXT, dict)
        assert result is False

    def test_get_supported_formats(self):
        """Test get_supported_formats method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        supported_formats = manager.get_supported_formats(dict)
        assert OutputFormat.TEXT in supported_formats
        assert OutputFormat.JSON in supported_formats

    def test_get_output_stats(self):
        """Test get_output_stats method."""
        console_manager = MockConsoleManager()
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
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
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )
        formatter = MockFormatter(data_type=dict)
        formatter_registry.register_formatter(formatter, dict)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
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
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
        )

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=Mock(spec=ConcreteTemplateEngine),
            template_registry=Mock(spec=TemplateRegistryProtocol),
            enable_logging=False,
        )

        data = {"test": "data"}
        invalid_config = "not a config"  # type: ignore

        with patch.object(console_manager.console, "print") as mock_print:
            manager.display(data, invalid_config)  # type: ignore

        # Should handle error gracefully
        mock_print.assert_called()
        assert manager._output_stats["errors"] == 1


# class TestGlobalOutputManager:
#     """Test cases for global output manager functionality."""

#     def test_get_output_manager_creates_singleton(self):
#         """Test that get_output_manager creates a singleton instance."""
#         # Reset the global instance to ensure clean test
#         import repomap_tool.cli.output.manager as manager_module

#         manager_module._global_output_manager = None

#         with patch("repomap_tool.cli.output.manager.create_container") as mock_create_container:

#             mock_container_instance = MagicMock()
#             mock_output_manager_instance = Mock(spec=OutputManager)
#             mock_create_container.return_value = mock_container_instance
#             mock_container_instance.output_manager.return_value = mock_output_manager_instance
#             MockOutputManagerClass.return_value = mock_output_manager_instance

#             # First call
#             manager1 = get_output_manager()
#             assert manager1 is mock_output_manager_instance

#             # Second call should return same instance
#             manager2 = get_output_manager()
#             assert manager2 is mock_output_manager_instance
#             assert manager1 is manager2

#             # create_container should be called once, and output_manager should be resolved from it.
#             mock_create_container.assert_called_once()
#             mock_container_instance.output_manager.assert_called_once()


class TestOutputManagerIntegration:
    """Integration tests for OutputManager with real formatters."""

    def test_display_with_real_project_info(self):
        """Test display with real ProjectInfo data."""
        console_manager = MockConsoleManager()
        template_engine = Mock(spec=ConcreteTemplateEngine)
        template_engine.render_template.return_value = (
            "Project Analysis\nTotal Files: 10\nTotal Identifiers: 50"
        )
        template_registry = Mock(spec=TemplateRegistryProtocol)
        formatter_registry = MockFormatterRegistry(
            console_manager=console_manager,
            template_engine=template_engine,
            template_registry=template_registry,
        )

        # Register a real formatter
        from repomap_tool.cli.output.standard_formatters import ProjectInfoFormatter

        formatter = ProjectInfoFormatter(
            console_manager=console_manager,
            template_engine=template_engine,
            template_registry=template_registry,
            enable_logging=False,
        )
        formatter_registry.register_formatter(formatter, ProjectInfo)

        manager = OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            template_engine=template_engine,
            template_registry=template_registry,
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
