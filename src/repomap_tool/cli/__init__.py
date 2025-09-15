"""
CLI package for RepoMap-Tool.

This package contains the refactored CLI implementation with proper separation of concerns.
"""

from .main import cli

# Re-export functions for backward compatibility with existing tests
from .config.loader import (
    load_config_file,
    create_default_config,
    create_search_config,
    create_tree_config,
    load_or_create_config,
    resolve_project_path,
    apply_environment_overrides,
    apply_cli_overrides,
)
from .output.formatters import (
    display_project_info,
    display_search_results,
)
from .utils.session import (
    get_project_path_from_session,
)

# Import from core modules for test compatibility
from ..core.repo_map import RepoMapService
from ..models import SearchRequest

# Import Rich objects that tests expect
from rich.console import Console
from rich.progress import Progress

# Note: console should be obtained via get_console(ctx) in functions that need it

__all__ = [
    "cli",
    # Config functions
    "load_config_file",
    "create_default_config",
    "create_search_config",
    "create_tree_config",
    "load_or_create_config",
    "resolve_project_path",
    "apply_environment_overrides",
    "apply_cli_overrides",
    # Output functions
    "display_project_info",
    "display_search_results",
    # Session functions
    "get_project_path_from_session",
    # Core classes for test compatibility
    "RepoMapService",
    "SearchRequest",
    # Rich objects
    "Console",
    "Progress",
]
