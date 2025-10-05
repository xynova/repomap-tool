"""
Centralized output manager for RepoMap-Tool CLI.

This module provides the main OutputManager class that serves as the central hub
for all output operations, integrating console management, formatter registry,
and output configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type, Union

import click
from rich.console import Console

from .console_manager import ConsoleManager
from .formats import OutputConfig, OutputFormat
from .protocols import FormatterProtocol, FormatterRegistry
from .standard_formatters import get_formatter_registry


class OutputManager:
    """Centralized output manager for all CLI output operations.

    This class serves as the main interface for output operations, providing:
    - Unified output formatting and display
    - Console management integration
    - Formatter registry coordination
    - Error handling and validation
    - Progress reporting integration
    """

    def __init__(
        self,
        console_manager: Optional[ConsoleManager] = None,
        formatter_registry: Optional[FormatterRegistry] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the output manager.

        Args:
            console_manager: Console manager for output operations
            formatter_registry: Registry for managing formatters
            enable_logging: Whether to enable logging
        """
        if console_manager is None:
            raise ValueError("ConsoleManager must be injected - no fallback allowed")
        if formatter_registry is None:
            raise ValueError("FormatterRegistry must be injected - no fallback allowed")

        self._console_manager = console_manager
        self._formatter_registry = formatter_registry
        self._enable_logging = enable_logging
        self._logger = logging.getLogger(__name__) if enable_logging else None

        # Track output statistics
        self._output_stats: Dict[str, int] = {
            "total_outputs": 0,
            "text_outputs": 0,
            "json_outputs": 0,
            "errors": 0,
        }

    def display(
        self,
        data: Any,
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display data using the specified output configuration.

        Args:
            data: The data to display
            config: Output configuration specifying format and options
            ctx: Click context for console configuration
        """
        try:
            # Validate the output configuration
            self._validate_config(config)

            # Get the appropriate formatter
            formatter = self._get_formatter(data, config.format)
            if formatter is None:
                raise ValueError(
                    f"No formatter found for data type {type(data)} and format {config.format}"
                )

            # Format the data
            formatted_output = formatter.format(data, config.format, config, ctx)
            if formatted_output is None:
                if self._logger:
                    self._logger.warning(
                        f"Formatter returned None for {type(data)} with format {config.format}"
                    )
                return

            # Get console and display the output
            console = self._console_manager.get_console(ctx)
            console.print(formatted_output)

            # Update statistics
            self._update_stats(config.format)

            if self._enable_logging and self._logger:
                self._logger.debug(
                    f"Displayed {type(data).__name__} in {config.format} format"
                )

        except Exception as e:
            self._handle_display_error(e, config, ctx)

    def display_error(
        self,
        error: Union[Exception, Any],
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display an error message using the specified output configuration.

        Args:
            error: The exception to display
            config: Output configuration specifying format and options
            ctx: Click context for console configuration
        """
        try:
            # Create error data structure
            error_data = {
                "error": {
                    "type": type(error).__name__,
                    "message": str(error),
                    "details": getattr(error, "details", None),
                }
            }

            # Display the error
            self.display(error_data, config, ctx)

            # Update error statistics
            self._output_stats["errors"] += 1

            if self._enable_logging and self._logger:
                self._logger.error(f"Displayed error: {type(error).__name__}: {error}")

        except Exception as display_error:
            # Fallback to basic error display
            console = self._console_manager.get_console(ctx)
            console.print(f"[red]Error: {error}[/red]")
            if self._enable_logging and self._logger:
                self._logger.error(f"Failed to display error properly: {display_error}")

    def display_success(
        self,
        message: str,
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display a success message using the specified output configuration.

        Args:
            message: The success message to display
            config: Output configuration specifying format and options
            ctx: Click context for console configuration
        """
        try:
            # Create success data structure
            success_data = {
                "success": {
                    "message": message,
                    "status": "completed",
                }
            }

            # Display the success message
            self.display(success_data, config, ctx)

            if self._enable_logging and self._logger:
                self._logger.debug(f"Displayed success message: {message}")

        except Exception as e:
            # Fallback to basic success display
            console = self._console_manager.get_console(ctx)
            console.print(f"[green]✅ {message}[/green]")
            if self._enable_logging and self._logger:
                self._logger.error(f"Failed to display success message properly: {e}")

    def display_progress(
        self,
        message: str,
        progress: Optional[float] = None,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display a progress message.

        Args:
            message: The progress message to display
            progress: Optional progress value (0.0 to 1.0)
            ctx: Click context for console configuration
        """
        try:
            console = self._console_manager.get_console(ctx)

            if progress is not None:
                # Display progress with percentage
                percentage = int(progress * 100)
                console.print(f"[blue]🔄 {message} ({percentage}%)[/blue]")
            else:
                # Display simple progress message
                console.print(f"[blue]🔄 {message}[/blue]")

            if self._enable_logging and self._logger:
                self._logger.debug(f"Displayed progress: {message} ({progress})")

        except Exception as e:
            if self._enable_logging and self._logger:
                self._logger.error(f"Failed to display progress: {e}")

    def validate_format(
        self,
        format_type: OutputFormat,
        data_type: Type[Any],
    ) -> bool:
        """Validate if a format is supported for a given data type.

        Args:
            format_type: The output format to validate
            data_type: The data type to check format support for

        Returns:
            True if the format is supported for the data type
        """
        try:
            formatter = self._formatter_registry.get_formatter(data_type, format_type)
            return formatter is not None
        except Exception as e:
            if self._enable_logging and self._logger:
                self._logger.error(
                    f"Error validating format {format_type} for {data_type}: {e}"
                )
            return False

    def get_supported_formats(self, data_type: Type[Any]) -> List[OutputFormat]:
        """Get all supported formats for a given data type.

        Args:
            data_type: The data type to get supported formats for

        Returns:
            List of supported output formats
        """
        try:
            supported_formats = []
            for format_type in OutputFormat:
                if self.validate_format(format_type, data_type):
                    supported_formats.append(format_type)
            return supported_formats
        except Exception as e:
            if self._enable_logging and self._logger:
                self._logger.error(
                    f"Error getting supported formats for {data_type}: {e}"
                )
            return []

    def get_output_stats(self) -> Dict[str, int]:
        """Get output statistics.

        Returns:
            Dictionary containing output statistics
        """
        return self._output_stats.copy()

    def reset_stats(self) -> None:
        """Reset output statistics."""
        self._output_stats = {
            "total_outputs": 0,
            "text_outputs": 0,
            "json_outputs": 0,
            "errors": 0,
        }

    def _validate_config(self, config: OutputConfig) -> None:
        """Validate output configuration.

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, OutputConfig):
            raise ValueError(f"Expected OutputConfig, got {type(config)}")

        if config.format not in OutputFormat:
            raise ValueError(f"Invalid output format: {config.format}")

    def _get_formatter(
        self,
        data: Any,
        format_type: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get the appropriate formatter for data and format.

        Args:
            data: The data to format
            format_type: The desired output format

        Returns:
            Formatter instance or None if not found
        """
        try:
            # Try to get formatter by data type
            formatter = self._formatter_registry.get_formatter(type(data), format_type)
            if formatter is not None:
                return formatter

            # Try to get formatter by validation
            for registered_formatter in self._formatter_registry.get_all_formatters():
                if (
                    hasattr(registered_formatter, "validate_data")
                    and registered_formatter.validate_data(data)
                    and registered_formatter.supports_format(format_type)
                ):
                    return registered_formatter

            return None

        except Exception as e:
            if self._enable_logging and self._logger:
                self._logger.error(
                    f"Error getting formatter for {type(data)} and {format_type}: {e}"
                )
            return None

    def _update_stats(self, format_type: OutputFormat) -> None:
        """Update output statistics.

        Args:
            format_type: The format that was used
        """
        self._output_stats["total_outputs"] += 1

        if format_type == OutputFormat.TEXT:
            self._output_stats["text_outputs"] += 1
        elif format_type == OutputFormat.JSON:
            self._output_stats["json_outputs"] += 1

    def _handle_display_error(
        self,
        error: Exception,
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Handle errors that occur during display operations.

        Args:
            error: The error that occurred
            config: The output configuration that was being used
            ctx: Click context for console configuration
        """
        self._output_stats["errors"] += 1

        if self._enable_logging and self._logger:
            self._logger.error(f"Display error: {error}")

        # Fallback to basic error display
        try:
            console = self._console_manager.get_console(ctx)
            console.print(f"[red]Error displaying output: {error}[/red]")
        except Exception as fallback_error:
            if self._enable_logging and self._logger:
                self._logger.error(f"Fallback display also failed: {fallback_error}")


class OutputManagerFactory:
    """Factory for creating OutputManager instances with proper dependency injection."""

    @staticmethod
    def create_output_manager(
        console_manager: Optional[ConsoleManager] = None,
        formatter_registry: Optional[FormatterRegistry] = None,
        enable_logging: bool = True,
    ) -> OutputManager:
        """Create an OutputManager instance.

        Args:
            console_manager: Console manager instance
            formatter_registry: Formatter registry instance
            enable_logging: Whether to enable logging

        Returns:
            Configured OutputManager instance
        """
        if console_manager is None:
            from .console_manager import ConsoleManagerFactory

            console_manager = ConsoleManagerFactory.create_default_manager(
                enable_logging=enable_logging
            )

        if formatter_registry is None:
            formatter_registry = get_formatter_registry()

        return OutputManager(
            console_manager=console_manager,
            formatter_registry=formatter_registry,
            enable_logging=enable_logging,
        )


# Global output manager instance
_global_output_manager: Optional[OutputManager] = None


def get_output_manager() -> OutputManager:
    """Get the global output manager instance.

    Returns:
        Global OutputManager instance
    """
    global _global_output_manager
    if _global_output_manager is None:
        _global_output_manager = OutputManagerFactory.create_output_manager()
    return _global_output_manager
