"""
Template engine for RepoMap-Tool CLI.

This module provides the core template rendering engine using Jinja2,
with support for custom filters, functions, and template inheritance.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, Dict, List, Optional, Union

# Try to import Jinja2
JINJA2_AVAILABLE = False
Environment: Any = None
FileSystemLoader: Any = None
Template: Any = None
TemplateNotFound: type[Exception] = Exception
TemplateSyntaxError: type[Exception] = Exception
FILTERS: dict[str, Any] = {}
GLOBALS: dict[str, Any] = {}

try:
    import jinja2
    from jinja2 import (
        Environment,
        FileSystemLoader,
        Template,
        TemplateNotFound,
        TemplateSyntaxError,
    )
    from jinja2.filters import FILTERS

    # GLOBALS is not available in newer Jinja2 versions
    GLOBALS = {}
    JINJA2_AVAILABLE = True
except ImportError as e:
    # Fallback for environments without Jinja2

    logger = get_logger(__name__)
    logger.warning(f"Jinja2 not available: {e}")
    JINJA2_AVAILABLE = False

from .config import TemplateConfig, TemplateOptions
from .registry import TemplateRegistryProtocol
from .loader import TemplateLoader, FileTemplateLoader


class TemplateEngine:
    """Template rendering engine using Jinja2."""

    def __init__(
        self,
        template_registry: TemplateRegistryProtocol,
        template_loader: Optional[TemplateLoader] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the template engine.

        Args:
            template_registry: Template registry to use
            template_loader: Template loader to use
            enable_logging: Whether to enable logging
        """
        self._enable_logging = enable_logging
        self._logger = get_logger(__name__) if enable_logging else None
        self.template_registry = template_registry

        if template_loader is None:
            self._template_loader: TemplateLoader = FileTemplateLoader(
                enable_logging=enable_logging
            )
        else:
            self._template_loader = template_loader

        # Initialize Jinja2 environment
        self._setup_jinja_environment()

    def _setup_jinja_environment(self) -> None:
        """Setup Jinja2 environment with custom filters and functions."""
        if not JINJA2_AVAILABLE:
            if self._logger:
                self._logger.warning(
                    "Jinja2 not available, using fallback template engine"
                )
            self._jinja_env = None
            return

        # Create Jinja2 environment
        if Environment is not None and FileSystemLoader is not None:
            self._jinja_env = Environment(
                loader=FileSystemLoader([]),  # We'll load templates manually
                autoescape=False,  # We're not dealing with HTML
                trim_blocks=True,
                lstrip_blocks=True,
            )
        else:
            self._jinja_env = None

        # Add custom filters
        if self._jinja_env is not None:
            self._jinja_env.filters.update(
                {
                    "truncate": self._filter_truncate,
                    "indent": self._filter_indent,
                    "format_number": self._filter_format_number,
                    "format_percentage": self._filter_format_percentage,
                    "format_duration": self._filter_format_duration,
                    "tree_prefix": self._filter_tree_prefix,
                    "emoji": self._filter_emoji,
                }
            )

        # Add custom functions
        if self._jinja_env is not None:
            self._jinja_env.globals.update(
                {
                    "get_tree_symbol": self._function_get_tree_symbol,
                    "format_centrality": self._function_format_centrality,
                    "format_impact_risk": self._function_format_impact_risk,
                    "get_risk_level": self._function_get_risk_level,
                }
            )

    def render_template(
        self,
        template_name: str,
        data: Any,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        """Render a template with data.

        Args:
            template_name: Name of the template to render
            data: Data to render with
            config: Optional template configuration

        Returns:
            Rendered template content

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateRenderError: If template rendering fails
        """
        try:
            # Get template content
            template_content = self.template_registry.get_template(template_name)
            if not template_content:
                raise TemplateNotFoundError(f"Template '{template_name}' not found")

            # Prepare rendering context
            context = self._prepare_context(data, config)

            # Render template
            if self._jinja_env:
                return self._render_with_jinja(template_content, context)
            else:
                return self._render_fallback(template_content, context)

        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to render template '{template_name}': {e}")
            raise TemplateRenderError(f"Template rendering failed: {e}")

    def render_string(
        self,
        template_string: str,
        data: Any,
        config: Optional[TemplateConfig] = None,
    ) -> str:
        """Render a template string with data.

        Args:
            template_string: Template string to render
            data: Data to render with
            config: Optional template configuration

        Returns:
            Rendered template content

        Raises:
            TemplateRenderError: If template rendering fails
        """
        try:
            # Prepare rendering context
            context = self._prepare_context(data, config)

            # Render template
            if self._jinja_env:
                return self._render_with_jinja(template_string, context)
            else:
                return self._render_fallback(template_string, context)

        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to render template string: {e}")
            raise TemplateRenderError(f"Template rendering failed: {e}")

    def _prepare_context(
        self, data: Any, config: Optional[TemplateConfig]
    ) -> Dict[str, Any]:
        """Prepare rendering context.

        Args:
            data: Data to include in context
            config: Template configuration

        Returns:
            Prepared context dictionary
        """
        context = {
            "data": data,
            "config": config,
        }

        if config:
            context.update(config.get_template_context())
            context.update(config.custom_variables)

        return context

    def _render_with_jinja(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template using Jinja2.

        Args:
            template_content: Template content
            context: Rendering context

        Returns:
            Rendered content
        """
        if self._jinja_env is None:
            # Fallback to simple string formatting
            return template_content.format(**context)

        try:
            template = self._jinja_env.from_string(template_content)
            result = template.render(**context)
            return str(result)
        except TemplateSyntaxError as e:
            raise TemplateRenderError(f"Template syntax error: {e}")
        except Exception as e:
            raise TemplateRenderError(f"Jinja2 rendering error: {e}")

    def _render_fallback(self, template_content: str, context: Dict[str, Any]) -> str:
        """Fallback template rendering without Jinja2.

        Args:
            template_content: Template content
            context: Rendering context

        Returns:
            Rendered content
        """
        # Simple string replacement fallback
        result = template_content
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, (str, int, float)):
                result = result.replace(placeholder, str(value))
        return result

    # Custom Jinja2 filters
    def _filter_truncate(self, text: str, length: int = 50, suffix: str = "...") -> str:
        """Truncate text to specified length."""
        if len(text) <= length:
            return text
        return text[: length - len(suffix)] + suffix

    def _filter_indent(self, text: str, width: int = 2, prefix: str = " ") -> str:
        """Indent text by specified width."""
        lines = text.split("\n")
        indented_lines = [prefix * width + line for line in lines]
        return "\n".join(indented_lines)

    def _filter_format_number(
        self, number: Union[int, float], precision: int = 2
    ) -> str:
        """Format number with specified precision."""
        if isinstance(number, int):
            return str(number)
        return f"{number:.{precision}f}"

    def _filter_format_percentage(self, value: float, precision: int = 1) -> str:
        """Format value as percentage."""
        return f"{value * 100:.{precision}f}%"

    def _filter_format_duration(self, milliseconds: float) -> str:
        """Format duration in milliseconds."""
        if milliseconds < 1000:
            return f"{milliseconds:.1f}ms"
        elif milliseconds < 60000:
            return f"{milliseconds / 1000:.1f}s"
        else:
            minutes = int(milliseconds / 60000)
            seconds = (milliseconds % 60000) / 1000
            return f"{minutes}m {seconds:.1f}s"

    def _filter_tree_prefix(self, is_last: bool, level: int = 0) -> str:
        """Generate tree prefix for hierarchical display."""
        if level == 0:
            return "└──" if is_last else "├──"
        else:
            prefix = "    " * level
            return prefix + ("└──" if is_last else "├──")

    def _filter_emoji(self, emoji: str, use_emojis: bool = True) -> str:
        """Conditionally include emoji based on configuration."""
        return emoji if use_emojis else ""

    # Custom Jinja2 functions
    def _function_get_tree_symbol(self, is_last: bool, level: int = 0) -> str:
        """Get tree symbol for hierarchical display."""
        return self._filter_tree_prefix(is_last, level)

    def _function_format_centrality(self, centrality: float, precision: int = 2) -> str:
        """Format centrality score."""
        return f"{centrality:.{precision}f}"

    def _function_format_impact_risk(self, risk: float, precision: int = 2) -> str:
        """Format impact risk score."""
        return f"{risk:.{precision}f}"

    def _function_get_risk_level(self, risk: float) -> str:
        """Get risk level string."""
        if risk > 0.7:
            return "HIGH"
        elif risk > 0.4:
            return "MEDIUM"
        else:
            return "LOW"


class TemplateEngineFactory:
    """Factory for creating template engine instances."""

    @staticmethod
    def create_template_engine(
        template_registry: TemplateRegistryProtocol, # Make it a required argument
        template_loader: Optional[TemplateLoader] = None,
        enable_logging: bool = True,
    ) -> TemplateEngine:
        """Create a TemplateEngine instance with optional template loader."""
        return TemplateEngine(
            template_registry=template_registry,
            template_loader=template_loader,
            enable_logging=enable_logging,
        )


class TemplateNotFoundError(Exception):
    """Raised when a template is not found."""

    pass


class TemplateRenderError(Exception):
    """Raised when template rendering fails."""

    pass


# Global template engine instance
_global_template_engine: Optional[TemplateEngine] = None


def get_template_engine() -> TemplateEngine:
    """Get the global template engine instance.

    Returns:
        Global template engine instance
    """
    global _global_template_engine
    if _global_template_engine is None:
        _global_template_engine = TemplateEngineFactory.create_template_engine()
    return _global_template_engine
