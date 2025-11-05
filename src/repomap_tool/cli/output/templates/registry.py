"""
Template registry for RepoMap-Tool CLI.

This module provides template registration and management functionality,
allowing dynamic template discovery and registration.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Any, Dict, List, Optional, Protocol, Union

from .config import TemplateConfig
from .loader import TemplateLoader, FileTemplateLoader
from repomap_tool.protocols import TemplateRegistryProtocol


class DefaultTemplateRegistry(
    TemplateRegistryProtocol
):  # Explicitly implement the protocol
    """Default implementation of template registry."""

    def __init__(
        self,
        template_loader: Optional[TemplateLoader] = None,
        enable_logging: bool = True,
        default_config: Optional[TemplateConfig] = None,  # Add default_config
    ) -> None:
        """Initialize the template registry."""
        self._templates: Dict[str, str] = {}
        self._registered_templates: Dict[str, str] = (
            {}
        )  # Initialize _registered_templates
        if template_loader is None:
            raise ValueError("TemplateLoader must be injected - no fallback allowed")
        self._template_loader = template_loader
        self._logger = get_logger(__name__) if enable_logging else None
        self._default_config = default_config

        # Load default templates from the file system (if loader is present)
        if self._template_loader:
            try:
                self._template_loader.load_default_templates(self)
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Failed to load default templates: {e}")

    def register_template(
        self, template_name: str, template_content: str, overwrite: bool = False
    ) -> None:
        """Register a template.

        Args:
            template_name: Name of the template
            template_content: Template content
            overwrite: Whether to overwrite existing template

        Raises:
            ValueError: If template already exists and overwrite is False
        """
        if template_name in self._registered_templates and not overwrite:
            raise ValueError(f"Template '{template_name}' already registered")

        self._registered_templates[template_name] = template_content

        if self._logger:
            self._logger.debug(f"Registered template '{template_name}'")

    def unregister_template(self, template_name: str) -> None:
        """Unregister a template.

        Args:
            template_name: Name of the template to unregister
        """
        if template_name in self._registered_templates:
            del self._registered_templates[template_name]
            if self._logger:
                self._logger.debug(f"Unregistered template '{template_name}'")

    def get_template(self, template_name: str) -> Optional[str]:
        """Get template content.

        Args:
            template_name: Name of the template

        Returns:
            Template content or None if not found
        """
        # First check registered templates
        if template_name in self._registered_templates:
            return self._registered_templates[template_name]

        # Then try to load from template loader
        try:
            return self._template_loader.load_template(template_name)
        except Exception:
            return None

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of template names
        """
        # Combine registered templates and loaded templates
        registered = set(self._registered_templates.keys())
        loaded = set(self._template_loader.list_templates())
        return sorted(registered | loaded)

    def template_exists(self, template_name: str) -> bool:
        """Check if template exists.

        Args:
            template_name: Name of the template

        Returns:
            True if template exists
        """
        return (
            template_name in self._registered_templates
            or self._template_loader.template_exists(template_name)
        )

    def load_default_templates(self) -> None:
        """Load default templates from the template loader."""
        try:
            available_templates = self._template_loader.list_templates()
            for template_name in available_templates:
                if template_name not in self._registered_templates:
                    try:
                        template_content = self._template_loader.load_template(
                            template_name
                        )
                        self._registered_templates[template_name] = template_content
                        if self._logger:
                            self._logger.debug(
                                f"Loaded default template '{template_name}'"
                            )
                    except Exception as e:
                        if self._logger:
                            self._logger.warning(
                                f"Failed to load template '{template_name}': {e}"
                            )
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to load default templates: {e}")


# Alias for backward compatibility
TemplateRegistry = DefaultTemplateRegistry
