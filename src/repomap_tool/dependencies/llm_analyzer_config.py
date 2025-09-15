"""
Configuration object for LLM file analyzer to reduce constructor parameters.

This module provides a configuration object that groups related parameters
for the LLM file analyzer, making it easier to manage and test.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


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


class LLMAnalyzerDependencies(BaseModel):
    """Dependency injection container for LLM analyzer components."""

    # Core dependencies
    dependency_graph: object = Field(..., description="Advanced dependency graph")
    project_root: str = Field(..., description="Project root path")

    # Analysis engines
    ast_analyzer: object = Field(..., description="AST file analyzer")
    token_optimizer: object = Field(..., description="Token optimizer")
    context_selector: object = Field(..., description="Context selector")
    hierarchical_formatter: object = Field(..., description="Hierarchical formatter")
    path_resolver: object = Field(..., description="Path resolver")
    impact_engine: object = Field(..., description="Impact analysis engine")
    centrality_engine: object = Field(..., description="Centrality analysis engine")
    centrality_calculator: object = Field(..., description="Centrality calculator")

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
    def validate_not_none(cls, v):
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
