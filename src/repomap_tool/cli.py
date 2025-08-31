#!/usr/bin/env python3
"""
cli.py - Command Line Interface for Docker RepoMap

This module provides a CLI interface using Click and Pydantic models
for argument validation and structured output.
"""

import json
import sys

from typing import Optional, Literal

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    SearchRequest,
    SearchResponse,
    ProjectInfo,
    create_error_response,
)
from .core import DockerRepoMap

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli() -> None:
    """Docker RepoMap - Intelligent code analysis and identifier matching."""
    pass


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
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
    "--threshold", "-t", type=float, default=0.7, help="Match threshold (0.0-1.0)"
)
@click.option(
    "--max-results", "-m", type=int, default=50, help="Maximum results to return"
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "text", "markdown"]),
    default="json",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--max-workers", type=int, default=4, help="Maximum worker threads for parallel processing")
@click.option("--parallel-threshold", type=int, default=10, help="Minimum files to trigger parallel processing")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
@click.option("--no-monitoring", is_flag=True, help="Disable performance monitoring")
@click.option("--allow-fallback", is_flag=True, help="Allow fallback to sequential processing on errors (not recommended)")
def analyze(
    project_path: str,
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
) -> None:
    """Analyze a project and generate a code map."""

    try:
        # Load configuration
        if config:
            config_obj = load_config_file(config)
        else:
            config_obj = create_default_config(
                project_path, fuzzy, semantic, threshold, max_results, output, verbose,
                max_workers, parallel_threshold, no_progress, no_monitoring, allow_fallback
            )  # type: ignore

        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing RepoMap...", total=None)

            repomap = DockerRepoMap(config_obj)
            progress.update(task, description="Analyzing project...")

            # Analyze project with progress tracking
            project_info = repomap.analyze_project_with_progress()

            progress.update(task, description="Analysis complete!")

        # Display results
        display_project_info(project_info, output)

    except Exception as e:
        error_response = create_error_response(str(e), "AnalysisError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument("query", type=str)
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
def search(
    project_path: str,
    query: str,
    match_type: Literal["fuzzy", "semantic", "hybrid"],
    threshold: float,
    max_results: int,
    strategies: tuple,
    output: str,
    verbose: bool,
) -> None:
    """Search for identifiers in a project."""

    try:
        # Create configuration
        config = create_search_config(project_path, match_type, verbose)

        # Create search request
        request = SearchRequest(
            query=query,
            match_type=match_type,
            threshold=threshold,
            max_results=max_results,
            strategies=list(strategies) if strategies else None,
        )

        # Initialize RepoMap
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing RepoMap...", total=None)

            repomap = DockerRepoMap(config)
            progress.update(task, description="Searching identifiers...")

            # Perform search
            response = repomap.search_identifiers(request)

            progress.update(task, description="Search complete!")

        # Display results
        display_search_results(response, output)

    except Exception as e:
        error_response = create_error_response(str(e), "SearchError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--output", "-o", type=click.Path(), help="Output file for configuration")
def config(project_path: str, output: Optional[str]) -> None:
    """Generate a configuration file for the project."""

    try:
        # Create default configuration
        config_obj = create_default_config(
            project_path,
            fuzzy=True,
            semantic=True,
            threshold=0.7,
            max_results=50,
            output="json",
            verbose=True,
        )

        # Convert to dictionary
        config_dict = config_obj.model_dump()

        if output:
            # Write to file
            with open(output, "w") as f:
                json.dump(config_dict, f, indent=2)
            console.print(f"[green]Configuration saved to: {output}[/green]")
        else:
            # Display configuration
            console.print(
                Panel(
                    json.dumps(config_dict, indent=2),
                    title="Generated Configuration",
                    border_style="blue",
                )
            )

    except Exception as e:
        error_response = create_error_response(str(e), "ConfigError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--max-workers", type=int, default=4, help="Maximum worker threads for parallel processing")
@click.option("--parallel-threshold", type=int, default=10, help="Minimum files to trigger parallel processing")
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
@click.option("--no-monitoring", is_flag=True, help="Disable performance monitoring")
@click.option("--allow-fallback", is_flag=True, help="Allow fallback to sequential processing on errors (not recommended)")
def performance(
    project_path: str,
    max_workers: int,
    parallel_threshold: int,
    no_progress: bool,
    no_monitoring: bool,
    allow_fallback: bool,
) -> None:
    """Show performance metrics for the project."""
    
    try:
        # Create performance-focused configuration
        from .models import PerformanceConfig, RepoMapConfig
        
        performance_config = PerformanceConfig(
            max_workers=max_workers,
            parallel_threshold=parallel_threshold,
            enable_progress=not no_progress,
            enable_monitoring=not no_monitoring,
            allow_fallback=allow_fallback,
        )
        
        config = RepoMapConfig(
            project_root=project_path,
            performance=performance_config,
            verbose=True,
        )
        
        # Initialize RepoMap
        repomap = DockerRepoMap(config)
        
        # Get performance metrics
        metrics = repomap.get_performance_metrics()
        
        # Display metrics
        if metrics.get("monitoring_disabled"):
            console.print("[yellow]Performance monitoring is disabled[/yellow]")
            return
        
        if "error" in metrics:
            console.print(f"[red]Error getting metrics: {metrics['error']}[/red]")
            return
        
        # Create rich table for display
        table = Table(title="Performance Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        # Configuration
        config_metrics = metrics.get("configuration", {})
        table.add_row("Max Workers", str(config_metrics.get("max_workers", "N/A")))
        table.add_row("Parallel Threshold", str(config_metrics.get("parallel_threshold", "N/A")))
        table.add_row("Progress Enabled", str(config_metrics.get("enable_progress", "N/A")))
        table.add_row("Monitoring Enabled", str(config_metrics.get("enable_monitoring", "N/A")))
        
        # Processing stats
        processing_stats = metrics.get("processing_stats", {})
        if processing_stats:
            table.add_row("Total Files", str(processing_stats.get("total_files", 0)))
            table.add_row("Successful Files", str(processing_stats.get("successful_files", 0)))
            table.add_row("Failed Files", str(processing_stats.get("failed_files", 0)))
            table.add_row("Success Rate", f"{processing_stats.get('success_rate', 0):.1f}%")
            table.add_row("Total Identifiers", str(processing_stats.get("total_identifiers", 0)))
            table.add_row("Processing Time", f"{processing_stats.get('processing_time', 0):.2f}s")
            table.add_row("Files per Second", f"{processing_stats.get('files_per_second', 0):.1f}")
        
        # File size stats
        file_size_stats = metrics.get("file_size_stats", {})
        if file_size_stats:
            table.add_row("Total Size (MB)", f"{file_size_stats.get('total_size_mb', 0):.2f}")
            table.add_row("Average Size (KB)", f"{file_size_stats.get('avg_size_kb', 0):.1f}")
            table.add_row("Largest File (KB)", f"{file_size_stats.get('largest_file_kb', 0):.1f}")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
def version() -> None:
    """Show version information."""
    console.print(
        Panel(
            "[bold blue]Docker RepoMap[/bold blue]\n"
            "Version: 0.1.0\n"
            "A portable code analysis tool using aider libraries\n"
            "with fuzzy and semantic matching capabilities.",
            title="Version Info",
            border_style="green",
        )
    )


def load_config_file(config_path: str) -> RepoMapConfig:
    """Load configuration from file."""
    try:
        with open(config_path, "r") as f:
            config_dict = json.load(f)
        return RepoMapConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")


def create_default_config(
    project_path: str,
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    max_results: int,
    output: Literal["json", "text", "markdown"],
    verbose: bool,
    max_workers: int = 4,
    parallel_threshold: int = 10,
    no_progress: bool = False,
    no_monitoring: bool = False,
    allow_fallback: bool = False,
) -> RepoMapConfig:
    """Create default configuration."""

    # Create fuzzy match config
    fuzzy_config = FuzzyMatchConfig(
        enabled=fuzzy,
        threshold=int(threshold * 100),  # Convert to percentage
        strategies=["prefix", "substring", "levenshtein"],
    )

    # Create semantic match config
    semantic_config = SemanticMatchConfig(
        enabled=semantic, threshold=threshold, use_tfidf=True
    )

    # Create performance config
    from .models import PerformanceConfig
    performance_config = PerformanceConfig(
        max_workers=max_workers,
        parallel_threshold=parallel_threshold,
        enable_progress=not no_progress,
        enable_monitoring=not no_monitoring,
        allow_fallback=allow_fallback,
    )

    # Create main config
    config = RepoMapConfig(
        project_root=project_path,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        performance=performance_config,
        max_results=max_results,
        output_format=output,
        verbose=verbose,
    )

    return config


def create_search_config(
    project_path: str, match_type: str, verbose: bool
) -> RepoMapConfig:
    """Create configuration for search operations."""

    # Enable appropriate matchers based on match type
    fuzzy_enabled = match_type in ["fuzzy", "hybrid"]
    semantic_enabled = match_type in ["semantic", "hybrid"]

    fuzzy_config = FuzzyMatchConfig(enabled=fuzzy_enabled)
    semantic_config = SemanticMatchConfig(enabled=semantic_enabled)

    config = RepoMapConfig(
        project_root=project_path,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        verbose=verbose,
    )

    return config


def display_project_info(project_info: ProjectInfo, output_format: str) -> None:
    """Display project analysis results."""

    if output_format == "json":
        console.print(project_info.model_dump_json(indent=2))
        return

    # Create rich table for display
    table = Table(title="Project Analysis Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Project Root", str(project_info.project_root))
    table.add_row("Total Files", str(project_info.total_files))
    table.add_row("Total Identifiers", str(project_info.total_identifiers))
    table.add_row("Analysis Time", f"{project_info.analysis_time_ms:.2f}ms")
    table.add_row(
        "Last Updated", project_info.last_updated.strftime("%Y-%m-%d %H:%M:%S")
    )

    if project_info.cache_size_bytes:
        table.add_row("Cache Size", f"{project_info.cache_size_bytes / 1024:.1f}KB")

    console.print(table)

    # Display file types
    if project_info.file_types:
        file_table = Table(title="File Types")
        file_table.add_column("Extension", style="cyan")
        file_table.add_column("Count", style="green")

        for ext, count in sorted(
            project_info.file_types.items(), key=lambda x: x[1], reverse=True
        ):
            file_table.add_row(ext, str(count))

        console.print(file_table)

    # Display identifier types
    if project_info.identifier_types:
        id_table = Table(title="Identifier Types")
        id_table.add_column("Type", style="cyan")
        id_table.add_column("Count", style="green")

        for id_type, count in sorted(
            project_info.identifier_types.items(), key=lambda x: x[1], reverse=True
        ):
            id_table.add_row(id_type, str(count))

        console.print(id_table)


def display_search_results(response: SearchResponse, output_format: str) -> None:
    """Display search results."""

    if output_format == "json":
        console.print(response.model_dump_json(indent=2))
        return

    # Create rich table for results
    table = Table(title=f"Search Results for '{response.query}'")
    table.add_column("Identifier", style="cyan")
    table.add_column("Score", style="green")
    table.add_column("Strategy", style="yellow")
    table.add_column("Type", style="magenta")

    for result in response.results:
        score_str = f"{result.score:.3f}"
        table.add_row(result.identifier, score_str, result.strategy, result.match_type)

    console.print(table)

    # Display summary
    summary = Panel(
        f"Found {response.total_results} results in {response.search_time_ms:.2f}ms\n"
        f"Match type: {response.match_type}\n"
        f"Threshold: {response.threshold}",
        title="Search Summary",
        border_style="blue",
    )
    console.print(summary)


if __name__ == "__main__":
    cli()
