"""
Centralized console management for RepoMap-Tool CLI.

This module provides a unified console management system with proper
dependency injection, error handling, and configuration management.
"""

from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Optional, Dict, Any, Protocol
from pathlib import Path

import click
from rich.console import Console
from rich.theme import Theme

from ..utils.console import (
    ConsoleProvider,
    RichConsoleFactory,
    get_console as get_console_legacy,
)


class ConsoleManager(Protocol):
    """Protocol for console manager implementations."""

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a configured console instance."""
        ...

    def configure_console(
        self, ctx: Optional[click.Context] = None, **kwargs: Any
    ) -> Console:
        """Configure and return a console instance with specific settings."""
        ...

    def log_console_usage(self, operation: str, **context: Any) -> None:
        """Log console usage for debugging and monitoring."""
        ...


class DefaultConsoleManager:
    """Default implementation of console manager with enhanced features."""

    def __init__(
        self, provider: Optional[ConsoleProvider] = None, enable_logging: bool = True
    ) -> None:
        """Initialize the console manager.

        Args:
            provider: Console provider for dependency injection
            enable_logging: Whether to enable console usage logging
        """
        if provider is None:
            raise ValueError("ConsoleProvider must be injected - no fallback allowed")
        self._provider = provider
        self._enable_logging = enable_logging
        self._logger = get_logger(__name__) if enable_logging else None
        self._usage_stats: Dict[str, int] = {}

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        """Get a configured console instance.

        Args:
            ctx: Click context for configuration

        Returns:
            Configured Console instance
        """
        try:
            console = self._provider.get_console(ctx)

            if self._enable_logging and self._logger:
                self._log_console_usage(
                    "get_console", context={"has_ctx": ctx is not None}
                )

            return console
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to get console: {e}")
            raise

    def configure_console(
        self, ctx: Optional[click.Context] = None, **kwargs: Any
    ) -> Console:
        """Configure and return a console instance with specific settings.

        Args:
            ctx: Click context for base configuration
            **kwargs: Additional console configuration options

        Returns:
            Configured Console instance
        """
        try:
            # Get base console from provider
            console = self._provider.get_console(ctx)

            # For now, we'll return the base console since we can't reconfigure it
            # without direct instantiation. In a real implementation, we might need
            # to extend the ConsoleProvider interface to support configuration.
            if self._enable_logging and self._logger:
                self._log_console_usage("configure_console", context=kwargs)

            return console
        except Exception as e:
            if self._logger:
                self._logger.error(f"Failed to configure console: {e}")
            raise

    def log_console_usage(self, operation: str, **context: Any) -> None:
        """Log console usage for debugging and monitoring.

        Args:
            operation: The operation being performed
            **context: Additional context information
        """
        if not self._enable_logging or not self._logger:
            return

        self._log_console_usage(operation, context)

    def _log_console_usage(self, operation: str, context: Dict[str, Any]) -> None:
        """Internal method to log console usage.

        Args:
            operation: The operation being performed
            context: Context information
        """
        if not self._logger:
            return

        # Track usage statistics
        self._usage_stats[operation] = self._usage_stats.get(operation, 0) + 1

        # Log the usage
        self._logger.debug(
            f"Console operation: {operation}",
            extra={
                "operation": operation,
                "context": context,
                "usage_count": self._usage_stats[operation],
            },
        )

    def get_usage_stats(self) -> Dict[str, int]:
        """Get console usage statistics.

        Returns:
            Dictionary of operation counts
        """
        return self._usage_stats.copy()

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self._usage_stats.clear()


class ConsoleManagerFactory:
    """Factory for creating console managers."""

    @staticmethod
    def create_default_manager(
        enable_logging: bool = True, provider: Optional[ConsoleProvider] = None
    ) -> DefaultConsoleManager:
        """Create a default console manager.

        Args:
            enable_logging: Whether to enable logging
            provider: Custom console provider

        Returns:
            Configured console manager
        """
        if provider is None:
            provider = ConsoleProvider(RichConsoleFactory())
        return DefaultConsoleManager(provider=provider, enable_logging=enable_logging)

    @staticmethod
    def create_console_manager(
        manager_type: str = "default", **kwargs: Any
    ) -> ConsoleManager:
        """Create a console manager of the specified type.

        Args:
            manager_type: Type of manager to create
            **kwargs: Additional configuration

        Returns:
            Console manager instance
        """
        if manager_type == "default":
            return ConsoleManagerFactory.create_default_manager(**kwargs)
        else:
            raise ValueError(f"Unknown console manager type: {manager_type}")


# Global console manager instance
_global_console_manager: Optional[ConsoleManager] = None


def get_console_manager() -> ConsoleManager:
    """Get the global console manager instance.

    Returns:
        Global console manager
    """
    global _global_console_manager
    if _global_console_manager is None:
        _global_console_manager = ConsoleManagerFactory.create_default_manager()
    return _global_console_manager


def set_console_manager(manager: ConsoleManager) -> None:
    """Set the global console manager instance.

    Args:
        manager: Console manager to set as global
    """
    global _global_console_manager
    _global_console_manager = manager


def get_managed_console(ctx: Optional[click.Context] = None) -> Console:
    """Get a console instance from the managed console system.

    This is the recommended way to get console instances in CLI commands.

    Args:
        ctx: Click context for configuration

    Returns:
        Configured Console instance
    """
    manager = get_console_manager()
    return manager.get_console(ctx)


def configure_managed_console(
    ctx: Optional[click.Context] = None, **kwargs: Any
) -> Console:
    """Configure and get a console instance from the managed system.

    Args:
        ctx: Click context for base configuration
        **kwargs: Additional console configuration

    Returns:
        Configured Console instance
    """
    manager = get_console_manager()
    return manager.configure_console(ctx, **kwargs)


# Convenience functions for backward compatibility
def get_console_from_context(ctx: Optional[click.Context] = None) -> Console:
    """Get console from context using the managed system.

    Args:
        ctx: Click context

    Returns:
        Console instance
    """
    return get_managed_console(ctx)


def log_console_operation(operation: str, **context: Any) -> None:
    """Log a console operation.

    Args:
        operation: Operation name
        **context: Additional context
    """
    manager = get_console_manager()
    manager.log_console_usage(operation, **context)
