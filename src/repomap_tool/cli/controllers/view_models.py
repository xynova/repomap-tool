from __future__ import annotations

from repomap_tool.core.config_service import get_config

"""
ViewModels for CLI Controllers.

This module defines the ViewModel classes that represent structured data
for the view layer, following proper MVC architecture patterns.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class AnalysisType(str, Enum):
    """Types of analysis that can be performed."""

    CENTRALITY = "centrality"
    IMPACT = "impact"
    EXPLORATION = "exploration"
    SEARCH = "search"


@dataclass
class SymbolViewModel:
    """ViewModel for code symbols."""

    name: str
    file_path: str
    line_number: int
    symbol_type: str  # function, class, method, etc.
    signature: Optional[str] = None
    critical_lines: Optional[List[str]] = None
    dependencies: Optional[List[str]] = None
    centrality_score: Optional[float] = None
    impact_risk: Optional[float] = None
    importance_score: Optional[float] = None
    is_critical: bool = False


@dataclass
class FileAnalysisViewModel:
    """ViewModel for file analysis results."""

    file_path: str
    line_count: int
    symbols: List[SymbolViewModel]
    imports: List[str]
    dependencies: List[str]
    centrality_score: Optional[float] = None
    impact_risk: Optional[float] = None
    complexity_score: Optional[float] = None
    token_count: Optional[int] = None
    analysis_type: AnalysisType = AnalysisType.CENTRALITY


@dataclass
class CentralityViewModel:
    """ViewModel for centrality analysis results."""

    files: List[FileAnalysisViewModel]
    rankings: List[Dict[str, Any]]
    total_files: int
    analysis_summary: Dict[str, Any]
    token_count: int
    max_tokens: int
    compression_level: str = "medium"


@dataclass
class ImpactViewModel:
    """ViewModel for impact analysis results."""

    changed_files: List[str]
    affected_files: List[FileAnalysisViewModel]
    impact_scope: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    total_affected: int
    token_count: int
    max_tokens: int
    compression_level: str = "medium"


@dataclass
class SearchViewModel:
    """ViewModel for search results."""

    query: str
    results: List[SymbolViewModel]
    total_results: int
    search_strategy: str
    execution_time: float
    token_count: int
    max_tokens: int
    compression_level: str = "medium"
    # Additional fields to match SearchResponse structure
    threshold: float = 0.7
    match_type: str = "hybrid"
    search_time_ms: float = 0.0
    cache_hit: bool = False
    spellcheck_suggestions: List[str] = None
    metadata: Optional[Dict[str, Any]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        """Initialize default values for optional fields."""
        if self.metadata is None:
            self.metadata = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.spellcheck_suggestions is None:
            self.spellcheck_suggestions = []


@dataclass
class TreeClusterViewModel:
    """ViewModel for tree cluster information."""

    tree_id: str
    context_name: str
    confidence: float
    entrypoints: List[Dict[str, Any]]
    total_nodes: int
    max_depth: int
    root_file: str
    description: str


@dataclass
class TreeFocusViewModel:
    """ViewModel for tree focus operations."""

    tree_id: str
    context_name: str
    current_focus: bool
    tree_structure: Dict[str, Any]
    expanded_areas: List[str]
    pruned_areas: List[str]
    total_nodes: int
    max_depth: int


@dataclass
class TreeExpansionViewModel:
    """ViewModel for tree expansion operations."""

    tree_id: str
    expanded_area: str
    new_nodes: List[SymbolViewModel]
    total_nodes: int
    expansion_depth: int
    confidence_score: float


@dataclass
class TreePruningViewModel:
    """ViewModel for tree pruning operations."""

    tree_id: str
    pruned_area: str
    removed_nodes: List[str]
    remaining_nodes: int
    pruning_reason: str


@dataclass
class TreeMappingViewModel:
    """ViewModel for tree mapping operations."""

    tree_id: str
    tree_structure: Dict[str, Any]
    total_nodes: int
    max_depth: int
    include_code: bool
    code_snippets: List[Dict[str, Any]]
    token_count: int
    max_tokens: int


@dataclass
class TreeListingViewModel:
    """ViewModel for tree listing operations."""

    session_id: str
    trees: List[TreeClusterViewModel]
    total_trees: int
    current_focus: Optional[str] = None


@dataclass
class SessionStatusViewModel:
    """ViewModel for session status operations."""

    session_id: str
    project_path: str
    total_trees: int
    current_focus: Optional[str]
    created_at: str
    last_activity: str
    session_stats: Dict[str, Any]


@dataclass
class ExplorationViewModel:
    """ViewModel for exploration session results."""

    session_id: str
    project_path: str
    intent: str
    trees: List[TreeClusterViewModel]
    total_trees: int
    confidence_scores: Dict[str, float]
    token_count: int
    max_tokens: int
    compression_level: str = "medium"
    execution_time: float = 0.0
    discovery_strategy: str = "hybrid"


@dataclass
class ProjectAnalysisViewModel:
    """ViewModel for project analysis results."""

    project_path: str
    total_files: int
    file_types: Dict[str, int]
    identifier_types: Dict[str, int]
    cache_stats: Dict[str, Any]
    analysis_time: float
    token_count: int
    max_tokens: int
    compression_level: str = "medium"


@dataclass
class ControllerConfig:
    """Configuration for Controllers."""

    max_tokens: int = get_config("MAX_TOKENS", 4000)
    compression_level: str = "medium"
    verbose: bool = False
    output_format: str = "text"
    analysis_type: AnalysisType = AnalysisType.CENTRALITY
    search_strategy: str = "hybrid"
    context_selection: str = "centrality_based"
