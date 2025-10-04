"""
Search commands for RepoMap-Tool CLI.

This module contains commands for searching and discovery.
"""

import sys
from typing import Optional, Literal

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from ...models import (
    SearchRequest,
    RepoMapConfig,
    DependencyConfig,
    create_error_response,
)
from ...core import RepoMapService
from ..config.loader import (
    resolve_project_path,
    create_search_config,
    create_tree_config,
)
from ..output.formatters import (
    display_search_results,
    display_dependency_results,
    display_cycles_results,
)
from ..utils.console import get_console


@click.group()
@click.pass_context
def search(ctx: click.Context) -> None:
    """Search and discovery commands.

    ⚠️  DEPRECATED: This command is deprecated and will be removed in a future version.
    Use 'repomap-tool inspect' instead for all search and analysis functionality.
    """
    import warnings

    warnings.warn(
        "The 'search' command is deprecated. Use 'inspect' instead. "
        "This command will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2,
    )


@search.command()
@click.argument("query", type=str)
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
@click.option(
    "--match-type",
    type=click.Choice(["fuzzy", "semantic", "hybrid"]),
    default="hybrid",
    help="Matching strategy",
)
@click.option(
    "--threshold", "-t", type=float, default=0.7, help="Match threshold (0.0-1.0)"
)
@click.option(
    "--max-results", "-m", type=int, default=10, help="Maximum results to return"
)
@click.option("--strategies", "-s", multiple=True, help="Specific matching strategies")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "text", "table"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.option(
    "--cache-size",
    type=int,
    default=1000,
    help="Maximum cache entries (100-10000)",
)
def identifiers(
    query: str,
    project_path: Optional[str],
    config: Optional[str],
    match_type: Literal["fuzzy", "semantic", "hybrid"],
    threshold: float,
    max_results: int,
    strategies: tuple,
    output: str,
    verbose: bool,
    log_level: str,
    cache_size: int,
) -> None:
    """Search for identifiers in a project."""

    # Get console instance (automatically configured with no-color if set)
    ctx = click.get_current_context()
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create configuration
        config_obj = create_search_config(
            resolved_project_path, match_type, verbose, log_level, cache_size
        )

        # Update configuration with threshold from CLI
        # Convert float threshold (0.0-1.0) to integer (0-100) for internal use
        threshold_int = int(threshold * 100) if threshold <= 1.0 else int(threshold)
        config_obj.fuzzy_match.threshold = threshold_int
        config_obj.semantic_match.threshold = threshold

        # Create search request
        request = SearchRequest(
            query=query,
            match_type=match_type,
            threshold=threshold,  # Keep as float for API consistency
            max_results=max_results,
            strategies=list(strategies) if strategies else None,
        )

        # Initialize RepoMap using service factory
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing RepoMap...", total=None)

            from repomap_tool.cli.services import get_service_factory

            service_factory = get_service_factory()
            repomap = service_factory.create_repomap_service(config_obj)

            progress.update(task, description="Searching identifiers...")

            # Perform search
            response = repomap.search_identifiers(request)

            progress.update(task, description="Search complete!")

        # Display results
        display_search_results(response, output)  # type: ignore[arg-type]

    except Exception as e:
        error_response = create_error_response(str(e), "SearchError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@search.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--max-files",
    type=int,
    default=1000,
    help="Maximum files to analyze (100-10000)",
)
@click.option(
    "--enable-call-graph",
    is_flag=True,
    default=True,
    help="Enable function call graph analysis",
)
@click.option(
    "--enable-impact-analysis",
    is_flag=True,
    default=True,
    help="Enable change impact analysis",
)
def dependencies(
    project_path: Optional[str],
    config: Optional[str],
    output: str,
    verbose: bool,
    max_files: int,
    enable_call_graph: bool,
    enable_impact_analysis: bool,
) -> None:
    """Analyze project dependencies and build dependency graph."""

    # Get console instance (automatically configured with no-color if set)
    ctx = click.get_current_context()
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create configuration using factory
        from repomap_tool.core.config_factory import get_config_factory

        config_factory = get_config_factory()
        config_obj = config_factory.create_analysis_config(
            project_root=resolved_project_path,
            enable_impact_analysis=enable_impact_analysis,
            max_graph_size=max_files,
            verbose=verbose,
        )

        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing dependencies...", total=None)

            from repomap_tool.cli.services import get_service_factory

            service_factory = get_service_factory()
            repomap = service_factory.create_repomap_service(config_obj)
            progress.update(task, description="Building dependency graph...")

            # Perform dependency analysis
            dependency_graph = repomap.build_dependency_graph()
            progress.update(task, description="Analysis complete!")

        # Prepare results
        results = {
            "total_files": len(dependency_graph.nodes) if dependency_graph else 0,
            "total_dependencies": (
                len(dependency_graph.graph.edges) if dependency_graph else 0
            ),
            "circular_dependencies": 0,  # TODO: Calculate actual cycles
        }

        # Display results
        display_dependency_results(results, output)  # type: ignore[arg-type]

    except Exception as e:
        error_response = create_error_response(str(e), "DependencyAnalysisError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@search.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table", "text"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cycles(
    project_path: Optional[str],
    config: Optional[str],
    output: str,
    verbose: bool,
) -> None:
    """Find circular dependencies in the project."""

    # Get console instance (automatically configured with no-color if set)
    ctx = click.get_current_context()
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create configuration using factory
        from repomap_tool.core.config_factory import get_config_factory

        config_factory = get_config_factory()
        config_obj = config_factory.create_basic_config(
            project_root=resolved_project_path,
            verbose=verbose,
        )

        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Finding circular dependencies...", total=None)

            from repomap_tool.cli.services import get_service_factory

            service_factory = get_service_factory()
            repomap = service_factory.create_repomap_service(config_obj)
            progress.update(task, description="Building dependency graph...")

            # Build dependency graph
            dependency_graph = repomap.build_dependency_graph()
            progress.update(task, description="Detecting cycles...")

            # Find cycles
            cycles = []
            if dependency_graph:
                cycles = repomap.find_circular_dependencies()

            progress.update(task, description="Analysis complete!")

        # Display results
        display_cycles_results(cycles, output)  # type: ignore[arg-type]

    except Exception as e:
        error_response = create_error_response(str(e), "CycleDetectionError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)
