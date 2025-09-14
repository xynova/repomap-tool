"""
Utility functions for RepoMap-Tool CLI.

This package contains utility functions used across CLI modules.
"""

from .session import (
    get_project_path_from_session,
    create_session_id,
    get_or_create_session,
)
from .console import (
    get_console,
    ConsoleFactory,
    RichConsoleFactory,
    ConsoleProvider,
    get_console_provider,
    set_console_provider,
)

__all__ = [
    "get_project_path_from_session",
    "create_session_id",
    "get_or_create_session",
    "get_console",
    "ConsoleFactory",
    "RichConsoleFactory",
    "ConsoleProvider",
    "get_console_provider",
    "set_console_provider",
]
