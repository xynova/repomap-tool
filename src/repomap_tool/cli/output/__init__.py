"""
Output formatting and display utilities for RepoMap-Tool CLI.

This package contains the unified output format system, formatters, and display utilities.
"""

from .formats import (
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
from .formatters import (
    display_project_info,
    display_search_results,
    display_dependency_results,
    display_cycles_results,
)

__all__ = [
    # Format system
    "OutputFormat",
    "OutputConfig",
    "FormatValidationError",
    "FormatConverter",
    "FormatRegistry",
    "format_registry",
    "get_output_config",
    "validate_output_format",
    "get_supported_formats",
    "is_valid_format",
    # Legacy formatters
    "display_project_info",
    "display_search_results",
    "display_dependency_results",
    "display_cycles_results",
]
