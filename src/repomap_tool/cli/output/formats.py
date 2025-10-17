"""
Unified output format system for RepoMap-Tool CLI.

This module provides a comprehensive format system for all CLI output,
including format definitions, validation utilities, and conversion helpers.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union, Type, get_args, get_origin

from pydantic import BaseModel, Field, field_validator

from repomap_tool.models import OutputFormat, AnalysisFormat, OutputConfig # Imported from models


# The OutputFormat, AnalysisFormat, and OutputConfig classes were moved to models.py
# The FormatValidationError class remains here as it's an output-specific exception.
class FormatValidationError(Exception):
    """Raised when format validation fails."""

    pass


class FormatConverter:
    """Utility class for format conversion and validation."""

    @staticmethod
    def validate_format(format_type: OutputFormat, data: Any) -> bool:
        """
        Validate that the given data is compatible with the specified format.

        Args:
            format_type: The output format to validate against
            data: The data to validate

        Returns:
            True if data is compatible with format, False otherwise

        Raises:
            FormatValidationError: If validation fails with details
        """
        try:
            if format_type == OutputFormat.JSON:
                return FormatConverter._validate_json_compatible(data)
            elif format_type == OutputFormat.TEXT:
                return FormatConverter._validate_text_compatible(data)
            else:
                raise FormatValidationError(f"Unknown format type: {format_type}")
        except Exception as e:
            raise FormatValidationError(f"Format validation failed: {e}")

    @staticmethod
    def _validate_json_compatible(data: Any) -> bool:
        """Validate that data is JSON serializable."""
        try:
            import json

            json.dumps(data)
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _validate_text_compatible(data: Any) -> bool:
        """Validate that data can be converted to text."""
        try:
            str(data)
            return True
        except Exception:
            return False

    @staticmethod
    def convert_to_format(
        data: Any, format_type: OutputFormat, config: Optional[OutputConfig] = None
    ) -> str:
        """
        Convert data to the specified format.

        Args:
            data: The data to convert
            format_type: The target format
            config: Optional output configuration

        Returns:
            Formatted string representation of the data

        Raises:
            FormatValidationError: If conversion fails
        """
        if not FormatConverter.validate_format(format_type, data):
            raise FormatValidationError(
                f"Data is not compatible with format {format_type}"
            )

        if format_type == OutputFormat.JSON:
            return FormatConverter._convert_to_json(data, config)
        elif format_type == OutputFormat.TEXT:
            return FormatConverter._convert_to_text(data, config)
        else:
            raise FormatValidationError(f"Unknown format type: {format_type}")

    @staticmethod
    def _convert_to_json(data: Any, config: Optional[OutputConfig] = None) -> str:
        """Convert data to JSON format."""
        import json

        indent = 2 if config and config.verbose else None
        return json.dumps(data, indent=indent, default=str)

    @staticmethod
    def _convert_to_text(data: Any, config: Optional[OutputConfig] = None) -> str:
        """Convert data to text format."""
        if hasattr(data, "model_dump"):
            # Pydantic model
            return str(data)
        elif isinstance(data, dict):
            # Dictionary - create hierarchical text representation
            return FormatConverter._dict_to_hierarchical_text(data, config)
        elif isinstance(data, list):
            # List - create structured text representation
            return FormatConverter._list_to_structured_text(data, config)
        else:
            # Fallback to string representation
            return str(data)

    @staticmethod
    def _dict_to_hierarchical_text(
        data: Dict[str, Any], config: Optional[OutputConfig] = None
    ) -> str:
        """Convert dictionary to hierarchical text format."""
        lines = []
        use_emojis = not (config and config.no_emojis)

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_value in value.items():
                    lines.append(f"  {sub_key}: {sub_value}")
            elif isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def _list_to_structured_text(
        data: List[Any], config: Optional[OutputConfig] = None
    ) -> str:
        """Convert list to structured text format."""
        lines = []
        use_emojis = not (config and config.no_emojis)

        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                lines.append(f"{i}. {item.get('name', 'Item')}:")
                for key, value in item.items():
                    if key != "name":
                        lines.append(f"   {key}: {value}")
            else:
                lines.append(f"{i}. {item}")

        return "\n".join(lines)


class FormatRegistry:
    """Registry for managing supported formats and their capabilities."""

    def __init__(self) -> None:
        self._supported_formats: Dict[Type, List[OutputFormat]] = {}
        self._format_capabilities: Dict[OutputFormat, Dict[str, Any]] = {}
        self._register_default_formats()

    def _register_default_formats(self) -> None:
        """Register default format capabilities."""
        # JSON format capabilities
        self._format_capabilities[OutputFormat.JSON] = {
            "supports_structured_data": True,
            "supports_hierarchical_data": True,
            "supports_metadata": True,
            "machine_readable": True,
            "human_readable": False,
            "supports_colors": False,
            "supports_emojis": False,
        }

        # TEXT format capabilities
        self._format_capabilities[OutputFormat.TEXT] = {
            "supports_structured_data": True,
            "supports_hierarchical_data": True,
            "supports_metadata": True,
            "machine_readable": False,
            "human_readable": True,
            "supports_colors": True,
            "supports_emojis": True,
        }

    def register_data_type(
        self, data_type: Type, supported_formats: List[OutputFormat]
    ) -> None:
        """
        Register which formats are supported for a specific data type.

        Args:
            data_type: The data type class
            supported_formats: List of formats that support this data type
        """
        self._supported_formats[data_type] = supported_formats

    def get_supported_formats(self, data_type: Type) -> List[OutputFormat]:
        """
        Get list of formats supported for a specific data type.

        Args:
            data_type: The data type to check

        Returns:
            List of supported formats for the data type
        """
        return self._supported_formats.get(data_type, list(OutputFormat))

    def get_format_capabilities(self, format_type: OutputFormat) -> Dict[str, Any]:
        """
        Get capabilities for a specific format.

        Args:
            format_type: The format to get capabilities for

        Returns:
            Dictionary of format capabilities
        """
        return self._format_capabilities.get(format_type, {})

    def is_format_supported(self, format_type: OutputFormat, data_type: Type) -> bool:
        """
        Check if a format is supported for a specific data type.

        Args:
            format_type: The format to check
            data_type: The data type to check

        Returns:
            True if format is supported for data type, False otherwise
        """
        supported_formats = self.get_supported_formats(data_type)
        return format_type in supported_formats


# Global format registry instance
format_registry = FormatRegistry()


def get_output_config(
    format_type: Union[str, OutputFormat] = OutputFormat.TEXT, **kwargs: Any
) -> OutputConfig:
    """
    Create an OutputConfig with the specified format and options.

    Args:
        format_type: The output format (string or enum)
        **kwargs: Additional configuration options

    Returns:
        Configured OutputConfig instance
    """
    if isinstance(format_type, str):
        format_type = OutputFormat(format_type)

    return OutputConfig(format=format_type, **kwargs)


def validate_output_format(format_type: Union[str, OutputFormat]) -> OutputFormat:
    """
    Validate and convert string format to OutputFormat enum.

    Args:
        format_type: Format as string or enum

    Returns:
        Validated OutputFormat enum

    Raises:
        ValueError: If format is invalid
    """
    if isinstance(format_type, OutputFormat):
        return format_type

    try:
        return OutputFormat(format_type)
    except ValueError:
        valid_formats = [f.value for f in OutputFormat]
        raise ValueError(
            f"Invalid output format '{format_type}'. Valid formats: {valid_formats}"
        )


def get_supported_formats() -> List[str]:
    """
    Get list of all supported format strings.

    Returns:
        List of supported format strings
    """
    return [format_type.value for format_type in OutputFormat]


def is_valid_format(format_type: str) -> bool:
    """
    Check if a format string is valid.

    Args:
        format_type: Format string to validate

    Returns:
        True if format is valid, False otherwise
    """
    try:
        OutputFormat(format_type)
        return True
    except ValueError:
        return False
