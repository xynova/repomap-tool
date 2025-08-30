"""
Main DockerRepoMap class.

This module contains the core DockerRepoMap class that orchestrates
code analysis and search functionality.
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..models import (
    RepoMapConfig,
    SearchRequest,
    SearchResponse,
    ProjectInfo,
)
from .file_scanner import get_project_files
from .analyzer import analyze_file_types, analyze_identifier_types, get_cache_size
from .search_engine import fuzzy_search, semantic_search, hybrid_search, basic_search

# Import matchers
try:
    from ..matchers.fuzzy_matcher import FuzzyMatcher
    from ..matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
    from ..matchers.hybrid_matcher import HybridMatcher

    MATCHERS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import matchers: {e}")
    MATCHERS_AVAILABLE = False


class DockerRepoMap:
    """
    Enhanced Docker RepoMap with Pydantic configuration and structured data handling.

    This class provides code analysis and identifier matching capabilities
    with improved configuration management using Pydantic models.
    """

    def __init__(self, config: RepoMapConfig):
        """
        Initialize Docker RepoMap with validated configuration.

        Args:
            config: Validated RepoMapConfig instance
        """
        self.config = config
        self.logger = self._setup_logging()

        # Initialize components
        self.repo_map: Optional[Any] = None
        self.fuzzy_matcher: Optional[FuzzyMatcher] = None
        self.semantic_matcher: Optional[AdaptiveSemanticMatcher] = None
        self.hybrid_matcher: Optional[HybridMatcher] = None

        # Initialize the system
        self._initialize_components()

        self.logger.info(f"Initialized DockerRepoMap for {self.config.project_root}")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging based on configuration."""
        logger = logging.getLogger(__name__)

        # Set log level
        level = getattr(logging, self.config.log_level)
        logger.setLevel(level)

        # Create handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        # Require aider dependencies - no fallback
        try:
            from aider.repomap import RepoMap
            from aider.io import InputOutput
        except ImportError as e:
            raise ImportError(
                f"aider-chat is required but not installed: {e}\n"
                "Install with: pip install aider-chat"
            ) from e

        # Create real components without LLM model to avoid unnecessary initialization
        io = InputOutput()

        # Initialize RepoMap without LLM model since we use our own semantic analysis
        self.repo_map = RepoMap(
            map_tokens=self.config.map_tokens,
            root=str(self.config.project_root),
            main_model=None,  # No LLM model needed - we use our own matchers
            io=io,
            verbose=self.config.verbose,
            refresh="auto" if self.config.refresh_cache else "no",
        )

        # Initialize matchers if available
        if MATCHERS_AVAILABLE:
            self._initialize_matchers()
        else:
            self.logger.warning("Matchers not available - matching features disabled")

    def _initialize_matchers(self) -> None:
        """Initialize matching components."""
        # Initialize fuzzy matcher
        if self.config.fuzzy_match.enabled:
            self.fuzzy_matcher = FuzzyMatcher(
                threshold=self.config.fuzzy_match.threshold,
                strategies=self.config.fuzzy_match.strategies,
                cache_results=self.config.fuzzy_match.cache_results,
                verbose=self.config.verbose,
            )
            self.logger.info(f"Initialized FuzzyMatcher: {self.config.fuzzy_match}")

        # Initialize semantic matcher
        if self.config.semantic_match.enabled:
            self.semantic_matcher = AdaptiveSemanticMatcher(verbose=self.config.verbose)
            self.logger.info(
                f"Initialized SemanticMatcher: {self.config.semantic_match}"
            )

        # Initialize hybrid matcher if both are enabled
        if self.config.fuzzy_match.enabled and self.config.semantic_match.enabled:
            self.hybrid_matcher = HybridMatcher(
                fuzzy_threshold=self.config.fuzzy_match.threshold,
                semantic_threshold=self.config.semantic_match.threshold,
                verbose=self.config.verbose,
            )
            self.logger.info("Initialized HybridMatcher")

    def analyze_project(self) -> ProjectInfo:
        """Get comprehensive project information."""
        start_time = time.time()

        # Get project files
        project_files = get_project_files(
            str(self.config.project_root), self.config.verbose
        )

        # Get project files and extract identifiers from tags
        project_files = get_project_files(
            str(self.config.project_root), self.config.verbose
        )

        # Extract identifiers from all project files
        identifier_list = self._extract_identifiers_from_files(project_files)
        identifiers = set(identifier_list)

        # Analyze project structure
        file_types = analyze_file_types(project_files)
        identifier_types = analyze_identifier_types(identifiers)

        # Calculate processing time
        processing_time = time.time() - start_time

        return ProjectInfo(
            project_root=str(self.config.project_root),
            total_files=len(project_files),
            total_identifiers=len(identifiers),
            file_types=file_types,
            identifier_types=identifier_types,
            analysis_time_ms=processing_time * 1000,  # Convert to milliseconds
            cache_size_bytes=get_cache_size(),
            last_updated=datetime.now(),
        )

    def search_identifiers(self, request: SearchRequest) -> SearchResponse:
        """Perform search based on request configuration."""
        start_time = time.time()

        # Get project files and extract identifiers from tags
        project_files = get_project_files(
            str(self.config.project_root), self.config.verbose
        )

        # Extract identifiers from all project files
        identifiers = self._extract_identifiers_from_files(project_files)

        if not identifiers:
            return SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=0,
                results=[],
                search_time_ms=(time.time() - start_time) * 1000,
            )

        # Perform search based on type
        if request.match_type == "fuzzy" and self.fuzzy_matcher:
            results = fuzzy_search(
                request.query, identifiers, self.fuzzy_matcher, request.max_results
            )
        elif request.match_type == "semantic" and self.semantic_matcher:
            results = semantic_search(
                request.query, identifiers, self.semantic_matcher, request.max_results
            )
        elif request.match_type == "hybrid" and self.hybrid_matcher:
            results = hybrid_search(
                request.query, identifiers, self.hybrid_matcher, request.max_results
            )
        else:
            # Fallback to basic search
            results = basic_search(request.query, identifiers, request.max_results)

        processing_time = time.time() - start_time

        return SearchResponse(
            query=request.query,
            match_type=request.match_type,
            threshold=request.threshold,
            total_results=len(results),
            results=results,
            search_time_ms=processing_time * 1000,  # Convert to milliseconds
        )

    def get_tags(self) -> List[str]:
        """Get all available tags/identifiers in the project."""
        project_files = get_project_files(
            str(self.config.project_root), self.config.verbose
        )

        # Extract identifiers from all project files
        identifiers = self._extract_identifiers_from_files(project_files)
        return sorted(list(set(identifiers)))

    def get_ranked_tags_map(self) -> Dict[str, float]:
        """Get a map of tags with their relevance scores."""
        project_files = get_project_files(
            str(self.config.project_root), self.config.verbose
        )

        # Extract identifiers from all project files
        identifier_list = self._extract_identifiers_from_files(project_files)
        identifiers = set(identifier_list)

        # Simple ranking based on identifier characteristics
        ranked_map = {}
        for identifier in identifiers:
            score = 1.0

            # Boost score for common patterns
            if identifier.startswith("get_") or identifier.startswith("set_"):
                score = 1.5
            elif identifier[0].isupper():  # Class names
                score = 1.3
            elif "_" in identifier and identifier.islower():  # function_names
                score = 1.2

            ranked_map[identifier] = score

        return ranked_map

    def _get_project_files(self) -> List[str]:
        """Get list of project files, respecting .gitignore patterns."""
        return get_project_files(str(self.config.project_root), self.config.verbose)

    def _extract_identifiers_from_files(self, project_files: List[str]) -> List[str]:
        """
        Extract identifiers from project files.

        Args:
            project_files: List of file paths to process

        Returns:
            List of identifier names extracted from the files
        """
        identifiers = []
        for file_path in project_files:
            try:
                if self.repo_map is not None:
                    # file_path is already relative, so we need to make it absolute for aider
                    abs_path = os.path.join(self.config.project_root, file_path)
                    self.logger.debug(f"Processing {file_path} -> {abs_path}")
                    tags = self.repo_map.get_tags(abs_path, file_path)
                    self.logger.debug(f"Found {len(tags)} tags in {file_path}")
                    for tag in tags:
                        if hasattr(tag, "name") and tag.name:
                            identifiers.append(tag.name)
                else:
                    self.logger.warning("repo_map is None")
            except Exception as e:
                self.logger.warning(f"Error processing {file_path}: {e}")
                import traceback
                self.logger.debug(f"Traceback: {traceback.format_exc()}")
                continue
        return identifiers
