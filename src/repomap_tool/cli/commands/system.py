from repomap_tool.core.config_service import get_config
from repomap_tool.core.logging_service import get_logger
from repomap_tool.core.container_config import configure_container

"""
System commands for RepoMap-Tool CLI.

This module contains system-level commands like version info and configuration.
"""

import json
import sys
from typing import Optional

import click
from pathlib import Path
import tempfile

from ...models import (
    RepoMapConfig,
    create_error_response,
    ProjectInfo,
    PerformanceConfig,
    DependencyConfig,
)
from ..config.loader import resolve_project_path, create_default_config
from ..output import OutputManager, OutputConfig, OutputFormat
from ..utils.console import get_console
from ..services import get_service_factory

logger = get_logger(__name__)


@click.group()
def system() -> None:
    """System information commands."""
    pass


@system.command()
@click.option(
    "--config",
    "-c",
    "config_file_path",  # Internal parameter name
    type=click.Path(),
    help="Output configuration file path",
)
@click.option("--fuzzy/--no-fuzzy", default=True, help="Enable fuzzy matching")
@click.option("--semantic/--no-semantic", default=True, help="Enable semantic matching")
@click.option(
    "--threshold",
    default=get_config("FUZZY_THRESHOLD", 0.7),
    type=float,
    help="Matching threshold (0.0-1.0)",
)
@click.option("--cache-size", default=1000, type=int, help="Cache size for results")
@click.pass_context
def config(
    ctx: click.Context,
    config_file_path: Optional[str],  # Use the new internal parameter name
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    cache_size: int,
) -> None:
    """Generate a configuration file for the project."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    try:
        # Resolve project path from argument or discovery
        project_root = ctx.obj.get("project_root", Path.cwd())
        project_path = resolve_project_path(None, project_root)
        # Create default configuration
        config_obj = create_default_config(
            project_path,
            fuzzy=fuzzy,
            semantic=semantic,
            threshold=threshold,
            max_results=50,
            output="json",
            verbose=True,
            cache_size=cache_size,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Convert to dictionary with proper serialization
        config_dict = config_obj.model_dump(mode="json")

        # Get output manager from context (after container is configured)
        output_manager: OutputManager = ctx.obj["container"].output_manager()

        if config_file_path:
            # Write to file
            with open(config_file_path, "w") as f:
                json.dump(config_dict, f, indent=2)
            # Use OutputManager for success message
            output_config = OutputConfig(format=OutputFormat.TEXT)
            output_manager.display_success(
                f"Configuration saved to: {config_file_path}", output_config
            )
        else:
            # Display configuration
            output_config = OutputConfig(format=OutputFormat.TEXT)
            config_text = f"Generated Configuration\n{'=' * 50}\n{json.dumps(config_dict, indent=2)}"
            output_manager.display(config_text, output_config)

    except Exception as e:
        error_response = create_error_response(str(e), "ConfigError")
        # Get output manager from context for error handling
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@system.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    # Configure the container with a minimal config for simple commands
    container = ctx.obj["container"]
    # Get project root from context, fallback to current directory for minimal config
    project_root = ctx.obj.get("project_root", Path.cwd())
    minimal_config = RepoMapConfig(project_root=project_root, cache_dir=tempfile.TemporaryDirectory().name) # Use a temp cache dir
    configure_container(container, minimal_config)

    # Get output manager from context (after container is configured)
    output_manager: OutputManager = ctx.obj["container"].output_manager()
    output_config = OutputConfig(format=OutputFormat.TEXT)

    version_info = {
        "tool": "RepoMap-Tool",
        "version": "0.1.0",
        "description": "A portable code analysis tool using tree-sitter with fuzzy and semantic matching capabilities.",
    }

    output_manager.display(version_info, output_config)


@system.command()
@click.pass_context
def cache_info(ctx: click.Context) -> None:
    """Show tree-sitter tag cache statistics"""
    from repomap_tool.cli.services import get_service_factory

    # Configure the container with a minimal config for simple commands
    container = ctx.obj["container"]
    # Get project root from context, fallback to current directory for minimal config
    project_root = ctx.obj.get("project_root", Path.cwd())
    minimal_config = RepoMapConfig(project_root=project_root, cache_dir=tempfile.TemporaryDirectory().name) # Use a temp cache dir
    configure_container(container, minimal_config)

    # Get output manager from context (after container is configured)
    output_manager: OutputManager = ctx.obj["container"].output_manager()

    # Use service factory to get cache
    config = RepoMapConfig(
        project_root=project_root,  # Use resolved project root
        performance=PerformanceConfig(),
        dependencies=DependencyConfig(),
    )
    service_factory = get_service_factory()
    repomap_service = service_factory.create_repomap_service(config)
    cache = repomap_service.tree_sitter_parser.tag_cache
    if cache is None:  # Add None check
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error("Tag cache is not available.", output_config)
        sys.exit(1)
    stats = cache.get_cache_stats()

    output_config = OutputConfig(format=OutputFormat.TEXT)

    cache_info_text = f"""Tree-Sitter Tag Cache Information
    {'=' * 50}
    Cache Location: {stats['cache_location']}
    Cached Files: {stats['cached_files']}
    Total Tags: {stats['total_tags']}
    Approx Size: {stats['approx_size_bytes'] / 1024:.2f} KB
    """
    output_manager.display(cache_info_text, output_config)


@system.command()
@click.option("--force", is_flag=True, help="Clear without confirmation")
@click.pass_context
def cache_clear(ctx: click.Context, force: bool) -> None:
    """Clear the tree-sitter tag cache"""
    from repomap_tool.core.tag_cache import TreeSitterTagCache

    # Configure the container with a minimal config for simple commands
    container = ctx.obj["container"]
    # Get project root from context, fallback to current directory for minimal config
    project_root = ctx.obj.get("project_root", Path.cwd())
    minimal_config = RepoMapConfig(project_root=project_root, cache_dir=tempfile.TemporaryDirectory().name) # Use a temp cache dir
    configure_container(container, minimal_config)

    # Get output manager from context (after container is configured)
    output_manager: OutputManager = ctx.obj["container"].output_manager()

    if not force:
        if not click.confirm("Clear all cached tags?"):
            return

    # Use service factory to get cache

    config = RepoMapConfig(
        project_root=project_root,  # Use resolved project root
        performance=PerformanceConfig(),
        dependencies=DependencyConfig(),
    )
    service_factory = get_service_factory()
    repomap_service = service_factory.create_repomap_service(config)
    cache = repomap_service.tree_sitter_parser.tag_cache
    if cache is None:  # Add None check
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error("Tag cache is not available.", output_config)
        sys.exit(1)
    cache.clear()

    output_config = OutputConfig(format=OutputFormat.TEXT)
    output_manager.display_success("Tag cache cleared", output_config)
