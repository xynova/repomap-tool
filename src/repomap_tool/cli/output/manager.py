"""
Centralized output manager for RepoMap-Tool CLI.

This module provides the main OutputManager class that serves as the central hub
for all output operations, integrating console management, formatter registry,
and output configuration.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, Dict, List, Optional, Type, Union

import click
from rich.console import Console
from rich.text import Text

from repomap_tool.models import (
    OutputFormat,
    ErrorResponse,
    SuccessResponse,
    OutputConfig,
    AnalysisFormat,
)  # Import OutputConfig and AnalysisFormat
from repomap_tool.protocols import (
    OutputManagerProtocol,
    TemplateRegistryProtocol,
)  # Import TemplateRegistryProtocol

from .console_manager import ConsoleManagerProtocol
from .standard_formatters import FormatterRegistry
from .templates.config import TemplateConfig
from .templates.engine import TemplateEngine
from .templates.registry import TemplateRegistryProtocol  # Use the protocol here

logger = get_logger(__name__)


class OutputManager(OutputManagerProtocol):
    """Central hub for all CLI output operations."""

    def __init__(
        self,
        console_manager: ConsoleManagerProtocol,
        formatter_registry: FormatterRegistry,
        template_engine: TemplateEngine,  # Add template_engine
        template_registry: TemplateRegistryProtocol,  # Add template_registry
        enable_logging: bool = True,
    ) -> None:
        """Initialize the OutputManager."""
        if console_manager is None:
            raise ValueError("ConsoleManager must be injected")
        if formatter_registry is None:
            raise ValueError("FormatterRegistry must be injected")
        if template_engine is None:  # Validate template_engine
            raise ValueError("TemplateEngine must be injected")
        if template_registry is None:  # Validate template_registry
            raise ValueError("TemplateRegistry must be injected")

        self.console_manager = console_manager
        self.formatter_registry = formatter_registry
        self.template_engine = template_engine
        self.template_registry = template_registry
        self.logger = get_logger(__name__)
        self.enable_logging = enable_logging
        if self.enable_logging:
            self.logger.debug(
                f"OutputManager initialized (id={id(self)}). FormatterRegistry id={id(self.formatter_registry)}, registered formatters: {len(self.formatter_registry.get_all_formatters())}"
            )

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

            self.logger.debug(
                f"OutputManager (id={id(self)}): Calling FormatterRegistry.get_formatter for data type {type(data)} and format {config.format}"
            )
            # Get the appropriate formatter
            formatter = self._get_formatter(data, config.format)
            self.logger.debug(
                f"OutputManager (id={id(self)}): FormatterRegistry.get_formatter returned: {type(formatter).__name__ if formatter else 'None'} (id={id(formatter) if formatter else 'None'})"
            )
            if formatter is None:
                raise ValueError(
                    f"No formatter found for data type {type(data)} and format {config.format}"
                )

            # Format the data
            formatted_output = formatter.format(data, config.format, config, ctx)
            if formatted_output is None:
                if self.logger:
                    self.logger.warning(
                        f"Formatter returned None for {type(data)} with format {config.format}"
                    )
                return

            # Get console and display the output
            console = self.console_manager.get_console(ctx)
            console.print(formatted_output)

            # Update statistics
            self._update_stats(config.format)

            if self.enable_logging and self.logger:
                self.logger.debug(
                    f"Displayed {type(data).__name__} in {config.format} format"
                )

        except Exception as e:
            self._handle_display_error(e, config, ctx)

    def display_error(
        self,
        error: Union[Exception, Any],
        config: OutputConfig,
        ctx: Optional[click.Context] = None,
        details: Optional[
            Dict[str, Any]
        ] = None,  # Add a details parameter for structured error info
    ) -> None:
        """Display an error message using the specified output configuration.

        Args:
            error: The exception to display
            config: Output configuration specifying format and options
            ctx: Click context for console configuration
        """
        try:
            # Create an ErrorResponse object with explicit error and error_type
            error_response = ErrorResponse(
                error=str(error),
                error_type=type(error).__name__,
                details=details,  # Pass the new details parameter
            )

            # Display the ErrorResponse object, which should be handled by ErrorResponseFormatter
            self.display(error_response, config, ctx)

            # Update error statistics
            self._output_stats["errors"] += 1

            if self.enable_logging and self.logger:
                self.logger.error(f"Displayed error: {type(error).__name__}: {error}")

        except Exception as display_error:
            # Fallback to basic error display
            console = self.console_manager.get_console(ctx)
            console.print(f"[red]Error: {error}[/red]")
            if self.enable_logging and self.logger:
                self.logger.error(f"Failed to display error properly: {display_error}")

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

            # Create a SuccessResponse object
            success_response = SuccessResponse(message=message, status_code=200)

            # Display the SuccessResponse object, which should be handled by SuccessResponseFormatter
            self.display(success_response, config, ctx)

            if self.enable_logging and self.logger:
                self.logger.debug(f"Displayed success message: {message}")

        except Exception as e:
            # Fallback to basic success display
            console = self.console_manager.get_console(ctx)
            console.print(f"[green]✅ {message}[/green]")
            if self.enable_logging and self.logger:
                self.logger.error(f"Failed to display success message properly: {e}")

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
            console = self.console_manager.get_console(ctx)

            if progress is not None:
                # Display progress with percentage
                percentage = int(progress * 100)
                console.print(f"[blue]🔄 {message} ({percentage}%)[/blue]")
            else:
                # Display simple progress message
                console.print(f"[blue]🔄 {message}[/blue]")

            if self.enable_logging and self.logger:
                self.logger.debug(f"Displayed progress: {message} ({progress})")

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.error(f"Failed to display progress: {e}")

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a configured console instance from the console manager.

        Args:
            ctx: Click context for console configuration

        Returns:
            Configured Console instance
        """
        return self.console_manager.get_console(ctx)

    def display_response(
        self,
        response: Union[SuccessResponse, ErrorResponse],
        output_config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> None:
        """Display a success or error response.

        Args:
            response: The success or error response to display
            output_config: Optional output configuration
            ctx: Click context
        """
        if output_config is None:
            output_config = OutputConfig()

        # Use the appropriate formatter based on the response type
        if isinstance(response, SuccessResponse):
            self.display_success(response.message, output_config, ctx)
        elif isinstance(response, ErrorResponse):
            # Pass the full ErrorResponse object to the generic display method
            # This allows the ErrorResponseFormatter to be correctly invoked.
            self.display(response, output_config, ctx)
        else:
            # Fallback for unexpected response types
            self.display(response, output_config, ctx)

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
            formatter = self.formatter_registry.get_formatter(data_type, format_type)
            return formatter is not None
        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.error(
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
            if self.enable_logging and self.logger:
                self.logger.error(
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
            self.logger.debug(
                f"OutputManager (id={id(self)}): Attempting to get formatter for data type {type(data)} and format {format_type}"
            )
            # Try to get formatter by data type
            formatter_by_type = self.formatter_registry.get_formatter(
                type(data), format_type
            )
            self.logger.debug(
                f"OutputManager (id={id(self)}): Formatter by data type returned: {type(formatter_by_type).__name__ if formatter_by_type else 'None'} (id={id(formatter_by_type) if formatter_by_type else 'None'})"
            )
            if formatter_by_type is not None:
                self.logger.debug(
                    f"OutputManager (id={id(self)}): Found formatter by data type: {type(formatter_by_type).__name__} (id={id(formatter_by_type)})."
                )
                return formatter_by_type

            self.logger.debug(
                f"OutputManager (id={id(self)}): No formatter found by exact data type. Trying to get formatter by validation for {type(data)}."
            )
            # Try to get formatter by validation
            for registered_formatter in self.formatter_registry.get_all_formatters():
                self.logger.debug(
                    f"OutputManager (id={id(self)}): Checking registered formatter {type(registered_formatter).__name__} with validate_data (id={id(registered_formatter)})."
                )
                if (
                    hasattr(registered_formatter, "validate_data")
                    and registered_formatter.validate_data(data)
                    and registered_formatter.supports_format(format_type)
                ):
                    self.logger.debug(
                        f"OutputManager (id={id(self)}): Found formatter by validation: {type(registered_formatter).__name__} (id={id(registered_formatter)})."
                    )
                    return registered_formatter

            self.logger.warning(
                f"OutputManager (id={id(self)}): No formatter found for data type {type(data)} and format {format_type}"
            )
            return None

        except Exception as e:
            if self.enable_logging and self.logger:
                self.logger.error(
                    f"OutputManager (id={id(self)}): Error getting formatter for {type(data)} and {format_type}: {e}"
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

        if self.enable_logging and self.logger:
            self.logger.error(f"Display error: {error}")

        # Fallback to basic error display
        try:
            console = self.console_manager.get_console(ctx)
            console.print(f"[red]Error displaying output: {error}[/red]")
        except Exception as fallback_error:
            if self.enable_logging and self.logger:
                self.logger.error(f"Fallback display also failed: {fallback_error}")
