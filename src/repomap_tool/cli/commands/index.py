from repomap_tool.core.config_service import get_config

"""
Index commands for RepoMap-Tool CLI.

This module contains commands for project indexing and setup.
"""

import sys
from typing import Optional, Literal

import click
from rich.console import Console

from ...models import create_error_response
from ...core import RepoMapService
from ..config.loader import (
    resolve_project_path,
    create_default_config,
    load_or_create_config,
)
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.console import get_console


# Use DI-provided console instead of direct instantiation
def get_index_console() -> Console:
    """Get console instance using dependency injection."""
    ctx = click.get_current_context()
    return get_console(ctx)


@click.group()
def index() -> None:
    """Project indexing and setup commands."""
    pass


@index.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file (JSON/YAML)",
)
@click.option("--fuzzy/--no-fuzzy", default=False, help="Enable fuzzy matching")
@click.option(
    "--semantic/--no-semantic", default=False, help="Enable semantic matching"
)
@click.option(
    "--threshold",
    default=get_config("FUZZY_THRESHOLD", 0.7),
    type=float,
    help="Match threshold (0.0-1.0)",
)
@click.option(
    "--max-results", "-m", type=int, default=50, help="Maximum results to return"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--max-workers", type=int, default=4, help="Maximum worker threads")
@click.option(
    "--parallel-threshold", type=int, default=100, help="Parallel processing threshold"
)
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
@click.option("--no-monitoring", is_flag=True, help="Disable performance monitoring")
@click.option("--allow-fallback", is_flag=True, help="Allow fallback to basic search")
@click.option("--cache-size", type=int, default=1000, help="Maximum cache entries")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.option("--refresh-cache", is_flag=True, help="Refresh existing cache")
@click.option("--no-emojis", is_flag=True, help="Disable emojis in output")
@click.option("--no-hierarchy", is_flag=True, help="Disable hierarchical structure")
@click.option("--no-line-numbers", is_flag=True, help="Disable line numbers")
@click.option("--no-centrality", is_flag=True, help="Disable centrality scores")
@click.option("--no-impact-risk", is_flag=True, help="Disable impact risk analysis")
@click.option(
    "--max-critical-lines", type=int, default=3, help="Max critical lines to show"
)
@click.option(
    "--max-dependencies", type=int, default=3, help="Max dependencies to show"
)
@click.option(
    "--compression",
    type=click.Choice(["low", "medium", "high"]),
    default="medium",
    help="Output compression level",
)
def create(
    project_path: Optional[str],
    config: Optional[str],
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    max_results: int,
    output: str,
    verbose: bool,
    max_workers: int,
    parallel_threshold: int,
    no_progress: bool,
    no_monitoring: bool,
    allow_fallback: bool,
    cache_size: int,
    log_level: str,
    refresh_cache: bool,
    no_emojis: bool,
    no_hierarchy: bool,
    no_line_numbers: bool,
    no_centrality: bool,
    no_impact_risk: bool,
    max_critical_lines: int,
    max_dependencies: int,
    compression: Literal["low", "medium", "high"],
) -> None:
    """Create project analysis and repository map."""

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Load or create configuration
        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            fuzzy=fuzzy,
            semantic=semantic,
            threshold=threshold,
            max_results=max_results,
            output=output,
            verbose=verbose,
            refresh_cache=refresh_cache,
            cache_size=cache_size,
            no_progress=no_progress,
            no_monitoring=no_monitoring,
            log_level=log_level,
        )

        # Initialize RepoMap using service factory
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config_obj)

        # Analyze project
        project_info = repomap.analyze_project()

        # Pre-compute embeddings during indexing
        if (
            hasattr(repomap, "embedding_matcher")
            and repomap.embedding_matcher
            and repomap.embedding_matcher.enabled
        ):
            console = get_index_console()
            console.print("[cyan]Computing embeddings for all identifiers...[/cyan]")

            # Get all identifiers from tree-sitter cache
            identifiers_with_files = {}
            if hasattr(repomap, "_get_cached_tags"):
                tags = repomap._get_cached_tags()
                for tag in tags:
                    if "name" in tag and "file" in tag:
                        identifiers_with_files[tag["name"]] = tag["file"]

            # Batch compute and cache
            if identifiers_with_files:
                repomap.embedding_matcher.batch_compute_embeddings(
                    identifiers_with_files
                )
                console.print(
                    f"[green]✓ Cached embeddings for {len(identifiers_with_files)} identifiers[/green]"
                )
            else:
                console.print(
                    "[yellow]No identifiers found for embedding computation[/yellow]"
                )

        # Create output configuration
        output_config = OutputConfig(
            format=OutputFormat(output),
            template_config={
                "no_emojis": no_emojis,
                "no_hierarchy": no_hierarchy,
                "no_line_numbers": no_line_numbers,
                "no_centrality": no_centrality,
                "no_impact_risk": no_impact_risk,
                "max_critical_lines": max_critical_lines,
                "max_dependencies": max_dependencies,
                "compression": compression,
            },
        )

        # Display results using OutputManager
        output_manager = get_output_manager()
        output_manager.display(project_info, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)
