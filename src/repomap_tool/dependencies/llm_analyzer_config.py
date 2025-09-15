"""
Configuration object for LLM file analyzer to reduce constructor parameters.

This module provides a configuration object that groups related parameters
for the LLM file analyzer, making it easier to manage and test.
"""

from typing import Optional, TYPE_CHECKING, Any
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from .advanced_dependency_graph import AdvancedDependencyGraph
    from .ast_file_analyzer import ASTFileAnalyzer
    from .centrality_calculator import CentralityCalculator
    from .impact_analyzer import ImpactAnalyzer
    from .impact_analysis_engine import ImpactAnalysisEngine
    from .centrality_analysis_engine import CentralityAnalysisEngine
    from .path_resolver import PathResolver
    from ..llm.token_optimizer import TokenOptimizer
    from ..llm.context_selector import ContextSelector
    from ..llm.hierarchical_formatter import HierarchicalFormatter
else:
    # Import for runtime to avoid circular imports
    from .advanced_dependency_graph import AdvancedDependencyGraph
    from .ast_file_analyzer import ASTFileAnalyzer
    from .centrality_calculator import CentralityCalculator
    from .impact_analyzer import ImpactAnalyzer
    from .impact_analysis_engine import ImpactAnalysisEngine
    from .centrality_analysis_engine import CentralityAnalysisEngine
    from .path_resolver import PathResolver
    from ..llm.token_optimizer import TokenOptimizer
    from ..llm.context_selector import ContextSelector
    from ..llm.hierarchical_formatter import HierarchicalFormatter


class LLMAnalyzerConfig(BaseModel):
    """Configuration for LLM file analyzer."""

    max_tokens: int = Field(
        default=4000, ge=1000, le=8000, description="Maximum tokens for LLM output"
    )
    enable_impact_analysis: bool = Field(
        default=True, description="Enable impact analysis"
    )
    enable_centrality_analysis: bool = Field(
        default=True, description="Enable centrality analysis"
    )
    enable_code_snippets: bool = Field(
        default=True, description="Enable code snippet extraction"
    )
    max_snippets_per_file: int = Field(
        default=3, ge=1, le=10, description="Maximum code snippets per file"
    )
    snippet_max_lines: int = Field(
        default=10, ge=5, le=20, description="Maximum lines per code snippet"
    )
    analysis_timeout: int = Field(
        default=30, ge=5, le=120, description="Analysis timeout in seconds"
    )
    cache_results: bool = Field(default=True, description="Cache analysis results")
    verbose: bool = Field(default=False, description="Enable verbose logging")

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"
        frozen = True
        arbitrary_types_allowed = True


class LLMAnalyzerDependencies(BaseModel):
    """Dependency injection container for LLM analyzer components."""

    # Core dependencies
    dependency_graph: Any = Field(..., description="Advanced dependency graph")
    project_root: str = Field(..., description="Project root path")

    # Analysis engines
    ast_analyzer: Any = Field(..., description="AST file analyzer")
    token_optimizer: Any = Field(..., description="Token optimizer")
    context_selector: Any = Field(..., description="Context selector")
    hierarchical_formatter: Any = Field(..., description="Hierarchical formatter")
    path_resolver: Any = Field(..., description="Path resolver")
    impact_engine: Any = Field(..., description="Impact analysis engine")
    centrality_engine: Any = Field(..., description="Centrality analysis engine")
    centrality_calculator: Any = Field(..., description="Centrality calculator")

    @field_validator(
        "dependency_graph",
        "ast_analyzer",
        "token_optimizer",
        "context_selector",
        "hierarchical_formatter",
        "path_resolver",
        "impact_engine",
        "centrality_engine",
        "centrality_calculator",
    )
    @classmethod
    def validate_not_none(cls, v: object) -> object:
        """Validate that dependency fields are not None."""
        if v is None:
            raise ValueError("Dependency fields cannot be None")
        return v

    class Config:
        """Pydantic configuration."""

        str_strip_whitespace = True
        validate_assignment = True
        extra = "forbid"
        frozen = True
        arbitrary_types_allowed = True
