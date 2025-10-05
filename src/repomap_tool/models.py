#!/usr/bin/env python3
"""
models.py - Pydantic models for RepoMap-Tool

This module defines structured data models for configuration, API requests/responses,
and match results using Pydantic for validation and serialization.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Literal, Union, Set
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PerformanceConfig(BaseModel):
    """Configuration for performance optimizations."""

    max_workers: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum number of worker threads for parallel processing",
    )
    cache_size: int = Field(
        default=1000, ge=100, le=10000, description="Maximum number of cache entries"
    )
    max_memory_mb: int = Field(
        default=100, ge=10, le=1000, description="Maximum memory usage in MB"
    )
    enable_progress: bool = Field(
        default=True, description="Enable progress bars for long-running operations"
    )
    enable_monitoring: bool = Field(
        default=True, description="Enable performance monitoring"
    )
    parallel_threshold: int = Field(
        default=10, description="Minimum number of files to trigger parallel processing"
    )
    cache_ttl: int = Field(default=3600, description="Cache time-to-live in seconds")
    allow_fallback: bool = Field(
        default=False,
        description="Allow fallback to sequential processing on parallel errors (not recommended for development)",
    )


class FuzzyMatchConfig(BaseModel):
    """Configuration for fuzzy matching."""

    enabled: bool = True
    threshold: int = Field(
        default=70, ge=0, le=100, description="Similarity threshold (0-100)"
    )
    strategies: List[str] = Field(
        default=["prefix", "substring", "levenshtein"],
        description="Matching strategies to use",
    )
    cache_results: bool = True

    @field_validator("strategies")
    @classmethod
    def validate_strategies(cls, v: List[str]) -> List[str]:
        """Validate that all strategies are valid."""
        valid_strategies = {"prefix", "suffix", "substring", "levenshtein", "word"}
        invalid_strategies = set(v) - valid_strategies
        if invalid_strategies:
            raise ValueError(
                f"Invalid strategies: {invalid_strategies}. Valid: {valid_strategies}"
            )
        return v


class SemanticMatchConfig(BaseModel):
    """Configuration for semantic matching."""

    enabled: bool = False
    threshold: float = Field(
        default=0.1, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)"
    )
    use_tfidf: bool = True
    min_word_length: int = Field(
        default=3, ge=1, description="Minimum word length for analysis"
    )
    cache_results: bool = True


class TreeConfig(BaseModel):
    """Configuration for tree exploration functionality."""

    max_depth: int = Field(default=3, ge=1, le=10, description="Maximum tree depth")
    max_trees_per_session: int = Field(
        default=10, ge=1, le=100, description="Maximum trees per session"
    )
    entrypoint_threshold: float = Field(
        default=0.6, ge=0.0, le=1.0, description="Entrypoint discovery threshold"
    )
    enable_code_snippets: bool = Field(
        default=True, description="Include code snippets in tree output"
    )
    cache_tree_structures: bool = Field(
        default=True, description="Cache tree structures for performance"
    )


class DependencyConfig(BaseModel):
    """Configuration for dependency analysis."""

    cache_graphs: bool = Field(default=True, description="Cache dependency graphs")
    max_graph_size: int = Field(
        default=10000, ge=100, le=100000, description="Maximum number of files in graph"
    )
    enable_call_graph: bool = Field(
        default=True, description="Enable function call graph analysis"
    )
    enable_impact_analysis: bool = Field(
        default=True, description="Enable change impact analysis"
    )
    centrality_algorithms: List[str] = Field(
        default=["degree", "betweenness", "pagerank"],
        description="Centrality algorithms to use",
    )
    max_centrality_cache_size: int = Field(
        default=1000, ge=100, le=10000, description="Maximum centrality scores to cache"
    )
    performance_threshold_seconds: float = Field(
        default=30.0,
        ge=5.0,
        le=300.0,
        description="Maximum time for graph construction (seconds)",
    )


class RepoMapConfig(BaseModel):
    """Main configuration for RepoMap-Tool."""

    project_root: Union[str, Path]
    map_tokens: int = Field(
        default=4096, ge=1, le=8192, description="Maximum tokens for map generation"
    )
    cache_dir: Optional[Union[str, Path]] = None
    verbose: bool = Field(default=True, description="Verbose output")
    log_level: str = Field(default="INFO", description="Logging level")

    # Performance configuration
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    # Matching configurations
    fuzzy_match: FuzzyMatchConfig = Field(default_factory=FuzzyMatchConfig)
    semantic_match: SemanticMatchConfig = Field(default_factory=SemanticMatchConfig)

    # Tree exploration configuration
    trees: TreeConfig = Field(default_factory=TreeConfig)

    # Dependency analysis configuration
    dependencies: DependencyConfig = Field(default_factory=DependencyConfig)

    # Advanced options
    refresh_cache: bool = Field(default=False, description="Refresh cache")
    output_format: Literal["text", "json"] = "text"
    max_results: int = Field(
        default=50, ge=1, le=1000, description="Maximum results to return"
    )

    @field_validator("project_root")
    @classmethod
    def validate_project_root(cls, v: Union[str, Path]) -> Path:
        """Convert to Path and validate it exists."""
        # Handle empty strings explicitly
        if isinstance(v, str) and not v.strip():
            raise ValueError("Project root cannot be empty or whitespace only")

        # Handle null bytes
        if isinstance(v, str) and "\x00" in v:
            raise ValueError("Project root cannot contain null bytes")

        # Check path length before resolving
        if isinstance(v, str) and len(v) > 4096:  # Reasonable limit
            raise ValueError("Project root path too long (max 4096 characters)")

        try:
            path = Path(v).resolve()
        except (OSError, ValueError) as e:
            if "File name too long" in str(e):
                raise ValueError("Project root path too long") from e
            raise ValueError(f"Invalid project root path: {e}") from e

        if not path.exists():
            raise ValueError(f"Project root does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Project root must be a directory: {path}")
        return path

    @field_validator("cache_dir")
    @classmethod
    def validate_cache_dir(cls, v: Optional[Union[str, Path]]) -> Optional[Path]:
        """Convert cache_dir to Path if provided."""
        if v is None:
            return None

        # Handle null bytes
        if isinstance(v, str) and "\x00" in v:
            raise ValueError("Cache directory cannot contain null bytes")

        # Check path length
        if isinstance(v, str) and len(v) > 4096:
            raise ValueError("Cache directory path too long (max 4096 characters)")

        try:
            return Path(v).resolve()
        except (OSError, ValueError) as e:
            if "File name too long" in str(e):
                raise ValueError("Cache directory path too long")
            raise ValueError(f"Invalid cache directory: {e}")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Valid: {valid_levels}")
        return v.upper()

    @model_validator(mode="after")
    def validate_matching_config(self) -> "RepoMapConfig":
        """Validate matching configuration."""
        # Fuzzy matching is always enabled, so no validation needed
        return self


class MatchResult(BaseModel):
    """Result of a single match."""

    identifier: str = Field(description="The matched identifier")
    score: float = Field(ge=0.0, le=1.0, description="Match confidence score (0.0-1.0)")
    strategy: str = Field(description="Matching strategy used")
    match_type: Literal["fuzzy", "semantic", "hybrid"] = Field(
        description="Type of matching"
    )
    file_path: Optional[str] = Field(
        default=None, description="File containing the identifier"
    )
    line_number: Optional[int] = Field(
        default=None, ge=1, description="Line number in file"
    )
    context: Optional[str] = Field(default=None, description="Context around the match")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @field_validator("score")
    @classmethod
    def normalize_score(cls, v: float) -> float:
        """Ensure score is between 0.0 and 1.0."""
        # Handle negative values by clamping to 0
        if v < 0.0:
            return 0.0
        # Handle values > 1.0 by clamping to 1
        if v > 1.0:
            return 1.0
        return v


class SearchRequest(BaseModel):
    """API request for searching identifiers."""

    query: str = Field(description="Search query")
    match_type: Literal["fuzzy", "semantic", "hybrid"] = Field(
        default="hybrid", description="Type of matching"
    )
    threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum score threshold"
    )
    max_results: int = Field(
        default=10, ge=1, le=100, description="Maximum results to return"
    )
    include_context: bool = Field(
        default=True, description="Include context in results"
    )
    strategies: Optional[List[str]] = Field(
        default=None, description="Specific strategies to use"
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Validate and clean query."""
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class SearchResponse(BaseModel):
    """API response for search results."""

    query: str = Field(description="Original search query")
    match_type: str = Field(description="Type of matching used")
    threshold: float = Field(description="Score threshold applied")
    total_results: int = Field(description="Total number of results found")
    results: List[MatchResult] = Field(description="List of match results")
    search_time_ms: float = Field(description="Search time in milliseconds")
    cache_hit: bool = Field(default=False, description="Whether result was from cache")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    performance_metrics: Dict[str, Any] = Field(
        default_factory=dict, description="Performance metrics and timing data"
    )


class ProjectInfo(BaseModel):
    """Information about the analyzed project."""

    project_root: str = Field(description="Project root path")
    total_files: int = Field(description="Total number of files analyzed")
    total_identifiers: int = Field(description="Total number of identifiers found")
    file_types: Dict[str, int] = Field(description="Count of files by type")
    identifier_types: Dict[str, int] = Field(description="Count of identifiers by type")
    analysis_time_ms: float = Field(description="Analysis time in milliseconds")
    cache_size_bytes: Optional[int] = Field(
        default=None, description="Cache size in bytes"
    )
    last_updated: datetime = Field(description="Last analysis timestamp")
    cache_stats: Dict[str, Any] = Field(
        default_factory=dict, description="Cache statistics and metrics"
    )

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", ser_json_timedelta="iso8601"
    )


class HealthCheck(BaseModel):
    """Health check response."""

    status: Literal["healthy", "unhealthy"] = Field(description="Service status")
    version: str = Field(description="Service version")
    uptime_seconds: float = Field(description="Service uptime in seconds")
    memory_usage_mb: Optional[float] = Field(
        default=None, description="Memory usage in MB"
    )
    cache_status: Dict[str, Any] = Field(
        default_factory=dict, description="Cache status"
    )
    errors: List[str] = Field(default_factory=list, description="Recent errors")


class ErrorResponse(BaseModel):
    """Error response for API endpoints."""

    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Error timestamp"
    )
    request_id: Optional[str] = Field(
        default=None, description="Request ID for tracking"
    )

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", ser_json_timedelta="iso8601"
    )


# Utility functions for working with models
def create_config_from_dict(config_dict: Optional[Dict[str, Any]]) -> RepoMapConfig:
    """Create a RepoMapConfig from a dictionary."""
    if config_dict is None:
        raise ValueError("Configuration dictionary cannot be None")
    if not isinstance(config_dict, dict):
        raise ValueError("Configuration must be a dictionary")
    return RepoMapConfig(**config_dict)


def config_to_dict(config: RepoMapConfig) -> Dict[str, Any]:
    """Convert a RepoMapConfig to a dictionary."""
    return config.model_dump()


def validate_search_request(data: Optional[Dict[str, Any]]) -> SearchRequest:
    """Validate and create a SearchRequest from dictionary data."""
    if data is None:
        raise ValueError("Search request data cannot be None")
    if not isinstance(data, dict):
        raise ValueError("Search request data must be a dictionary")
    return SearchRequest(**data)


def create_error_response(
    error: str,
    error_type: str = "ValidationError",
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        error=error, error_type=error_type, details=details, request_id=request_id
    )


# Tree Exploration Models
class TreeNode(BaseModel):
    """Represents a node in the exploration tree."""

    identifier: str = Field(description="Function/class name or symbol identifier")
    location: str = Field(description="File path and line number (file:line)")
    node_type: str = Field(
        description="Type of node: entrypoint, function, class, import"
    )
    depth: int = Field(description="Depth in the tree (0 = root)")
    children: List["TreeNode"] = Field(default_factory=list, description="Child nodes")
    parent: Optional["TreeNode"] = Field(default=None, description="Parent node")
    expanded: bool = Field(
        default=False, description="Whether this node has been expanded"
    )
    structural_info: Dict[str, Any] = Field(
        default_factory=dict, description="Dependencies, calls, etc."
    )

    # Phase 2: Dependency analysis integration
    dependency_centrality: Optional[float] = Field(
        default=None, description="Dependency centrality score (0-1)"
    )
    import_count: Optional[int] = Field(
        default=None, description="Number of files that import this node"
    )
    dependency_count: Optional[int] = Field(
        default=None, description="Number of files this node depends on"
    )
    impact_risk: Optional[float] = Field(
        default=None, description="Impact risk score if this node changes (0-1)"
    )
    refactoring_priority: Optional[float] = Field(
        default=None, description="Refactoring priority score (0-1)"
    )

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", arbitrary_types_allowed=True
    )


class Entrypoint(BaseModel):
    """Represents a potential entrypoint for code exploration."""

    identifier: str
    file_path: Path
    score: float
    structural_context: Dict[str, Any] = Field(default_factory=dict)
    centrality_score: Optional[float] = None
    categories: List[str] = Field(default_factory=list)

    # Dependency analysis fields
    dependency_centrality: Optional[float] = None
    import_count: Optional[int] = None
    dependency_count: Optional[int] = None
    impact_risk: Optional[float] = None
    refactoring_priority: Optional[float] = None

    @property
    def location(self) -> Path:
        return self.file_path


class TreeCluster(BaseModel):
    """Represents a cluster of related entrypoints."""

    context_name: str = Field(
        description="Human-readable context name like 'Auth Error Handling'"
    )
    entrypoints: List[Entrypoint] = Field(description="Entrypoints in this cluster")
    confidence: float = Field(ge=0.0, le=1.0, description="Cluster confidence score")
    tree_id: str = Field(
        description="Unique identifier for the tree built from this cluster"
    )


class ExplorationTree(BaseModel):
    """Represents a tree structure for exploring code related to an intent."""

    tree_id: str = Field(description="Unique tree identifier")
    root_entrypoint: Entrypoint = Field(description="Root entrypoint of the tree")
    max_depth: int = Field(default=3, description="Maximum tree depth")
    tree_structure: Optional[TreeNode] = Field(
        default=None, description="Tree structure"
    )
    expanded_areas: Set[str] = Field(
        default_factory=set, description="Areas that have been expanded"
    )
    pruned_areas: Set[str] = Field(
        default_factory=set, description="Areas that have been pruned"
    )
    context_name: str = Field(default="", description="Human-readable context name")
    confidence: float = Field(default=0.0, description="Tree confidence score")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Tree creation timestamp"
    )
    last_modified: datetime = Field(
        default_factory=datetime.now, description="Last modification timestamp"
    )

    model_config = ConfigDict(
        validate_assignment=True, extra="forbid", arbitrary_types_allowed=True
    )


class ExplorationSession(BaseModel):
    """Represents an exploration session with multiple trees."""

    session_id: str = Field(description="Unique session identifier")
    project_path: str = Field(description="Project path being explored")
    exploration_trees: Dict[str, ExplorationTree] = Field(
        default_factory=dict, description="Trees in this session"
    )
    current_focus: Optional[str] = Field(
        default=None, description="Currently focused tree ID"
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Session creation timestamp"
    )
    last_activity: datetime = Field(
        default_factory=datetime.now, description="Last activity timestamp"
    )
