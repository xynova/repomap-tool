"""
Protocols for type safety in repomap-tool.

This module defines protocols and type-safe interfaces for the core components.
"""

from typing import Protocol, List, Set, Optional, Dict, Any, TypedDict
from pathlib import Path


class RepoMapProtocol(Protocol):
    """Protocol for RepoMap-like objects."""

    def get_tags(self, file_path: str, rel_fname: str) -> List[Any]: ...

    def get_ranked_tags_map(
        self, files: List[str], max_tokens: int
    ) -> Optional[str]: ...


class MatcherProtocol(Protocol):
    """Protocol for matcher objects."""

    def match_identifiers(
        self, query: str, all_identifiers: Set[str]
    ) -> List[tuple[str, int]]: ...

    def clear_cache(self) -> None: ...

    def get_cache_stats(self) -> Dict[str, Any]: ...


class FuzzyMatcherProtocol(MatcherProtocol):
    """Protocol for fuzzy matcher objects."""

    threshold: int
    strategies: List[str]
    cache_results: bool
    verbose: bool
    enabled: bool


class SemanticMatcherProtocol(MatcherProtocol):
    """Protocol for semantic matcher objects."""

    threshold: float
    use_tfidf: bool
    min_word_length: int
    cache_results: bool
    enabled: bool


class HybridMatcherProtocol(MatcherProtocol):
    """Protocol for hybrid matcher objects."""

    fuzzy_threshold: int
    semantic_threshold: float
    verbose: bool
    enabled: bool


class CacheManagerProtocol(Protocol):
    """Protocol for cache manager objects."""

    def get(self, key: str) -> Optional[Any]: ...

    def set(self, key: str, value: Any) -> None: ...

    def clear(self) -> None: ...

    def get_stats(self) -> Dict[str, Any]: ...

    def cleanup_expired(self) -> int: ...

    def resize(self, new_max_size: int) -> None: ...


class FileScannerProtocol(Protocol):
    """Protocol for file scanner objects."""

    def scan_files(self, project_root: Path) -> List[str]: ...

    def should_ignore_file(self, file_path: str) -> bool: ...


class ProjectAnalyzerProtocol(Protocol):
    """Protocol for project analyzer objects."""

    def analyze_project(self) -> Dict[str, Any]: ...

    def get_project_info(self) -> Dict[str, Any]: ...


# TypedDict definitions for structured data
class Tag(TypedDict):
    """Tag structure for project identifiers."""

    name: str
    type: Optional[str]
    file: Optional[str]
    line: Optional[int]


class FileData(TypedDict):
    """File data structure in project map."""

    identifiers: Optional[List[str]]
    tags: Optional[List[Tag]]
    content: Optional[str]


class ProjectMap(TypedDict):
    """Structured project map data."""

    tags: Optional[List[Tag]]
    identifiers: Optional[List[str]]
    files: Optional[Dict[str, FileData]]


# Type aliases for better readability
IdentifierSet = Set[str]
MatchResult = tuple[str, int]
CacheStats = Dict[str, Any]
ProjectInfo = Dict[str, Any]
