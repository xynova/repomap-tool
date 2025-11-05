"""
Formatters for Exploration ViewModels.

This module provides formatters for exploration-related ViewModels,
following proper MVC architecture patterns and AI optimization principles.
"""

from __future__ import annotations

from repomap_tool.core.logging_service import get_logger
from typing import Any, List, Optional, Type

import click

from repomap_tool.protocols import (
    DataFormatter,
    TemplateRegistryProtocol,
)
from .templates.engine import TemplateEngine
from .console_manager import ConsoleManagerProtocol
from .formats import OutputFormat, OutputConfig
from .template_formatter import TemplateBasedFormatter

# Removed local import of TemplateEngine - relying on TypeVar in protocols.py
# from .templates.engine import TemplateEngine
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


logger = get_logger(__name__)


class TreeClusterViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeClusterViewModel objects."""

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
        """Format TreeClusterViewModel data.

        Args:
            data: TreeClusterViewModel to format
            output_format: Desired output format
            ctx: Click context for configuration

        Returns:
            Formatted string
        """
        if not isinstance(data, TreeClusterViewModel):
            raise ValueError(f"Expected TreeClusterViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_cluster", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class TreeFocusViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeFocusViewModel objects."""

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
        """Format TreeFocusViewModel data.

        Args:
            data: TreeFocusViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, TreeFocusViewModel):
            raise ValueError(f"Expected TreeFocusViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_focus", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class TreeExpansionViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeExpansionViewModel objects."""

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
        """Format TreeExpansionViewModel data.

        Args:
            data: TreeExpansionViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, TreeExpansionViewModel):
            raise ValueError(f"Expected TreeExpansionViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_expansion", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class TreePruningViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreePruningViewModel objects."""

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
        """Format TreePruningViewModel data.

        Args:
            data: TreePruningViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, TreePruningViewModel):
            raise ValueError(f"Expected TreePruningViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_pruning", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class TreeMappingViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeMappingViewModel objects."""

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
        """Format TreeMappingViewModel data.

        Args:
            data: TreeMappingViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, TreeMappingViewModel):
            raise ValueError(f"Expected TreeMappingViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_mapping", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class TreeListingViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeListingViewModel objects."""

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
        """Format TreeListingViewModel data.

        Args:
            data: TreeListingViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, TreeListingViewModel):
            raise ValueError(f"Expected TreeListingViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("tree_listing", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class SessionStatusViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for SessionStatusViewModel objects."""

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
        """Format SessionStatusViewModel data.

        Args:
            data: SessionStatusViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, SessionStatusViewModel):
            raise ValueError(f"Expected SessionStatusViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("session_status", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")


class ExplorationViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for ExplorationViewModel objects."""

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
        """Format ExplorationViewModel data.

        Args:
            data: ExplorationViewModel to format
            output_format: Desired output format
            config: Output configuration
            ctx: Click context

        Returns:
            Formatted string
        """
        if not isinstance(data, ExplorationViewModel):
            raise ValueError(f"Expected ExplorationViewModel, got {type(data)}")

        if output_format == OutputFormat.JSON:
            # Serialize dataclass to JSON using proper method
            import json

            return json.dumps(data.__dict__, indent=2, default=str)
        elif output_format == OutputFormat.TEXT:
            return self.render_template("exploration", data, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def get_data_type(self) -> Type[Any]:
        """Get the data type this formatter handles."""
        return ExplorationViewModel
