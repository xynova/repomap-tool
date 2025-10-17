"""
Standard formatter implementations for RepoMap-Tool CLI.

This module provides concrete implementations of the formatter protocols
for common data types used in the RepoMap tool.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import click
from rich.console import Console
from rich.table import Table
from rich.text import Text
from unittest.mock import Mock

from repomap_tool.core.logging_service import get_logger

from repomap_tool.models import (
    AnalysisFormat,
    ProjectInfo,
    SearchResponse,
    OutputFormat,
    OutputConfig, # Import OutputConfig
    ErrorResponse, # Import ErrorResponse
    SuccessResponse, # Import SuccessResponse
)

from repomap_tool.protocols import TemplateRegistryProtocol, FormatterProtocol, BaseFormatter, DataFormatter
from .console_manager import ConsoleManagerProtocol
from .template_formatter import TemplateBasedFormatter
from .templates.engine import TemplateEngine
from .templates.registry import DefaultTemplateRegistry # Import DefaultTemplateRegistry
from .controller_formatters import (
    CentralityViewModelFormatter,
    ImpactViewModelFormatter,
    SearchViewModelFormatter,
)

logger = get_logger(__name__)

class ProjectInfoFormatter(BaseFormatter, DataFormatter): # Inherit from BaseFormatter and DataFormatter
    """Formatter for ProjectInfo data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the ProjectInfo formatter."""
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        """Format ProjectInfo data."""
        if not isinstance(data, ProjectInfo):
            raise ValueError(f"Expected ProjectInfo, got {type(data)}")
        self.log_formatting("format_project_info", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            # Use template formatter for text output
            return self._template_formatter.format(data, output_format, config, ctx)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if format is supported."""
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get supported formats."""
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        """Validate data is ProjectInfo."""
        return isinstance(data, ProjectInfo)

    def get_data_type(self) -> Type[Any]:
        """Get data type."""
        return ProjectInfo


class DictFormatter(BaseFormatter, DataFormatter):
    """Formatter for dictionary data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the Dict formatter."""
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        """Format dictionary data."""
        if not isinstance(data, dict):
            raise ValueError(f"Expected dict, got {type(data)}")
        self.log_formatting("format_dict", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return json.dumps(data, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            # Check if this is error/success data that should use templates
            if "error" in data or "success" in data:
                return self._template_formatter.format(data, output_format, config, ctx)
            else:
                return self._template_formatter.format(data, output_format, config, ctx) # Use a generic dict template
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if format is supported."""
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get supported formats."""
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        """Validate data is dictionary."""
        return isinstance(data, dict)

    def get_data_type(self) -> Type[Any]:
        """Get data type."""
        return dict


class ListFormatter(BaseFormatter, DataFormatter):
    """Formatter for list data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the List formatter."""
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        """Format list data."""
        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data)}")
        self.log_formatting("format_list", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return json.dumps(data, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self._template_formatter.format(data, output_format, config, ctx) # Use a generic list template
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if format is supported."""
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get supported formats."""
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        """Validate data is list."""
        return isinstance(data, list)

    def get_data_type(self) -> Type[Any]:
        """Get data type."""
        return list


class StringFormatter(BaseFormatter, DataFormatter):
    """Formatter for string data."""

    def __init__(self, template_engine: Optional[TemplateEngine] = None,
                 template_registry: Optional[TemplateRegistryProtocol] = None,
                 console_manager: Optional[ConsoleManagerProtocol] = None,
                 enable_logging: bool = True) -> None:
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        # StringFormatter does not directly use template_engine or template_registry
        # but accepts them for consistency with other formatters if needed in future.
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format string data."""
        if not isinstance(data, str):
            raise ValueError(f"Expected string, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return json.dumps(data, indent=2)
        elif output_format == OutputFormat.TEXT:
            return data

        raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if formatter supports the given format."""
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported formats."""
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        """Validate that data is a string."""
        return isinstance(data, str)

    def get_data_type(self) -> Type[Any]:
        """Get data type."""
        return str


class SearchResponseFormatter(BaseFormatter, DataFormatter):
    """Formatter for SearchResponse data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        if not isinstance(data, SearchResponse):
            raise ValueError(f"Expected SearchResponse, got {type(data)}")
        self.log_formatting("format_search_response", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self._template_formatter.format(data, output_format, config, ctx)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        return isinstance(data, SearchResponse)

    def get_data_type(self) -> Type[Any]:
        return SearchResponse


class FormatterRegistry:
    """Registry for managing formatters."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: ConsoleManagerProtocol,
    ) -> None:
        """Initialize the formatter registry."""
        self._formatters: List[FormatterProtocol] = []
        self._template_engine = template_engine
        self._template_registry = template_registry
        self._console_manager = console_manager
        self.logger = logger # Assign the module-level logger
        self.logger.debug(f"FormatterRegistry initialized (id={id(self)}). TemplateRegistry id={id(template_registry)}, ConsoleManager id={id(console_manager)}")
        
        # Register all default formatters
        self._register_default_formatters()

    def _register_default_formatters(self) -> None:
        """Register all default formatters."""
        # Register ProjectInfoFormatter
        project_info_formatter = ProjectInfoFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(project_info_formatter)
        
        # Register SearchResponseFormatter
        search_response_formatter = SearchResponseFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(search_response_formatter)
        
        # Register ErrorResponseFormatter
        error_response_formatter = ErrorResponseFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(error_response_formatter)
        
        # Register SuccessResponseFormatter
        success_response_formatter = SuccessResponseFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(success_response_formatter)
        
        # Register DictFormatter
        dict_formatter = DictFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(dict_formatter)
        
        # Register ListFormatter
        list_formatter = ListFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(list_formatter)
        
        # Register StringFormatter
        string_formatter = StringFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(string_formatter)
        
        # Register SearchViewModelFormatter
        search_view_model_formatter = SearchViewModelFormatter(
            template_engine=self._template_engine,
            template_registry=self._template_registry,
            console_manager=self._console_manager,
        )
        self.register_formatter(search_view_model_formatter)

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter."""
        self.logger.debug(f"FormatterRegistry (id={id(self)}): Attempting to register formatter: {type(formatter).__name__} (id={id(formatter)}) for data_type: {data_type}")
        self._formatters.append(formatter)

        # Use formatter's own get_data_type if not explicitly provided
        if data_type is None and hasattr(formatter, "get_data_type"):
            data_type = formatter.get_data_type()
            self.logger.debug(f"FormatterRegistry (id={id(self)}): Inferred data_type for registration: {data_type}")

        if data_type:
            # The original code had a _type_formatters dictionary, but it was not used in get_formatter.
            # The new code removes _type_formatters and its lookup.
            # So, we just register the formatter directly.
            self.logger.debug(f"FormatterRegistry (id={id(self)}): Registered formatter {type(formatter).__name__} (id={id(formatter)}) for type {data_type}. Total registered: {len(self._formatters)}")
        else:
            self.logger.warning(f"FormatterRegistry (id={id(self)}): Formatter {type(formatter).__name__} (id={id(formatter)}) registered without a specific data_type.")


    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format."""
        self.logger.debug(f"FormatterRegistry (id={id(self)}): Searching for formatter for data_type: {data_type}, format: {output_format}")
        
        # Iterate through all registered formatters
        for formatter in self._formatters:
            formatter_data_type = None
            if hasattr(formatter, "get_data_type"):
                formatter_data_type = formatter.get_data_type()
            
            is_sub = issubclass(data_type, formatter_data_type) if formatter_data_type else False
            supports_fmt = formatter.supports_format(output_format)
            self.logger.debug(
                f"FormatterRegistry (id={id(self)}): Checking formatter {type(formatter).__name__} (id={id(formatter)}). "
                f"Formatter's data_type: {formatter_data_type}, Target data_type: {data_type}. "
                f"issubclass: {is_sub}, supports_format: {supports_fmt}"
            )

            if (
                formatter_data_type is not None
                and is_sub
                and supports_fmt
            ):
                self.logger.debug(f"FormatterRegistry (id={id(self)}): Found matching formatter: {type(formatter).__name__} (id={id(formatter)})")
                return formatter

        self.logger.debug(f"FormatterRegistry (id={id(self)}): No formatter found for data type {data_type} and format {output_format}")
        return None

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters."""
        self.logger.debug(f"FormatterRegistry (id={id(self)}): get_all_formatters called. Total registered: {len(self._formatters)}")
        return self._formatters.copy()


# Global formatter registry
# _global_formatter_registry: Optional[FormatterRegistry] = None


# def get_formatter_registry() -> FormatterRegistry:
#     """Get the global formatter registry.
#
#     This function should only be used in scenarios where the DI container
#     cannot be directly accessed (e.g., global Click contexts for utilities).
#     For most services, inject FormatterRegistry via the DI container.
#
#     Returns:
#         Global FormatterRegistry instance
#
#     Raises:
#         RuntimeError: If the DI container is not yet initialized or
#                       FormatterRegistry cannot be resolved.
#     """
#     global _global_formatter_registry
#     if _global_formatter_registry is None:
#         logger = get_logger(__name__)
#         logger.debug("Initializing global FormatterRegistry instance.")
#
#         # Attempt to get container from click.Context if available
#         # This ensures that if we're in a Click context that has a container, we use it.
#         try:
#             import click
#             ctx = click.get_current_context(silent=True)
#             if ctx and ctx.obj and "container" in ctx.obj:
#                 logger.debug("Retrieving container from click.Context.")
#                 container = ctx.obj["container"]
#                 _global_formatter_registry = container.formatter_registry()
#             else:
#                 # Fallback: if no container in context, try to create a dummy one
#                 # This path is generally for tests or very early initialization outside CLI
#                 logger.debug("No container found in click.Context. Attempting to create a dummy container for formatter registry.")
#                 from repomap_tool.core.container import create_container
#                 from repomap_tool.models import RepoMapConfig
#                 dummy_config = RepoMapConfig(project_root="/tmp", cache_dir="/tmp")
#                 container = create_container(dummy_config)
#                 _global_formatter_registry = container.formatter_registry()
#
#         except Exception as e:
#             logger.error(f"Failed to initialize global FormatterRegistry: {e}")
#             raise RuntimeError("Failed to initialize global FormatterRegistry.") from e
#
#     return _global_formatter_registry


class ErrorResponseFormatter(BaseFormatter, DataFormatter):
    """Formatter for ErrorResponse data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        if not isinstance(data, ErrorResponse):
            raise ValueError(f"Expected ErrorResponse, got {type(data)}")
        self.log_formatting("format_error_response", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self._template_formatter.format(data, output_format, config, ctx)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        return isinstance(data, ErrorResponse)

    def get_data_type(self) -> Type[Any]:
        return ErrorResponse


class SuccessResponseFormatter(BaseFormatter, DataFormatter):
    """Formatter for SuccessResponse data."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol] = None,
        enable_logging: bool = True,
    ) -> None:
        super().__init__(console_manager=console_manager,
                         template_engine=template_engine,
                         template_registry=template_registry,
                         enable_logging=enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
            enable_logging=enable_logging,
        )

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        if not isinstance(data, SuccessResponse):
            raise ValueError(f"Expected SuccessResponse, got {type(data)}")
        self.log_formatting("format_success_response", format=str(output_format))

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self._template_formatter.format(data, output_format, config, ctx)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def supports_format(self, output_format: OutputFormat) -> bool:
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        return self._supported_formats.copy()

    def validate_data(self, data: Any) -> bool:
        return isinstance(data, SuccessResponse)

    def get_data_type(self) -> Type[Any]:
        return SuccessResponse
