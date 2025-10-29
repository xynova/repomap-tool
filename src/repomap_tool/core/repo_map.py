"""
Main RepoMapService class.

This module contains the core RepoMapService class that orchestrates
code analysis and search functionality.
"""

import logging
from .config_service import get_config
from .logging_service import get_logger
from .file_scanner import get_project_files
import os
import time
import traceback
from datetime import datetime  # Import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from repomap_tool.code_analysis.models import CodeTag
from repomap_tool.code_analysis.tree_sitter_parser import TreeSitterParser
from repomap_tool.code_analysis.dependency_graph import DependencyGraph
from repomap_tool.code_analysis.centrality_calculator import CentralityCalculator
from repomap_tool.code_analysis.file_discovery_service import FileDiscoveryService
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher
from repomap_tool.code_search.semantic_matcher import DomainSemanticMatcher
from repomap_tool.code_search.embedding_matcher import EmbeddingMatcher
from repomap_tool.code_search.hybrid_matcher import HybridMatcher
from repomap_tool.code_analysis.impact_analyzer import ImpactAnalyzer
from repomap_tool.core.spellchecker_service import SpellCheckerService
from repomap_tool.core.tag_cache import TreeSitterTagCache
from repomap_tool.protocols import RepoMapProtocol
from rich.console import Console

logger = get_logger(__name__)  # Initialize logger at module level

from ..models import (
    RepoMapConfig,
    SearchRequest,
    SearchResponse,
    ProjectInfo,
    MatchResult,
)
from .analyzer import analyze_file_types, analyze_identifier_types, get_cache_size
from .search_engine import fuzzy_search, semantic_search, hybrid_search, basic_search

# Import matchers
try:
    from repomap_tool.code_search.adaptive_semantic_matcher import (
        AdaptiveSemanticMatcher,
    )

    MATCHERS_AVAILABLE = True
except ImportError:
    logger.warning("Could not import one or more matcher components.")
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
        console: Console,
        fuzzy_matcher: FuzzyMatcher,
        dependency_graph: DependencyGraph,
        centrality_calculator: CentralityCalculator,
        tree_sitter_parser: TreeSitterParser,
        tag_cache: TreeSitterTagCache,
        file_discovery_service: FileDiscoveryService,
        semantic_matcher: Optional[DomainSemanticMatcher] = None,
        embedding_matcher: Optional[EmbeddingMatcher] = None,
        hybrid_matcher: Optional[HybridMatcher] = None,
        impact_analyzer: Optional[ImpactAnalyzer] = None,
        spellchecker_service: Optional[SpellCheckerService] = None,
    ):
        """
        Initialize RepoMapService with validated configuration and injected dependencies.

        Args:
            config: Validated RepoMapConfig instance
            console: Rich console instance (injected)
            fuzzy_matcher: Fuzzy matcher instance (injected)
            dependency_graph: Dependency graph instance (injected)
            centrality_calculator: Centrality calculator instance (injected)
            tree_sitter_parser: Tree-sitter parser instance (injected)
            tag_cache: Tag cache instance (injected)
            file_discovery_service: File discovery service instance (injected)
            semantic_matcher: Semantic matcher instance (injected)
            embedding_matcher: Embedding matcher instance (injected)
            hybrid_matcher: Hybrid matcher instance (injected)
            impact_analyzer: Impact analyzer instance (injected)
            spellchecker_service: Spell checker service instance (injected)
        """
        self.config = config
        self.logger = self._setup_logging()

        # All core dependencies are required and injected via DI container
        # Optional dependencies (semantic_matcher, embedding_matcher, etc.) are truly optional

        self.console = console
        self.fuzzy_matcher = fuzzy_matcher
        self.semantic_matcher = semantic_matcher
        self.embedding_matcher = embedding_matcher
        self.hybrid_matcher = hybrid_matcher
        self.dependency_graph = dependency_graph
        self.impact_analyzer = impact_analyzer
        self.centrality_calculator = centrality_calculator
        self.spellchecker_service = spellchecker_service
        self.tree_sitter_parser = tree_sitter_parser  # Assign injected parser
        self.tag_cache = tag_cache  # Assign injected cache
        self.import_analysis_cache: Dict[str, Any] = (
            {}
        )  # Separate cache for import analysis
        self.file_discovery_service = (
            file_discovery_service  # Assign injected file discovery service
        )

        # Initialize components
        self.repo_map: Optional[RepoMapProtocol] = None
        self.analysis_results: Optional[Any] = None

        # No longer need to initialize components directly
        # self._initialize_components()

        self.logger.debug(f"Initialized RepoMapService for {self.config.project_root}")

        # Invalidate stale caches on initialization
        self._invalidate_stale_caches()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging based on configuration."""
        # Use centralized logging service - don't add custom handlers
        # The centralized service already handles worker isolation
        logger = get_logger(__name__)

        # Set log level based on config
        level = getattr(logging, self.config.log_level)
        logger.setLevel(level)

        return logger

    def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        # This method is no longer needed as TreeSitterParser and TagCache are injected.
        pass

    def _populate_tree_sitter_cache(self) -> None:
        """Populate tree-sitter cache by parsing all project files."""
        # Ensure that tree_sitter_parser is initialized. If not, this is a dependency error.
        if not self.tree_sitter_parser:
            self.logger.error(
                "TreeSitterParser not initialized during cache population."
            )
            raise ValueError("TreeSitterParser dependency missing.")

        try:
            # Get all project files
            project_files = get_project_files(
                str(self.config.project_root),
                self.config.verbose,  # Pass Path object directly
            )
            self.logger.debug(
                f"_populate_tree_sitter_cache: Found {len(project_files)} project files for caching."
            )

            self.logger.info(
                f"Populating tree-sitter cache with {len(project_files)} files"
            )

            # Parse each file to populate the cache
            for file_path in project_files:
                self.logger.debug(
                    f"_populate_tree_sitter_cache: Processing file: {file_path}"
                )
                try:
                    # This will parse the file and cache the results
                    tags = self.tree_sitter_parser.get_tags(file_path)
                    self.logger.debug(
                        f"_populate_tree_sitter_cache: Retrieved {len(tags)} tags for {file_path}"
                    )
                except Exception as e:
                    self.logger.debug(
                        f"_populate_tree_sitter_cache: Failed to parse {file_path}: {e}"
                    )
                    continue

            self.logger.info("Tree-sitter cache populated successfully")

        except Exception as e:
            self.logger.warning(f"Failed to populate tree-sitter cache: {e}")

    def _get_cached_identifiers(self) -> List[str]:
        """Get all identifiers from tree-sitter cache"""
        all_identifiers = set()

        # Use cached tags directly instead of re-parsing
        cached_tags = self._get_cached_tags()
        self.logger.info(
            f"_get_cached_identifiers: Retrieved {len(cached_tags)} cached tags"
        )

        for tag in cached_tags:
            all_identifiers.add(tag.name)
            self.logger.debug(f"Added identifier: {tag.name} (type: {tag.kind})")

        self.logger.info(f"Retrieved {len(all_identifiers)} identifiers from cache")
        return list(all_identifiers)

    def _invalidate_stale_caches(self) -> None:
        """Invalidate cache entries for files that have been modified since caching."""
        try:
            # Get current project files
            project_files = get_project_files(
                str(self.config.project_root),
                self.config.verbose,  # Pass Path object directly
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
            if self.embedding_matcher and hasattr(
                self.embedding_matcher, "cache_manager"
            ):
                cache_manager = self.embedding_matcher.cache_manager
                if cache_manager:
                    invalidated = cache_manager.invalidate_stale_files(project_files)
                    if invalidated > 0:
                        self.logger.info(f"Invalidated {invalidated} embedding caches")

        except Exception as e:
            self.logger.warning(f"Error during cache invalidation: {e}")

    def analyze_project(self, files: Optional[List[str]] = None) -> ProjectInfo:
        """Get comprehensive project information."""
        start_time = time.time()

        # Get project files
        all_project_files = get_project_files(
            str(self.config.project_root),
            self.config.verbose,  # Pass Path object directly
        )

        # Filter project files if specific files are provided
        project_files = files if files else all_project_files

        # Ensure that only files within the project root are processed
        if self.config.project_root and project_files:
            project_root_path = Path(self.config.project_root)
            project_files = [
                f
                for f in project_files
                if Path(f).is_relative_to(project_root_path)
                or Path(f).samefile(project_root_path)
            ]

        # If no specific input_paths, the RepoMapService will analyze the entire project_root
        if not project_files:
            self.logger.warning("No project files found for analysis.")
            return ProjectInfo(
                project_root=str(self.config.project_root),
                total_files=0,
                total_identifiers=0,
                file_types={},
                identifier_types={},
                analysis_time_ms=0.0,
                cache_size_bytes=get_cache_size(),
                last_updated=datetime.now(),
            )

        # Extract identifiers from all project files
        identifier_list = self._extract_identifiers_from_files(project_files)
        identifiers = {tag.name for tag in identifier_list}  # Convert to set of names

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
            # Call analyze_project without specifying files, it will use all_project_files
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
                str(self.config.project_root),
                self.config.verbose,  # Pass Path object directly
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
            identifiers = {
                tag.name for tag in identifier_list
            }  # Convert to set of names
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
        self.logger.debug(
            f"Search request: query='{request.query}', match_type={request.match_type}, threshold={request.threshold}"
        )

        # Force cache refresh if empty
        if (
            not self.tree_sitter_parser or not self.tag_cache
        ):  # Check injected tag_cache
            self.logger.debug("Tree-sitter cache is empty or missing, forcing refresh")
            project_files = self.file_discovery_service.get_tree_sitter_supported_files(
                self.tree_sitter_parser, exclude_tests=True
            )
            if self.repo_map and project_files:
                try:
                    self.repo_map.get_ranked_tags_map(project_files, max_tokens=4000)
                except ZeroDivisionError:
                    # Handle case where tree-sitter library encounters division by zero
                    self.logger.warning(
                        "No files found for RepoMap integration, skipping tree-sitter processing"
                    )
                    pass

        # ALWAYS use tree-sitter - no fallbacks
        tags = self._get_cached_tags()

        # Log tag count
        self.logger.debug(f"Found {len(tags) if tags else 0} cached tags")

        if not tags:
            # Force tree-sitter to scan files and populate cache
            self.logger.debug("Cache empty, forcing tree-sitter tag extraction")

            # Get project files that are supported by tree-sitter
            project_files = self.file_discovery_service.get_tree_sitter_supported_files(
                self.tree_sitter_parser, exclude_tests=True
            )

            # Force tree-sitter to extract tags
            if self.tree_sitter_parser:
                # This populates tree-sitter cache by parsing files
                try:
                    # Parse files to populate cache
                    for file_path in project_files:
                        self.tree_sitter_parser.get_tags(file_path, use_cache=True)
                except ZeroDivisionError:
                    # Handle case where tree-sitter library encounters division by zero
                    self.logger.warning(
                        "No files found for RepoMap integration, skipping tree-sitter processing"
                    )
                    pass

                # Get cached tags from tree-sitter (now populated)
                tags = self._get_cached_tags()

            if not tags:
                # If still no tags, the project has no identifiers (empty project)
                self.logger.warning(
                    "No tags found after tree-sitter extraction - empty project?"
                )
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
        identifiers = [tag.name for tag in tags]

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
                request.query,
                identifiers,
                self.hybrid_matcher,
                request.max_results,
                request.threshold,
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
                if tag.name == result.identifier:
                    matching_tag = tag
                    break

            # Create enhanced result with file path and line number
            # Filter out invalid line numbers (must be >= 1)
            line_number = None
            if matching_tag and matching_tag.line is not None:
                line_num = matching_tag.line
                if isinstance(line_num, int) and line_num >= 1:
                    line_number = line_num

            enhanced_result = MatchResult(
                identifier=result.identifier,
                score=result.score,
                strategy=result.strategy,
                match_type=result.match_type,
                file_path=matching_tag.file if matching_tag else None,
                line_number=line_number,
                context=result.context,
                metadata=result.metadata,
            )
            enhanced_results.append(enhanced_result)

        processing_time = time.time() - start_time

        # Get spellchecker suggestions if no results or few results
        spellcheck_suggestions = []
        self.logger.debug(
            f"Spellchecker service available: {self.spellchecker_service is not None}"
        )
        if (
            len(enhanced_results) == 0 or len(enhanced_results) < 3
        ) and self.spellchecker_service:
            try:
                self.logger.debug(
                    f"Getting spellchecker suggestions for: '{request.query}'"
                )
                suggestions = self.spellchecker_service.get_did_you_mean_suggestions(
                    request.query
                )
                spellcheck_suggestions = suggestions
                if suggestions:
                    self.logger.debug(f"Spellchecker suggestions: {suggestions}")
                else:
                    self.logger.debug("No spellchecker suggestions found")
            except Exception as e:
                self.logger.error(f"Spellchecker error: {e}")
        else:
            self.logger.debug(
                f"Skipping spellchecker: results={len(enhanced_results)}, service={self.spellchecker_service is not None}"
            )

        self.logger.debug(
            f"Creating SearchResponse with spellcheck_suggestions: {spellcheck_suggestions}"
        )
        return SearchResponse(
            query=request.query,
            match_type=request.match_type,
            threshold=request.threshold,
            total_results=len(enhanced_results),
            results=enhanced_results,
            search_time_ms=processing_time * 1000,  # Convert to milliseconds
            spellcheck_suggestions=spellcheck_suggestions,
        )

    def _get_cached_tags(self) -> List[CodeTag]:
        """
        Get all tags with full information from the tree-sitter cache.

        Returns:
            List of tag dictionaries with name, type, file, and line information
        """
        if (
            not self.tree_sitter_parser or not self.tag_cache
        ):  # Check injected tag_cache
            self.logger.debug("No tree-sitter cache available")
            return []

        self.logger.info(
            f"_get_cached_tags called - tree_sitter_parser: {self.tree_sitter_parser is not None}, has cache: {self.tag_cache is not None if self.tag_cache else False}"
        )

        try:
            # Try to get cache stats, but don't fail if cache is disabled
            try:
                cache_stats = (
                    self.tag_cache.get_cache_stats() if self.tag_cache else "N/A"
                )
            except Exception:
                cache_stats = "disabled"

            self.logger.info(
                f"Tree-sitter cache type: {type(self.tag_cache)}, size: {cache_stats}"
            )

            # Get tree-sitter supported files and retrieve their cached tags
            project_files = self.file_discovery_service.get_tree_sitter_supported_files(
                self.tree_sitter_parser, exclude_tests=True
            )

            all_tags = []
            files_with_tags = 0
            for file_path in project_files:
                try:
                    # Use tree_sitter_parser.get_tags() which handles cache fallback automatically
                    tags = self.tree_sitter_parser.get_tags(file_path, use_cache=True)
                    if tags:
                        all_tags.extend(tags)
                        files_with_tags += 1
                        self.logger.debug(f"Retrieved {len(tags)} tags for {file_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to retrieve tags for {file_path}: {e}")

            self.logger.info(
                f"Retrieved tags from {files_with_tags} files out of {len(project_files)} total files"
            )

            self.logger.info(f"Retrieved {len(all_tags)} total tags from cache")
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
                str(self.config.project_root),
                self.config.verbose,  # Pass Path object directly
            )
            identifiers = [
                tag.name for tag in self._extract_identifiers_from_files(project_files)
            ]

        return sorted(list(set(identifiers)))

    def get_ranked_tags_map(self, files: List[str], max_tokens: int) -> Optional[str]:
        """Get a map of tags with their relevance scores."""
        try:
            # Use the provided files parameter
            identifier_list = self._extract_identifiers_from_files(files)

            if not identifier_list:
                return None

            identifiers = {
                tag for tag in identifier_list
            }  # Keep CodeTag objects for richer context in ranking

            # Simple ranking based on identifier characteristics
            ranked_map = {}
            for identifier in identifiers:
                score = 1.0

                # Boost score for common patterns
                if identifier.name.startswith("get_") or identifier.name.startswith(
                    "set_"
                ):
                    score = 1.5
                elif identifier.name[0].isupper():  # Class names
                    score = 1.3
                elif (
                    "_" in identifier.name and identifier.name.islower()
                ):  # function_names
                    score = 1.2

                ranked_map[identifier] = score

            # Convert to string representation
            result_lines = []
            for identifier, score in sorted(
                ranked_map.items(), key=lambda x: x[1], reverse=True
            ):
                result_lines.append(
                    f"{identifier.name}: {score}"
                )  # Access identifier.name here

            # Limit output based on max_tokens (rough estimation)
            result = "\n".join(result_lines)
            if len(result) > max_tokens:
                # Truncate to fit within token limit
                lines = result.split("\n")
                truncated_lines = []
                current_length = 0
                for line in lines:
                    if current_length + len(line) + 1 <= max_tokens:
                        truncated_lines.append(line)
                        current_length += len(line) + 1
                    else:
                        break
                result = "\n".join(truncated_lines)

            return result

        except Exception as e:
            self.logger.error(f"Error in get_ranked_tags_map: {e}")
            return None

    def _get_project_files(self) -> List[str]:
        """Get list of project files, respecting .gitignore patterns."""
        return get_project_files(
            str(self.config.project_root), self.config.verbose
        )  # Pass Path object directly

    def _extract_identifiers_from_files(
        self, project_files: List[str]
    ) -> List[CodeTag]:
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

    def _extract_identifiers_parallel(self, project_files: List[str]) -> List[CodeTag]:
        """
        Extract identifiers from files using parallel processing.

        For development tools: fails fast with helpful error messages.

        Args:
            project_files: List of file paths to process

        Returns:
            List of CodeTag objects extracted from the files

        Raises:
            Exception: If parallel processing fails, with helpful debugging info
        """
        try:
            identifiers: List[CodeTag]
            stats: Any
            # Fallback to sequential processing since parallel_extractor is removed
            identifiers = self._extract_identifiers_sequential(project_files)
            stats = type(
                "obj",
                (object,),
                {
                    "successful_files": len(project_files),
                    "total_files": len(project_files),
                    "total_identifiers": len(identifiers),
                    "processing_time": 0.0,
                },
            )()

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

    def _extract_identifiers_sequential(self, file_paths: List[str]) -> List[CodeTag]:
        """Extract identifiers from files sequentially."""
        all_identifiers: List[CodeTag] = []
        ts_parser = self.tree_sitter_parser  # Resolve the instance from the provider
        if ts_parser is None:
            self.logger.error("Tree-sitter parser is not available.")  # type: ignore[unreachable]
            return []

        for file_path in file_paths:
            try:
                tags = ts_parser.get_tags(file_path)
                all_identifiers.extend(tags)
            except Exception as e:
                self.logger.warning(
                    f"_extract_identifiers_sequential: Error processing {file_path}: {e}"
                )
                self.logger.debug(
                    f"_extract_identifiers_sequential: Traceback: {traceback.format_exc()}"
                )
                continue
        return all_identifiers

    def _get_cached_import_analysis(self) -> Optional[Any]:
        """
        Get cached import analysis results from persistent cache.

        Returns:
            Cached ProjectImports object or None if not available
        """
        if (
            not self.tree_sitter_parser or not self.tag_cache
        ):  # Check injected tag_cache
            self.logger.debug("No tree-sitter cache available for import analysis")
            return None

        try:
            cache = self.import_analysis_cache  # Use separate import analysis cache
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
        if (
            not self.tree_sitter_parser or not self.tag_cache
        ):  # Check injected tag_cache
            self.logger.debug(
                "No tree-sitter cache available for caching import analysis"
            )
            return

        try:
            cache = self.import_analysis_cache  # Use separate import analysis cache
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
            self.logger.debug(f"Project imports count: {len(project_imports.files)}")
            if len(project_imports.files) > self.config.dependencies.max_graph_size:
                self.logger.warning(
                    f"Project has {len(project_imports.files)} files, limiting to "
                    f"{self.config.dependencies.max_graph_size} for dependency analysis"
                )
                # Create a limited version of project_imports
                limited_files = list(project_imports.files.keys())[
                    : self.config.dependencies.max_graph_size
                ]
                limited_file_imports = {
                    k: v for k, v in project_imports.files.items() if k in limited_files
                }
                project_imports.files = limited_file_imports

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
                f"Built dependency graph: {len(project_imports.files)} files in {construction_time:.2f}s"
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
            assert self.centrality_calculator is not None  # For mypy  # nosec B101
            return self.centrality_calculator.calculate_composite_importance()
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
            assert self.impact_analyzer is not None  # For mypy  # nosec B101
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
            assert self.dependency_graph is not None  # For mypy  # nosec B101
            return self.dependency_graph.find_cycles()
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
