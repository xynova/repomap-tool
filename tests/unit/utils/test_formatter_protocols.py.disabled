"""
Tests for the formatter interface protocols and implementations.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Any, Dict, List, Optional, Type

import click
from rich.console import Console

from repomap_tool.protocols import FormatterProtocol, BaseFormatter
from repomap_tool.cli.output.protocols import (
    DataFormatter,
    TemplateFormatter,
    FormatterRegistry as FormatterRegistryProtocol,
    FormatterFactory,
    OutputHandler,
    validate_formatter,
    get_formatter_info,
    create_formatter_config,
)
from repomap_tool.cli.output.standard_formatters import (
    ProjectInfoFormatter,
    DictFormatter,
    ListFormatter,
    FormatterRegistry,
    get_formatter_registry,
)
from repomap_tool.cli.output.formats import OutputFormat, OutputConfig
from repomap_tool.cli.output.console_manager import ConsoleManager
from repomap_tool.models import ProjectInfo, SearchResponse


class TestFormatterProtocol:
    """Test the FormatterProtocol interface."""

    def test_formatter_protocol_interface(self):
        """Test that FormatterProtocol defines the correct interface."""

        # Create a mock formatter that implements the protocol
        class MockFormatter:
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted_data"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT, OutputFormat.JSON]

        formatter = MockFormatter()

        # Should implement all required methods
        assert hasattr(formatter, "format")
        assert hasattr(formatter, "supports_format")
        assert hasattr(formatter, "get_supported_formats")

        # Should be callable
        assert callable(formatter.format)
        assert callable(formatter.supports_format)
        assert callable(formatter.get_supported_formats)

    def test_validate_formatter_valid(self):
        """Test formatter validation with valid formatter."""

        class ValidFormatter:
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = ValidFormatter()
        assert validate_formatter(formatter) is True

    def test_validate_formatter_invalid(self):
        """Test formatter validation with invalid formatter."""

        class InvalidFormatter:
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            # Missing required methods

        formatter = InvalidFormatter()
        assert validate_formatter(formatter) is False

    def test_get_formatter_info(self):
        """Test getting formatter information."""

        class TestFormatter:
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = TestFormatter()
        info = get_formatter_info(formatter)

        assert info["class_name"] == "TestFormatter"
        assert info["module"] == "test_formatter_protocols"
        assert info["supported_formats"] == [OutputFormat.TEXT]
        assert info["is_valid"] is True


class TestBaseFormatter:
    """Test the BaseFormatter abstract class."""

    def test_base_formatter_initialization(self):
        """Test BaseFormatter initialization."""

        class ConcreteFormatter(BaseFormatter):
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = ConcreteFormatter()
        assert formatter._console_manager is None
        assert formatter._enable_logging is True
        assert formatter._logger is not None

    def test_base_formatter_with_console_manager(self):
        """Test BaseFormatter with console manager."""
        mock_console_manager = Mock(spec=ConsoleManager)
        mock_console = Mock(spec=Console)
        mock_console_manager.get_console.return_value = mock_console

        class ConcreteFormatter(BaseFormatter):
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = ConcreteFormatter(console_manager=mock_console_manager)
        console = formatter.get_console()

        assert console == mock_console
        mock_console_manager.get_console.assert_called_once_with(None)

    def test_base_formatter_logging_disabled(self):
        """Test BaseFormatter with logging disabled."""

        class ConcreteFormatter(BaseFormatter):
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = ConcreteFormatter(enable_logging=False)
        assert formatter._enable_logging is False
        assert formatter._logger is None

    def test_base_formatter_logging(self):
        """Test BaseFormatter logging functionality."""

        class ConcreteFormatter(BaseFormatter):
            def format(self, data, output_format, config=None, ctx=None):
                return "formatted"

            def supports_format(self, output_format):
                return True

            def get_supported_formats(self):
                return [OutputFormat.TEXT]

        formatter = ConcreteFormatter()

        with patch.object(formatter._logger, "debug") as mock_debug:
            formatter.log_formatting("test_operation", key="value")

            mock_debug.assert_called_once()
            call_args = mock_debug.call_args
            assert "test_operation" in call_args[0][0]
            assert call_args[1]["extra"]["operation"] == "test_operation"
            assert call_args[1]["extra"]["formatter"] == "ConcreteFormatter"
            assert call_args[1]["extra"]["context"]["key"] == "value"


class TestDataFormatter:
    """Test the DataFormatter protocol."""

    def test_data_formatter_interface(self):
        """Test that DataFormatter defines the correct interface."""

        class MockDataFormatter:
            def format_data(self, data, output_format, config=None, ctx=None):
                return "formatted_data"

            def validate_data(self, data):
                return True

            def get_data_type(self):
                return str

        formatter = MockDataFormatter()

        # Should implement all required methods
        assert hasattr(formatter, "format_data")
        assert hasattr(formatter, "validate_data")
        assert hasattr(formatter, "get_data_type")

        # Should be callable
        assert callable(formatter.format_data)
        assert callable(formatter.validate_data)
        assert callable(formatter.get_data_type)


class TestProjectInfoFormatter:
    """Test the ProjectInfoFormatter implementation."""

    def test_project_info_formatter_initialization(self):
        """Test ProjectInfoFormatter initialization."""
        formatter = ProjectInfoFormatter()

        assert OutputFormat.TEXT in formatter.get_supported_formats()
        assert OutputFormat.JSON in formatter.get_supported_formats()
        assert formatter.get_data_type() == ProjectInfo

    def test_project_info_formatter_validate_data(self):
        """Test ProjectInfo data validation."""
        formatter = ProjectInfoFormatter()

        # Valid data
        project_info = ProjectInfo(
            project_root="/test",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={".py": 5, ".js": 3},
            identifier_types={"function": 20, "class": 10},
            last_updated="2024-01-01T00:00:00Z",
        )
        assert formatter.validate_data(project_info) is True

        # Invalid data
        assert formatter.validate_data("not_project_info") is False
        assert formatter.validate_data(None) is False

    def test_project_info_formatter_supports_format(self):
        """Test format support checking."""
        formatter = ProjectInfoFormatter()

        assert formatter.supports_format(OutputFormat.TEXT) is True
        assert formatter.supports_format(OutputFormat.JSON) is True

    def test_project_info_formatter_json_output(self):
        """Test JSON output formatting."""
        formatter = ProjectInfoFormatter()

        project_info = ProjectInfo(
            project_root="/test",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={".py": 5, ".js": 3},
            identifier_types={"function": 20, "class": 10},
            last_updated="2024-01-01T00:00:00Z",
        )

        result = formatter.format(project_info, OutputFormat.JSON)

        assert result is not None
        assert '"project_root": "/test"' in result
        assert '"total_files": 10' in result

    def test_project_info_formatter_text_output(self):
        """Test text output formatting."""
        formatter = ProjectInfoFormatter()

        project_info = ProjectInfo(
            project_root="/test",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={".py": 5, ".js": 3},
            identifier_types={"function": 20, "class": 10},
            last_updated="2024-01-01T00:00:00Z",
        )

        result = formatter.format(project_info, OutputFormat.TEXT)

        assert result is not None
        assert "🧠 LLM-Optimized Project Analysis" in result
        assert "Project Root: /test" in result
        assert "Total Files: 10" in result

    def test_project_info_formatter_text_output_no_emojis(self):
        """Test text output formatting without emojis."""
        formatter = ProjectInfoFormatter()

        project_info = ProjectInfo(
            project_root="/test",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={".py": 5, ".js": 3},
            identifier_types={"function": 20, "class": 10},
            last_updated="2024-01-01T00:00:00Z",
        )

        config = OutputConfig(
            format=OutputFormat.TEXT, template_config={"no_emojis": True}
        )

        result = formatter.format(project_info, OutputFormat.TEXT, config)

        assert result is not None
        assert "Project Analysis" in result  # No emoji
        assert "🧠" not in result

    def test_project_info_formatter_unsupported_format(self):
        """Test handling of unsupported format."""
        formatter = ProjectInfoFormatter()

        project_info = ProjectInfo(
            project_root="/test",
            total_files=10,
            total_identifiers=50,
            analysis_time_ms=100.0,
            file_types={".py": 5, ".js": 3},
            identifier_types={"function": 20, "class": 10},
            last_updated="2024-01-01T00:00:00Z",
        )

        # This should raise an error for unsupported format
        with pytest.raises(ValueError, match="Unsupported format"):
            formatter.format(project_info, "unsupported_format")


class TestDictFormatter:
    """Test the DictFormatter implementation."""

    def test_dict_formatter_initialization(self):
        """Test DictFormatter initialization."""
        formatter = DictFormatter()

        assert OutputFormat.TEXT in formatter.get_supported_formats()
        assert OutputFormat.JSON in formatter.get_supported_formats()
        assert formatter.get_data_type() == dict

    def test_dict_formatter_validate_data(self):
        """Test dictionary data validation."""
        formatter = DictFormatter()

        assert formatter.validate_data({"key": "value"}) is True
        assert formatter.validate_data("not_dict") is False
        assert formatter.validate_data(None) is False

    def test_dict_formatter_json_output(self):
        """Test JSON output formatting."""
        formatter = DictFormatter()

        data = {"key": "value", "number": 42}
        result = formatter.format(data, OutputFormat.JSON)

        assert result is not None
        assert '"key": "value"' in result
        assert '"number": 42' in result

    def test_dict_formatter_dependency_data(self):
        """Test formatting dependency analysis data."""
        formatter = DictFormatter()

        data = {"total_files": 10, "total_dependencies": 25, "circular_dependencies": 2}

        result = formatter.format(data, OutputFormat.TEXT)

        assert result is not None
        assert "Dependency Analysis Results" in result
        assert "Total Files" in result
        assert "10" in result


class TestListFormatter:
    """Test the ListFormatter implementation."""

    def test_list_formatter_initialization(self):
        """Test ListFormatter initialization."""
        formatter = ListFormatter()

        assert OutputFormat.TEXT in formatter.get_supported_formats()
        assert OutputFormat.JSON in formatter.get_supported_formats()
        assert formatter.get_data_type() == list

    def test_list_formatter_validate_data(self):
        """Test list data validation."""
        formatter = ListFormatter()

        assert formatter.validate_data(["item1", "item2"]) is True
        assert formatter.validate_data("not_list") is False
        assert formatter.validate_data(None) is False

    def test_list_formatter_json_output(self):
        """Test JSON output formatting."""
        formatter = ListFormatter()

        data = ["item1", "item2", "item3"]
        result = formatter.format(data, OutputFormat.JSON)

        assert result is not None
        assert '"item1"' in result
        assert '"item2"' in result

    def test_list_formatter_cycle_data(self):
        """Test formatting cycle detection data."""
        formatter = ListFormatter()

        data = [["file1.py", "file2.py"], ["file3.py", "file4.py"]]
        result = formatter.format(data, OutputFormat.TEXT)

        assert result is not None
        assert "Circular Dependencies (2 found)" in result
        assert "Cycle #1:" in result
        assert "file1.py" in result
        assert "→ file2.py" in result
        assert "→ file1.py" in result

    def test_list_formatter_empty_list(self):
        """Test formatting empty list."""
        formatter = ListFormatter()

        result = formatter.format([], OutputFormat.TEXT)

        assert result is not None
        # Empty list is detected as cycle data, so it returns the cycle message
        assert "No circular dependencies found" in result


class TestFormatterRegistry:
    """Test the FormatterRegistry implementation."""

    def test_formatter_registry_initialization(self):
        """Test FormatterRegistry initialization."""
        registry = FormatterRegistry()

        assert len(registry.get_all_formatters()) == 0

    def test_register_formatter(self):
        """Test registering formatters."""
        registry = FormatterRegistry()
        formatter = ProjectInfoFormatter()

        registry.register_formatter(formatter, ProjectInfo)

        assert formatter in registry.get_all_formatters()
        assert len(registry.get_all_formatters()) == 1

    def test_get_formatter(self):
        """Test getting formatters by data type and format."""
        registry = FormatterRegistry()
        formatter = ProjectInfoFormatter()

        registry.register_formatter(formatter, ProjectInfo)

        # Should find the formatter
        found_formatter = registry.get_formatter(ProjectInfo, OutputFormat.TEXT)
        assert found_formatter == formatter

        # Should not find formatter for unsupported format
        found_formatter = registry.get_formatter(ProjectInfo, "unsupported")
        assert found_formatter is None

    def test_unregister_formatter(self):
        """Test unregistering formatters."""
        registry = FormatterRegistry()
        formatter = ProjectInfoFormatter()

        registry.register_formatter(formatter, ProjectInfo)
        assert len(registry.get_all_formatters()) == 1

        registry.unregister_formatter(formatter)
        assert len(registry.get_all_formatters()) == 0

    def test_get_formatter_registry_global(self):
        """Test getting the global formatter registry."""
        registry = get_formatter_registry()

        assert isinstance(registry, FormatterRegistry)
        assert len(registry.get_all_formatters()) > 0  # Should have default formatters


class TestUtilityFunctions:
    """Test utility functions."""

    def test_create_formatter_config(self):
        """Test creating formatter configuration."""
        config = create_formatter_config(
            OutputFormat.TEXT,
            verbose=True,
            no_emojis=True,
            no_color=True,
            custom_option="value",
        )

        assert config.format == OutputFormat.TEXT
        assert config.template_config["verbose"] is True
        assert config.template_config["no_emojis"] is True
        assert config.template_config["no_color"] is True
        assert config.template_config["custom_option"] == "value"
