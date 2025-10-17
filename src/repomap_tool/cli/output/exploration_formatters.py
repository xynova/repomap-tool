"""
Formatters for Exploration ViewModels.

This module provides formatters for exploration-related ViewModels,
following proper MVC architecture patterns and AI optimization principles.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, List, Optional

import click

from .protocols import DataFormatter
from .formats import OutputFormat, OutputConfig
from .template_formatter import TemplateBasedFormatter
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

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter.

        Args:
            template_engine: Template engine for rendering
            template_registry: Template registry for rendering
            console_manager: Console manager for rendering
        """
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the given output format.

        Args:
            output_format: Output format to check

        Returns:
            True if format is supported
        """
        return output_format in [OutputFormat.TEXT, OutputFormat.JSON]

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported output formats
        """
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
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreeClusterViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "tree_id": data.tree_id,
                "context_name": data.context_name,
                "confidence": data.confidence,
                "entrypoints": data.entrypoints,
                "total_nodes": data.total_nodes,
                "max_depth": data.max_depth,
                "root_file": data.root_file,
                "description": data.description,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreeClusterViewModel."""
        return "tree_cluster"

    def _format_text(
        self,
        data: TreeClusterViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class TreeFocusViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeFocusViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format TreeFocusViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreeFocusViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "tree_id": data.tree_id,
                "context_name": data.context_name,
                "current_focus": data.current_focus,
                "tree_structure": data.tree_structure,
                "expanded_areas": data.expanded_areas,
                "pruned_areas": data.pruned_areas,
                "total_nodes": data.total_nodes,
                "max_depth": data.max_depth,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreeFocusViewModel."""
        return "tree_focus"

    def _format_text(
        self,
        data: TreeFocusViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class TreeExpansionViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeExpansionViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format TreeExpansionViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreeExpansionViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "tree_id": data.tree_id,
                "expanded_area": data.expanded_area,
                "new_nodes": [
                    {
                        "name": node.name,
                        "file_path": node.file_path,
                        "line_number": node.line_number,
                        "symbol_type": node.symbol_type,
                    }
                    for node in data.new_nodes
                ],
                "total_nodes": data.total_nodes,
                "expansion_depth": data.expansion_depth,
                "confidence_score": data.confidence_score,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreeExpansionViewModel."""
        return "tree_expansion"

    def _format_text(
        self,
        data: TreeExpansionViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class TreePruningViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreePruningViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format TreePruningViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreePruningViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "tree_id": data.tree_id,
                "pruned_area": data.pruned_area,
                "removed_nodes": data.removed_nodes,
                "remaining_nodes": data.remaining_nodes,
                "pruning_reason": data.pruning_reason,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreePruningViewModel."""
        return "tree_pruning"

    def _format_text(
        self,
        data: TreePruningViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class TreeMappingViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeMappingViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format TreeMappingViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreeMappingViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "tree_id": data.tree_id,
                "tree_structure": data.tree_structure,
                "total_nodes": data.total_nodes,
                "max_depth": data.max_depth,
                "include_code": data.include_code,
                "code_snippets": data.code_snippets,
                "token_count": data.token_count,
                "max_tokens": data.max_tokens,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreeMappingViewModel."""
        return "tree_mapping"

    def _format_text(
        self,
        data: TreeMappingViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class TreeListingViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for TreeListingViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format TreeListingViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: TreeListingViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "session_id": data.session_id,
                "trees": [
                    {
                        "tree_id": tree.tree_id,
                        "context_name": tree.context_name,
                        "confidence": tree.confidence,
                    }
                    for tree in data.trees
                ],
                "total_trees": data.total_trees,
                "current_focus": data.current_focus,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for TreeListingViewModel."""
        return "tree_listing"

    def _format_text(
        self,
        data: TreeListingViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class SessionStatusViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for SessionStatusViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format SessionStatusViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: SessionStatusViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "session_id": data.session_id,
                "project_path": data.project_path,
                "total_trees": data.total_trees,
                "current_focus": data.current_focus,
                "created_at": data.created_at,
                "last_activity": data.last_activity,
                "session_stats": data.session_stats,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for SessionStatusViewModel."""
        return "session_status"

    def _format_text(
        self,
        data: SessionStatusViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))


class ExplorationViewModelFormatter(TemplateBasedFormatter, DataFormatter):
    """Formatter for ExplorationViewModel objects."""

    def __init__(self, template_engine: Optional[Any] = None,
                 template_registry: Optional[Any] = None,
                 console_manager: Optional[Any] = None):
        """Initialize the formatter."""
        super().__init__(template_engine=template_engine, template_registry=template_registry, console_manager=console_manager)

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
        """Format ExplorationViewModel data."""
        if output_format == OutputFormat.JSON:
            return self._format_json(data)
        elif output_format == OutputFormat.TEXT:
            return self._format_text(data, ctx, config)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

    def _format_json(self, data: ExplorationViewModel) -> str:
        """Format as JSON."""
        import json

        return json.dumps(
            {
                "session_id": data.session_id,
                "project_path": data.project_path,
                "intent": data.intent,
                "trees": [
                    {
                        "tree_id": tree.tree_id,
                        "context_name": tree.context_name,
                        "confidence": tree.confidence,
                    }
                    for tree in data.trees
                ],
                "total_trees": data.total_trees,
                "confidence_scores": data.confidence_scores,
                "token_count": data.token_count,
                "max_tokens": data.max_tokens,
                "compression_level": data.compression_level,
            },
            indent=2,
        )

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name for ExplorationViewModel."""
        return "exploration"

    def _format_text(
        self,
        data: ExplorationViewModel,
        ctx: Optional[click.Context] = None,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Format as text using template."""
        template_name = self._get_template_name(data)
        if template_name:
            return self.render_template(template_name, data, config)
        return self._format_fallback(data, self._create_template_config(config))
