#!/usr/bin/env python3
"""
RepoMap-Tool Tool - A comprehensive tool for analyzing Docker repositories
and finding similar identifiers across different codebases.
"""

import sys
import types
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

this_file = Path(__file__).resolve()
src_dir = str(this_file.parent.parent)  # points to .../src

try:
    this_file = Path(__file__).resolve()
    src_dir = str(this_file.parent.parent)  # points to .../src
    if "src" not in sys.modules:
        src_pkg = types.ModuleType("src")
        # Mark as package by providing __path__ where Python can find subpackages
        src_pkg.__path__ = [src_dir]
        sys.modules["src"] = src_pkg
except Exception as e:
    # Log package setup failure for debugging, but don't fail import
    logger.debug(f"Package shim setup failed: {e}")

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
cli = None

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
        IdentifierSet,
        MatchResult as ProtocolMatchResult,
        CacheStats,
        ProjectInfo as ProtocolProjectInfo,
    )
except ImportError:
    # Fallback imports
    RepoMapProtocol = None  # type: ignore[assignment,misc]
    MatcherProtocol = None  # type: ignore[assignment,misc]
    FuzzyMatcherProtocol = None  # type: ignore[assignment,misc]
    SemanticMatcherProtocol = None  # type: ignore[assignment,misc]
    HybridMatcherProtocol = None  # type: ignore[assignment,misc]
    CacheManagerProtocol = None  # type: ignore[assignment,misc]
    FileScannerProtocol = None  # type: ignore[assignment,misc]
    ProjectAnalyzerProtocol = None  # type: ignore[assignment,misc]
    IdentifierSet = None  # type: ignore[assignment,misc]
    ProtocolMatchResult = None  # type: ignore[assignment,misc]
    CacheStats = None  # type: ignore[assignment,misc]
    ProtocolProjectInfo = None  # type: ignore[assignment,misc]

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
