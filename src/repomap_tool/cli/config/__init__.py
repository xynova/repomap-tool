"""
Configuration management for RepoMap-Tool CLI.

This package contains configuration loading, validation, and management utilities.
"""

from .loader import (
    load_config_file,
    resolve_project_path,
    create_default_config,
    load_or_create_config,
    apply_environment_overrides,
    apply_cli_overrides,
    create_search_config,
    create_tree_config,
)

__all__ = [
    "load_config_file",
    "resolve_project_path",
    "create_default_config",
    "load_or_create_config",
    "apply_environment_overrides",
    "apply_cli_overrides",
    "create_search_config",
    "create_tree_config",
]
