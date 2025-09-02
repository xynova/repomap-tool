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
from pydantic import ValidationError
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
    type=click.Choice(["json", "text", "markdown", "table"]),
    default="json",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--max-workers",
    type=int,
    default=4,
    help="Maximum worker threads for parallel processing",
)
@click.option(
    "--parallel-threshold",
    type=int,
    default=10,
    help="Minimum files to trigger parallel processing",
)
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
@click.option("--no-monitoring", is_flag=True, help="Disable performance monitoring")
@click.option(
    "--allow-fallback",
    is_flag=True,
    help="Allow fallback to sequential processing on errors (not recommended)",
)
@click.option(
    "--cache-size",
    type=int,
    default=1000,
    help="Maximum cache entries (100-10000)",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Logging level",
)
@click.option(
    "--refresh-cache",
    is_flag=True,
    help="Refresh cache before analysis",
)
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
    cache_size: int,
    log_level: str,
    refresh_cache: bool,
) -> None:
    """Analyze a project and generate a code map."""

    try:
        # Load configuration
        if config:
            config_obj = load_config_file(config)
            # Apply CLI overrides to loaded config
            if fuzzy is not None:
                config_obj.fuzzy_match.enabled = fuzzy
            if semantic is not None:
                config_obj.semantic_match.enabled = semantic
            if threshold is not None:
                config_obj.fuzzy_match.threshold = int(threshold * 100)
                config_obj.semantic_match.threshold = threshold
            if max_results is not None:
                config_obj.max_results = max_results
            if output is not None:
                config_obj.output_format = output  # type: ignore[assignment]
            if verbose is not None:
                config_obj.verbose = verbose
            if max_workers is not None:
                config_obj.performance.max_workers = max_workers
            if parallel_threshold is not None:
                config_obj.performance.parallel_threshold = parallel_threshold
            if no_progress is not None:
                config_obj.performance.enable_progress = not no_progress
            if no_monitoring is not None:
                config_obj.performance.enable_monitoring = not no_monitoring
            if allow_fallback is not None:
                config_obj.performance.allow_fallback = allow_fallback
            if cache_size is not None:
                config_obj.performance.cache_size = cache_size
            if log_level is not None:
                config_obj.log_level = log_level
            if refresh_cache is not None:
                config_obj.refresh_cache = refresh_cache
        else:
            config_obj = create_default_config(
                project_path,
                fuzzy,
                semantic,
                threshold,
                max_results,
                output,  # type: ignore[arg-type]
                verbose,
                max_workers,
                parallel_threshold,
                no_progress,
                no_monitoring,
                allow_fallback,
                cache_size,
                log_level,
                refresh_cache,
            )

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
        display_project_info(project_info, output)  # type: ignore[arg-type]

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
def search(
    project_path: str,
    query: str,
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

    try:
        # Create configuration
        config = create_search_config(
            project_path, match_type, verbose, log_level, cache_size
        )

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
        display_search_results(response, output)  # type: ignore[arg-type]

    except Exception as e:
        error_response = create_error_response(str(e), "SearchError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option("--output", "-o", type=click.Path(), help="Output file for configuration")
@click.option(
    "--fuzzy/--no-fuzzy",
    default=True,
    help="Enable fuzzy matching in generated config",
)
@click.option(
    "--semantic/--no-semantic",
    default=True,
    help="Enable semantic matching in generated config",
)
@click.option(
    "--threshold",
    type=float,
    default=0.7,
    help="Match threshold for generated config",
)
@click.option(
    "--cache-size",
    type=int,
    default=1000,
    help="Cache size for generated config",
)
def config(
    project_path: str,
    output: Optional[str],
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    cache_size: int,
) -> None:
    """Generate a configuration file for the project."""

    try:
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
@click.option(
    "--max-workers",
    type=int,
    default=4,
    help="Maximum worker threads for parallel processing",
)
@click.option(
    "--parallel-threshold",
    type=int,
    default=10,
    help="Minimum files to trigger parallel processing",
)
@click.option("--no-progress", is_flag=True, help="Disable progress bars")
@click.option("--no-monitoring", is_flag=True, help="Disable performance monitoring")
@click.option(
    "--allow-fallback",
    is_flag=True,
    help="Allow fallback to sequential processing on errors (not recommended)",
)
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

        from .models import FuzzyMatchConfig, SemanticMatchConfig

        fuzzy_config = FuzzyMatchConfig(
            enabled=True,
            threshold=70,
            strategies=["prefix", "substring", "levenshtein"],
            cache_results=True,
        )
        semantic_config = SemanticMatchConfig(
            enabled=True,
            threshold=0.7,
            use_tfidf=True,
            min_word_length=3,
            cache_results=True,
        )

        config = RepoMapConfig(
            project_root=project_path,
            performance=performance_config,
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
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
        table.add_row(
            "Parallel Threshold", str(config_metrics.get("parallel_threshold", "N/A"))
        )
        table.add_row(
            "Progress Enabled", str(config_metrics.get("enable_progress", "N/A"))
        )
        table.add_row(
            "Monitoring Enabled", str(config_metrics.get("enable_monitoring", "N/A"))
        )

        # Processing stats
        processing_stats = metrics.get("processing_stats", {})
        if processing_stats:
            table.add_row("Total Files", str(processing_stats.get("total_files", 0)))
            table.add_row(
                "Successful Files", str(processing_stats.get("successful_files", 0))
            )
            table.add_row("Failed Files", str(processing_stats.get("failed_files", 0)))
            table.add_row(
                "Success Rate", f"{processing_stats.get('success_rate', 0):.1f}%"
            )
            table.add_row(
                "Total Identifiers", str(processing_stats.get("total_identifiers", 0))
            )
            table.add_row(
                "Processing Time", f"{processing_stats.get('processing_time', 0):.2f}s"
            )
            table.add_row(
                "Files per Second", f"{processing_stats.get('files_per_second', 0):.1f}"
            )

        # File size stats
        file_size_stats = metrics.get("file_size_stats", {})
        if file_size_stats:
            table.add_row(
                "Total Size (MB)", f"{file_size_stats.get('total_size_mb', 0):.2f}"
            )
            table.add_row(
                "Average Size (KB)", f"{file_size_stats.get('avg_size_kb', 0):.1f}"
            )
            table.add_row(
                "Largest File (KB)", f"{file_size_stats.get('largest_file_kb', 0):.1f}"
            )

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
    """Load and validate configuration from file."""
    try:
        with open(config_path, "r") as f:
            config_dict = json.load(f)

        # Validate against RepoMapConfig model
        config = RepoMapConfig(**config_dict)
        return config
    except ValidationError as e:
        raise ValueError(f"Invalid configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")


def create_default_config(
    project_path: str,
    fuzzy: bool,
    semantic: bool,
    threshold: float,
    max_results: int,
    output: Literal["json", "text", "markdown", "table"],
    verbose: bool,
    max_workers: int = 4,
    parallel_threshold: int = 10,
    no_progress: bool = False,
    no_monitoring: bool = False,
    allow_fallback: bool = False,
    cache_size: int = 1000,
    log_level: str = "INFO",
    refresh_cache: bool = False,
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
        cache_size=cache_size,
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
        log_level=log_level,
        refresh_cache=refresh_cache,
    )

    return config


def create_search_config(
    project_path: str,
    match_type: str,
    verbose: bool,
    log_level: str = "INFO",
    cache_size: int = 1000,
) -> RepoMapConfig:
    """Create configuration for search operations."""

    # Enable appropriate matchers based on match type
    # Default to hybrid if invalid match type is provided
    if match_type not in ["fuzzy", "semantic", "hybrid"]:
        match_type = "hybrid"

    fuzzy_enabled = match_type in ["fuzzy", "hybrid"]
    semantic_enabled = match_type in ["semantic", "hybrid"]

    fuzzy_config = FuzzyMatchConfig(enabled=fuzzy_enabled)
    semantic_config = SemanticMatchConfig(enabled=semantic_enabled)

    # Create performance config with cache settings
    from .models import PerformanceConfig

    performance_config = PerformanceConfig(
        cache_size=cache_size,
    )

    config = RepoMapConfig(
        project_root=project_path,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        performance=performance_config,
        verbose=verbose,
        log_level=log_level,
    )

    return config


def display_project_info(
    project_info: ProjectInfo,
    output_format: Literal["json", "text", "markdown", "table"],
) -> None:
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


def display_search_results(
    response: SearchResponse,
    output_format: Literal["json", "text", "markdown", "table"],
) -> None:
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


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.argument("intent", type=str)
@click.option("--session", "-s", help="Session ID (or use REPOMAP_SESSION env var)")
@click.option("--max-depth", default=3, help="Maximum tree depth")
def explore(project_path: str, intent: str, session: Optional[str], max_depth: int):
    """Discover exploration trees from intent."""
    
    try:
        import os
        import time
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            session_id = f"explore_{int(time.time())}"
            console.print(f"💡 Using session: {session_id}")
            console.print(f"Set: export REPOMAP_SESSION={session_id}")
        
        # Create configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig(max_depth=max_depth, entrypoint_threshold=0.6)
        
        config = RepoMapConfig(
            project_root=project_path,
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config,
            verbose=True
        )
        
        # Initialize RepoMap
        repomap = DockerRepoMap(config)
        
        # Import tree components
        from .trees import EntrypointDiscoverer, TreeClusterer, TreeBuilder, SessionManager
        
        # Discover entrypoints
        discoverer = EntrypointDiscoverer(repomap)
        entrypoints = discoverer.discover_entrypoints(project_path, intent)
        
        if not entrypoints:
            console.print(f"⚠️  No high-confidence entrypoints found for intent: \"{intent}\"")
            console.print("\n💡 Suggestions:")
            console.print(f"  • Try broader terms: \"{intent.split()[0]}\", \"{intent.split()[-1] if len(intent.split()) > 1 else 'code'}\"")
            console.print(f"  • Use semantic search: repomap-tool search \"{intent}\"")
            console.print("\n🔧 Alternative approaches:")
            console.print(f"  repomap-tool analyze {project_path}               # Get general overview")
            console.print(f"  repomap-tool search \"{intent}\" --fuzzy          # Fuzzy search")
            return
        
        # Cluster into trees
        clusterer = TreeClusterer()
        clusters = clusterer.cluster_entrypoints(entrypoints)
        
        # Build exploration trees
        tree_builder = TreeBuilder(repomap)
        session_manager = SessionManager()
        session = session_manager.get_or_create_session(session_id, project_path)
        
        console.print(f"🔍 Found {len(clusters)} exploration contexts:")
        
        for cluster in clusters:
            # Build tree from cluster
            tree = tree_builder.build_exploration_tree(cluster.entrypoints[0], max_depth)
            tree.context_name = cluster.context_name
            tree.confidence = cluster.confidence
            
            # Store in session
            session.exploration_trees[tree.tree_id] = tree
            
            console.print(f"  • {tree.context_name} [id: {tree.tree_id}] (confidence: {tree.confidence:.2f})")
        
        session_manager.persist_session(session)
        
        console.print(f"\n💡 Next steps:")
        console.print(f"  repomap-tool focus <tree_id>    # Focus on specific tree")
        console.print(f"  repomap-tool map                # View current tree")
        
    except Exception as e:
        error_response = create_error_response(str(e), "ExplorationError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("tree_id", type=str)
@click.option("--session", "-s", help="Session ID")
def focus(tree_id: str, session: Optional[str]):
    """Focus on specific exploration tree (stateful)."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool focus <tree_id> --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",  # Project path from session
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap and TreeManager
        repomap = DockerRepoMap(config)
        from .trees import TreeManager
        
        tree_manager = TreeManager(repomap)
        
        if tree_manager.focus_tree(session_id, tree_id):
            console.print(f"✅ Focused on tree: {tree_id}")
        else:
            console.print(f"❌ Failed to focus on tree: {tree_id}")
            console.print("💡 Check that the tree exists in your session")
            
    except Exception as e:
        error_response = create_error_response(str(e), "FocusError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("expansion_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def expand(expansion_area: str, session: Optional[str], tree: Optional[str]):
    """Expand tree in specific area."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool expand <area> --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap and TreeManager
        repomap = DockerRepoMap(config)
        from .trees import TreeManager
        
        tree_manager = TreeManager(repomap)
        
        if tree_manager.expand_tree(session_id, expansion_area, tree):
            console.print(f"✅ Expanded tree in area: {expansion_area}")
        else:
            console.print(f"❌ Failed to expand tree in area: {expansion_area}")
            console.print("💡 Check that the area exists in your focused tree")
            
    except Exception as e:
        error_response = create_error_response(str(e), "ExpansionError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("prune_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def prune(prune_area: str, session: Optional[str], tree: Optional[str]):
    """Prune branch from tree."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool prune <area> --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap and TreeManager
        repomap = DockerRepoMap(config)
        from .trees import TreeManager
        
        tree_manager = TreeManager(repomap)
        
        if tree_manager.prune_tree(session_id, prune_area, tree):
            console.print(f"✅ Pruned tree in area: {prune_area}")
        else:
            console.print(f"❌ Failed to prune tree in area: {prune_area}")
            console.print("💡 Check that the area exists in your focused tree")
            
    except Exception as e:
        error_response = create_error_response(str(e), "PruningError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
@click.option("--include-code", is_flag=True, help="Include code snippets")
def map(session: Optional[str], tree: Optional[str], include_code: bool):
    """Generate repomap from current tree state."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool map --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap, TreeManager, and TreeMapper
        repomap = DockerRepoMap(config)
        from .trees import TreeManager, TreeMapper
        
        tree_manager = TreeManager(repomap)
        tree_mapper = TreeMapper(repomap)
        
        current_tree = tree_manager.get_tree_state(session_id, tree)
        if not current_tree:
            console.print("❌ No tree found. Use 'repomap-tool focus <tree_id>' first")
            return
        
        tree_map = tree_mapper.generate_tree_map(current_tree, include_code)
        console.print(tree_map)
        
    except Exception as e:
        error_response = create_error_response(str(e), "MappingError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--session", "-s", help="Session ID")
def list_trees(session: Optional[str]):
    """List all trees in a session."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool list-trees --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap and TreeManager
        repomap = DockerRepoMap(config)
        from .trees import TreeManager
        
        tree_manager = TreeManager(repomap)
        
        trees_info = tree_manager.list_trees(session_id)
        
        if not trees_info:
            console.print(f"📋 No trees found in session '{session_id}'")
            console.print("💡 Use 'repomap-tool explore <project> <intent>' to create trees")
            return
        
        console.print(f"📋 Trees in session '{session_id}':")
        
        for tree_info in trees_info:
            focus_indicator = " [FOCUSED]" if tree_info['is_focused'] else ""
            console.print(f"  • {tree_info['tree_id']}{focus_indicator} - {tree_info['context_name']}")
            console.print(f"    Root: {tree_info['root_entrypoint']}")
            console.print(f"    Confidence: {tree_info['confidence']:.2f}, Nodes: {tree_info['node_count']}")
            
            if tree_info['expanded_areas']:
                console.print(f"    Expanded: {', '.join(tree_info['expanded_areas'])}")
            
            if tree_info['pruned_areas']:
                console.print(f"    Pruned: {', '.join(tree_info['pruned_areas'])}")
            
            console.print("")
        
    except Exception as e:
        error_response = create_error_response(str(e), "ListTreesError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--session", "-s", help="Session ID")
def status(session: Optional[str]):
    """Show session status and current tree information."""
    
    try:
        import os
        
        session_id = session or os.environ.get('REPOMAP_SESSION')
        if not session_id:
            console.print("❌ No session specified")
            console.print("💡 Use: export REPOMAP_SESSION=<session_id>")
            console.print("   Or: repomap-tool status --session <session_id>")
            return
        
        # Create minimal configuration
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig, TreeConfig
        
        fuzzy_config = FuzzyMatchConfig(enabled=True, threshold=70, cache_results=True)
        semantic_config = SemanticMatchConfig(enabled=True, threshold=0.7, cache_results=True)
        tree_config = TreeConfig()
        
        config = RepoMapConfig(
            project_root=".",
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            trees=tree_config
        )
        
        # Initialize RepoMap and TreeManager
        repomap = DockerRepoMap(config)
        from .trees import TreeManager, SessionManager
        
        tree_manager = TreeManager(repomap)
        session_manager = SessionManager()
        
        # Get session info
        current_session = session_manager.get_session(session_id)
        if not current_session:
            console.print(f"❌ Session '{session_id}' not found")
            return
        
        # Get current tree info
        current_tree = None
        if current_session.current_focus:
            current_tree = tree_manager.get_tree_state(session_id, current_session.current_focus)
        
        # Display status
        console.print(f"📊 Session Status: {session_id}")
        console.print("═══════════════════════════════════════")
        console.print("")
        
        if current_session.current_focus:
            console.print(f"🎯 Current Focus: {current_session.current_focus}")
        else:
            console.print("🎯 Current Focus: None")
        
        console.print(f"📅 Session Started: {current_session.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"🕐 Last Activity: {current_session.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
        console.print("")
        
        # Tree information
        trees_info = tree_manager.list_trees(session_id)
        console.print(f"🌳 Exploration Trees ({len(trees_info)} total):")
        
        for i, tree_info in enumerate(trees_info, 1):
            focus_indicator = "🎯" if tree_info['is_focused'] else "📋"
            console.print(f"  {i}. {focus_indicator} {tree_info['tree_id']} - {tree_info['context_name']}")
        
        console.print("")
        
        if current_tree:
            console.print("💡 Quick Actions:")
            console.print("  repomap-tool map                          # View current focused tree")
            console.print(f"  repomap-tool expand <area>               # Expand current tree")
            console.print(f"  repomap-tool prune <area>                # Prune current tree")
        
    except Exception as e:
        error_response = create_error_response(str(e), "StatusError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


@cli.command()
@click.argument(
    "project_path", type=click.Path(exists=True, file_okay=False, dir_okay=True)
)
@click.option(
    "--refresh",
    is_flag=True,
    help="Refresh/clear all caches before showing status",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["json", "table"]),
    default="table",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cache(
    project_path: str,
    refresh: bool,
    output: str,
    verbose: bool,
) -> None:
    """Show cache status and optionally refresh caches."""
    
    try:
        # Create minimal configuration for cache operations
        from .models import RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig
        
        fuzzy_config = FuzzyMatchConfig(
            enabled=True,
            threshold=70,
            cache_results=True,
        )
        semantic_config = SemanticMatchConfig(
            enabled=True,
            threshold=0.7,
            cache_results=True,
        )
        
        config = RepoMapConfig(
            project_root=project_path,
            fuzzy_match=fuzzy_config,
            semantic_match=semantic_config,
            verbose=verbose,
        )
        
        # Initialize RepoMap
        repomap = DockerRepoMap(config)
        
        # Refresh caches if requested
        if refresh:
            console.print("[yellow]Refreshing all caches...[/yellow]")
            repomap.refresh_all_caches()
            console.print("[green]✓ All caches cleared[/green]")
        
        # Get cache status
        status = repomap.get_cache_status()
        
        # Display results
        if output == "json":
            import json
            console.print(json.dumps(status, indent=2, default=str))
        else:
            # Create table display
            table = Table(title="Cache Status")
            table.add_column("Component", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Details", style="yellow")
            
            # Cache enabled status
            cache_enabled = "✓ Enabled" if status["cache_enabled"] else "✗ Disabled"
            table.add_row("Cache System", cache_enabled, f"Project: {status['project_root']}")
            
            # Fuzzy matcher cache details
            if status["fuzzy_matcher_cache"]:
                cache_stats = status["fuzzy_matcher_cache"]
                cache_details = (
                    f"Size: {cache_stats['cache_size']}/{cache_stats['max_size']} entries\n"
                    f"Hit rate: {cache_stats['hit_rate_percent']}%\n"
                    f"Files tracked: {cache_stats['tracked_files']}"
                )
                table.add_row("Fuzzy Matcher", "✓ Active", cache_details)
            else:
                table.add_row("Fuzzy Matcher", "✗ No cache", "Cache disabled or not initialized")
            
            console.print(table)
            
            # Show tracked files if verbose
            if verbose and status["tracked_files"]:
                files_table = Table(title="Tracked Files")
                files_table.add_column("File Path", style="cyan")
                
                for file_path in status["tracked_files"]:
                    files_table.add_row(file_path)
                
                console.print(files_table)
        
    except Exception as e:
        error_response = create_error_response(str(e), "CacheError")
        console.print(f"[red]Error: {error_response.error}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()
