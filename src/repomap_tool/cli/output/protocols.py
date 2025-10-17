"""
Formatter interface protocols for RepoMap-Tool CLI.

This module defines the standardized interfaces and protocols for all output formatters,
ensuring consistency and extensibility across the output system.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from abc import ABC, abstractmethod
from typing import Any, List, Optional, Protocol, Type, TypeVar, Union
from pathlib import Path

import click
from rich.console import Console

from repomap_tool.models import AnalysisFormat, OutputConfig, OutputFormat
from .console_manager import ConsoleManagerProtocol

# Type variables for generic formatters
T = TypeVar("T")
FormatterResult = Union[str, None]


class FormatterProtocol(Protocol):
    """Protocol for all formatter implementations."""

    def format(
        self,
        data: T,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> FormatterResult:
        """Format data to the specified output format.

        Args:
            data: The data to format
            output_format: The target output format
            config: Optional output configuration
            ctx: Optional Click context for console access

        Returns:
            Formatted string or None if formatting should be handled by console
        """
        ...

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the specified format.

        Args:
            output_format: The format to check

        Returns:
            True if the format is supported
        """
        ...

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported formats
        """
        ...


class BaseFormatter(ABC):
    """Abstract base class for all formatters."""

    def __init__(
        self,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the formatter.

        Args:
            console_manager: Console manager for output
            enable_logging: Whether to enable logging
        """
        self._console_manager = console_manager
        self._enable_logging = enable_logging
        self._logger = get_logger(__name__) if enable_logging else None

    @abstractmethod
    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> FormatterResult:
        """Format data to the specified output format.

        Args:
            data: The data to format
            output_format: The target output format
            config: Optional output configuration
            ctx: Optional Click context for console access

        Returns:
            Formatted string or None if formatting should be handled by console
        """
        pass

    @abstractmethod
    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the specified format.

        Args:
            output_format: The format to check

        Returns:
            True if the format is supported
        """
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported formats
        """
        pass

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get console instance for output.

        Args:
            ctx: Optional Click context

        Returns:
            Console instance
        """
        if self._console_manager:
            return self._console_manager.get_console(ctx)
        else:
            # Fallback to direct console creation
            from ..utils.console import get_console

            return get_console(ctx)

    def log_formatting(self, operation: str, **context: Any) -> None:
        """Log formatting operation.

        Args:
            operation: The operation being performed
            **context: Additional context information
        """
        if self._enable_logging and self._logger:
            self._logger.debug(
                f"Formatter operation: {operation}",
                extra={
                    "operation": operation,
                    "formatter": self.__class__.__name__,
                    "context": context,
                },
            )


class DataFormatter(FormatterProtocol):
    """Protocol for data-specific formatters."""

    def format_data(
        self,
        data: T,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> FormatterResult:
        """Format specific data type.

        Args:
            data: The data to format
            output_format: The target output format
            config: Optional output configuration
            ctx: Optional Click context

        Returns:
            Formatted string or None
        """
        ...

    def validate_data(self, data: Any) -> bool:
        """Validate that data is compatible with this formatter.

        Args:
            data: The data to validate

        Returns:
            True if data is compatible
        """
        return True

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles.

        Returns:
            The data type class
        """
        return Any


class TemplateFormatter(FormatterProtocol):
    """Protocol for template-based formatters."""

    def load_template(
        self,
        template_name: str,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Load a template for formatting.

        Args:
            template_name: Name of the template to load
            config: Optional configuration for template loading

        Returns:
            Template content
        """
        return ""

    def render_template(
        self,
        template: str,
        data: T,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Render template with data.

        Args:
            template: Template content
            data: Data to render
            config: Optional configuration

        Returns:
            Rendered content
        """
        return ""

    def get_available_templates(self) -> List[str]:
        """Get list of available templates.

        Returns:
            List of template names
        """
        return []


class FormatterRegistry(Protocol):
    """Protocol for formatter registry."""

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter.

        Args:
            formatter: The formatter to register
            data_type: Optional specific data type for the formatter
        """
        ...

    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format.

        Args:
            data_type: The data type
            output_format: The output format

        Returns:
            Matching formatter or None
        """
        ...

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters.

        Returns:
            List of all formatters
        """
        ...

    def unregister_formatter(
        self,
        formatter: FormatterProtocol,
    ) -> None:
        """Unregister a formatter.

        Args:
            formatter: The formatter to unregister
        """
        ...


class FormatterFactory(Protocol):
    """Protocol for formatter factory."""

    def create_formatter(
        self,
        formatter_type: str,
        **kwargs: Any,
    ) -> FormatterProtocol:
        """Create a formatter of the specified type.

        Args:
            formatter_type: Type of formatter to create
            **kwargs: Additional configuration

        Returns:
            Created formatter instance
        """
        ...

    def get_available_types(self) -> List[str]:
        """Get list of available formatter types.

        Returns:
            List of formatter type names
        """
        ...


# Utility functions for formatter management
def validate_formatter(formatter: FormatterProtocol) -> bool:
    """Validate that a formatter implements the protocol correctly.

    Args:
        formatter: The formatter to validate

    Returns:
        True if formatter is valid
    """
    try:
        # Check required methods exist
        assert hasattr(formatter, "format")
        assert hasattr(formatter, "supports_format")
        assert hasattr(formatter, "get_supported_formats")

        # Check methods are callable
        assert callable(formatter.format)
        assert callable(formatter.supports_format)
        assert callable(formatter.get_supported_formats)

        return True
    except AssertionError:
        return False


def get_formatter_info(formatter: FormatterProtocol) -> Dict[str, Any]:
    """Get information about a formatter.

    Args:
        formatter: The formatter to inspect

    Returns:
        Dictionary with formatter information
    """
    return {
        "class_name": formatter.__class__.__name__,
        "module": formatter.__class__.__module__,
        "supported_formats": formatter.get_supported_formats(),
        "is_valid": validate_formatter(formatter),
    }


def create_formatter_config(
    output_format: OutputFormat,
    verbose: bool = False,
    no_emojis: bool = False,
    no_color: bool = False,
    **kwargs: Any,
) -> OutputConfig:
    """Create output configuration for formatters.

    Args:
        output_format: The output format
        verbose: Whether to use verbose output
        no_emojis: Whether to disable emojis
        no_color: Whether to disable colors
        **kwargs: Additional configuration options

    Returns:
        Output configuration
    """
    template_config = {
        "verbose": verbose,
        "no_emojis": no_emojis,
        "no_color": no_color,
        **kwargs,
    }

    return OutputConfig(
        format=output_format,
        template_config=template_config,
    )
