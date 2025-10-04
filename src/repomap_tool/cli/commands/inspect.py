"""
Inspect commands for RepoMap-Tool CLI.

This module contains commands for code inspection, analysis, and discovery.
Merges functionality from the previous 'analyze' and 'search' commands.
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
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.console import get_console


@click.group()
@click.pass_context
def inspect(ctx: click.Context) -> None:
    """Inspect and analyze code repository structure, dependencies, and patterns."""
    pass


@inspect.command()
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
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
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
def find(
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
    """Find identifiers in a project using intelligent matching."""

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

        # Display results using OutputManager
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(response, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)


@inspect.command()
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
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def cycles(
    project_path: Optional[str],
    config: Optional[str],
    output: str,
    verbose: bool,
) -> None:
    """Inspect for circular dependencies in the project."""

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

        # Display results using OutputManager
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(cycles, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)


@inspect.command()
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="Specific files to inspect (relative to project root)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--max-tokens",
    type=int,
    default=4000,
    help="Maximum tokens for LLM optimization",
)
@click.pass_context
def centrality(
    ctx: click.Context,
    project_path: Optional[str],
    files: tuple,
    output: str,
    verbose: bool,
    config: Optional[str],
    max_tokens: int,
) -> None:
    """Inspect centrality analysis for project files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create configuration using factory
        from repomap_tool.core.config_factory import get_config_factory

        config_factory = get_config_factory()
        config_obj = config_factory.create_analysis_config(
            project_root=resolved_project_path,
            verbose=verbose,
        )

        # Use OutputManager for progress messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🎯 Inspecting centrality for project: {resolved_project_path}"
        )

        if files:
            output_manager.display_progress(f"📁 Files: {', '.join(files)}")
        else:
            output_manager.display_progress("📁 Inspecting all files")

        # Use service factory for proper dependency injection
        from repomap_tool.cli.services import get_service_factory
        from repomap_tool.dependencies import AnalysisFormat

        # Create services using DI
        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config_obj)

        # Build dependency graph
        dependency_graph = repomap_service.build_dependency_graph()

        # Get LLM analyzer from service factory
        llm_analyzer = service_factory.get_llm_analyzer(config_obj)

        # Determine files to analyze
        if files:
            file_paths = list(files)
        else:
            # Analyze all files in the project
            from repomap_tool.core.file_scanner import get_project_files

            all_files = get_project_files(resolved_project_path, verbose=verbose)
            file_paths = all_files

        # Convert output format - text uses TEXT for rich hierarchical output, json for structured data
        format_mapping = {
            "text": AnalysisFormat.TEXT,  # Rich hierarchical format (most informative for LLM)
            "json": AnalysisFormat.JSON,
        }
        analysis_format = format_mapping.get(output, AnalysisFormat.TEXT)

        # Perform centrality analysis
        try:
            result = llm_analyzer.analyze_file_centrality(file_paths, analysis_format)
            output_manager.display(result, output_config)
        except Exception as analysis_error:
            output_manager.display_error(analysis_error, output_config)
            output_manager.display_progress(
                "This might be due to missing dependency analysis. Try running dependency analysis first."
            )

        output_manager.display_success("Centrality inspection completed", output_config)
        output_manager.display_progress(f"📊 Output format: {output}")
        output_manager.display_progress(f"🔢 Max tokens: {max_tokens}")

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)


@inspect.command()
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
    "--files",
    "-f",
    multiple=True,
    required=True,
    help="Files to inspect impact for (relative to project root)",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option(
    "--max-tokens",
    type=int,
    default=4000,
    help="Maximum tokens for LLM optimization",
)
@click.pass_context
def impact(
    ctx: click.Context,
    project_path: Optional[str],
    config: Optional[str],
    files: tuple,
    output: str,
    verbose: bool,
    max_tokens: int,
) -> None:
    """Inspect impact of changes to specific files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    if not files:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(
            ValueError("Must specify at least one file with --files"), output_config
        )
        sys.exit(1)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Create configuration using factory
        from repomap_tool.core.config_factory import get_config_factory

        config_factory = get_config_factory()
        config_obj = config_factory.create_analysis_config(
            project_root=resolved_project_path,
            verbose=verbose,
        )

        # Use OutputManager for progress messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🎯 Inspecting impact for project: {resolved_project_path}"
        )
        output_manager.display_progress(f"📁 Target files: {', '.join(files)}")

        # Get service factory and create services
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap_service = service_factory.create_repomap_service(config_obj)
        llm_analyzer = service_factory.get_llm_analyzer(config_obj)

        # Build dependency graph (required for reverse dependency analysis)
        dependency_graph = repomap_service.build_dependency_graph()

        # Set max tokens for the analyzer
        llm_analyzer.max_tokens = max_tokens

        # Use OutputManager for progress messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        # Perform impact analysis
        try:
            # Print output format
            output_manager.display_progress(f"📊 Output format: {output}")

            # Convert output format string to enum - text uses TEXT for best LLM consumption
            from repomap_tool.dependencies import AnalysisFormat

            format_mapping = {
                "text": AnalysisFormat.TEXT,  # Most informative for LLM
                "json": AnalysisFormat.JSON,
            }
            format_enum = format_mapping.get(output, AnalysisFormat.TEXT)

            # Analyze impact for the specified files
            result = llm_analyzer.analyze_file_impact(files, format_enum)

            # Display the result using OutputManager
            output_manager.display(result, output_config)

            # Print completion message
            output_manager.display_success("Impact inspection completed", output_config)

        except Exception as analysis_error:
            output_manager.display_error(analysis_error, output_config)
            if verbose:
                import traceback

                output_manager.display_progress(f"Traceback: {traceback.format_exc()}")
            sys.exit(1)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)
