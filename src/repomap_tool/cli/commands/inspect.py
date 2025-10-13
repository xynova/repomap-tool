"""
Inspect commands for RepoMap-Tool CLI.

This module contains commands for code inspection, analysis, and discovery.
Merges functionality from the previous 'analyze' and 'search' commands.
"""

import os
import sys
from typing import Optional, Literal

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from repomap_tool.core.config_service import get_config

from ...models import (
    SearchRequest,
    RepoMapConfig,
    DependencyConfig,
    create_error_response,
)
from ...core import RepoMapService
from ..config.loader import (
    resolve_project_path,
)
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.console import get_console


@click.group()
@click.pass_context
def inspect(ctx: click.Context) -> None:
    """Inspect and analyze code repository structure, dependencies, and patterns."""
    pass


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

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=False,
            verbose=verbose,
        )

        # Initialize RepoMap with detailed progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading configuration...", total=None)

            from repomap_tool.cli.services import get_service_factory

            progress.update(task, description="Creating service factory...")
            service_factory = get_service_factory()
            
            progress.update(task, description="Initializing RepoMap service...")
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

        # Display results using OutputManager (with improved formatting)
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

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=False,
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

        # Use DI container to get Controllers
        from repomap_tool.core.container import create_container
        from repomap_tool.cli.controllers import ControllerConfig

        # Create DI container and get Controller
        container = create_container(config_obj)
        centrality_controller = container.centrality_controller()

        # Configure Controller
        controller_config = ControllerConfig(
            max_tokens=max_tokens, verbose=verbose, output_format=output
        )
        centrality_controller.config = controller_config

        # Perform centrality analysis using Controller
        # The controller will handle file discovery internally using the centralized service
        try:
            # Execute Controller to get ViewModel (no need to pass files)
            view_model = centrality_controller.execute()

            # Display the ViewModel using OutputManager
            output_manager.display(view_model, output_config)
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

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=False,
            verbose=verbose,
        )

        # Use OutputManager for progress messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🎯 Inspecting impact for project: {resolved_project_path}"
        )
        output_manager.display_progress(f"📁 Target files: {', '.join(files)}")

        # Use DI container to get Controllers
        from repomap_tool.core.container import create_container
        from repomap_tool.cli.controllers import ControllerConfig

        # Create DI container and get Controller
        container = create_container(config_obj)
        impact_controller = container.impact_controller()

        # Configure Controller
        controller_config = ControllerConfig(
            max_tokens=max_tokens, verbose=verbose, output_format=output
        )
        impact_controller.config = controller_config

        # Use OutputManager for progress messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        # Perform impact analysis using Controller
        try:
            # Print output format
            output_manager.display_progress(f"📊 Output format: {output}")

            # Execute Controller to get ViewModel
            view_model = impact_controller.execute(list(files))

            # Display the ViewModel using OutputManager
            output_manager.display(view_model, output_config)

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
