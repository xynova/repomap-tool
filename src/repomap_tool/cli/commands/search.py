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
from pathlib import Path

from ..config.loader import load_or_create_config, resolve_project_path
from ..utils.console import get_console
from ...core.config_service import get_config
from ...core.container_config import configure_container
from ...models import create_error_response
from ..output import OutputManager, OutputConfig, OutputFormat


@click.command()
@click.argument("query", type=str)
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
@click.argument("input_paths", nargs=-1, type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True, path_type=Path), required=False)
def search(
    ctx: click.Context,
    query: str,
    config: Optional[str],
    match_type: str,
    threshold: float,
    max_results: int,
    strategies: tuple,
    output: str,
    verbose: bool,
    log_level: str,
    cache_size: int,
    input_paths: tuple,
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
        # Resolve project path and load config
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(None, project_root)

        if resolved_project_path is None:
            raise click.BadParameter("Project path could not be resolved.")

        # If specific input_paths are provided, ensure they are absolute
        target_files = []
        if input_paths:
            for p in input_paths:
                abs_path = Path(p).resolve()
                if not abs_path.is_relative_to(resolved_project_path):
                    raise click.BadParameter(f"Input path '{p}' is not within the project root '{resolved_project_path}'.")
                target_files.append(str(abs_path))

        config_obj, was_created = load_or_create_config(
            project_root=resolved_project_path,
            config_file=config,
            create_if_missing=False,
            verbose=verbose,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

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
            target_files=target_files if target_files else None,
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
            container = ctx.obj["container"]

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
                project_root=resolved_project_path,  # Pass project_root
                verbose=verbose,
                output_format=OutputFormat(output),
                max_tokens=get_config("MAX_TOKENS_SEARCH", 2000),
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

        # Get output manager from context (after container is configured and search is complete)
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(search_view_model, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(e, output_config)
        sys.exit(1)
