"""
Formatter interface protocols for RepoMap-Tool CLI.

This module defines the standardized interfaces and protocols for all output formatters,
ensuring consistency and extensibility across the output system.
"""

from __future__ import annotations

from repomap_tool.core.logging_service import get_logger
from typing import Any, List, Optional, Protocol, Type, TypeVar, Union

import click
from rich.console import Console

from repomap_tool.models import AnalysisFormat, OutputConfig, OutputFormat
from repomap_tool.protocols import FormatterProtocol
from .console_manager import ConsoleManagerProtocol

# Type variables for generic formatters
T = TypeVar("T")
FormatterResult = Union[str, None]


class FormatterFactoryProtocol(Protocol):  # Renamed for clarity
    """Protocol for formatter factory."""

    def create_formatter(
        self,
        formatter_type: str,
        **kwargs: Any,
    ) -> FormatterProtocol:
        """Create a formatter of the specified type."""
        ...

    def get_available_types(self) -> List[str]:
        """Get list of available formatter types."""
        ...
