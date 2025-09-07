"""
Main RepoMapService class.

This module contains the core RepoMapService class that orchestrates
code analysis and search functionality.
"""

import logging
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
)
from .file_scanner import get_project_files
from .analyzer import analyze_file_types, analyze_identifier_types, get_cache_size
from .search_engine import fuzzy_search, semantic_search, hybrid_search, basic_search
from .parallel_processor import ParallelTagExtractor
from rich.console import Console

# Import matchers
try:
    from ..matchers.fuzzy_matcher import FuzzyMatcher
    from ..matchers.adaptive_semantic_matcher import AdaptiveSemanticMatcher
    from ..matchers.hybrid_matcher import HybridMatcher

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

    def __init__(self, config: RepoMapConfig):
        """
        Initialize RepoMapService with validated configuration.

        Args:
            config: Validated RepoMapConfig instance
        """
        self.config = config
        self.logger = self._setup_logging()
        self.console = Console()

        # Initialize components
        self.repo_map: Optional[RepoMapProtocol] = None
        self.fuzzy_matcher: Optional[FuzzyMatcherProtocol] = None
        self.semantic_matcher: Optional[SemanticMatcherProtocol] = None
        self.hybrid_matcher: Optional[HybridMatcherProtocol] = None

        # Phase 2: Initialize dependency analysis components
        self.dependency_graph: Optional[Any] = None
        self.impact_analyzer: Optional[Any] = None
        self.centrality_calculator: Optional[Any] = None
        self.analysis_results: Optional[Any] = None

        # Initialize parallel processing
        self.parallel_extractor = ParallelTagExtractor(
            max_workers=self.config.performance.max_workers,
            enable_progress=self.config.performance.enable_progress,
            console=self.console,
        )

        # Initialize the system
        self._initialize_components()

        self.logger.info(f"Initialized RepoMapService for {self.config.project_root}")

        # Invalidate stale caches on initialization
        self._invalidate_stale_caches()

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

        # Initialize matchers if available
        if MATCHERS_AVAILABLE:
            self._initialize_matchers()
        else:
            self.logger.warning("Matchers not available - matching features disabled")
            # Type ignore for matcher assignments since they're not available

    def _initialize_matchers(self) -> None:
        """Initialize matching components."""
        # Initialize fuzzy matcher
        if self.config.fuzzy_match.enabled:
            self.fuzzy_matcher = FuzzyMatcher(  # type: ignore
                threshold=self.config.fuzzy_match.threshold,
                strategies=self.config.fuzzy_match.strategies,
                cache_results=self.config.fuzzy_match.cache_results,
                verbose=self.config.verbose,
            )
            self.logger.info(f"Initialized FuzzyMatcher: {self.config.fuzzy_match}")

        # Initialize semantic matcher
        if self.config.semantic_match.enabled:
            self.semantic_matcher = AdaptiveSemanticMatcher(verbose=self.config.verbose)  # type: ignore
            self.logger.info(
                f"Initialized SemanticMatcher: {self.config.semantic_match}"
            )

        # Initialize hybrid matcher if both are enabled
        if self.config.fuzzy_match.enabled and self.config.semantic_match.enabled:
            self.hybrid_matcher = HybridMatcher(  # type: ignore
                fuzzy_threshold=self.config.fuzzy_match.threshold,
                semantic_threshold=self.config.semantic_match.threshold,
                verbose=self.config.verbose,
            )
            self.logger.info("Initialized HybridMatcher")

        # Phase 2: Initialize dependency analysis components
        if self.config.dependencies.enabled:
            self._initialize_dependency_analysis()
            self.logger.info("Initialized dependency analysis components")

    def _initialize_dependency_analysis(self) -> None:
        """Initialize dependency analysis components."""
        try:
            from ..dependencies import (
                AdvancedDependencyGraph,
                ImpactAnalyzer,
                CentralityCalculator,
            )

            # Initialize advanced dependency graph
            self.dependency_graph = AdvancedDependencyGraph()

            # Initialize impact analyzer
            if self.config.dependencies.enable_impact_analysis:
                self.impact_analyzer = ImpactAnalyzer(self.dependency_graph)

            # Initialize centrality calculator
            self.centrality_calculator = CentralityCalculator(self.dependency_graph)

            self.logger.info("Dependency analysis components initialized successfully")

        except ImportError as e:
            self.logger.warning(f"Failed to import dependency analysis components: {e}")
            self.logger.warning("Dependency analysis features will be disabled")
        except Exception as e:
            self.logger.error(f"Error initializing dependency analysis: {e}")
            self.logger.warning("Dependency analysis features will be disabled")

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

    # Phase 2: Dependency Analysis Methods

    def build_dependency_graph(self) -> Any:
        """Build dependency graph for the project."""
        if not self.config.dependencies.enabled:
            raise RuntimeError("Dependency analysis is not enabled")

        if self.dependency_graph is None:
            raise RuntimeError("Dependency analysis components not initialized")

        start_time = time.time()

        try:
            # Import the ImportAnalyzer
            from ..dependencies.import_analyzer import ImportAnalyzer

            # Initialize import analyzer with project root
            import_analyzer = ImportAnalyzer(project_root=str(self.config.project_root))

            # Analyze project imports
            project_imports = import_analyzer.analyze_project_imports(
                str(self.config.project_root)
            )

            # Limit files if configured
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

            self.logger.info(
                f"Built dependency graph: {len(project_imports)} files in {construction_time:.2f}s"
            )

            return self.dependency_graph

        except Exception as e:
            self.logger.error(f"Failed to build dependency graph: {e}")
            raise

    def get_centrality_scores(self) -> Dict[str, float]:
        """Get centrality scores for all files in the dependency graph."""
        if not self.config.dependencies.enabled:
            raise RuntimeError("Dependency analysis is not enabled")

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
        if not self.config.dependencies.enabled:
            raise RuntimeError("Dependency analysis is not enabled")

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
        if not self.config.dependencies.enabled:
            raise RuntimeError("Dependency analysis is not enabled")

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

        # This is a simplified search. A real implementation would be more complex.
        all_symbols = self.get_all_symbols()
        results = []
        for symbol in all_symbols:
            # A real implementation would use a more sophisticated similarity metric.
            if query.lower() in symbol["identifier"].lower():
                results.append({"symbol": symbol, "score": 0.8})  # Dummy score
        return results

    def fuzzy_search(self, query: str) -> List[Any]:
        """Perform a fuzzy search for a query."""
        if not self.fuzzy_matcher or not self.fuzzy_matcher.enabled:
            return []

        # This is a simplified search.
        all_symbols = self.get_all_symbols()
        results = []
        for symbol in all_symbols:
            if query.lower() in symbol["identifier"].lower():
                # The real fuzzy_search returns a list of MatchResult objects
                from repomap_tool.models import MatchResult

                results.append(
                    MatchResult(
                        identifier=symbol["identifier"],
                        score=0.8,
                        strategy="substring",
                        match_type="fuzzy",
                        file_path=symbol.get("file_path"),
                    )
                )
        return results

    def get_dependency_enhanced_trees(
        self, session_id: str, intent: str, current_files: Optional[List[str]] = None
    ) -> List[Any]:
        """Generate enhanced exploration trees with dependency intelligence."""
        if not self.config.dependencies.enabled:
            raise RuntimeError("Dependency analysis is not enabled")

        if self.dependency_graph is None or not self.dependency_graph.nodes:
            # Build graph if not already built
            self.build_dependency_graph()

        try:
            # Import here to avoid circular imports
            from ..trees.discovery_engine import EntrypointDiscoverer

            # Use enhanced entrypoint discovery (Phase 1 + Phase 2)
            enhanced_discoverer = EntrypointDiscoverer(self)
            entrypoints = enhanced_discoverer.discover_entrypoints(
                str(self.config.project_root), intent
            )

            # For now, return entrypoints with dependency information
            # TODO: Implement full tree building with dependency intelligence
            return entrypoints

        except Exception as e:
            self.logger.error(f"Failed to generate dependency-enhanced trees: {e}")
            raise
