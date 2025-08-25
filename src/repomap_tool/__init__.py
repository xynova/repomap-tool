#!/usr/bin/env python3
"""
repomap_tool - Docker RepoMap Tool Package

A portable code analysis tool using aider libraries with fuzzy and semantic matching.
"""

from .core import DockerRepoMap
from .cli import cli
from ..models import (
    RepoMapConfig, FuzzyMatchConfig, SemanticMatchConfig,
    MatchResult, SearchRequest, SearchResponse, ProjectInfo,
    HealthCheck, ErrorResponse
)

__version__ = "0.1.0"
__author__ = "Docker RepoMap Team"

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
