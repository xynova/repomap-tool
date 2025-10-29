"""
Template-based formatter for RepoMap-Tool CLI.

This module provides a template-based formatter that uses the template engine
to render output using Jinja2 templates.
"""

from __future__ import annotations

import logging
from typing import Any, Optional, List, Dict

import click

from repomap_tool.models import OutputConfig, OutputFormat, AnalysisFormat
from repomap_tool.protocols import (
    TemplateRegistryProtocol,
    FormatterProtocol,
    BaseFormatter,
    ConsoleManagerProtocol,
)
from .templates.config import TemplateConfig
from .templates.engine import TemplateEngine
from repomap_tool.core.logging_service import get_logger


class TemplateBasedFormatter(BaseFormatter):
    """Base formatter that uses Jinja2 templates for rendering output."""

    def __init__(
        self,
        template_engine: TemplateEngine,
        template_registry: TemplateRegistryProtocol,
        console_manager: Optional[ConsoleManagerProtocol],
        enable_logging: bool = True,
    ) -> None:
        """Initialize the template-based formatter.

        Args:
            template_engine: The Jinja2 template engine instance.
            template_registry: The template registry for lookup.
            console_manager: Optional console manager for output.
            enable_logging: Whether to enable logging for this formatter.
        """
        super().__init__(
            console_manager=console_manager,
            template_engine=template_engine,
            template_registry=template_registry,
            enable_logging=enable_logging,
        )
        self._template_engine = template_engine
        self._template_registry = template_registry
        self._supported_formats = [OutputFormat.TEXT]
        self._template_config_class = TemplateConfig  # Default template config class

    def format(
        self,
        data: Any,
        output_format: OutputFormat,
        config: Optional[OutputConfig] = None,
        ctx: Optional[click.Context] = None,
    ) -> Optional[str]:
        """Format data using templates.

        Args:
            data: The data to format
            output_format: The target output format
            config: Optional output configuration
            ctx: Optional Click context for console access

        Returns:
            Formatted string or None if formatting should be handled by console
        """
        if not self.supports_format(output_format):
            raise ValueError(f"Unsupported format: {output_format}")

        # Determine template name based on data type
        template_name = self._get_template_name(data)
        if not template_name:
            if self._logger:
                self._logger.warning(f"No template found for data type {type(data)}")
            return None

        # Create template configuration
        template_config = self._create_template_config(config)

        try:
            # Render template
            result = self._template_engine.render_template(
                template_name, data, template_config
            )
            return result if isinstance(result, str) else None
        except Exception as e:
            if self._logger:
                self._logger.error(f"Template rendering failed: {e}")
            # Fallback to basic formatting
            return self._format_fallback(data, template_config)

    def supports_format(self, output_format: OutputFormat) -> bool:
        """Check if this formatter supports the specified format.

        Args:
            output_format: The format to check.

        Returns:
            True if the format is supported (only TEXT for templates).
        """
        return output_format in self._supported_formats

    def get_supported_formats(self) -> List[OutputFormat]:
        """Get list of supported output formats.

        Returns:
            List of supported formats
        """
        return self._supported_formats.copy()

    def load_template(
        self,
        template_name: str,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Load a template for formatting.

        Args:
            template_name: Name of the template to load
            config: Optional configuration for template loading

        Returns:
            Template content
        """
        try:
            return (
                self._template_engine._template_registry.get_template(template_name)
                or ""
            )
        except Exception:
            return ""

    def render_template(
        self,
        template_name: str,
        data: Any,
        config: Optional[OutputConfig] = None,
    ) -> str:
        """Render template with data.

        Args:
            template_name: Name of the template to render
            data: Data to render
            config: Optional template configuration

        Returns:
            Rendered content
        """
        try:
            if config is None:
                template_config = self._create_template_config(None)
            else:
                template_config = self._create_template_config(config)
            result = self._template_engine.render_template(
                template_name, data, template_config
            )
            return result if isinstance(result, str) else ""
        except Exception as e:
            if self._logger:
                self._logger.error(f"Template rendering failed: {e}")
            return str(data)

    def get_available_templates(self) -> List[str]:
        """Get list of available templates.

        Returns:
            List of template names
        """
        return self._template_engine._template_registry.list_templates()  # type: ignore[no-any-return]

    def _get_template_name(self, data: Any) -> Optional[str]:
        """Get template name based on data type.

        Args:
            data: Data to determine template for

        Returns:
            Template name or None if not found
        """
        # Map data types to template names
        template_mapping = {
            "ProjectInfo": "project_info",
            "SuccessResponse": "success",
            "ErrorResponse": "error",
            "dict": self._get_dict_template_name(data),
            "list": "list",
        }

        # Get data type name
        data_type = type(data).__name__
        if data_type in template_mapping:
            return template_mapping[data_type]

        # Check for special data structures
        if isinstance(data, dict):
            return self._get_dict_template_name(data)

        return None

    def _get_dict_template_name(self, data: Dict[str, Any]) -> Optional[str]:
        """Get template name for dictionary data.

        Args:
            data: Dictionary data

        Returns:
            Template name or None if not found
        """
        # Check for error structure
        if "error" in data:
            return "error"

        # Check for success structure
        if "success" in data:
            return "success"

        # Check for project info structure
        if "project_root" in data and "total_files" in data:
            return "project_info"

        return "generic"

    def _create_template_config(self, config: Optional[OutputConfig]) -> TemplateConfig:
        """Create template configuration from output configuration.

        Args:
            config: Output configuration

        Returns:
            Template configuration
        """
        if config and hasattr(config, "template_config") and config.template_config:
            # Convert template_config dict to TemplateConfig
            template_options = config.template_config
            return TemplateConfig.create_config(
                use_emojis=not template_options.get("no_emojis", False),
                use_hierarchical_structure=template_options.get("hierarchical", True),
                include_line_numbers=template_options.get("line_numbers", True),
                include_centrality_scores=template_options.get("centrality", True),
                include_impact_risk=template_options.get("impact_risk", True),
                max_critical_lines=template_options.get("max_critical_lines", 3),
                max_dependencies=template_options.get("max_dependencies", 3),
                compression_level=template_options.get("compression_level", "medium"),
                format_style=template_options.get("format_style", "rich"),
            )
        else:
            # Use default configuration
            return TemplateConfig.create_config()

    def _format_fallback(self, data: Any, template_config: TemplateConfig) -> str:
        """Fallback formatting when template rendering fails.

        Args:
            data: Data to format
            template_config: Template configuration

        Returns:
            Fallback formatted string
        """
        if isinstance(data, dict):
            if "error" in data:
                return f"Error: {data['error'].get('message', 'Unknown error')}"
            elif "success" in data:
                return (
                    f"Success: {data['success'].get('message', 'Operation completed')}"
                )
            else:
                return str(data)
        else:
            return str(data)
