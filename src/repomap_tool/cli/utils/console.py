"""
Console factory and dependency injection for RepoMap-Tool CLI.

This module provides a factory pattern for creating console instances
with proper dependency injection support.
"""

import click
from rich.console import Console
from typing import Optional, Protocol


class ConsoleFactory(Protocol):
    """Protocol for console factory implementations."""

    def create_console(self, no_color: bool = False) -> Console:
        """Create a new console instance.

        Args:
            no_color: Whether to disable colors

        Returns:
            Configured Console instance
        """


class RichConsoleFactory:
    """Factory for creating Rich Console instances."""

    def create_console(self, no_color: bool = False) -> Console:
        """Create a new Rich Console instance.

        Args:
            no_color: Whether to disable colors

        Returns:
            Configured Console instance
        """
        console = Console()
        console.no_color = no_color
        return console


class ConsoleProvider:
    """Dependency injection provider for console instances."""

    def __init__(self, factory: Optional[ConsoleFactory] = None):
        """Initialize the console provider.

        Args:
            factory: Console factory implementation
        """
        self._factory = factory or RichConsoleFactory()

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a console instance, optionally configured from context.

        Args:
            ctx: Click context to check for no-color setting

        Returns:
            Configured Console instance
        """
        no_color = False
        if ctx and ctx.obj and ctx.obj.get("no_color", False):
            no_color = True

        return self._factory.create_console(no_color=no_color)


# Global provider instance
_global_provider: Optional[ConsoleProvider] = None


def get_console_provider() -> ConsoleProvider:
    """Get the global console provider instance.

    Returns:
        Global ConsoleProvider instance
    """
    global _global_provider
    if _global_provider is None:
        _global_provider = ConsoleProvider()
    return _global_provider


def set_console_provider(provider: ConsoleProvider) -> None:
    """Set the global console provider instance.

    Args:
        provider: ConsoleProvider instance to use globally
    """
    global _global_provider
    _global_provider = provider


def get_console(ctx: Optional[click.Context] = None) -> Console:
    """Get a console instance from context or global provider.

    Args:
        ctx: Click context containing console_provider and no-color setting

    Returns:
        Configured Console instance
    """
    # If context is provided and has a console_provider, use it
    if ctx and ctx.obj and "console_provider" in ctx.obj:
        provider: ConsoleProvider = ctx.obj["console_provider"]
        return provider.get_console(ctx)

    # Fallback to global provider
    provider = get_console_provider()
    return provider.get_console(ctx)
