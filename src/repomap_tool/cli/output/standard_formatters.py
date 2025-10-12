"""
Standard formatter implementations for RepoMap-Tool CLI.

This module provides concrete implementations of the formatter protocols
for common data types used in the RepoMap tool.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from tabulate import tabulate

from .protocols import BaseFormatter, DataFormatter, FormatterProtocol
from .formats import OutputFormat, OutputConfig
from .console_manager import ConsoleManager
from .template_formatter import TemplateBasedFormatter
from .controller_formatters import (
    CentralityViewModelFormatter,
    ImpactViewModelFormatter,
)

from ...models import ProjectInfo, SearchResponse


class ProjectInfoFormatter(BaseFormatter, DataFormatter):
    """Formatter for ProjectInfo data."""

    def __init__(
        self,
        console_manager: Optional[ConsoleManager] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the ProjectInfo formatter."""
        super().__init__(console_manager, enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
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

    def _format_to_text(
        self,
        project_info: ProjectInfo,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format ProjectInfo to text format."""
        use_emojis = True
        if config and config.template_config:
            use_emojis = not config.template_config.get("no_emojis", False)

        lines = []

        # Title
        title = (
            "🧠 LLM-Optimized Project Analysis" if use_emojis else "Project Analysis"
        )
        lines.append(title)
        lines.append("=" * 60)
        lines.append("")

        # Summary section
        summary_icon = "📊" if use_emojis else ""
        lines.append(f"{summary_icon} SUMMARY:")
        lines.append(f"├── Project Root: {project_info.project_root}")
        lines.append(f"├── Total Files: {project_info.total_files}")
        lines.append(f"├── Total Identifiers: {project_info.total_identifiers}")
        lines.append(f"└── Analysis Time: {project_info.analysis_time_ms:.2f}ms")
        lines.append("")

        # File types breakdown
        if project_info.file_types:
            files_icon = "📁" if use_emojis else ""
            lines.append(f"{files_icon} FILE TYPES:")
            for ext, count in project_info.file_types.items():
                lines.append(f"├── {ext}: {count} files")
            lines.append("")

        # Identifier types breakdown
        if project_info.identifier_types:
            id_icon = "🏷️" if use_emojis else ""
            lines.append(f"{id_icon} IDENTIFIER TYPES:")
            for id_type, count in project_info.identifier_types.items():
                lines.append(f"├── {id_type}: {count} identifiers")
            lines.append("")

        # Cache statistics
        if project_info.cache_stats:
            cache_icon = "💾" if use_emojis else ""
            lines.append(f"{cache_icon} CACHE STATISTICS:")
            for key, value in project_info.cache_stats.items():
                lines.append(f"├── {key.replace('_', ' ').title()}: {value}")
            lines.append("")

        return "\n".join(lines)

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
        console_manager: Optional[ConsoleManager] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the Dict formatter."""
        super().__init__(console_manager, enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]
        self._template_formatter = TemplateBasedFormatter(
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
                return self._format_to_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_to_text(
        self,
        data: Dict[str, Any],
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format dictionary to text format."""
        use_emojis = True
        if config and config.template_config:
            use_emojis = not config.template_config.get("no_emojis", False)

        # Check if this looks like dependency results
        if self._is_dependency_data(data):
            return self._format_dependency_data(data, use_emojis)

        # Generic dictionary formatting
        lines = []
        for key, value in data.items():
            formatted_key = key.replace("_", " ").title()
            lines.append(f"{formatted_key}: {value}")

        return "\n".join(lines)

    def _is_dependency_data(self, data: Dict[str, Any]) -> bool:
        """Check if data looks like dependency analysis results."""
        dependency_keys = {"total_files", "total_dependencies", "circular_dependencies"}
        return any(key in data for key in dependency_keys)

    def _format_dependency_data(self, data: Dict[str, Any], use_emojis: bool) -> str:
        """Format dependency analysis data."""
        table_data = [
            ["Total Files", str(data.get("total_files", 0))],
            ["Total Dependencies", str(data.get("total_dependencies", 0))],
            ["Circular Dependencies", str(data.get("circular_dependencies", 0))],
        ]

        headers = ["Metric", "Value"]
        table_str = tabulate(table_data, headers=headers, tablefmt="grid")

        lines = []
        deps_icon = "📊" if use_emojis else ""
        lines.append(f"{deps_icon} Dependency Analysis Results")
        lines.append(table_str)

        return "\n".join(lines)

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
        console_manager: Optional[ConsoleManager] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the List formatter."""
        super().__init__(console_manager, enable_logging)
        self._supported_formats = [OutputFormat.TEXT, OutputFormat.JSON]

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
            return self._format_to_text(data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_to_text(
        self,
        data: List[Any],
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format list to text format."""
        use_emojis = True
        if config and config.template_config:
            use_emojis = not config.template_config.get("no_emojis", False)

        # Check if this looks like cycle data
        if self._is_cycle_data(data):
            return self._format_cycle_data(data, use_emojis)

        # Generic list formatting
        if not data:
            empty_icon = "📋" if use_emojis else ""
            return f"{empty_icon} Empty list"

        lines = []
        for i, item in enumerate(data, 1):
            lines.append(f"{i}. {item}")

        return "\n".join(lines)

    def _is_cycle_data(self, data: List[Any]) -> bool:
        """Check if data looks like cycle detection results."""
        # Empty list is valid cycle data (no cycles found)
        if not data:
            return True
        return all(isinstance(item, list) and len(item) > 0 for item in data)

    def _format_cycle_data(self, data: List[List[str]], use_emojis: bool) -> str:
        """Format cycle detection data."""
        if not data:
            no_cycles_icon = "🔄" if use_emojis else ""
            return f"{no_cycles_icon} No circular dependencies found! 🎉"

        lines = []
        cycle_icon = "🔄" if use_emojis else ""
        lines.append(f"{cycle_icon} Circular Dependencies ({len(data)} found)")
        lines.append("")

        for i, cycle in enumerate(data, 1):
            lines.append(f"Cycle #{i}:")

            # Format each file in the cycle with proper indentation
            for j, file_path in enumerate(cycle):
                if j == 0:
                    # First file
                    lines.append(f"  {file_path}")
                else:
                    # Subsequent files with arrow and indentation
                    lines.append(f"    → {file_path}")

            # Close the cycle by showing the first file again
            lines.append(f"    → {cycle[0]}")

            # Add spacing between cycles (except for the last one)
            if i < len(data):
                lines.append("")

        return "\n".join(lines)

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

    def __init__(self, console_manager: Optional[ConsoleManager] = None) -> None:
        super().__init__(console_manager)
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


class FormatterRegistry:
    """Registry for managing formatters."""

    def __init__(self) -> None:
        """Initialize the formatter registry."""
        self._formatters: List[FormatterProtocol] = []
        self._type_formatters: Dict[Type[Any], List[FormatterProtocol]] = {}

    def register_formatter(
        self,
        formatter: FormatterProtocol,
        data_type: Optional[Type[Any]] = None,
    ) -> None:
        """Register a formatter."""
        self._formatters.append(formatter)

        if data_type:
            if data_type not in self._type_formatters:
                self._type_formatters[data_type] = []
            self._type_formatters[data_type].append(formatter)

    def get_formatter(
        self,
        data_type: Type[Any],
        output_format: OutputFormat,
    ) -> Optional[FormatterProtocol]:
        """Get formatter for data type and format."""
        # Try specific type formatters first
        if data_type in self._type_formatters:
            for formatter in self._type_formatters[data_type]:
                if formatter.supports_format(output_format):
                    return formatter

        # Try all formatters
        for formatter in self._formatters:
            if (
                hasattr(formatter, "validate_data")
                and hasattr(formatter, "supports_format")
                and formatter.supports_format(output_format)
            ):
                return formatter

        return None

    def get_all_formatters(self) -> List[FormatterProtocol]:
        """Get all registered formatters."""
        return self._formatters.copy()

    def unregister_formatter(
        self,
        formatter: FormatterProtocol,
    ) -> None:
        """Unregister a formatter."""
        if formatter in self._formatters:
            self._formatters.remove(formatter)

        # Remove from type-specific registrations
        for formatters in self._type_formatters.values():
            if formatter in formatters:
                formatters.remove(formatter)


# Global formatter registry
_global_formatter_registry: Optional[FormatterRegistry] = None


def get_formatter_registry() -> FormatterRegistry:
    """Get the global formatter registry."""
    global _global_formatter_registry
    if _global_formatter_registry is None:
        _global_formatter_registry = FormatterRegistry()
        _register_default_formatters(_global_formatter_registry)
    return _global_formatter_registry


def _register_default_formatters(registry: FormatterRegistry) -> None:
    """Register default formatters."""
    # Register standard formatters
    registry.register_formatter(ProjectInfoFormatter(), ProjectInfo)
    registry.register_formatter(DictFormatter(), dict)
    registry.register_formatter(ListFormatter(), list)
    registry.register_formatter(StringFormatter(), str)

    # Register controller ViewModel formatters
    from ..controllers.view_models import CentralityViewModel, ImpactViewModel

    registry.register_formatter(CentralityViewModelFormatter(), CentralityViewModel)
    registry.register_formatter(ImpactViewModelFormatter(), ImpactViewModel)

    # Register SearchViewModel formatter
    from .controller_formatters import SearchViewModelFormatter
    from ..controllers.view_models import SearchViewModel

    registry.register_formatter(SearchViewModelFormatter(), SearchViewModel)

    # Register exploration ViewModel formatters
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
    from ..controllers.view_models import (
        TreeClusterViewModel,
        TreeFocusViewModel,
        TreeExpansionViewModel,
        TreePruningViewModel,
        TreeMappingViewModel,
        TreeListingViewModel,
        SessionStatusViewModel,
        ExplorationViewModel,
    )

    registry.register_formatter(TreeClusterViewModelFormatter(), TreeClusterViewModel)
    registry.register_formatter(TreeFocusViewModelFormatter(), TreeFocusViewModel)
    registry.register_formatter(
        TreeExpansionViewModelFormatter(), TreeExpansionViewModel
    )
    registry.register_formatter(TreePruningViewModelFormatter(), TreePruningViewModel)
    registry.register_formatter(TreeMappingViewModelFormatter(), TreeMappingViewModel)
    registry.register_formatter(TreeListingViewModelFormatter(), TreeListingViewModel)
    registry.register_formatter(
        SessionStatusViewModelFormatter(), SessionStatusViewModel
    )
    registry.register_formatter(ExplorationViewModelFormatter(), ExplorationViewModel)
