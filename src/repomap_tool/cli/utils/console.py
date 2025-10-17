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

    def __init__(self, factory: Optional[ConsoleFactory] = None, no_color: bool = False):
        """Initialize the console provider.

        Args:
            factory: Console factory implementation
            no_color: Whether to disable colors by default for consoles created by this provider.
        """
        if factory is None:
            factory = RichConsoleFactory()
        self._factory = factory
        self._no_color = no_color

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a console instance, optionally configured from context.

        Args:
            ctx: Click context to check for no-color setting

        Returns:
            Configured Console instance
        """
        # Prioritize no_color from Click context, then from provider's init
        no_color_from_ctx = ctx.obj.get("no_color", False) if ctx and ctx.obj else False
        effective_no_color = no_color_from_ctx or self._no_color

        return self._factory.create_console(no_color=effective_no_color)


# Global provider instance
_global_provider: Optional[ConsoleProvider] = None


def get_console_provider() -> ConsoleProvider:
    """Get the global console provider instance.

    Returns:
        Global ConsoleProvider instance
    """
    global _global_provider
    if _global_provider is None:
        # Ensure factory is always set, and it's a new instance to avoid shared state issues.
        _global_provider = ConsoleProvider(factory=RichConsoleFactory(), no_color=False)
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
    # If context is provided and has a console_manager, use it
    if ctx and ctx.obj and "console_manager" in ctx.obj:
        console_manager = ctx.obj["console_manager"]
        return console_manager.get_console(ctx)

    # Fallback to the global console provider if no console_manager is found in context.
    # This ensures consistent console behavior even outside of a fully initialized Click context.
    return get_console_provider().get_console(ctx)
