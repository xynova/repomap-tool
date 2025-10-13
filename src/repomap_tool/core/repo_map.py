"""
Main RepoMapService class.

This module contains the core RepoMapService class that orchestrates
code analysis and search functionality.
"""

import logging
from .config_service import get_config
from .logging_service import get_logger
import os
import time
import traceback
from typing import List, Dict, Optional, Any
from ..protocols import (
    RepoMapProtocol,
    FuzzyMatcherProtocol,
    SemanticMatcherProtocol,
    HybridMatcherProtocol,
)
from datetime import datetime

from ..models import (
    RepoMapConfig,
    SearchRequest,
    SearchResponse,
    ProjectInfo,
    MatchResult,
)
from .file_scanner import get_project_files
from .analyzer import analyze_file_types, analyze_identifier_types, get_cache_size
from .search_engine import fuzzy_search, semantic_search, hybrid_search, basic_search
from .parallel_processor import ParallelTagExtractor
from rich.console import Console

# Import matchers
try:
    from ..code_search.fuzzy_matcher import FuzzyMatcher
    from ..code_search.adaptive_semantic_matcher import AdaptiveSemanticMatcher
    from ..code_search.hybrid_matcher import HybridMatcher

    MATCHERS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Failed to import matchers: {e}")
    MATCHERS_AVAILABLE = False


class RepoMapService:
    """
    Repository analysis service with Pydantic configuration and structured data handling.

    This service orchestrates code analysis and identifier matching capabilities
    with improved configuration management using Pydantic models.
    """

    def __init__(
        self,
        config: RepoMapConfig,
        console: Optional[Any] = None,
        parallel_extractor: Optional[Any] = None,
        fuzzy_matcher: Optional[Any] = None,
        semantic_matcher: Optional[Any] = None,
        embedding_matcher: Optional[Any] = None,
        hybrid_matcher: Optional[Any] = None,
        dependency_graph: Optional[Any] = None,
        impact_analyzer: Optional[Any] = None,
        centrality_calculator: Optional[Any] = None,
        spellchecker_service: Optional[Any] = None,
    ):
        """
        Initialize RepoMapService with validated configuration and injected dependencies.

        Args:
            config: Validated RepoMapConfig instance
            console: Rich console instance (injected)
            parallel_extractor: Parallel tag extractor (injected)
            fuzzy_matcher: Fuzzy matcher instance (injected)
            semantic_matcher: Semantic matcher instance (injected)
            hybrid_matcher: Hybrid matcher instance (injected)
            dependency_graph: Dependency graph instance (injected)
            impact_analyzer: Impact analyzer instance (injected)
            centrality_calculator: Centrality calculator instance (injected)
        """
        self.config = config
        self.logger = self._setup_logging()

        # All dependencies must be injected - no fallback allowed
        if console is None:
            raise ValueError("Console must be injected - no fallback allowed")
        if parallel_extractor is None:
            raise ValueError(
                "ParallelTagExtractor must be injected - no fallback allowed"
            )
        if fuzzy_matcher is None:
            raise ValueError("FuzzyMatcher must be injected - no fallback allowed")
        if dependency_graph is None:
            raise ValueError("DependencyGraph must be injected - no fallback allowed")
        if centrality_calculator is None:
            raise ValueError(
                "CentralityCalculator must be injected - no fallback allowed"
            )

        self.console = console
        self.parallel_extractor = parallel_extractor
        self.fuzzy_matcher = fuzzy_matcher
        self.semantic_matcher = semantic_matcher
        self.embedding_matcher = embedding_matcher
        self.hybrid_matcher = hybrid_matcher
        self.dependency_graph = dependency_graph
        self.impact_analyzer = impact_analyzer
        self.centrality_calculator = centrality_calculator
        self.spellchecker_service = spellchecker_service

        # Initialize components
        self.repo_map: Optional[RepoMapProtocol] = None
        self.analysis_results: Optional[Any] = None

        # Initialize the system
        self._initialize_components()

        self.logger.debug(f"Initialized RepoMapService for {self.config.project_root}")

        # Invalidate stale caches on initialization
        self._invalidate_stale_caches()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging based on configuration."""
        logger = get_logger(__name__)

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
            from pathlib import Path
            from diskcache import Cache
        except ImportError as e:
            raise ImportError(
                f"aider-chat is required but not installed: {e}\n"
                "Install with: pip install aider-chat"
            ) from e

        # Create real components without LLM model to avoid unnecessary initialization
        io = InputOutput()

        # Create custom RepoMap that can use absolute cache directory
        class CustomRepoMap(RepoMap):
            def __init__(
                self, cache_dir: str | None = None, *args: object, **kwargs: object
            ) -> None:
                # Set cache directory BEFORE calling parent __init__ to ensure
                # load_tags_cache() uses the correct directory
                if cache_dir:
                    self.TAGS_CACHE_DIR = cache_dir
                super().__init__(*args, **kwargs)

            def load_tags_cache(self) -> None:
                # Override to use absolute path if cache_dir is absolute
                if hasattr(self, "TAGS_CACHE_DIR") and os.path.isabs(
                    self.TAGS_CACHE_DIR
                ):
                    path = Path(self.TAGS_CACHE_DIR)
                else:
                    path = Path(self.root) / self.TAGS_CACHE_DIR

                try:
                    self.TAGS_CACHE = Cache(path)
                except Exception as e:
                    self.tags_cache_error(e)

        # Determine cache directory
        cache_dir = None
        if self.config.cache_dir:
            cache_dir = str(self.config.cache_dir)
        elif os.environ.get("CACHE_DIR"):
            cache_dir = os.environ.get("CACHE_DIR")

        # Initialize RepoMap without LLM model since we use our own semantic analysis
        self.repo_map = CustomRepoMap(
            cache_dir=cache_dir,
            map_tokens=self.config.map_tokens,
            root=str(self.config.project_root),
            main_model=None,  # No LLM model needed - we use our own matchers
            io=io,
            verbose=self.config.verbose,
            refresh="auto" if self.config.refresh_cache else "no",
        )

        # Matchers are now initialized via DI container in _initialize_with_di_container

    def _invalidate_stale_caches(self) -> None:
        """Invalidate cache entries for files that have been modified since caching."""
        try:
            # Get current project files
            project_files = get_project_files(
                str(self.config.project_root), self.config.verbose
            )

            # Check and invalidate stale caches in fuzzy matcher
            if self.fuzzy_matcher and hasattr(self.fuzzy_matcher, "cache_manager"):
                cache_manager = self.fuzzy_matcher.cache_manager
                if cache_manager:
                    invalidated_files = cache_manager.invalidate_stale_files(
                        project_files
                    )
                    if invalidated_files > 0:
                        self.logger.info(
                            f"Invalidated caches for {invalidated_files} modified files"
                        )

            # Invalidate embedding caches
            if self.embedding_matcher and hasattr(self.embedding_matcher, "cache_manager"):
                cache_manager = self.embedding_matcher.cache_manager
                if cache_manager:
                    invalidated = cache_manager.invalidate_stale_files(project_files)
                    if invalidated > 0:
                        self.logger.info(f"Invalidated {invalidated} embedding caches")

        except Exception as e:
            self.logger.warning(f"Error during cache invalidation: {e}")

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

    def analyze_project_with_progress(self) -> ProjectInfo:
        """
        Analyze the project with progress indication.

        Returns:
            ProjectInfo object with analysis results
        """
        if not self.config.performance.enable_progress:
            return self.analyze_project()

        from rich.progress import (
            Progress,
            SpinnerColumn,
            TextColumn,
            BarColumn,
            TimeElapsedColumn,
        )

        start_time = time.time()
        self.logger.info("Starting project analysis with progress tracking...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
        ) as progress:

            # Task 1: Scan files
            scan_task = progress.add_task("Scanning project files...", total=None)
            project_files = get_project_files(
                str(self.config.project_root), self.config.verbose
            )
            progress.update(scan_task, completed=True)

            # Task 2: Extract identifiers
            extract_task = progress.add_task(
                f"Extracting identifiers from {len(project_files)} files...",
                total=(
                    len(project_files)
                    if len(project_files) < self.config.performance.parallel_threshold
                    else None
                ),
            )
            identifier_list = self._extract_identifiers_from_files(project_files)
            progress.update(extract_task, completed=True)

            # Task 3: Analyze results
            analyze_task = progress.add_task("Analyzing results...", total=None)
            identifiers = set(identifier_list)
            file_types = analyze_file_types(project_files)
            identifier_types = analyze_identifier_types(identifiers)
            progress.update(analyze_task, completed=True)

        processing_time = time.time() - start_time

        project_info = ProjectInfo(
            project_root=str(self.config.project_root),
            total_files=len(project_files),
            total_identifiers=len(identifiers),
            file_types=file_types,
            identifier_types=identifier_types,
            analysis_time_ms=processing_time * 1000,  # Convert to milliseconds
            cache_size_bytes=get_cache_size(),
            last_updated=datetime.now(),
        )

        self.logger.info(
            f"Project analysis completed in {processing_time:.2f}s: "
            f"{len(project_files)} files, {len(identifiers)} identifiers"
        )

        return project_info

    def search_identifiers(self, request: SearchRequest) -> SearchResponse:
        """Perform search based on request configuration using tree-sitter."""
        start_time = time.time()

        # Debug logging (only shows with --verbose)
        self.logger.debug(f"Search request: query='{request.query}', match_type={request.match_type}, threshold={request.threshold}")

        # Force cache refresh if empty
        if not self.repo_map or not hasattr(self.repo_map, 'TAGS_CACHE') or not self.repo_map.TAGS_CACHE:
            self.logger.debug("TAGS_CACHE is empty or missing, forcing refresh")
            project_files = get_project_files(str(self.config.project_root), self.config.verbose)
            if self.repo_map:
                self.repo_map.get_ranked_tags_map(project_files)

        # ALWAYS use tree-sitter - no fallbacks
        tags = self._get_cached_tags()
        
        # Log tag count
        self.logger.debug(f"Found {len(tags) if tags else 0} cached tags")

        if not tags:
            # Force tree-sitter to scan files and populate cache
            self.logger.debug("Cache empty, forcing tree-sitter tag extraction")
            
            # Get project files
            project_files = get_project_files(
                str(self.config.project_root), self.config.verbose
            )
            
            # Force tree-sitter to extract tags
            if self.repo_map:
                # This populates TAGS_CACHE via tree-sitter
                self.repo_map.get_ranked_tags_map(project_files)
                
                # Get cached tags from tree-sitter (now populated)
                tags = self._get_cached_tags()
            
            if not tags:
                # If still no tags, the project has no identifiers (empty project)
                self.logger.warning("No tags found after tree-sitter extraction - empty project?")
        else:
            self.logger.debug(f"Using cached tags from tree-sitter: {len(tags)} found")

        if not tags:
            return SearchResponse(
                query=request.query,
                match_type=request.match_type,
                threshold=request.threshold,
                total_results=0,
                results=[],
                search_time_ms=(time.time() - start_time) * 1000,
            )

        # Extract identifiers for search
        identifiers = [tag["name"] for tag in tags]
        
        # Log identifier count
        self.logger.debug(f"Extracted {len(identifiers)} identifiers from tags")
        self.logger.debug(f"Sample identifiers: {identifiers[:10]}")

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
                request.query, identifiers, self.hybrid_matcher, request.max_results, request.threshold
            )
        else:
            # Fallback to basic search
            results = basic_search(request.query, identifiers, request.max_results)

        # Enhance results with file path and line number information
        enhanced_results = []
        for result in results:
            # Find the corresponding tag for this identifier
            matching_tag = None
            for tag in tags:
                if tag["name"] == result.identifier:
                    matching_tag = tag
                    break

            # Create enhanced result with file path and line number
            # Filter out invalid line numbers (must be >= 1)
            line_number = None
            if matching_tag and matching_tag["line"] is not None:
                line_num = matching_tag["line"]
                if isinstance(line_num, int) and line_num >= 1:
                    line_number = line_num

            enhanced_result = MatchResult(
                identifier=result.identifier,
                score=result.score,
                strategy=result.strategy,
                match_type=result.match_type,
                file_path=matching_tag["file"] if matching_tag else None,
                line_number=line_number,
                context=result.context,
                metadata=result.metadata,
            )
            enhanced_results.append(enhanced_result)

        processing_time = time.time() - start_time

        # Get spellchecker suggestions if no results or few results
        spellcheck_suggestions = []
        self.logger.debug(f"Spellchecker service available: {self.spellchecker_service is not None}")
        if (len(enhanced_results) == 0 or len(enhanced_results) < 3) and self.spellchecker_service:
            try:
                self.logger.debug(f"Getting spellchecker suggestions for: '{request.query}'")
                suggestions = self.spellchecker_service.get_did_you_mean_suggestions(request.query)
                spellcheck_suggestions = suggestions
                if suggestions:
                    self.logger.debug(f"Spellchecker suggestions: {suggestions}")
                else:
                    self.logger.debug("No spellchecker suggestions found")
            except Exception as e:
                self.logger.error(f"Spellchecker error: {e}")
        else:
            self.logger.debug(f"Skipping spellchecker: results={len(enhanced_results)}, service={self.spellchecker_service is not None}")

        self.logger.debug(f"Creating SearchResponse with spellcheck_suggestions: {spellcheck_suggestions}")
        return SearchResponse(
            query=request.query,
            match_type=request.match_type,
            threshold=request.threshold,
            total_results=len(enhanced_results),
            results=enhanced_results,
            search_time_ms=processing_time * 1000,  # Convert to milliseconds
            spellcheck_suggestions=spellcheck_suggestions,
        )

    def _get_cached_identifiers(self) -> List[str]:
        """
        Get all identifiers from the aider cache.

        Returns:
            List of identifier names from cache, or empty list if cache unavailable
        """
        if not self.repo_map or not hasattr(self.repo_map, "TAGS_CACHE"):
            self.logger.debug("No aider cache available")
            return []

        try:
            cache = self.repo_map.TAGS_CACHE
            all_identifiers = set()

            # Iterate through all cached files
            for key in cache:
                try:
                    value = cache[key]
                    if isinstance(value, dict) and "data" in value:
                        data = value["data"]
                        if isinstance(data, list):
                            for tag in data:
                                if hasattr(tag, "name") and tag.name:
                                    all_identifiers.add(tag.name)
                except Exception as e:
                    self.logger.debug(f"Error processing cache entry {key}: {e}")
                    continue

            identifiers_list = list(all_identifiers)
            self.logger.debug(
                f"Retrieved {len(identifiers_list)} identifiers from cache"
            )
            return identifiers_list

        except Exception as e:
            self.logger.warning(f"Failed to retrieve identifiers from cache: {e}")
            return []

    def _get_cached_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags with full information from the aider cache.

        Returns:
            List of tag dictionaries with name, type, file, and line information
        """
        if not self.repo_map or not hasattr(self.repo_map, "TAGS_CACHE"):
            self.logger.debug("No aider cache available")
            return []

        try:
            cache = self.repo_map.TAGS_CACHE
            self.logger.debug(f"TAGS_CACHE type: {type(cache)}, size: {len(cache) if cache else 0}")
            
            if not cache:
                self.logger.debug("TAGS_CACHE is empty")
                return []
            
            all_tags = []

            # Iterate through all cached files
            for key in cache:
                try:
                    value = cache[key]
                    if isinstance(value, dict) and "data" in value:
                        data = value["data"]
                        if isinstance(data, list):
                            self.logger.debug(f"File {key}: {len(data)} tags")
                            for tag in data:
                                if hasattr(tag, "name") and tag.name:
                                    # Extract full tag information
                                    # Use the cache key as the file path if tag.file is not available
                                    file_path = getattr(tag, "file", None)
                                    if not file_path:
                                        # The cache key is likely the file path
                                        file_path = key

                                    tag_info = {
                                        "name": tag.name,
                                        "type": getattr(tag, "type", None),
                                        "file": file_path,
                                        "line": getattr(tag, "line", None),
                                    }
                                    all_tags.append(tag_info)
                except Exception as e:
                    self.logger.debug(f"Error processing cache entry {key}: {e}")
                    continue

            self.logger.debug(f"Total tags extracted: {len(all_tags)}")
            return all_tags

        except Exception as e:
            self.logger.warning(f"Failed to retrieve tags from cache: {e}")
            return []

    def get_tags(self) -> List[str]:
        """Get all available tags/identifiers in the project."""
        # Try to use cached identifiers first
        identifiers = self._get_cached_identifiers()

        if not identifiers:
            # Fallback: re-parse files
            project_files = get_project_files(
                str(self.config.project_root), self.config.verbose
            )
            identifiers = self._extract_identifiers_from_files(project_files)

        return sorted(list(set(identifiers)))

    def get_ranked_tags_map(self) -> Dict[str, float]:
        """Get a map of tags with their relevance scores."""
        # Try to use cached identifiers first
        identifier_list = self._get_cached_identifiers()

        if not identifier_list:
            # Fallback: re-parse files
            project_files = get_project_files(
                str(self.config.project_root), self.config.verbose
            )
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
        Extract identifiers from project files using parallel processing when beneficial.

        Args:
            project_files: List of file paths to process

        Returns:
            List of identifier names extracted from the files
        """
        # Use parallel processing if we have enough files and it's enabled
        if (
            len(project_files) >= self.config.performance.parallel_threshold
            and self.config.performance.enable_progress
        ):

            self.logger.info(
                f"Using parallel processing for {len(project_files)} files"
            )
            return self._extract_identifiers_parallel(project_files)
        else:
            self.logger.debug(
                f"Using sequential processing for {len(project_files)} files"
            )
            return self._extract_identifiers_sequential(project_files)

    def _extract_identifiers_parallel(self, project_files: List[str]) -> List[str]:
        """
        Extract identifiers from files using parallel processing.

        For development tools: fails fast with helpful error messages.

        Args:
            project_files: List of file paths to process

        Returns:
            List of identifier names extracted from the files

        Raises:
            Exception: If parallel processing fails, with helpful debugging info
        """
        try:
            identifiers: List[str]
            stats: Any
            identifiers, stats = self.parallel_extractor.extract_tags_parallel(
                files=project_files,
                project_root=str(self.config.project_root),
                repo_map=self.repo_map,
            )

            # Log performance statistics
            if self.config.performance.enable_monitoring:
                self.logger.info(
                    f"Parallel processing completed: "
                    f"{stats.successful_files}/{stats.total_files} files successful, "
                    f"{stats.total_identifiers} identifiers found, "
                    f"{stats.processing_time:.2f}s total time"
                )

            return identifiers

        except Exception as e:
            # Development-focused: fail fast with helpful error messages
            self.logger.error(f"Parallel processing failed: {e}")
            self.logger.error("This might be due to:")
            self.logger.error("  - Too many worker threads for your system")
            self.logger.error("  - File system issues or permissions")
            self.logger.error("  - Memory constraints")
            self.logger.error("")
            self.logger.error("Try these solutions:")
            self.logger.error(
                f"  - Reduce --max-workers (current: {self.config.performance.max_workers})"
            )
            self.logger.error("  - Use --no-progress to disable progress tracking")
            self.logger.error("  - Check file permissions and disk space")
            self.logger.error("")

            # Provide specific suggestions based on error type
            error_str = str(e).lower()
            if "memory" in error_str or "out of memory" in error_str:
                self.logger.error("💡 Memory issue detected - try: --max-workers 2")
            elif "thread" in error_str or "pool" in error_str:
                self.logger.error("💡 Threading issue detected - try: --max-workers 1")
            elif "file" in error_str or "permission" in error_str:
                self.logger.error("💡 File system issue detected - try: --no-progress")
            elif "timeout" in error_str:
                self.logger.error("💡 Timeout issue detected - try: --max-workers 1")

            # Fail fast for development - let developer handle it
            if self.config.performance.allow_fallback:
                self.logger.warning(
                    "Fallback enabled - switching to sequential processing..."
                )
                return self._extract_identifiers_sequential(project_files)
            else:
                raise

    def _extract_identifiers_sequential(self, project_files: List[str]) -> List[str]:
        """
        Extract identifiers from files using sequential processing.

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
                self.logger.debug(f"Traceback: {traceback.format_exc()}")
                continue
        return identifiers

    def _get_cached_import_analysis(self) -> Optional[Any]:
        """
        Get cached import analysis results from persistent cache.

        Returns:
            Cached ProjectImports object or None if not available
        """
        if not self.repo_map or not hasattr(self.repo_map, "TAGS_CACHE"):
            self.logger.debug("No aider cache available for import analysis")
            return None

        try:
            cache = self.repo_map.TAGS_CACHE
            # Include max_graph_size in cache key to ensure different configs get different cache entries
            # Also include refresh_cache flag to force cache miss when refresh is requested
            refresh_flag = "refresh" if self.config.refresh_cache else "normal"
            cache_key = f"import_analysis_{self.config.project_root}_maxsize_{self.config.dependencies.max_graph_size}_{refresh_flag}"
            self.logger.debug(f"Cache key: {cache_key}")
            self.logger.debug(
                f"Config max_graph_size: {self.config.dependencies.max_graph_size}"
            )
            self.logger.debug(f"Config refresh_cache: {self.config.refresh_cache}")

            if cache_key in cache:
                cached_data = cache[cache_key]
                self.logger.debug("Using cached import analysis results")
                return cached_data
            else:
                self.logger.debug("No cached import analysis found")
                return None

        except Exception as e:
            self.logger.warning(f"Failed to retrieve cached import analysis: {e}")
            return None

    def _cache_import_analysis(self, project_imports: Any) -> None:
        """
        Cache import analysis results to persistent cache.

        Args:
            project_imports: ProjectImports object to cache
        """
        if not self.repo_map or not hasattr(self.repo_map, "TAGS_CACHE"):
            self.logger.debug("No aider cache available for caching import analysis")
            return

        try:
            cache = self.repo_map.TAGS_CACHE
            # Include max_graph_size in cache key to ensure different configs get different cache entries
            # Also include refresh_cache flag to force cache miss when refresh is requested
            refresh_flag = "refresh" if self.config.refresh_cache else "normal"
            cache_key = f"import_analysis_{self.config.project_root}_maxsize_{self.config.dependencies.max_graph_size}_{refresh_flag}"
            cache[cache_key] = project_imports
            self.logger.info("Cached import analysis results to persistent storage")
        except Exception as e:
            self.logger.warning(f"Failed to cache import analysis: {e}")

    # Phase 2: Dependency Analysis Methods

    def build_dependency_graph(self) -> Any:
        """Build dependency graph for the project."""
        if self.dependency_graph is None:
            raise RuntimeError("Dependency analysis components not initialized")

        start_time = time.time()

        try:
            # Try to use cached import analysis first
            project_imports = self._get_cached_import_analysis()

            if project_imports is None:
                # Fallback: Use DI container to get ImportAnalyzer
                from ..core.container import create_container

                # Create container and get import analyzer
                container = create_container(self.config)
                import_analyzer = container.import_analyzer()

                # Analyze project imports
                project_imports = import_analyzer.analyze_project_imports(
                    str(self.config.project_root)
                )

                # Cache the results for future use
                self._cache_import_analysis(project_imports)

            # Limit files if configured
            self.logger.debug(
                f"Configuration max_graph_size: {self.config.dependencies.max_graph_size}"
            )
            self.logger.debug(f"Project imports count: {len(project_imports)}")
            if len(project_imports) > self.config.dependencies.max_graph_size:
                self.logger.warning(
                    f"Project has {len(project_imports)} files, limiting to "
                    f"{self.config.dependencies.max_graph_size} for dependency analysis"
                )
                # Create a limited version of project_imports
                limited_files = list(project_imports.file_imports.keys())[
                    : self.config.dependencies.max_graph_size
                ]
                limited_file_imports = {
                    k: v
                    for k, v in project_imports.file_imports.items()
                    if k in limited_files
                }
                project_imports.file_imports = limited_file_imports

            # Build the dependency graph
            self.dependency_graph.build_graph(project_imports)

            # Add construction time to statistics
            construction_time = time.time() - start_time
            self.dependency_graph.construction_time = construction_time

            # Check performance threshold
            if (
                construction_time
                > self.config.dependencies.performance_threshold_seconds
            ):
                self.logger.warning(
                    f"Dependency graph construction took {construction_time:.2f}s, "
                    f"exceeding threshold of {self.config.dependencies.performance_threshold_seconds}s"
                )

            self.logger.debug(
                f"Built dependency graph: {len(project_imports)} files in {construction_time:.2f}s"
            )

            return self.dependency_graph

        except Exception as e:
            self.logger.error(f"Failed to build dependency graph: {e}")
            raise

    def get_centrality_scores(self) -> Dict[str, float]:
        """Get centrality scores for all files in the dependency graph."""
        # Dependency analysis is always enabled

        if self.centrality_calculator is None:
            raise RuntimeError("Centrality calculator not initialized")

        if self.dependency_graph is None or not self.dependency_graph.nodes:
            # Build graph if not already built
            self.build_dependency_graph()

        try:
            assert self.centrality_calculator is not None  # For mypy
            return self.centrality_calculator.calculate_composite_importance()  # type: ignore
        except Exception as e:
            self.logger.error(f"Failed to calculate centrality scores: {e}")
            raise

    def analyze_change_impact(self, file_path: str) -> Dict[str, Any]:
        """Analyze the impact of changes to a specific file."""
        # Dependency analysis is always enabled

        if not self.config.dependencies.enable_impact_analysis:
            raise RuntimeError("Impact analysis is not enabled")

        if self.impact_analyzer is None:
            raise RuntimeError("Impact analyzer not initialized")

        if self.dependency_graph is None or not self.dependency_graph.nodes:
            # Build graph if not already built
            self.build_dependency_graph()

        try:
            assert self.impact_analyzer is not None  # For mypy
            return self.impact_analyzer.analyze_change_impact([file_path])  # type: ignore
        except Exception as e:
            self.logger.error(f"Failed to analyze change impact: {e}")
            raise

    def find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependencies in the project."""
        # Dependency analysis is always enabled

        if self.dependency_graph is None or not self.dependency_graph.nodes:
            # Build graph if not already built
            self.build_dependency_graph()

        try:
            assert self.dependency_graph is not None  # For mypy
            return self.dependency_graph.find_cycles()  # type: ignore
        except Exception as e:
            self.logger.error(f"Failed to find circular dependencies: {e}")
            raise

    def get_all_symbols(self) -> List[Dict[str, Any]]:
        """Get all symbols from the project."""
        if not self.analysis_results:
            self.analyze_project()

        if self.analysis_results is None:
            return []

        symbols = []
        for file_path, file_info in self.analysis_results.files.items():
            for identifier, details in file_info.identifiers.items():
                symbols.append(
                    {
                        "identifier": identifier,
                        "file_path": file_path,
                        "line_number": details.line_number,
                        "type": details.type,
                    }
                )
        return symbols

    def semantic_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a semantic search for a query."""
        if not self.semantic_matcher or not self.semantic_matcher.enabled:
            return []

        # Use real search engine implementation
        all_symbols = self.get_all_symbols()
        identifiers = [symbol["identifier"] for symbol in all_symbols]

        # Get real search results with actual similarity scores
        match_results = semantic_search(
            query=query,
            identifiers=identifiers,
            semantic_matcher=self.semantic_matcher,
            limit=get_config("DEFAULT_LIMIT", 5),
        )

        # Convert MatchResult objects to the expected format
        results = []
        for match_result in match_results:
            # Find the corresponding symbol data
            symbol_data = next(
                (
                    symbol
                    for symbol in all_symbols
                    if symbol["identifier"] == match_result.identifier
                ),
                {
                    "identifier": match_result.identifier,
                    "file_path": match_result.file_path,
                },
            )
            results.append(
                {
                    "symbol": symbol_data,
                    "score": match_result.score,  # Real score from semantic matcher
                    "strategy": match_result.strategy,
                    "match_type": match_result.match_type,
                    "context": match_result.context,
                }
            )

        return results

    def fuzzy_search(self, query: str) -> List[Any]:
        """Perform a fuzzy search for a query."""
        if not self.fuzzy_matcher:
            return []

        # Use real search engine implementation
        all_symbols = self.get_all_symbols()
        identifiers = [symbol["identifier"] for symbol in all_symbols]

        # Get real search results with actual similarity scores
        match_results = fuzzy_search(
            query=query,
            identifiers=identifiers,
            fuzzy_matcher=self.fuzzy_matcher,
            limit=get_config("DEFAULT_LIMIT", 5),
        )

        # Return MatchResult objects directly (as expected by the interface)
        return match_results

    def get_dependency_enhanced_trees(
        self, session_id: str, intent: str, current_files: Optional[List[str]] = None
    ) -> List[Any]:
        """Generate enhanced exploration trees with dependency intelligence."""
        # Dependency analysis is always enabled

        if self.dependency_graph is None or not self.dependency_graph.nodes:
            # Build graph if not already built
            self.build_dependency_graph()

        try:
            # Use service factory for proper dependency injection
            from ..cli.services import get_service_factory

            service_factory = get_service_factory()

            # Create services with proper DI
            enhanced_discoverer = service_factory.create_entrypoint_discoverer(
                self, self.config
            )
            entrypoints = enhanced_discoverer.discover_entrypoints(
                str(self.config.project_root), intent
            )

            # Build full exploration trees with dependency intelligence
            tree_builder = service_factory.create_tree_builder(self, self.config)
            exploration_trees = []

            for entrypoint in entrypoints:
                try:
                    # Build tree with dependency intelligence
                    tree = tree_builder.build_exploration_tree_with_dependencies(
                        entrypoint=entrypoint,
                        max_depth=self._calculate_optimal_depth(entrypoint),
                        current_files=current_files,
                    )
                    exploration_trees.append(tree)

                except Exception as e:
                    self.logger.warning(
                        f"Failed to build tree for {entrypoint.identifier}: {e}"
                    )
                    # Fallback to simple tree structure
                    tree = tree_builder.build_exploration_tree(entrypoint)
                    exploration_trees.append(tree)

            self.logger.info(
                f"Built {len(exploration_trees)} dependency-enhanced trees"
            )
            return exploration_trees

        except Exception as e:
            self.logger.error(f"Failed to generate dependency-enhanced trees: {e}")
            raise

    def _calculate_optimal_depth(self, entrypoint: Any) -> int:
        """Calculate optimal tree depth based on entrypoint complexity and centrality."""
        try:
            if not self.centrality_calculator:
                return 3  # Default depth

            # Get centrality scores for the entrypoint file
            file_path = str(entrypoint.location)
            centrality_scores = (
                self.centrality_calculator.calculate_composite_importance()
            )

            if file_path in centrality_scores:
                importance = centrality_scores[file_path]
                # Higher importance = deeper exploration (max 5, min 2)
                depth = max(2, min(5, int(importance * 5) + 2))
                self.logger.debug(
                    f"Calculated depth {depth} for {file_path} (importance: {importance:.3f})"
                )
                return depth

            return 3  # Default depth

        except Exception as e:
            self.logger.warning(f"Failed to calculate optimal depth: {e}")
            return 3
