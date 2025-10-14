#!/usr/bin/env python3
"""
Search commands for RepoMap-Tool CLI.

This module provides search functionality for finding identifiers, functions, classes,
and other code elements within the project.
"""

import sys
from typing import Any, Optional

import click
from rich.console import Console

from ..config.loader import load_or_create_config, resolve_project_path
from ..utils.console import get_console
from ...core.config_service import get_config
from ...models import create_error_response
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager


@click.command()
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
    "--threshold",
    default=get_config("HYBRID_THRESHOLD", 0.2),
    type=float,
    help="Match threshold (0.0-1.0)",
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
@click.pass_context
def search(
    ctx: click.Context,
    query: str,
    project_path: Optional[str],
    config: Optional[str],
    match_type: str,
    threshold: float,
    max_results: int,
    strategies: tuple,
    output: str,
    verbose: bool,
    log_level: str,
    cache_size: int,
) -> None:
    """Search for identifiers using intelligent matching strategies.

    Supports fuzzy, semantic, and hybrid matching via --match-type flag.

    Examples:
        repomap search "user authentication" --match-type hybrid
        repomap search "matcher" --match-type fuzzy --threshold 0.3
        repomap search "database" --match-type semantic --max-results 20
    """

    # Get console instance (automatically configured with no-color if set)
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Load or create configuration (properly handles config files)
        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=False,
            verbose=verbose,
        )

        # Override specific search settings
        config_obj.fuzzy_match.enabled = match_type in ["fuzzy", "hybrid"]
        config_obj.semantic_match.enabled = match_type in ["semantic", "hybrid"]
        config_obj.performance.cache_size = cache_size
        config_obj.log_level = log_level

        # Update configuration with threshold from CLI
        # Convert float threshold (0.0-1.0) to integer (0-100) for internal use
        threshold_int = int(threshold * 100) if threshold <= 1.0 else int(threshold)
        config_obj.fuzzy_match.threshold = threshold_int
        config_obj.semantic_match.threshold = threshold

        # Create search request
        from repomap_tool.models import SearchRequest

        request = SearchRequest(
            query=query,
            match_type=match_type,  # type: ignore[arg-type]
            threshold=threshold,  # Keep as float for API consistency
            max_results=max_results,
            strategies=list(strategies) if strategies else None,
        )

        # Initialize services using service factory with detailed progress
        from rich.progress import Progress, SpinnerColumn, TextColumn

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading configuration...", total=None)

            from repomap_tool.cli.services import get_service_factory
            from repomap_tool.cli.controllers.search_controller import SearchController
            from repomap_tool.cli.controllers.view_models import (
                ControllerConfig,
                AnalysisType,
            )
            from repomap_tool.core.container import create_container

            progress.update(task, description="Creating service factory...")
            service_factory = get_service_factory()

            progress.update(task, description="Initializing RepoMap service...")
            repomap = service_factory.create_repomap_service(config_obj)

            progress.update(
                task, description="Loading dependency injection container..."
            )
            container = create_container(config_obj)

            progress.update(task, description="Initializing fuzzy matcher...")
            fuzzy_matcher = container.fuzzy_matcher()

            progress.update(task, description="Initializing semantic matcher...")
            semantic_matcher = (
                container.adaptive_semantic_matcher()
                if config_obj.semantic_match.enabled
                else None
            )

            progress.update(task, description="Loading embedding model...")
            embedding_matcher = container.embedding_matcher()

            progress.update(task, description="Initializing hybrid matcher...")
            hybrid_matcher = container.hybrid_matcher()

            progress.update(task, description="Creating search controller...")

            # Create controller configuration
            controller_config = ControllerConfig(
                max_tokens=get_config("MAX_TOKENS", 4000),
                compression_level="medium",
                verbose=verbose,
                output_format=output,
                analysis_type=AnalysisType.SEARCH,
                search_strategy=match_type,
                context_selection="centrality_based",
            )

            # Create search controller
            search_controller = SearchController(
                repomap_service=repomap,
                search_engine=None,  # Not needed for search controller
                fuzzy_matcher=fuzzy_matcher,
                semantic_matcher=semantic_matcher,
                config=controller_config,
            )

            progress.update(task, description="Searching identifiers...")

            # Execute search using controller
            search_view_model = search_controller.execute(request)

            progress.update(task, description="Search complete!")

        # Display results using OutputManager
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(search_view_model, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)
