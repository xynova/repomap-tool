"""
Tests for the unified output format system.
"""

import pytest
from typing import Dict, Any

from repomap_tool.cli.output.formats import (
    OutputFormat,
    OutputConfig,
    FormatValidationError,
    FormatConverter,
    FormatRegistry,
    format_registry,
    get_output_config,
    validate_output_format,
    get_supported_formats,
    is_valid_format,
)


class TestOutputFormat:
    """Test the OutputFormat enum."""

    def test_output_format_values(self):
        """Test that OutputFormat has correct values."""
        assert OutputFormat.TEXT == "text"
        assert OutputFormat.JSON == "json"

    def test_output_format_enumeration(self):
        """Test that OutputFormat can be enumerated."""
        formats = list(OutputFormat)
        assert len(formats) == 2
        assert OutputFormat.TEXT in formats
        assert OutputFormat.JSON in formats


class TestOutputConfig:
    """Test the OutputConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = OutputConfig()
        assert config.format == OutputFormat.TEXT
        assert config.verbose is False
        assert config.no_emojis is False
        assert config.no_color is False
        assert config.max_critical_lines == 3
        assert config.max_dependencies == 3
        assert config.compression == "medium"

    def test_custom_config(self):
        """Test custom configuration values."""
        config = OutputConfig(
            format=OutputFormat.JSON,
            verbose=True,
            no_emojis=True,
            max_critical_lines=5,
            compression="high",
        )
        assert config.format == OutputFormat.JSON
        assert config.verbose is True
        assert config.no_emojis is True
        assert config.max_critical_lines == 5
        assert config.compression == "high"

    def test_compression_validation(self):
        """Test compression level validation."""
        # Valid compression levels
        for level in ["low", "medium", "high"]:
            config = OutputConfig(compression=level)
            assert config.compression == level

        # Invalid compression level
        with pytest.raises(ValueError, match="Compression must be one of"):
            OutputConfig(compression="invalid")


class TestFormatConverter:
    """Test the FormatConverter utility class."""

    def test_validate_json_compatible(self):
        """Test JSON compatibility validation."""
        # Valid JSON-compatible data
        assert FormatConverter._validate_json_compatible({"key": "value"})
        assert FormatConverter._validate_json_compatible([1, 2, 3])
        assert FormatConverter._validate_json_compatible("string")
        assert FormatConverter._validate_json_compatible(123)
        assert FormatConverter._validate_json_compatible(True)

        # Invalid JSON-compatible data (functions, complex objects)
        assert not FormatConverter._validate_json_compatible(lambda x: x)
        assert not FormatConverter._validate_json_compatible(object())

    def test_validate_text_compatible(self):
        """Test text compatibility validation."""
        # Valid text-compatible data
        assert FormatConverter._validate_text_compatible("string")
        assert FormatConverter._validate_text_compatible(123)
        assert FormatConverter._validate_text_compatible({"key": "value"})

        # Invalid text-compatible data (should be rare)
        # Most objects can be converted to string
        assert FormatConverter._validate_text_compatible(object())

    def test_validate_format(self):
        """Test format validation."""
        # Valid formats
        assert FormatConverter.validate_format(OutputFormat.JSON, {"key": "value"})
        assert FormatConverter.validate_format(OutputFormat.TEXT, "string")

        # Invalid format
        with pytest.raises(FormatValidationError):
            FormatConverter.validate_format("invalid_format", "data")

    def test_convert_to_json(self):
        """Test JSON conversion."""
        data = {"key": "value", "number": 123}
        result = FormatConverter._convert_to_json(data)

        import json

        expected = json.dumps(data, indent=None, default=str)
        assert result == expected

    def test_convert_to_json_with_config(self):
        """Test JSON conversion with configuration."""
        data = {"key": "value"}
        config = OutputConfig(verbose=True)
        result = FormatConverter._convert_to_json(data, config)

        import json

        expected = json.dumps(data, indent=2, default=str)
        assert result == expected

    def test_convert_to_text_dict(self):
        """Test text conversion for dictionaries."""
        data = {"key": "value", "nested": {"subkey": "subvalue"}}
        result = FormatConverter._convert_to_text(data)

        # Should create hierarchical text representation
        assert "key: value" in result
        assert "nested:" in result
        assert "subkey: subvalue" in result

    def test_convert_to_text_list(self):
        """Test text conversion for lists."""
        data = [{"name": "item1", "value": 1}, {"name": "item2", "value": 2}]
        result = FormatConverter._convert_to_text(data)

        # Should create structured text representation
        assert "1. item1:" in result
        assert "value: 1" in result
        assert "2. item2:" in result
        assert "value: 2" in result

    def test_convert_to_format(self):
        """Test format conversion."""
        data = {"key": "value"}

        # JSON format
        json_result = FormatConverter.convert_to_format(data, OutputFormat.JSON)
        assert '"key": "value"' in json_result

        # TEXT format
        text_result = FormatConverter.convert_to_format(data, OutputFormat.TEXT)
        assert "key: value" in text_result


class TestFormatRegistry:
    """Test the FormatRegistry class."""

    def test_default_format_capabilities(self):
        """Test default format capabilities."""
        # JSON format capabilities
        json_caps = format_registry.get_format_capabilities(OutputFormat.JSON)
        assert json_caps["supports_structured_data"] is True
        assert json_caps["machine_readable"] is True
        assert json_caps["human_readable"] is False

        # TEXT format capabilities
        text_caps = format_registry.get_format_capabilities(OutputFormat.TEXT)
        assert text_caps["supports_structured_data"] is True
        assert text_caps["machine_readable"] is False
        assert text_caps["human_readable"] is True

    def test_register_data_type(self):
        """Test data type registration."""
        registry = FormatRegistry()

        # Register a custom data type
        class CustomData:
            pass

        registry.register_data_type(CustomData, [OutputFormat.TEXT])

        # Check supported formats
        supported = registry.get_supported_formats(CustomData)
        assert OutputFormat.TEXT in supported
        assert OutputFormat.JSON not in supported

    def test_is_format_supported(self):
        """Test format support checking."""
        registry = FormatRegistry()

        # All formats should be supported by default
        assert registry.is_format_supported(OutputFormat.TEXT, dict)
        assert registry.is_format_supported(OutputFormat.JSON, dict)


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_output_config(self):
        """Test get_output_config function."""
        # With string format
        config = get_output_config("json", verbose=True)
        assert config.format == OutputFormat.JSON
        assert config.verbose is True

        # With enum format
        config = get_output_config(OutputFormat.TEXT, no_emojis=True)
        assert config.format == OutputFormat.TEXT
        assert config.no_emojis is True

    def test_validate_output_format(self):
        """Test validate_output_format function."""
        # Valid string format
        result = validate_output_format("text")
        assert result == OutputFormat.TEXT

        # Valid enum format
        result = validate_output_format(OutputFormat.JSON)
        assert result == OutputFormat.JSON

        # Invalid format
        with pytest.raises(ValueError, match="Invalid output format"):
            validate_output_format("invalid")

    def test_get_supported_formats(self):
        """Test get_supported_formats function."""
        formats = get_supported_formats()
        assert len(formats) == 2
        assert "text" in formats
        assert "json" in formats

    def test_is_valid_format(self):
        """Test is_valid_format function."""
        # Valid formats
        assert is_valid_format("text")
        assert is_valid_format("json")

        # Invalid formats
        assert not is_valid_format("invalid")
        assert not is_valid_format("table")
        assert not is_valid_format("markdown")


class TestIntegration:
    """Integration tests for the format system."""

    def test_end_to_end_format_conversion(self):
        """Test complete format conversion workflow."""
        # Sample data
        data = {
            "project": "test-project",
            "files": ["file1.py", "file2.py"],
            "metrics": {"lines": 100, "functions": 10},
        }

        # Convert to JSON
        json_output = FormatConverter.convert_to_format(data, OutputFormat.JSON)
        assert '"project": "test-project"' in json_output
        assert '"files":' in json_output

        # Convert to TEXT
        text_output = FormatConverter.convert_to_format(data, OutputFormat.TEXT)
        assert "project: test-project" in text_output
        assert "files:" in text_output
        assert "file1.py" in text_output

    def test_config_integration(self):
        """Test configuration integration with format conversion."""
        data = {"key": "value"}
        config = OutputConfig(format=OutputFormat.JSON, verbose=True, no_emojis=True)

        # Convert with configuration
        result = FormatConverter.convert_to_format(data, config.format, config)

        # Should use verbose JSON formatting
        import json

        expected = json.dumps(data, indent=2, default=str)
        assert result == expected
