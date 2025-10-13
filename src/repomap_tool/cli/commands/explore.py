"""
Explore commands for RepoMap-Tool CLI.

This module contains commands for session-based exploration.
"""

import sys
from typing import Any, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ...models import create_error_response
from ...core import RepoMapService
from ...core.config_service import get_config
from ..config.loader import resolve_project_path
from ..output import OutputManager, OutputConfig, OutputFormat, get_output_manager
from ..utils.session import get_project_path_from_session, get_or_create_session
from ..utils.console import get_console


# Use DI-provided console instead of direct instantiation
def get_explore_console() -> Console:
    """Get console instance using dependency injection."""
    ctx = click.get_current_context()
    return get_console(ctx)


def create_exploration_controller_with_repomap(
    config_obj: Any, output_format: str = "text", verbose: bool = True
) -> Any:
    """
    Create and properly configure an ExplorationController with repomap injection.

    This helper function centralizes the controller setup logic and ensures
    the critical repomap service is properly injected into all dependencies.

    Args:
        config_obj: RepoMapConfig object
        output_format: Output format for the controller
        verbose: Whether to enable verbose logging

    Returns:
        Properly configured ExplorationController instance
    """
    from repomap_tool.core.container import create_container
    from repomap_tool.cli.controllers import ControllerConfig
    from repomap_tool.cli.services import get_service_factory

    # Create DI container
    container = create_container(config_obj)

    # Initialize RepoMap service (critical for controller dependencies)
    service_factory = get_service_factory()
    repomap = service_factory.create_repomap_service(config_obj)

    # Create controller configuration
    controller_config = ControllerConfig(
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
@click.argument("intent", type=str)
@click.argument(
    "project_path",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    required=False,
)
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
def start(
    intent: str,
    project_path: Optional[str],
    session: Optional[str],
    max_depth: int,
    output: str,
    config: Optional[str],
) -> None:
    """Discover exploration trees from intent."""

    try:
        ctx = click.get_current_context()
        # Resolve project path from argument, config file, or discovery
        resolved_project_path = resolve_project_path(project_path, config)

        # Get or create session ID
        session_id = get_or_create_session(session)

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=resolved_project_path,
            config_file=config,
            create_if_missing=False,
            verbose=True,
        )

        # Override tree-specific settings
        config_obj.trees.max_depth = max_depth

        # Initialize RepoMap using service factory
        from repomap_tool.cli.services import get_service_factory

        service_factory = get_service_factory()
        repomap = service_factory.create_repomap_service(config_obj)

        # Use OutputManager for progress and success messages
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat(output))

        output_manager.display_progress(
            f"🌳 Starting exploration session: {session_id}"
        )
        output_manager.display_progress(f"🎯 Intent: {intent}")
        output_manager.display_progress(f"📁 Project: {resolved_project_path}")

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
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
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(result_view_model, output_config, ctx)

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
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Use OutputManager for progress message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display_progress(
            f"🎯 Focused on tree: {tree_id} in session {session_id}"
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            config_obj, output_format=output, verbose=True
        )

        # Execute focus operation
        result_view_model = exploration_controller.focus_tree(
            session_id=session_id,
            tree_id=tree_id,
        )

        # Display results
        output_config = OutputConfig(format=OutputFormat(output))
        output_manager.display(result_view_model, output_config, ctx)

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
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Expanded area: {expansion_area} in tree {tree_id}", output_config
        )
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            config_obj, output_format="text", verbose=True
        )

        # Execute expansion operation
        result_view_model = exploration_controller.expand_tree(
            session_id=session_id,
            tree_id=tree_id,
            area=expansion_area,
        )

        # Display results
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display(result_view_model, output_config, ctx)

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
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Pruned area: {prune_area} from tree {tree_id}", output_config
        )
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
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
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display(result_view_model, output_config, ctx)

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
        ctx = click.get_current_context()
        session_id = session or get_or_create_session(session)
        tree_id = tree or "current"
        # Use OutputManager for success message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_success(
            f"Generated map for tree {tree_id} (include_code: {include_code})",
            output_config,
        )
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
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
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display(result_view_model, output_config, ctx)

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
        ctx = click.get_current_context()
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
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            config_obj, output_format="text", verbose=True
        )

        # Execute tree listing operation
        result_view_model = exploration_controller.list_trees(session_id=session_id)

        # Display results
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "TreeListError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)


@explore.command()
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
    default=get_config("HYBRID_THRESHOLD", 0.3),
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
def find(
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
    """Find identifiers in a project using intelligent matching for exploration."""
    
    # Get console instance (automatically configured with no-color if set)
    ctx = click.get_current_context()
    console = get_console(ctx)

    try:
        # Resolve project path from argument, config file, or discovery
        from repomap_tool.cli.config.loader import resolve_project_path
        resolved_project_path = resolve_project_path(project_path, config)

        # Load or create configuration (properly handles config files)
        from repomap_tool.cli.config.loader import load_or_create_config

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
            match_type=match_type,
            threshold=threshold,  # Keep as float for API consistency
            max_results=max_results,
            strategies=list(strategies) if strategies else None,
        )

        # Initialize services using service factory
        from rich.progress import Progress, SpinnerColumn, TextColumn
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Initializing services...", total=None)

            from repomap_tool.cli.services import get_service_factory
            from repomap_tool.cli.controllers.search_controller import SearchController
            from repomap_tool.cli.controllers.view_models import (
                ControllerConfig,
                AnalysisType,
            )
            from repomap_tool.core.container import create_container

            service_factory = get_service_factory()
            repomap = service_factory.create_repomap_service(config_obj)

            # Get matchers from the container
            container = create_container(config_obj)
            fuzzy_matcher = container.fuzzy_matcher()
            semantic_matcher = (
                container.adaptive_semantic_matcher()
                if config_obj.semantic_match.enabled
                else None
            )

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


@explore.command()
@click.option("--session", "-s", help="Session ID")
def status(session: Optional[str]) -> None:
    """Show current exploration session status."""

    try:
        ctx = click.get_current_context()
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
        # Load configuration
        from repomap_tool.cli.config.loader import load_or_create_config

        config_obj, was_created = load_or_create_config(
            project_path=None,  # Will be resolved from session
            config_file=None,
            create_if_missing=False,
            verbose=True,
        )

        # Create properly configured exploration controller with repomap injection
        exploration_controller = create_exploration_controller_with_repomap(
            config_obj, output_format="text", verbose=True
        )

        # Execute status operation
        result_view_model = exploration_controller.get_session_status(
            session_id=session_id
        )

        # Display results
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display(result_view_model, output_config, ctx)

    except Exception as e:
        error_response = create_error_response(str(e), "StatusError")
        # Use OutputManager for error message
        output_manager = get_output_manager()
        output_config = OutputConfig(format=OutputFormat.TEXT)
        output_manager.display_error(error_response, output_config)
        sys.exit(1)
