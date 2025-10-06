"""
Template loading utilities for RepoMap-Tool CLI.

This module provides template loading functionality, including file-based
template loading and template content management.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .config import TemplateConfig


class TemplateLoader(ABC):
    """Abstract base class for template loaders."""

    def __init__(self, enable_logging: bool = True) -> None:
        """Initialize the template loader."""
        self._enable_logging = enable_logging
        self._logger = get_logger(__name__) if enable_logging else None

    @abstractmethod
    def load_template(
        self, template_name: str, config: Optional[TemplateConfig] = None
    ) -> str:
        """Load a template by name.

        Args:
            template_name: Name of the template to load
            config: Optional template configuration

        Returns:
            Template content as string

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateLoadError: If template cannot be loaded
        """
        pass

    @abstractmethod
    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of available template names
        """
        pass

    @abstractmethod
    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.

        Args:
            template_name: Name of the template to check

        Returns:
            True if template exists
        """
        pass


class FileTemplateLoader(TemplateLoader):
    """Template loader that loads templates from files."""

    def __init__(
        self,
        template_dirs: Optional[List[Union[str, Path]]] = None,
        enable_logging: bool = True,
    ) -> None:
        """Initialize the file template loader.

        Args:
            template_dirs: List of directories to search for templates
            enable_logging: Whether to enable logging
        """
        super().__init__(enable_logging)
        self._template_dirs = template_dirs or []
        self._template_cache: Dict[str, str] = {}
        self._setup_default_dirs()

    def _setup_default_dirs(self) -> None:
        """Setup default template directories."""
        if not self._template_dirs:
            # Add default template directory
            current_dir = Path(__file__).parent
            jinja_dir = current_dir / "jinja"
            if jinja_dir.exists():
                self._template_dirs.append(jinja_dir)

    def load_template(
        self, template_name: str, config: Optional[TemplateConfig] = None
    ) -> str:
        """Load a template from file.

        Args:
            template_name: Name of the template to load
            config: Optional template configuration

        Returns:
            Template content as string

        Raises:
            TemplateNotFoundError: If template is not found
            TemplateLoadError: If template cannot be loaded
        """
        # Check cache first
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        # Try to find template file
        template_path = self._find_template_file(template_name)
        if not template_path:
            raise TemplateNotFoundError(f"Template '{template_name}' not found")

        try:
            # Load template content
            with open(template_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Cache the template
            self._template_cache[template_name] = content

            if self._logger:
                self._logger.debug(
                    f"Loaded template '{template_name}' from {template_path}"
                )

            return content

        except Exception as e:
            raise TemplateLoadError(f"Failed to load template '{template_name}': {e}")

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of available template names
        """
        templates = []
        for template_dir in self._template_dirs:
            template_path = Path(template_dir)
            if template_path.exists():
                for template_file in template_path.glob("*.jinja2"):
                    template_name = template_file.stem
                    templates.append(template_name)
        return sorted(templates)

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.

        Args:
            template_name: Name of the template to check

        Returns:
            True if template exists
        """
        return self._find_template_file(template_name) is not None

    def _find_template_file(self, template_name: str) -> Optional[Path]:
        """Find template file by name.

        Args:
            template_name: Name of the template to find

        Returns:
            Path to template file or None if not found
        """
        for template_dir in self._template_dirs:
            template_path = Path(template_dir)
            if template_path.exists():
                # Try different extensions
                for ext in [".jinja2", ".j2", ".template", ".txt"]:
                    template_file = template_path / f"{template_name}{ext}"
                    if template_file.exists():
                        return template_file
        return None

    def add_template_dir(self, template_dir: Union[str, Path]) -> None:
        """Add a template directory.

        Args:
            template_dir: Directory path to add
        """
        template_path = Path(template_dir)
        if template_path.exists() and template_path not in self._template_dirs:
            self._template_dirs.append(template_path)
            # Clear cache when adding new directories
            self._template_cache.clear()

    def clear_cache(self) -> None:
        """Clear template cache."""
        self._template_cache.clear()


class InMemoryTemplateLoader(TemplateLoader):
    """Template loader that stores templates in memory."""

    def __init__(self, enable_logging: bool = True) -> None:
        """Initialize the in-memory template loader."""
        super().__init__(enable_logging)
        self._templates: Dict[str, str] = {}

    def load_template(
        self, template_name: str, config: Optional[TemplateConfig] = None
    ) -> str:
        """Load a template from memory.

        Args:
            template_name: Name of the template to load
            config: Optional template configuration

        Returns:
            Template content as string

        Raises:
            TemplateNotFoundError: If template is not found
        """
        if template_name not in self._templates:
            raise TemplateNotFoundError(f"Template '{template_name}' not found")
        return self._templates[template_name]

    def list_templates(self) -> List[str]:
        """List all available templates.

        Returns:
            List of available template names
        """
        return list(self._templates.keys())

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists.

        Args:
            template_name: Name of the template to check

        Returns:
            True if template exists
        """
        return template_name in self._templates

    def add_template(self, template_name: str, template_content: str) -> None:
        """Add a template to memory.

        Args:
            template_name: Name of the template
            template_content: Template content
        """
        self._templates[template_name] = template_content

    def remove_template(self, template_name: str) -> None:
        """Remove a template from memory.

        Args:
            template_name: Name of the template to remove
        """
        self._templates.pop(template_name, None)


class TemplateNotFoundError(Exception):
    """Raised when a template is not found."""

    pass


class TemplateLoadError(Exception):
    """Raised when a template cannot be loaded."""

    pass
