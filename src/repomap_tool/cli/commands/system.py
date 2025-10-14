from repomap_tool.core.config_service import get_config

"""
System commands for RepoMap-Tool CLI.

This module contains system-level commands like version info and configuration.
"""

import json
import sys
from typing import Optional

import click

from ...models import RepoMapConfig, create_error_response
from ..config.loader import resolve_project_path, create_default_config
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.console import get_console


@click.group()
def system() -> None:
    """System information commands."""
    pass


@system.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--output", "-o", type=click.Path(), help="Output configuration file path"
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
    project_path: Optional[str],
    output: Optional[str],
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
        project_path = resolve_project_path(project_path, None)
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

        # Convert to dictionary with proper serialization
        config_dict = config_obj.model_dump(mode="json")

        if output:
            # Write to file
            with open(output, "w") as f:
                json.dump(config_dict, f, indent=2)
            # Use OutputManager for success message
            output_manager = get_output_manager()
            output_config = OutputConfig(format=OutputFormat.TEXT)
            output_manager.display_success(
                f"Configuration saved to: {output}", output_config
            )
        else:
            # Display configuration
            output_manager = get_output_manager()
            output_config = OutputConfig(format=OutputFormat.TEXT)
            config_text = f"Generated Configuration\n{'=' * 50}\n{json.dumps(config_dict, indent=2)}"
            output_manager.display(config_text, output_config)

    except Exception as e:
        error_response = create_error_response(str(e), "ConfigError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@system.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """Show version information."""
    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    # Use OutputManager for version display
    output_manager = get_output_manager()
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
    from repomap_tool.core.tag_cache import TreeSitterTagCache
    
    cache = TreeSitterTagCache()
    stats = cache.get_cache_stats()
    
    output_manager = get_output_manager()
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
    
    if not force:
        if not click.confirm("Clear all cached tags?"):
            return
    
    cache = TreeSitterTagCache()
    cache.clear()
    
    output_manager = get_output_manager()
    output_config = OutputConfig(format=OutputFormat.TEXT)
    output_manager.display_success("Tag cache cleared", output_config)
