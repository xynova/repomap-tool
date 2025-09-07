#!/usr/bin/env python3
"""
RepoMap-Tool Tool - A comprehensive tool for analyzing Docker repositories
and finding similar identifiers across different codebases.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Import core functionality
try:
    from .core import RepoMapService
except ImportError:
    RepoMapService = None  # type: ignore

# Import CLI - removed to prevent circular import issues
# CLI should be imported directly when needed, not at package level
cli = None  # type: ignore

# Import models
try:
    from .models import (
        RepoMapConfig,
        FuzzyMatchConfig,
        SemanticMatchConfig,
        MatchResult,
        SearchRequest,
        SearchResponse,
        ProjectInfo,
        HealthCheck,
        ErrorResponse,
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

# Import protocols for type safety
try:
    from .protocols import (
        RepoMapProtocol,
        MatcherProtocol,
        FuzzyMatcherProtocol,
        SemanticMatcherProtocol,
        HybridMatcherProtocol,
        CacheManagerProtocol,
        FileScannerProtocol,
        ProjectAnalyzerProtocol,
        ProjectMap,
        Tag,
        FileData,
        IdentifierSet,
        MatchResult as ProtocolMatchResult,
        CacheStats,
        ProjectInfo as ProtocolProjectInfo,
    )
except ImportError:
    # Fallback imports
    RepoMapProtocol = None  # type: ignore
    MatcherProtocol = None  # type: ignore
    FuzzyMatcherProtocol = None  # type: ignore
    SemanticMatcherProtocol = None  # type: ignore
    HybridMatcherProtocol = None  # type: ignore
    CacheManagerProtocol = None  # type: ignore
    FileScannerProtocol = None  # type: ignore
    ProjectAnalyzerProtocol = None  # type: ignore
    ProjectMap = None  # type: ignore
    Tag = None  # type: ignore
    FileData = None  # type: ignore
    IdentifierSet = None  # type: ignore
    ProtocolMatchResult = None  # type: ignore
    CacheStats = None  # type: ignore
    ProtocolProjectInfo = None  # type: ignore

# Import exception hierarchy
try:
    from .exceptions import (
        RepoMapError,
        ConfigurationError,
        FileAccessError,
        TagExtractionError,
        MatcherError,
        CacheError,
        ValidationError,
        SearchError,
        ProjectAnalysisError,
        RepoMapMemoryError,
        NetworkError,
        RepoMapTimeoutError,
        safe_operation,
        handle_errors,
    )
except ImportError:
    # Fallback imports
    RepoMapError = None  # type: ignore
    ConfigurationError = None  # type: ignore
    FileAccessError = None  # type: ignore
    TagExtractionError = None  # type: ignore
    MatcherError = None  # type: ignore
    CacheError = None  # type: ignore
    ValidationError = None  # type: ignore
    SearchError = None  # type: ignore
    ProjectAnalysisError = None  # type: ignore
    RepoMapMemoryError = None  # type: ignore
    NetworkError = None  # type: ignore
    RepoMapTimeoutError = None  # type: ignore
    safe_operation = None  # type: ignore
    handle_errors = None  # type: ignore

__all__ = [
    "RepoMapService",
    "cli",
    "RepoMapConfig",
    "FuzzyMatchConfig",
    "SemanticMatchConfig",
    "MatchResult",
    "SearchRequest",
    "SearchResponse",
    "ProjectInfo",
    "HealthCheck",
    "ErrorResponse",
    # Protocol exports
    "RepoMapProtocol",
    "MatcherProtocol",
    "FuzzyMatcherProtocol",
    "SemanticMatcherProtocol",
    "HybridMatcherProtocol",
    "CacheManagerProtocol",
    "FileScannerProtocol",
    "ProjectAnalyzerProtocol",
    "ProjectMap",
    "Tag",
    "FileData",
    "IdentifierSet",
    "ProtocolMatchResult",
    "CacheStats",
    "ProtocolProjectInfo",
    # Exception exports
    "RepoMapError",
    "ConfigurationError",
    "FileAccessError",
    "TagExtractionError",
    "MatcherError",
    "CacheError",
    "ValidationError",
    "SearchError",
    "ProjectAnalysisError",
    "RepoMapMemoryError",
    "NetworkError",
    "RepoMapTimeoutError",
    "safe_operation",
    "handle_errors",
]
