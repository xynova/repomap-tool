#!/usr/bin/env python3
"""
Main CLI entry point for RepoMap-Tool.

This module provides the main CLI group and orchestrates all command groups.
"""

# Configure external library logging as early as possible
from ..core.logging_service import _suppress_external_library_logs

_suppress_external_library_logs()

import click
import tempfile
from pathlib import Path

# Import command groups
from .commands.system import system
from .commands.index import index
from .commands.search import search
from .commands.explore import explore
from .commands.inspect import inspect
from .utils.console import ConsoleProvider, RichConsoleFactory


@click.group()
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx: click.Context, no_color: bool) -> None:
    """RepoMap-Tool: Intelligent code repository mapping and analysis."""
    ctx.ensure_object(dict)
    ctx.obj["no_color"] = no_color

    # Initialize console provider with dependency injection
    from repomap_tool.core.container import create_container
    from repomap_tool.models import RepoMapConfig
    from repomap_tool.cli.output.console_manager import DefaultConsoleManager # Import DefaultConsoleManager

    # Use the current working directory as a fallback for project_root
    initial_project_root = Path.cwd()
    dummy_config = RepoMapConfig(project_root=initial_project_root, cache_dir=None)
    container = create_container(dummy_config)
    # Explicitly configure DefaultConsoleManager with no_color setting
    console_manager_instance = DefaultConsoleManager(
        provider=container.console_manager.provider(),  # Get the underlying ConsoleProvider
        enable_logging=True  # Default to true for now
    )
    ctx.obj["console_manager"] = console_manager_instance  # Use the configured instance
    ctx.obj["container"] = container # Store the container in ctx.obj


# Register command groups
cli.add_command(system)
cli.add_command(index)
cli.add_command(search)
cli.add_command(explore)
cli.add_command(inspect)


if __name__ == "__main__":
    cli()
