"""
Explore commands for RepoMap-Tool CLI.

This module contains commands for session-based exploration.
"""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...models import create_error_response
from ...core import RepoMapService
from ..config.loader import resolve_project_path, create_tree_config
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.session import get_project_path_from_session, get_or_create_session
from ..utils.console import get_console


# Use DI-provided console instead of direct instantiation
def get_explore_console() -> Console:
    """Get console instance using dependency injection."""
    ctx = click.get_current_context()
    return get_console(ctx)


@click.group()
def explore() -> None:
    """Session-based exploration commands."""
    pass


@explore.command()
@click.argument("intent", type=str)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
@click.option("--session", "-s", help="Session ID (or use REPOMAP_SESSION env var)")
@click.option("--max-depth", default=3, help="Maximum tree depth")
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Configuration file path",
)
def start(
    intent: str,
    project_path: Optional[str],
    session: Optional[str],
    max_depth: int,
    config: Optional[str],
) -> None:
    """Discover exploration trees from intent."""

    try:
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Get or create session ID
        session_id = get_or_create_session(session)

        # Create configuration
        config_obj = create_tree_config(resolved_project_path, max_depth, verbose=True)

        # Initialize RepoMap using service factory
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config_obj)

        # Use OutputManager for progress and success messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)

        output_manager.display_progress(
            f"🌳 Starting exploration session: {session_id}"
        )
        output_manager.display_progress(f"🎯 Intent: {intent}")
        output_manager.display_progress(f"📁 Project: {resolved_project_path}")

        # Placeholder for tree discovery logic
        # TODO: Implement actual tree discovery
        output_manager.display_success("Exploration session created", output_config)
        output_manager.display_progress("Use: focus tree_1 to focus on a tree")

    except Exception as e:
        error_response = create_error_response(str(e), "ExplorationError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.argument("tree_id", type=str)
@click.option("--session", "-s", help="Session ID")
def focus(tree_id: str, session: Optional[str]) -> None:
    """Focus on a specific exploration tree."""

    try:
        session_id = session or get_or_create_session(session)
        # Use OutputManager for progress message
        output_manager = get_output_manager()
        output_manager.display_progress(
            f"🎯 Focused on tree: {tree_id} in session {session_id}"
        )
        # TODO: Implement actual tree focus logic

    except Exception as e:
        error_response = create_error_response(str(e), "FocusError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.argument("expansion_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def expand(expansion_area: str, session: Optional[str], tree: Optional[str]) -> None:
    """Expand specific areas of the exploration tree."""

    try:
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Expanded area: {expansion_area} in tree {tree_id}", output_config
        )
        # TODO: Implement actual tree expansion logic

    except Exception as e:
        error_response = create_error_response(str(e), "ExpansionError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.argument("prune_area", type=str)
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
def prune(prune_area: str, session: Optional[str], tree: Optional[str]) -> None:
    """Prune specific areas of the exploration tree."""

    try:
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Pruned area: {prune_area} from tree {tree_id}", output_config
        )
        # TODO: Implement actual tree pruning logic

    except Exception as e:
        error_response = create_error_response(str(e), "PruningError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
@click.option("--tree", "-t", help="Tree ID (uses current focus if not specified)")
@click.option("--include-code", is_flag=True, help="Include code snippets in output")
def map(session: Optional[str], tree: Optional[str], include_code: bool) -> None:
    """Generate repomap from current tree state."""

    try:
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Generated map for tree {tree_id} (include_code: {include_code})",
            output_config,
        )
        # TODO: Implement actual tree mapping logic

    except Exception as e:
        error_response = create_error_response(str(e), "MappingError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
def trees(session: Optional[str]) -> None:
    """List all exploration trees in the session."""

    try:
        session_id = session or get_or_create_session(session)

        # Display placeholder trees table
        output_manager = get_output_manager()
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
        # TODO: Implement actual tree listing logic

    except Exception as e:
        error_response = create_error_response(str(e), "TreeListError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
@click.option("--session", "-s", help="Session ID")
def status(session: Optional[str]) -> None:
    """Show current exploration session status."""

    try:
        session_id = session or get_or_create_session(session)

        # Display session info
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        table = Table(title=f"📊 Session Status: {session_id}")
        table.add_column("Property", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")

        table.add_row("Session ID", session_id)
        table.add_row("Project Path", "/current/project")
        table.add_row("Total Trees", "2")
        table.add_row("Current Focus", "tree_1")

        output_manager.display(table, output_config)
        # TODO: Implement actual session status logic

    except Exception as e:
        error_response = create_error_response(str(e), "StatusError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)
