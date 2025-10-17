
from __future__ import annotations

import logging
from repomap_tool.core.logging_service import get_logger
from typing import Optional, Dict, Any, Protocol
from pathlib import Path

import click
from rich.console import Console
from rich.theme import Theme
from abc import abstractmethod

from ..utils.console import ConsoleProvider, RichConsoleFactory


class ConsoleManagerProtocol(Protocol):
    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        ...

    @abstractmethod
    def configure(self, no_color: bool = False) -> None:
        ...

    @abstractmethod
    def log_operation(self, operation: str, context: Dict[str, Any]) -> None:
        ...

    def get_usage_stats(self) -> Dict[str, Any]:
        ...

    def reset_usage_stats(self) -> None:
        ...


class DefaultConsoleManager(ConsoleManagerProtocol):
    def __init__(
        self,
        provider: ConsoleProvider,
        enable_logging: bool = True,
        log_level: int = logging.INFO,
        theme: Optional[Theme] = None,
    ) -> None:
        if provider is None:
            raise ValueError("ConsoleProvider must be injected - no fallback allowed")

        self.logger = get_logger(self.__class__.__name__) if enable_logging else None # Conditionally initialize logger
        self.enable_logging = enable_logging
        self._provider = provider
        self._log_level = log_level
        self._theme = theme
        self._usage_stats: Dict[str, int] = {}

    def get_console(self, ctx: Optional[click.Context] = None) -> Console:
        if self.enable_logging and self.logger:
            self._log_operation("get_console", context={"ctx_obj": str(ctx.obj) if ctx else "None"}) # Changed to _log_operation
        return self._provider.get_console(ctx)

    def configure(self, no_color: bool = False) -> None:
        self._provider = ConsoleProvider(factory=RichConsoleFactory(), no_color=no_color)
        if self.enable_logging and self.logger:
            self._log_operation("configure_console", context={"no_color": no_color}) # Changed to _log_operation

    def log_operation(self, operation: str, context: Dict[str, Any]) -> None:
        self._log_operation(operation, context)

    def _log_operation(self, operation: str, context: Dict[str, Any] = {}) -> None: # Renamed 'details' to 'context'
        if self.enable_logging and self.logger:
            self.logger.debug(
                f"Console operation: {operation}",
                extra={
                    "operation": operation,
                    "console_manager": self.__class__.__name__,
                    "context": context, # Changed 'details' to 'context'
                },
            )
        self._usage_stats[operation] = self._usage_stats.get(operation, 0) + 1

    def get_usage_stats(self) -> Dict[str, int]:
        # Do not log this operation to avoid skewing stats for the test
        return self._usage_stats.copy()

    def reset_usage_stats(self) -> None:
        if self.enable_logging and self.logger:
            self._log_operation("reset_usage_stats", context={}) # Changed to _log_operation
        self._usage_stats = {}


_global_console_manager: Optional[ConsoleManagerProtocol] = None


def get_console_manager() -> ConsoleManagerProtocol:
    global _global_console_manager
    if _global_console_manager is None:
        _global_console_manager = DefaultConsoleManager(
            provider=ConsoleProvider(factory=RichConsoleFactory()),
            enable_logging=True,
        )
    return _global_console_manager


def set_console_manager(manager: ConsoleManagerProtocol) -> None:
    global _global_console_manager
    _global_console_manager = manager


def get_managed_console(ctx: Optional[click.Context] = None) -> Console:
    return get_console_manager().get_console(ctx)


def get_console_from_context(ctx: Optional[click.Context] = None) -> Console:
    return get_managed_console(ctx)


def log_console_operation(operation: str, **context: Any) -> None:
    manager = get_console_manager()
    manager.log_operation(operation, context=context)

