#!/usr/bin/env python3
"""
models.py - Pydantic models for Docker RepoMap

This module defines structured data models for configuration, API requests/responses,
and match results using Pydantic for validation and serialization.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Literal, Union
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FuzzyMatchConfig(BaseModel):
    """Configuration for fuzzy matching."""
    
    enabled: bool = False
    threshold: int = Field(default=70, ge=0, le=100, description="Similarity threshold (0-100)")
    strategies: List[str] = Field(
        default=['prefix', 'substring', 'levenshtein'],
        description="Matching strategies to use"
    )
    cache_results: bool = True
    
    @field_validator('strategies')
    @classmethod
    def validate_strategies(cls, v: List[str]) -> List[str]:
        """Validate that all strategies are valid."""
        valid_strategies = {'prefix', 'suffix', 'substring', 'levenshtein', 'word'}
        invalid_strategies = set(v) - valid_strategies
        if invalid_strategies:
            raise ValueError(f"Invalid strategies: {invalid_strategies}. Valid: {valid_strategies}")
        return v


class SemanticMatchConfig(BaseModel):
    """Configuration for semantic matching."""
    
    enabled: bool = False
    threshold: float = Field(default=0.1, ge=0.0, le=1.0, description="Similarity threshold (0.0-1.0)")
    use_tfidf: bool = True
    min_word_length: int = Field(default=3, ge=1, description="Minimum word length for analysis")
    cache_results: bool = True


class RepoMapConfig(BaseModel):
    """Main configuration for Docker RepoMap."""
    
    project_root: Union[str, Path]
    map_tokens: int = Field(default=4096, ge=1, le=8192, description="Maximum tokens for map generation")
    cache_dir: Optional[Union[str, Path]] = None
    verbose: bool = True
    log_level: str = Field(default="INFO", description="Logging level")
    
    # Matching configurations
    fuzzy_match: FuzzyMatchConfig = Field(default_factory=FuzzyMatchConfig)
    semantic_match: SemanticMatchConfig = Field(default_factory=SemanticMatchConfig)
    
    # Advanced options
    refresh_cache: bool = False
    output_format: Literal['json', 'text', 'markdown'] = 'json'
    max_results: int = Field(default=50, ge=1, le=1000, description="Maximum results to return")
    
    @field_validator('project_root')
    @classmethod
    def validate_project_root(cls, v: Union[str, Path]) -> Path:
        """Convert to Path and validate it exists."""
        path = Path(v).resolve()
        if not path.exists():
            raise ValueError(f"Project root does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"Project root must be a directory: {path}")
        return path
    
    @field_validator('cache_dir')
    @classmethod
    def validate_cache_dir(cls, v: Optional[Union[str, Path]]) -> Optional[Path]:
        """Convert cache_dir to Path if provided."""
        if v is None:
            return None
        return Path(v).resolve()
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Valid: {valid_levels}")
        return v.upper()


class MatchResult(BaseModel):
    """Result of a single match."""
    
    identifier: str = Field(description="The matched identifier")
    score: float = Field(ge=0.0, le=1.0, description="Match confidence score (0.0-1.0)")
    strategy: str = Field(description="Matching strategy used")
    match_type: Literal['fuzzy', 'semantic', 'hybrid'] = Field(description="Type of matching")
    file_path: Optional[str] = Field(default=None, description="File containing the identifier")
    line_number: Optional[int] = Field(default=None, ge=1, description="Line number in file")
    context: Optional[str] = Field(default=None, description="Context around the match")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('score')
    @classmethod
    def normalize_score(cls, v: float) -> float:
        """Ensure score is between 0.0 and 1.0."""
        return max(0.0, min(1.0, v))


class SearchRequest(BaseModel):
    """API request for searching identifiers."""
    
    query: str = Field(description="Search query")
    match_type: Literal['fuzzy', 'semantic', 'hybrid'] = Field(default='hybrid', description="Type of matching")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum score threshold")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum results to return")
    include_context: bool = Field(default=True, description="Include context in results")
    strategies: Optional[List[str]] = Field(default=None, description="Specific strategies to use")
    
    @field_validator('query')
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
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ProjectInfo(BaseModel):
    """Information about the analyzed project."""
    
    project_root: str = Field(description="Project root path")
    total_files: int = Field(description="Total number of files analyzed")
    total_identifiers: int = Field(description="Total number of identifiers found")
    file_types: Dict[str, int] = Field(description="Count of files by type")
    identifier_types: Dict[str, int] = Field(description="Count of identifiers by type")
    analysis_time_ms: float = Field(description="Analysis time in milliseconds")
    cache_size_bytes: Optional[int] = Field(default=None, description="Cache size in bytes")
    last_updated: datetime = Field(description="Last analysis timestamp")


class HealthCheck(BaseModel):
    """Health check response."""
    
    status: Literal['healthy', 'unhealthy'] = Field(description="Service status")
    version: str = Field(description="Service version")
    uptime_seconds: float = Field(description="Service uptime in seconds")
    memory_usage_mb: Optional[float] = Field(default=None, description="Memory usage in MB")
    cache_status: Dict[str, Any] = Field(default_factory=dict, description="Cache status")
    errors: List[str] = Field(default_factory=list, description="Recent errors")


class ErrorResponse(BaseModel):
    """Error response for API endpoints."""
    
    error: str = Field(description="Error message")
    error_type: str = Field(description="Type of error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracking")


# Utility functions for working with models
def create_config_from_dict(config_dict: Dict[str, Any]) -> RepoMapConfig:
    """Create a RepoMapConfig from a dictionary."""
    return RepoMapConfig(**config_dict)


def config_to_dict(config: RepoMapConfig) -> Dict[str, Any]:
    """Convert a RepoMapConfig to a dictionary."""
    return config.model_dump()


def validate_search_request(data: Dict[str, Any]) -> SearchRequest:
    """Validate and create a SearchRequest from dictionary data."""
    return SearchRequest(**data)


def create_error_response(error: str, error_type: str = "ValidationError", 
                         details: Optional[Dict[str, Any]] = None,
                         request_id: Optional[str] = None) -> ErrorResponse:
    """Create an error response."""
    return ErrorResponse(
        error=error,
        error_type=error_type,
        details=details,
        request_id=request_id
    )
