#!/usr/bin/env python3
"""
Docker RepoMap Tool - A comprehensive tool for analyzing Docker repositories
and finding similar identifiers across different codebases.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import core functionality
try:
    from .core import DockerRepoMap
except ImportError:
    DockerRepoMap = None  # type: ignore

# Import CLI
try:
    from .cli import cli
except ImportError:
    cli = None  # type: ignore

# Import models
try:
    from .models import (
        RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig,
        MatchResult, SearchRequest, SearchResponse, ProjectInfo,
        HealthCheck, ErrorResponse
    )
except ImportError:
    # Fallback imports
    RepoMapConfig = None  # type: ignore
    FuzzyMatchConfig = None  # type: ignore
    SemanticMatchConfig = None  # type: ignore
    MatchResult = None  # type: ignore
    SearchRequest = None  # type: ignore
    SearchResponse = None  # type: ignore
    ProjectInfo = None  # type: ignore
    HealthCheck = None  # type: ignore
    ErrorResponse = None  # type: ignore

__all__ = [
    "DockerRepoMap",
    "cli",
    "RepoMapConfig",
    "FuzzyMatchConfig", 
    "SemanticMatchConfig",
    "MatchResult",
    "SearchRequest",
    "SearchResponse",
    "ProjectInfo",
    "HealthCheck",
    "ErrorResponse"
]
