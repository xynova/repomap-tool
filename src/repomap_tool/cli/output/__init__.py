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

# Legacy formatters removed - all output now handled by OutputManager
from .console_manager import (
    ConsoleManager,
    DefaultConsoleManager,
    ConsoleManagerFactory,
    get_console_manager,
    set_console_manager,
    get_managed_console,
    configure_managed_console,
    get_console_from_context,
    log_console_operation,
)
from .protocols import (
    FormatterProtocol,
    BaseFormatter,
    DataFormatter,
    TemplateFormatter,
    FormatterRegistry as FormatterRegistryProtocol,
    FormatterFactory,
    OutputHandler,
    validate_formatter,
    get_formatter_info,
    create_formatter_config,
)
from .standard_formatters import (
    ProjectInfoFormatter,
    SearchResponseFormatter,
    DictFormatter,
    ListFormatter,
    StringFormatter,
    FormatterRegistry,
    get_formatter_registry,
)
from .template_formatter import TemplateBasedFormatter
from .manager import OutputManager, OutputManagerFactory, get_output_manager
from .templates import (
    TemplateEngine,
    TemplateEngineFactory,
    TemplateRegistry,
    get_template_registry,
    TemplateConfig,
    TemplateOptions,
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
    # Legacy formatters removed - all output now handled by OutputManager
    # Console management
    "ConsoleManager",
    "DefaultConsoleManager",
    "ConsoleManagerFactory",
    "get_console_manager",
    "set_console_manager",
    "get_managed_console",
    "configure_managed_console",
    "get_console_from_context",
    "log_console_operation",
    # Formatter protocols
    "FormatterProtocol",
    "BaseFormatter",
    "DataFormatter",
    "TemplateFormatter",
    "TemplateBasedFormatter",
    "FormatterRegistryProtocol",
    "FormatterFactory",
    "OutputHandler",
    "validate_formatter",
    "get_formatter_info",
    "create_formatter_config",
    # Standard formatters
    "ProjectInfoFormatter",
    "SearchResponseFormatter",
    "DictFormatter",
    "ListFormatter",
    "StringFormatter",
    "FormatterRegistry",
    "get_formatter_registry",
    # Template system
    "TemplateEngine",
    "TemplateEngineFactory",
    "TemplateRegistry",
    "get_template_registry",
    "TemplateConfig",
    "TemplateOptions",
    # Output manager
    "OutputManager",
    "OutputManagerFactory",
    "get_output_manager",
]
