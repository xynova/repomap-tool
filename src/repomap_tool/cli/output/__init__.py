"""
Output formatting and display utilities for RepoMap-Tool CLI.

This package contains the unified output format system, formatters, and display utilities.
"""

from .console_manager import (
    ConsoleManagerProtocol,
    DefaultConsoleManager,
    ConsoleManagerFactory,
)
from repomap_tool.models import OutputFormat, OutputConfig, AnalysisFormat
from .manager import OutputManager, get_output_manager
from repomap_tool.protocols import OutputManagerProtocol
from .protocols import (
    BaseFormatter,
    DataFormatter,
    FormatterProtocol,
)
from .standard_formatters import (
    DictFormatter,
    ListFormatter,
    ProjectInfoFormatter,
    StringFormatter,
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
from .templates.engine import TemplateEngine
from .templates.registry import TemplateRegistryProtocol
from .templates.config import TemplateConfig

__all__ = [
    "OutputManager",
    "get_output_manager",
    "OutputFormat",
    "OutputConfig",
    "AnalysisFormat",
    "BaseFormatter",
    "DataFormatter",
    "FormatterProtocol",
    "DictFormatter",
    "ListFormatter",
    "ProjectInfoFormatter",
    "StringFormatter",
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
    "ConsoleManagerProtocol",
    "DefaultConsoleManager",
    "ConsoleManagerFactory",
    "OutputManagerProtocol",
    "TemplateEngine",
    "TemplateRegistryProtocol",
    "TemplateConfig",
]
