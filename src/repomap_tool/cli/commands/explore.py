"""
Explore commands for RepoMap-Tool CLI.

This module contains commands for session-based exploration.
"""

import sys
from typing import Any, Optional
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...models import create_error_response, RepoMapConfig
from ...core import RepoMapService
from ...core.config_service import get_config
from ...core.container_config import configure_container
from ..controllers.exploration_controller import ExplorationController
from ..config.loader import resolve_project_path
from ..output import OutputManager, OutputConfig, OutputFormat
from ..utils.session import get_project_path_from_session, get_or_create_session
from ..utils.console import get_console
from dependency_injector.containers import DynamicContainer


# Use DI-provided console instead of direct instantiation
# def get_explore_console() -> Console:
#     """Get console instance using dependency injection."""
#     ctx = click.get_current_context()
#     return get_console(ctx)


def create_exploration_controller_with_repomap(
    container: DynamicContainer, # Accept container instance
    config_obj: RepoMapConfig, output_format: str = "text", verbose: bool = True
) -> ExplorationController:
    """Create and properly configure an ExplorationController with repomap injection.

    This helper function centralizes the controller setup logic and ensures
    the critical repomap service is properly injected into all dependencies.

    Args:
        container: The main DI container instance.
        config_obj: RepoMapConfig object
        output_format: Output format for the controller
        verbose: Whether to enable verbose logging

    Returns:
        Properly configured ExplorationController instance
    """
    from repomap_tool.cli.controllers import ControllerConfig
    # from repomap_tool.cli.services import get_service_factory # No longer directly needed here

    # Initialize RepoMap service (critical for controller dependencies) from the provided container
    repomap = container.repo_map_service()

    # Create controller configuration
    controller_config = ControllerConfig(
        project_root=config_obj.project_root,  # Pass project_root from config_obj
        max_tokens=get_config("EXPLORATION_MAX_TOKENS", 4000),
        output_format=output_format,
        verbose=verbose,
    )

    # Create exploration controller with injected dependencies
    exploration_controller = container.exploration_controller()
    exploration_controller.config = controller_config

    # CRITICAL: Inject repomap into all controller dependencies
    # This is the bug fix - these injections were missing in focus/expand/prune/map/trees commands
    exploration_controller.search_controller.repomap_service = repomap
    exploration_controller.tree_builder.repo_map = repomap
    exploration_controller.tree_builder.entrypoint_discoverer.repo_map = repomap
    exploration_controller.search_controller.config = controller_config

    return exploration_controller


@click.group()
def explore() -> None:
    """Session-based exploration commands."""
    pass


@explore.command()
@click.argument("intent")
@click.option("--session", "-s", help="Session ID (or use REPOMAP_SESSION env var)")
@click.option("--max-depth", default=3, help="Maximum tree depth")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
@click.pass_context
@click.argument("input_paths", nargs=-1, type=click.Path(exists=True, file_okay=True, dir_okay=True, resolve_path=True, path_type=Path), required=False)
def start(
    ctx: click.Context,
    intent: str,
    session: Optional[str],
    max_depth: int,
    output: str,
    config: Optional[str],
    input_paths: tuple,
) -> None:
    """Discover exploration trees from intent."""

    try:
        ctx = click.get_current_context()
        # Resolve project path from argument, config file, or discovery
        # Use project_root from ctx.obj if available, otherwise resolve from current working directory
        project_root = ctx.obj.get("project_root")
        resolved_project_path = resolve_project_path(project_root, None)

        # Get or create session ID
        session_id = get_or_create_session(session)

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Override tree-specific settings
        config_obj.trees.max_depth = max_depth

        # Use OutputManager for progress and success messages
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat(output))

        output_manager.display_progress(
            f"🌳 Starting exploration session: {session_id}"
        )
        output_manager.display_progress(f"🎯 Intent: {intent}")
        output_manager.display_progress(f"📁 Project: {resolved_project_path}")

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format=output, verbose=True
        )

        # Execute exploration
        result_view_model = exploration_controller.start_exploration(
            intent=intent,
            project_path=resolved_project_path,
            max_depth=max_depth,
            max_tokens=get_config("EXPLORATION_MAX_TOKENS", 4000),
        )

        # Display results
        # output_config is already defined above, no need to redefine
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "ExplorationError")
        # Ensure output_manager is available even in error case if it was not instantiated
        # or if an error occurred during its instantiation.
        # However, for consistency and adherence to DI principles, we assume it's always available
        # after configure_container.
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.argument("tree_id", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option(
    "--output",
    "-o",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format: 'text' for rich LLM-optimized output, 'json' for structured data",
)
def focus(tree_id: str, session: Optional[str], output: str) -> None:
    """Focus on a specific exploration tree."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)

        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for progress message
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display_progress(
            f"🎯 Focused on tree: {tree_id} in session {session_id}"
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format=output, verbose=True
        )

        # Execute focus operation
        result_view_model = exploration_controller.focus_tree(
            session_id=session_id,
            tree_id=tree_id,
        )

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "FocusError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.argument("expansion_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def expand(expansion_area: str, session: Optional[str], tree: Optional[str]) -> None:
    """Expand specific areas of the exploration tree."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for success message
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Expanded area: {expansion_area} in tree {tree_id}", output_config
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format="text", verbose=True
        )

        # Execute expansion operation
        result_view_model = exploration_controller.expand_tree(
            session_id=session_id,
            tree_id=tree_id,
            area=expansion_area,
        )

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "ExpansionError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.argument("prune_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def prune(prune_area: str, session: Optional[str], tree: Optional[str]) -> None:
    """Prune specific areas of the exploration tree."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for success message
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Pruned area: {prune_area} from tree {tree_id}", output_config
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format="text", verbose=True
        )

        # Execute pruning operation
        result_view_model = exploration_controller.prune_tree(
            session_id=session_id,
            tree_id=tree_id,
            area=prune_area,
            reason="User requested",
        )

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "PruningError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
@click.option("--include-code", is_flag=True, help="Include code snippets in output")
def map(session: Optional[str], tree: Optional[str], include_code: bool) -> None:
    """Generate repomap from current tree state."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for success message
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Generated map for tree {tree_id} (include_code: {include_code})",
            output_config,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format="text", verbose=True
        )

        # Execute mapping operation
        result_view_model = exploration_controller.map_tree(
            session_id=session_id,
            tree_id=tree_id,
            include_code=include_code,
            max_tokens=get_config("EXPLORATION_MAX_TOKENS", 4000),
        )

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "MappingError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
def trees(session: Optional[str]) -> None:
    """List all exploration trees in the session."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)

        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for placeholder trees table
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        table = Table(title=f"🌳 Trees in Session: {session_id}")
        table.add_column("Tree ID", style="cyan", no_wrap=True)
        table.add_column("Root", style="green")
        table.add_column("Nodes", justify="right", style="magenta")
        table.add_column("Status", style="yellow")

        # Placeholder data
        table.add_row("tree_1", "main.py", "15", "🎯 FOCUSED")
        table.add_row("tree_2", "auth.py", "8", "")

        output_manager.display(table, output_config)

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format="text", verbose=True
        )

        # Execute tree listing operation
        result_view_model = exploration_controller.list_trees(session_id=session_id)

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "TreeListError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
def status(session: Optional[str]) -> None:
    """Show current exploration session status."""

    try:
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)

        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=ctx.obj.get("project_root"),
            config_file=None,
            create_if_missing=True,
            verbose=True,
        )

        # Configure the container with the loaded config_obj
        configure_container(ctx.obj["container"], config_obj)

        # Use OutputManager for session info
        output_manager: OutputManager = ctx.obj["container"].output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        table = Table(title=f"📊 Session Status: {session_id}")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Session ID", session_id)
        table.add_row("Project Path", "/current/project")
        table.add_row("Total Trees", "2")
        table.add_row("Current Focus", "tree_1")

        output_manager.display(table, output_config)

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            ctx.obj["container"], # Pass the container instance
            config_obj, output_format="text", verbose=True
        )

        # Execute status operation
        result_view_model = exploration_controller.get_session_status(
            session_id=session_id
        )

        # Display results
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "StatusError")
        # Ensure output_manager is available even in error case
        output_manager_error: OutputManager = ctx.obj["container"].output_manager()
        output_config_error = OutputConfig(format=OutputFormat.TEXT)
        output_manager_error.display_error(error_response, output_config_error)
        sys.exit(1)
