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
from typing import Optional, Any
from repomap_tool.core.config_service import ConfigService
from repomap_tool.cli.config.loader import load_or_create_config
from repomap_tool.core.logging_service import get_logger
from repomap_tool.models import RepoMapConfig

logger = get_logger(__name__)


# Import command groups
from .commands.system import system
from .commands.index import index
from .commands.search import search
from .commands.explore import explore
from .commands.inspect import inspect
from .utils.console import ConsoleProvider, RichConsoleFactory


@click.group()
@click.option(
    "--project-root",
    type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path
    ),
    default=None,
    help="Specify the project root directory.",
)
@click.option("--no-color", is_flag=True, help="Disable colored output")
@click.pass_context
def cli(ctx: click.Context, project_root: Optional[Path], no_color: bool) -> None:
    """RepoMap-Tool: Intelligent code repository mapping and analysis."""
    ctx.ensure_object(dict)
    ctx.obj["no_color"] = no_color

    # Use the provided project_root or fallback to current working directory
    effective_project_root = project_root if project_root else Path.cwd()
    ctx.obj["project_root"] = str(effective_project_root)

    # Initialize console provider with dependency injection
    from repomap_tool.core.container import create_container
    from repomap_tool.cli.output.console_manager import (
        DefaultConsoleManager,
    )  # Import DefaultConsoleManager

    # Initialize an empty container and attach it to the context
    # The container will be configured with the actual RepoMapConfig in each command
    if "container" not in ctx.obj:
        container = create_container(
            RepoMapConfig(
                project_root=effective_project_root,
                cache_dir=tempfile.TemporaryDirectory().name,
            )
        )
        ctx.obj["container"] = container

    # If console_manager is not already set in ctx.obj, retrieve it from the container.
    if "console_manager" not in ctx.obj:
        ctx.obj["console_manager"] = ctx.obj["container"].console_manager()

    logger.debug(
        f"Type of ctx.obj['console_manager'] after setting: {type(ctx.obj['console_manager'])}"
    )

    # Retrieve the console manager from the container and configure it.
    console_manager_instance = ctx.obj["console_manager"]
    console_manager_instance.configure(
        no_color=ctx.obj.get("no_color", False)
    )  # Directly call configure on the instance

    # Pass the container to the context object


# Register command groups
cli.add_command(system)
cli.add_command(index)
cli.add_command(search)
cli.add_command(explore)
cli.add_command(inspect)


if __name__ == "__main__":
    cli()
