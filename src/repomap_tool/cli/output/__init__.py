"""
Output formatting and display utilities for RepoMap-Tool CLI.

This package contains the unified output format system, formatters, and display utilities.
"""

from repomap_tool.models import OutputConfig, OutputFormat, AnalysisFormat
from repomap_tool.protocols import ConsoleManagerProtocol, FormatterRegistryProtocol, OutputManagerProtocol, TemplateRegistryProtocol # Import protocols from centralized location
from .console_manager import DefaultConsoleManager, get_console_manager, set_console_manager, get_managed_console, get_console_from_context, log_console_operation # Expose public console management functions
from .manager import OutputManager
from .standard_formatters import (
    ProjectInfoFormatter,
    DictFormatter,
    ListFormatter,
    StringFormatter,
    ErrorResponseFormatter,
    SuccessResponseFormatter,
    SearchResponseFormatter,
)
from .controller_formatters import (
    CentralityViewModelFormatter,
    ImpactViewModelFormatter,
    SearchViewModelFormatter,
    DensityAnalysisFormatter,
)
from .exploration_formatters import (
    TreeClusterViewModelFormatter,
    TreeFocusViewModelFormatter,
    TreeExpansionViewModelFormatter,
    TreePruningViewModelFormatter,
    TreeMappingViewModelFormatter,
    TreeListingViewModelFormatter,
    SessionStatusViewModelFormatter,
    ExplorationViewModelFormatter,
)
from .template_formatter import TemplateBasedFormatter
from .templates.engine import TemplateEngine
from .templates.loader import TemplateLoader, FileTemplateLoader
from .templates.registry import DefaultTemplateRegistry # Import DefaultTemplateRegistry


__all__ = [
    # Manager classes and accessors
    "OutputManager",
    "DefaultConsoleManager",
    "get_console_manager",
    "set_console_manager",
    "get_managed_console",
    "get_console_from_context",
    "log_console_operation",
    # Output formats and config
    "OutputConfig",
    "OutputFormat",
    "AnalysisFormat",
    # Formatters
    "ProjectInfoFormatter",
    "DictFormatter",
    "ListFormatter",
    "StringFormatter",
    "ErrorResponseFormatter",
    "SuccessResponseFormatter",
    "SearchResponseFormatter",
    "CentralityViewModelFormatter",
    "ImpactViewModelFormatter",
    "SearchViewModelFormatter",
    "DensityAnalysisFormatter",
    "TreeClusterViewModelFormatter",
    "TreeFocusViewModelFormatter",
    "TreeExpansionViewModelFormatter",
    "TreePruningViewModelFormatter",
    "TreeMappingViewModelFormatter",
    "TreeListingViewModelFormatter",
    "SessionStatusViewModelFormatter",
    "ExplorationViewModelFormatter",
    "TemplateBasedFormatter",
    # Templates
    "TemplateEngine",
    "TemplateLoader",
    "FileTemplateLoader",
    "DefaultTemplateRegistry", # Expose DefaultTemplateRegistry
    # Protocols
    "ConsoleManagerProtocol",
    "FormatterRegistryProtocol",
    "OutputManagerProtocol",
    "TemplateRegistryProtocol",
]
