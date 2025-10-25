"""
Inspect commands for RepoMap-Tool CLI.

This module contains commands for code inspection, analysis, and discovery.
Merges functionality from the previous 'analyze' and 'search' commands.
"""

import os
import sys
from typing import Optional, Literal, List
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from repomap_tool.core.config_service import get_config
from repomap_tool.core.container_config import configure_container
from repomap_tool.cli.config.loader import load_or_create_config

from ...models import (
    SearchRequest,
    RepoMapConfig,
    DependencyConfig,
    create_error_response,
)
from ...core import RepoMapService
from ..config.loader import (
    resolve_project_path,
    load_or_create_config,
)
from ..output import OutputManager, OutputConfig, OutputFormat  # , get_output_manager
from ..utils.console import get_console


@click.group()
@click.pass_context
def inspect(ctx: click.Context) -> None:
    """Inspect and analyze code repository structure, dependencies, and patterns."""
    pass


@inspect.command()
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
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(project_root, None)

        # Load or create configuration (properly handles config files)
        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            verbose=verbose,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for progress and success messages
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat(output))

        # Initialize RepoMap with detailed progress
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Loading configuration...", total=None)

            # Initialize RepoMap service via DI container (no longer using service factory here)
            repomap = ctx.obj["container"].repo_map_service()
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
        output_manager.display(cycles, output_config)

    except Exception as e:
        # Use OutputManager for error handling
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(e, output_config_error)
        sys.exit(1)


@inspect.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.option(
    "--scope",
    type=click.Choice(["file", "package"]),
    default="file",
    help="Analysis scope: 'file' for individual files, 'package' for directories",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=10,
    help="Maximum number of results to show",
)
@click.option(
    "--min-identifiers",
    type=int,
    default=1,
    help="Minimum number of identifiers to include",
)
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format",
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, resolve_path=True, path_type=Path
    ),
    required=False,
)
def density(
    ctx: click.Context,
    config: Optional[str],
    scope: str,
    limit: int,
    min_identifiers: int,
    output: str,
    verbose: bool,
    input_paths: tuple,
) -> None:
    """Inspect code density - files/packages with most identifiers by type."""

    console = get_console(ctx)

    try:
        # Resolve project path and load config
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(project_root, None)

        if resolved_project_path is None:
            raise click.BadParameter("Project path could not be resolved.")

        # If specific input_paths are provided, ensure they are absolute
        target_files = []
        if input_paths:
            for p in input_paths:
                abs_path = Path(p).resolve()
                if not abs_path.is_relative_to(resolved_project_path):
                    raise click.BadParameter(
                        f"Input path '{p}' is not within the project root '{resolved_project_path}'."
                    )
                target_files.append(str(abs_path))
        else:
            # If no specific input_paths, analyze the entire project_root
            target_files = [str(resolved_project_path)]

        config_obj, _ = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            verbose=verbose,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for progress
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat(output))

        output_manager.display_progress(
            f"🎯 Analyzing code density: {resolved_project_path}"
        )

        # Use DI container to get controller
        container = ctx.obj["container"]
        density_controller = container.density_controller()

        # Configure controller
        from repomap_tool.cli.controllers import ControllerConfig

        controller_config = ControllerConfig(
            project_root=resolved_project_path,  # Now a required argument
            verbose=verbose,
            output_format=output,
            scope=scope,
            limit=limit,
            min_identifiers=min_identifiers,
        )
        density_controller.config = controller_config

        # Execute analysis
        view_model = density_controller.execute(
            file_paths=None, scope=scope, limit=limit, min_identifiers=min_identifiers
        )

        # Display results
        output_manager.display(view_model, output_config)
        output_manager.display_success("Density analysis completed", output_config)

    except Exception as e:
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(e, output_config_error)
        sys.exit(1)


@inspect.command()
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
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, resolve_path=True, path_type=Path
    ),
    required=False,
)
def centrality(
    ctx: click.Context,
    files: tuple,
    output: str,
    verbose: bool,
    config: Optional[str],
    max_tokens: int,
    input_paths: tuple,
) -> None:
    """Inspect centrality analysis for project files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(project_root, None)

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            verbose=verbose,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for progress messages
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🎯 Inspecting centrality for project: {resolved_project_path}"
        )

        # Determine target files for analysis
        target_files = []
        if files and input_paths:
            raise click.BadParameter(
                "Cannot specify both --files and positional input paths."
            )
        elif files:
            target_files = []
            project_path = Path(resolved_project_path)
            for f in files:
                file_path = Path(f)
                if file_path.is_absolute():
                    # Absolute path - validate it's within project root
                    if not file_path.is_relative_to(project_path):
                        raise click.BadParameter(
                            f"File '{f}' is not within the project root '{resolved_project_path}'."
                        )
                    target_files.append(str(file_path))
                else:
                    # Relative path - join with project root
                    target_files.append(str(project_path / f))
        elif input_paths:
            project_path = Path(resolved_project_path)
            for p in input_paths:
                abs_path = Path(p).resolve()
                if not abs_path.is_relative_to(project_path):
                    raise click.BadParameter(
                        f"Input path '{p}' is not within the project root '{resolved_project_path}'."
                    )
                target_files.append(str(abs_path))
        else:
            # If no specific files, the controller will discover them within the project_root
            pass

        if target_files:
            output_manager.display_progress(f"📁 Files: {', '.join(target_files)}")
        else:
            output_manager.display_progress("📁 Inspecting all files")

        # Use DI container to get Controllers
        container = ctx.obj["container"]
        centrality_controller = container.centrality_controller()

        # Configure Controller
        from repomap_tool.cli.controllers import ControllerConfig

        controller_config = ControllerConfig(
            project_root=resolved_project_path,  # Add missing project_root
            verbose=verbose,
            output_format=output,
            max_tokens=max_tokens,
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
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(e, output_config_error)
        sys.exit(1)


@inspect.command()
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
@click.argument(
    "input_paths",
    nargs=-1,
    type=click.Path(
        exists=True, file_okay=True, dir_okay=True, resolve_path=True, path_type=Path
    ),
    required=False,
)
def impact(
    ctx: click.Context,
    config: Optional[str],
    files: tuple,
    output: str,
    verbose: bool,
    max_tokens: int,
    input_paths: tuple,
) -> None:
    """Inspect impact of changes to specific files with AST-based analysis."""

    # Get console instance (automatically handles dependency injection from context)
    console = get_console(ctx)

    # Determine target files for analysis
    target_files_for_impact = []
    if files and input_paths:
        raise click.BadParameter(
            "Cannot specify both --files and positional input paths."
        )
    elif files:
        # Ensure files are absolute paths - use the project root from context
        project_root = Path(ctx.obj.get("project_root", ".")).resolve()
        for f in files:
            abs_path = Path(f).resolve()
            if not abs_path.is_relative_to(project_root):  # type: ignore
                raise click.BadParameter(
                    f"File '{f}' is not within the project root '{project_root}'."
                )
            target_files_for_impact.append(str(abs_path))

    elif input_paths:
        project_root = Path(ctx.obj.get("project_root", ".")).resolve()
        for p in input_paths:
            abs_path = Path(p).resolve()
            if not abs_path.is_relative_to(project_root):  # type: ignore
                raise click.BadParameter(
                    f"Input path '{p}' is not within the project root '{project_root}'."
                )
            target_files_for_impact.append(str(abs_path))

    if not target_files_for_impact:
        # Use OutputManager for error handling
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(
            ValueError(
                "Must specify at least one file with --files or as a positional argument."
            ),
            output_config,
        )
        sys.exit(1)

    try:
        # Resolve project path from argument, config file, or discovery
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(project_root, None)

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            verbose=verbose,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for progress messages
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🎯 Inspecting impact for project: {resolved_project_path}"
        )
        output_manager.display_progress(
            f"📁 Target files: {', '.join(target_files_for_impact)}"
        )

        # Use DI container to get Controllers
        container = ctx.obj["container"]
        impact_controller = container.impact_controller()

        # Configure Controller
        from repomap_tool.cli.controllers import ControllerConfig

        controller_config = ControllerConfig(
            project_root=resolved_project_path,  # Add missing project_root
            verbose=verbose,
            output_format=output,
            max_tokens=max_tokens,
        )
        impact_controller.config = controller_config

        # Perform impact analysis using Controller
        try:
            # Print output format
            output_manager.display_progress(f"📊 Output format: {output}")

            # Execute Controller to get ViewModel
            view_model = impact_controller.execute(list(target_files_for_impact))

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
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(e, output_config_error)
        sys.exit(1)
