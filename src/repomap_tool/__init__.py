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
    DockerRepoMap = None

# Import CLI
try:
    from .cli import cli
except ImportError:
    cli = None

# Import models
try:
    from ..models import (
        RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig,
        MatchResult, SearchRequest, SearchResponse, ProjectInfo,
        HealthCheck, ErrorResponse
    )
except ImportError:
    # Fallback imports
    RepoMapConfig = None
    FuzzyMatchConfig = None
    SemanticMatchConfig = None
    MatchResult = None
    SearchRequest = None
    SearchResponse = None
    ProjectInfo = None
    HealthCheck = None
    ErrorResponse = None

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
