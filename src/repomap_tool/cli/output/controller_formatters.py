"""
Formatters for Controller ViewModels.

This module provides formatters for the ViewModels returned by Controllers,
following proper MVC architecture patterns.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, List, Optional, Type

import click

from repomap_tool.protocols import (
    DataFormatter,
    TemplateRegistryProtocol,
    ConsoleManagerProtocol,
)
from .formats import OutputConfig, OutputFormat
from .template_formatter import TemplateBasedFormatter
from .templates.engine import TemplateEngine
from ..controllers.view_models import (
    SearchViewModel,
    CentralityViewModel,
    ImpactViewModel,
    TreeClusterViewModel,
    TreeFocusViewModel,
    TreeExpansionViewModel,
    TreePruningViewModel,
    TreeMappingViewModel,
    TreeListingViewModel,
    SessionStatusViewModel,
    ExplorationViewModel,
    ProjectAnalysisViewModel,
    FileDensityViewModel,
    PackageDensityViewModel,
    DensityAnalysisViewModel,
)


logger = get_logger(__name__)


class CentralityViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for CentralityViewModel objects."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: ConsoleManagerProtocol,
    ) -> None:
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
            template_registry: Template registry for rendering
            console_manager: Console manager for rendering
        """
        super().__init__(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
        )

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return CentralityViewModel

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format CentralityViewModel data.

        Args:
            data: CentralityViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, CentralityViewModel):
            raise ValueError(f"Expected CentralityViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("centrality_analysis", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class ImpactViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for ImpactViewModel objects."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: ConsoleManagerProtocol,
    ) -> None:
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
            template_registry: Template registry for rendering
            console_manager: Console manager for rendering
        """
        super().__init__(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
        )

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return ImpactViewModel

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format ImpactViewModel data.

        Args:
            data: ImpactViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, ImpactViewModel):
            raise ValueError(f"Expected ImpactViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("impact_analysis", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class SearchViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for SearchViewModel objects."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: ConsoleManagerProtocol,
    ) -> None:
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
            template_registry: Template registry for rendering
            console_manager: Console manager for rendering
        """
        super().__init__(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
        )

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return SearchViewModel

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format SearchViewModel data.

        Args:
            data: SearchViewModel to format
            output_format: Output format (TEXT or JSON)
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, SearchViewModel):
            raise ValueError(f"Expected SearchViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            return data.model_dump_json(indent=2)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("search_results", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class DensityAnalysisFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for DensityAnalysisViewModel."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: ConsoleManagerProtocol,
    ) -> None:
        """Initialize the formatter."""
        super().__init__(
            template_engine=template_engine,
            template_registry=template_registry,
            console_manager=console_manager,
        )

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return DensityAnalysisViewModel

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format."""
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats."""
        return [OutputFormat.TEXT, OutputFormat.JSON]

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> str:
        """Format DensityAnalysisViewModel data."""
        if not isinstance(data, DensityAnalysisViewModel):
            raise ValueError(f"Expected DensityAnalysisViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            import json
            from dataclasses import asdict

            return json.dumps(asdict(data), indent=2)  # Use asdict for dataclass
        elif output_format == OutputFormat.TEXT:
            return self.render_template("density_analysis", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
