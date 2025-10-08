from repomap_tool.core.config_service import get_config

"""
Configuration loading and management utilities.

This module handles loading, creating, and managing RepoMap configurations.
"""

import json
import os
from pathlib import Path
from typing import Optional, Literal, Union, Dict, Any, Tuple

from pydantic import ValidationError
from rich.console import Console

from ...models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    PerformanceConfig,
    TreeConfig,
)
from ...utils.file_validator import FileValidator, safe_read_text, safe_write_text

# Note: console should be obtained via get_console(ctx) in functions that need it
from ..utils.console import get_console
import click


def load_config_file(config_path: str) -> RepoMapConfig:
    """Load and validate configuration from file."""
    try:
        # Initialize validator
        validator = FileValidator()

        # Validate and read config file safely
        validated_path = validator.validate_path(
            config_path, must_exist=True, must_be_file=True, allow_create=False
        )

        json_content = validator.safe_read_text(validated_path)
        config_dict = json.loads(json_content)

        # Validate against RepoMapConfig model
        config = RepoMapConfig(**config_dict)
        return config
    except ValidationError as e:
        raise ValueError(f"Invalid configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load configuration file: {e}")


def get_config_file_path(project_path: str) -> Path:
    """Get the path to the .repomap/config.json file for a project."""
    return Path(project_path) / ".repomap" / "config.json"


def discover_config_file(project_path: str) -> Optional[str]:
    """Discover existing config file in the project directory."""
    config_path = get_config_file_path(project_path)
    if config_path.exists():
        return str(config_path)
    return None


def discover_config_file_in_current_dir() -> Optional[RepoMapConfig]:
    """Discover and load config file in current directory or parent directories."""
    current_dir = Path.cwd()

    # Check current directory and parent directories
    for directory in [current_dir] + list(current_dir.parents):
        config_path = directory / ".repomap" / "config.json"
        if config_path.exists():
            try:
                return load_config_file(str(config_path))
            except Exception:
                # If we can't load this config file, continue searching
                continue

    # Also check Docker workspace directory (configurable via env var)
    workspace_dir = os.environ.get("REPOMAP_WORKSPACE_DIR", "/workspace")
    if workspace_dir:
        workspace_path = Path(workspace_dir)
        if workspace_path.exists():
            config_path = workspace_path / ".repomap" / "config.json"
            if config_path.exists():
                try:
                    return load_config_file(str(config_path))
                except Exception:
                    pass

    return None


def resolve_project_path(
    provided_path: Optional[str], config_file: Optional[str]
) -> str:
    """Resolve project path from provided path, config file, or discovered config.

    Args:
        provided_path: Explicitly provided project path
        config_file: Explicitly provided config file path

    Returns:
        Resolved project path

    Raises:
        SystemExit: If no project path can be resolved
    """
    if provided_path:
        return provided_path

    # Try to load config file to get project_root
    config_obj = None
    if config_file:
        config_obj = load_config_file(config_file)
    else:
        # Try to discover config file
        config_obj = discover_config_file_in_current_dir()

    if config_obj is None:
        # Use current directory as fallback when no project path or config is provided
        current_dir = str(Path.cwd())
        # Get console from Click context
        ctx = click.get_current_context(silent=True)
        console = get_console(ctx)
        console.print(
            f"[blue]No project path provided, using current directory: {current_dir}[/blue]"
        )
        return current_dir

    project_path = str(config_obj.project_root)
    # Get console from Click context
    ctx = click.get_current_context(silent=True)
    console = get_console(ctx)
    console.print(f"[blue]Using project path from config: {project_path}[/blue]")
    return project_path


def create_default_config_file(project_path: str, config: RepoMapConfig) -> str:
    """Create a default config file in .repomap/config.json."""
    # Initialize validator
    validator = FileValidator()

    config_path = get_config_file_path(project_path)

    # Create .repomap directory if it doesn't exist using safe directory creation
    config_dir = validator.safe_create_directory(config_path.parent)

    # Validate config file path
    validated_config_path = validator.validate_path(
        config_path, must_exist=False, must_be_file=False, allow_create=True
    )

    # Save config to file using safe writing
    json_content = json.dumps(config.model_dump(), indent=2, default=str)
    validator.safe_write_text(validated_config_path, json_content)

    return str(validated_config_path)


def create_default_config(
    project_path: str,
    fuzzy: bool = True,
    semantic: bool = True,
    threshold: float = get_config("FUZZY_THRESHOLD", 0.7),
    max_results: int = 50,
    output: Literal["text", "json"] = "text",
    verbose: bool = False,
    cache_size: int = get_config("CACHE_SIZE", 1000),
    no_progress: Optional[bool] = None,
    no_monitoring: Optional[bool] = None,
    log_level: Optional[str] = None,
    refresh_cache: Optional[bool] = None,
    **kwargs: Any,  # Accept any other parameters for test compatibility
) -> RepoMapConfig:
    """Create default configuration."""
    if not project_path:
        raise ValueError("Project root cannot be empty")

    # Convert threshold from 0.0-1.0 float to 0-100 integer for FuzzyMatchConfig
    fuzzy_threshold = int(threshold * 100) if threshold <= 1.0 else int(threshold)

    config = RepoMapConfig(
        project_root=Path(project_path),
        verbose=verbose,
        max_results=max_results,
        output_format=output,
        fuzzy_match=FuzzyMatchConfig(
            enabled=fuzzy,
            threshold=fuzzy_threshold,
        ),
        semantic_match=SemanticMatchConfig(
            enabled=semantic,
            threshold=threshold,  # SemanticMatchConfig might still use float
        ),
        performance=PerformanceConfig(
            cache_size=cache_size,
        ),
    )

    # Apply optional parameters
    if log_level is not None:
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log level: {log_level}. Must be one of {valid_log_levels}"
            )
        config.log_level = log_level.upper()
    if refresh_cache is not None:
        config.refresh_cache = refresh_cache
    if no_progress is not None:
        config.performance.enable_progress = not no_progress
    if no_monitoring is not None:
        config.performance.enable_monitoring = not no_monitoring

    return config


def apply_environment_overrides(config: RepoMapConfig) -> RepoMapConfig:
    """Apply environment variable overrides to configuration."""
    # Core configuration
    verbose_env = os.environ.get("REPOMAP_VERBOSE")
    if verbose_env:
        config.verbose = verbose_env.lower() in ("true", "1", "yes")

    log_level_env = os.environ.get("REPOMAP_LOG_LEVEL")
    if log_level_env:
        config.log_level = log_level_env

    output_format_env = os.environ.get("REPOMAP_OUTPUT_FORMAT")
    if output_format_env:
        config.output_format = output_format_env  # type: ignore

    # Fuzzy matching configuration
    fuzzy_threshold_env = os.environ.get("REPOMAP_FUZZY_THRESHOLD")
    if fuzzy_threshold_env:
        try:
            config.fuzzy_match.threshold = int(fuzzy_threshold_env)
        except ValueError:
            pass  # Keep default if invalid

    fuzzy_strategies_env = os.environ.get("REPOMAP_FUZZY_STRATEGIES")
    if fuzzy_strategies_env:
        config.fuzzy_match.strategies = [
            s.strip() for s in fuzzy_strategies_env.split(",")
        ]

    fuzzy_cache_results_env = os.environ.get("REPOMAP_FUZZY_CACHE_RESULTS")
    if fuzzy_cache_results_env:
        config.fuzzy_match.cache_results = fuzzy_cache_results_env.lower() in (
            "true",
            "1",
            "yes",
        )

    semantic_enabled_env = os.environ.get("REPOMAP_SEMANTIC_ENABLED")
    if semantic_enabled_env:
        config.semantic_match.enabled = semantic_enabled_env.lower() in (
            "true",
            "1",
            "yes",
        )

    semantic_threshold_env = os.environ.get("REPOMAP_SEMANTIC_THRESHOLD")
    if semantic_threshold_env:
        try:
            config.semantic_match.threshold = float(semantic_threshold_env)
        except ValueError:
            pass  # Keep default if invalid

    max_results_env = os.environ.get("REPOMAP_MAX_RESULTS")
    if max_results_env:
        try:
            config.max_results = int(max_results_env)
        except ValueError:
            pass  # Keep default if invalid

    # Performance configuration
    max_workers_env = os.environ.get("REPOMAP_MAX_WORKERS")
    if max_workers_env:
        try:
            config.performance.max_workers = int(max_workers_env)
        except ValueError:
            pass

    enable_monitoring_env = os.environ.get("REPOMAP_ENABLE_MONITORING")
    if enable_monitoring_env:
        config.performance.enable_monitoring = enable_monitoring_env.lower() in (
            "true",
            "1",
            "yes",
        )

    cache_size_env = os.environ.get("REPOMAP_CACHE_SIZE")
    if cache_size_env:
        try:
            config.performance.cache_size = int(cache_size_env)
        except ValueError:
            pass  # Keep default if invalid

    enable_progress_env = os.environ.get("REPOMAP_ENABLE_PROGRESS")
    if enable_progress_env:
        config.performance.enable_progress = enable_progress_env.lower() in (
            "true",
            "1",
            "yes",
        )

    # Tree configuration
    tree_max_depth_env = os.environ.get("REPOMAP_TREE_MAX_DEPTH")
    if tree_max_depth_env:
        try:
            config.trees.max_depth = int(tree_max_depth_env)
        except ValueError:
            pass

    tree_max_trees_per_session_env = os.environ.get(
        "REPOMAP_TREE_MAX_TREES_PER_SESSION"
    )
    if tree_max_trees_per_session_env:
        try:
            config.trees.max_trees_per_session = int(tree_max_trees_per_session_env)
        except ValueError:
            pass

    tree_entrypoint_threshold_env = os.environ.get("REPOMAP_TREE_ENTRYPOINT_THRESHOLD")
    if tree_entrypoint_threshold_env:
        try:
            config.trees.entrypoint_threshold = float(tree_entrypoint_threshold_env)
        except ValueError:
            pass

    tree_enable_code_snippets_env = os.environ.get("REPOMAP_TREE_ENABLE_CODE_SNIPPETS")
    if tree_enable_code_snippets_env:
        config.trees.enable_code_snippets = tree_enable_code_snippets_env.lower() in (
            "true",
            "1",
            "yes",
        )

    tree_cache_tree_structures_env = os.environ.get(
        "REPOMAP_TREE_CACHE_TREE_STRUCTURES"
    )
    if tree_cache_tree_structures_env:
        config.trees.cache_tree_structures = tree_cache_tree_structures_env.lower() in (
            "true",
            "1",
            "yes",
        )

    # Dependency configuration
    dep_cache_graphs_env = os.environ.get("REPOMAP_DEP_CACHE_GRAPHS")
    if dep_cache_graphs_env:
        config.dependencies.cache_graphs = dep_cache_graphs_env.lower() in (
            "true",
            "1",
            "yes",
        )

    dep_max_graph_size_env = os.environ.get("REPOMAP_DEP_MAX_GRAPH_SIZE")
    if dep_max_graph_size_env:
        try:
            config.dependencies.max_graph_size = int(dep_max_graph_size_env)
        except ValueError:
            pass

    dep_enable_call_graph_env = os.environ.get("REPOMAP_DEP_ENABLE_CALL_GRAPH")
    if dep_enable_call_graph_env:
        config.dependencies.enable_call_graph = dep_enable_call_graph_env.lower() in (
            "true",
            "1",
            "yes",
        )

    dep_enable_impact_analysis_env = os.environ.get(
        "REPOMAP_DEP_ENABLE_IMPACT_ANALYSIS"
    )
    if dep_enable_impact_analysis_env:
        config.dependencies.enable_impact_analysis = (
            dep_enable_impact_analysis_env.lower() in ("true", "1", "yes")
        )

    dep_centrality_algorithms_env = os.environ.get("REPOMAP_DEP_CENTRALITY_ALGORITHMS")
    if dep_centrality_algorithms_env:
        config.dependencies.centrality_algorithms = [
            alg.strip() for alg in dep_centrality_algorithms_env.split(",")
        ]

    dep_max_centrality_cache_size_env = os.environ.get(
        "REPOMAP_DEP_MAX_CENTRALITY_CACHE_SIZE"
    )
    if dep_max_centrality_cache_size_env:
        try:
            config.dependencies.max_centrality_cache_size = int(
                dep_max_centrality_cache_size_env
            )
        except ValueError:
            pass

    dep_performance_threshold_env = os.environ.get(
        "REPOMAP_DEP_PERFORMANCE_THRESHOLD_SECONDS"
    )
    if dep_performance_threshold_env:
        try:
            config.dependencies.performance_threshold_seconds = float(
                dep_performance_threshold_env
            )
        except ValueError:
            pass

    refresh_cache_env = os.environ.get("REPOMAP_REFRESH_CACHE")
    if refresh_cache_env:
        config.refresh_cache = refresh_cache_env.lower() in ("true", "1", "yes")

    # Cache configuration
    cache_dir_env = os.environ.get("REPOMAP_CACHE_DIR")
    if cache_dir_env:
        config.cache_dir = Path(cache_dir_env)
    else:
        legacy_cache_dir = os.environ.get("CACHE_DIR")  # Legacy support
        if legacy_cache_dir:
            config.cache_dir = Path(legacy_cache_dir)

    return config


def apply_cli_overrides(
    config: RepoMapConfig,
    project_path: Optional[Union[str, Dict[str, Any]]] = None,
    config_file: Optional[str] = None,
    fuzzy: Optional[bool] = None,
    semantic: Optional[bool] = None,
    threshold: Optional[float] = None,
    fuzzy_threshold: Optional[int] = None,  # Accept legacy parameter name
    max_results: Optional[int] = None,
    output: Optional[str] = None,
    verbose: Optional[bool] = None,
    refresh_cache: Optional[bool] = None,
    cache_size: Optional[int] = None,
    no_progress: Optional[bool] = None,
    no_monitoring: Optional[bool] = None,
    log_level: Optional[str] = None,
    **kwargs: Any,  # Accept any other parameters for backward compatibility
) -> RepoMapConfig:
    """Apply CLI argument overrides to configuration."""

    # Handle legacy test calling pattern: apply_cli_overrides(config, overrides_dict)
    if isinstance(project_path, dict):
        # Merge the dict into kwargs and reset project_path
        kwargs.update(project_path)
        project_path = kwargs.pop("project_path", None)
        fuzzy = kwargs.pop("fuzzy", fuzzy)
        semantic = kwargs.pop("semantic", semantic)
        threshold = kwargs.pop("threshold", threshold)
        fuzzy_threshold = kwargs.pop("fuzzy_threshold", fuzzy_threshold)
        max_results = kwargs.pop("max_results", max_results)
        output = kwargs.pop("output", output)
        verbose = kwargs.pop("verbose", verbose)
        refresh_cache = kwargs.pop("refresh_cache", refresh_cache)
        cache_size = kwargs.pop("cache_size", cache_size)
        no_progress = kwargs.pop("no_progress", no_progress)
        no_monitoring = kwargs.pop("no_monitoring", no_monitoring)
        log_level = kwargs.pop("log_level", log_level)

    # Override project_root if provided
    if project_path:
        config.project_root = Path(str(project_path))

    # Override core settings if provided
    if fuzzy is not None:
        config.fuzzy_match.enabled = fuzzy
    if semantic is not None:
        config.semantic_match.enabled = semantic
    if threshold is not None:
        # Convert float threshold (0.0-1.0) to integer for FuzzyMatchConfig
        fuzzy_thresh = int(threshold * 100) if threshold <= 1.0 else int(threshold)
        config.fuzzy_match.threshold = fuzzy_thresh
        config.semantic_match.threshold = threshold
    if fuzzy_threshold is not None:
        # Direct integer threshold for FuzzyMatchConfig
        config.fuzzy_match.threshold = fuzzy_threshold
    if max_results is not None:
        config.max_results = max_results
    if output is not None:
        config.output_format = output  # type: ignore
    if verbose is not None:
        config.verbose = verbose
    if refresh_cache is not None:
        config.refresh_cache = refresh_cache
    if log_level is not None:
        config.log_level = log_level

    # Handle additional parameters from kwargs (for test compatibility)
    if "semantic_enabled" in kwargs:
        config.semantic_match.enabled = kwargs["semantic_enabled"]
    if "max_workers" in kwargs:
        config.performance.max_workers = kwargs["max_workers"]

    # Override performance settings if provided
    if cache_size is not None:
        config.performance.cache_size = cache_size
    if no_progress is not None:
        config.performance.enable_progress = not no_progress
    if no_monitoring is not None:
        config.performance.enable_monitoring = not no_monitoring

    return config


def load_or_create_config(
    project_path: Optional[str] = None,
    config_file: Optional[str] = None,
    create_if_missing: bool = False,
    **cli_overrides: Any,
) -> Tuple[RepoMapConfig, bool]:
    """Load configuration from file or create default configuration."""
    config = None

    # 1. Try to load from config file if provided
    if config_file:
        config = load_config_file(config_file)
    else:
        # Try to discover config file in current directory
        config = discover_config_file_in_current_dir()

    # 2. If no config file found, create default config
    was_created = False
    if config is None:
        # Resolve project path for default config
        project_path = resolve_project_path(project_path, config_file)
        config = create_default_config(
            project_path,
            fuzzy=True,
            semantic=True,
            threshold=get_config("FUZZY_THRESHOLD", 0.7),
            max_results=50,
            output="json",
            verbose=False,
            cache_size=get_config("CACHE_SIZE", 1000),
        )
        was_created = True

        # Optionally create config file
        if create_if_missing:
            create_default_config_file(project_path, config)

    # 3. Apply environment overrides
    config = apply_environment_overrides(config)

    # 4. Apply CLI overrides
    config = apply_cli_overrides(config, project_path=project_path, **cli_overrides)

    return config, was_created


def create_tree_config(
    project_path: Optional[str],
    max_depth: int = get_config("MAX_DEPTH", 3),
    verbose: bool = True,
) -> RepoMapConfig:
    """Create configuration for tree-related operations (explore, focus, expand, prune, map, list_trees, status)."""
    if project_path is None:
        raise ValueError("project_path is required for create_tree_config")

    fuzzy_config = FuzzyMatchConfig(threshold=70, cache_results=True)
    semantic_config = SemanticMatchConfig(
        enabled=True, threshold=get_config("FUZZY_THRESHOLD", 0.7), cache_results=True
    )
    tree_config = TreeConfig(max_depth=max_depth, entrypoint_threshold=0.6)

    # Get cache directory from environment variable if set
    cache_dir_env = os.environ.get("CACHE_DIR")
    cache_dir = Path(cache_dir_env) if cache_dir_env is not None else None

    config = RepoMapConfig(
        project_root=project_path,
        cache_dir=cache_dir,
        fuzzy_match=fuzzy_config,
        semantic_match=semantic_config,
        trees=tree_config,
        verbose=verbose,
    )

    return config
