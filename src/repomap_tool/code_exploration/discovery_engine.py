"""
Entrypoint discovery engine for tree exploration.

This module discovers relevant code entry points using existing semantic and fuzzy matching
capabilities, providing the foundation for building exploration trees.
"""

import os
import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import List, Dict, Any, Optional
from pathlib import Path

from repomap_tool.models import Entrypoint, RepoMapConfig
from repomap_tool.core import RepoMapService
from repomap_tool.code_search.semantic_matcher import DomainSemanticMatcher
from repomap_tool.code_search.fuzzy_matcher import FuzzyMatcher

# Phase 2: Dependency analysis integration
from repomap_tool.code_analysis import (
    ImportAnalyzer,
    DependencyGraph,
)

logger = get_logger(__name__)


class EntrypointDiscoverer:
    """Discovers relevant entrypoints using existing semantic/fuzzy matching."""

    def __init__(
        self,
        repo_map: Optional[RepoMapService] = None,
        import_analyzer: Optional[Any] = None,
        dependency_graph: Optional[Any] = None,
        centrality_calculator: Optional[Any] = None,
        impact_analyzer: Optional[Any] = None,
    ):
        """Initialize entrypoint discoverer with injected dependencies.

        Args:
            repo_map: RepoMapService instance with semantic/fuzzy matchers
            import_analyzer: Import analyzer instance (injected)
            dependency_graph: Dependency graph instance (injected)
            centrality_calculator: Centrality calculator instance (injected)
            impact_analyzer: Impact analyzer instance (injected)
        """
        self.repo_map = repo_map
        # Get semantic matcher from repo_map
        semantic_matcher = getattr(repo_map, "semantic_matcher", None)
        if semantic_matcher is None:
            semantic_matcher = getattr(repo_map, "domain_semantic_matcher", None)
        self.semantic_matcher = semantic_matcher
        self.fuzzy_matcher = getattr(repo_map, "fuzzy_matcher", None)

        # Use semantic matcher threshold from config if available
        if repo_map and repo_map.config and repo_map.config.trees:
            self.semantic_threshold = repo_map.config.trees.entrypoint_threshold
        else:
            self.semantic_threshold = 0.6

        # Fuzzy matching threshold (70% similarity)
        self.fuzzy_threshold = get_config("FUZZY_THRESHOLD", 0.7)

        # All dependencies must be injected - no fallback allowed
        if import_analyzer is None:
            raise ValueError("ImportAnalyzer must be injected - no fallback allowed")
        if dependency_graph is None:
            raise ValueError("DependencyGraph must be injected - no fallback allowed")
        if centrality_calculator is None:
            raise ValueError(
                "CentralityCalculator must be injected - no fallback allowed"
            )

        self.import_analyzer = import_analyzer
        self.dependency_graph = dependency_graph
        self.centrality_calculator = centrality_calculator
        self.impact_analyzer = impact_analyzer

        logger.debug(
            f"EntrypointDiscoverer initialized with semantic_threshold={self.semantic_threshold}, fuzzy_threshold={self.fuzzy_threshold}"
        )

    def discover_entrypoints(self, project_path: str, intent: str) -> List[Entrypoint]:
        """Find relevant entrypoints using existing semantic/fuzzy matching.

        Args:
            project_path: Path to the project to analyze
            intent: User intent description (e.g., "authentication bugs")

        Returns:
            List of relevant entrypoints with scores
        """
        logger.info(f"Discovering entrypoints for intent: '{intent}' in {project_path}")

        # Initialize dependency components with project_path
        self._initialize_dependency_components(project_path)

        # Get all project symbols using existing infrastructure
        all_symbols = self._get_project_symbols(project_path)
        if not all_symbols:
            logger.warning(f"No symbols found in project {project_path}")
            return []

        relevant_entrypoints = []

        # Use existing semantic matching to find relevant symbols
        if self.semantic_matcher and self.semantic_matcher.enabled:
            semantic_entrypoints = self._discover_semantic_entrypoints(
                intent, all_symbols, project_path
            )
            relevant_entrypoints.extend(semantic_entrypoints)
            logger.debug(
                f"Found {len(semantic_entrypoints)} entrypoints via semantic matching"
            )

        # Use existing fuzzy matching for additional matches
        if self.fuzzy_matcher:
            fuzzy_entrypoints = self._discover_fuzzy_entrypoints(
                intent, all_symbols, project_path
            )
            relevant_entrypoints.extend(fuzzy_entrypoints)
            logger.debug(
                f"Found {len(fuzzy_entrypoints)} entrypoints via fuzzy matching"
            )

        # Remove duplicates and sort by score
        unique_entrypoints = self._deduplicate_entrypoints(relevant_entrypoints)
        unique_entrypoints.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"Discovered {len(unique_entrypoints)} unique entrypoints")

        # Phase 2: Enhance entrypoints with dependency analysis
        if self.dependency_graph:
            try:
                self._build_dependency_graph(project_path)
                unique_entrypoints = self._enhance_with_dependency_scores(
                    unique_entrypoints
                )
            except Exception as e:
                logger.error(f"Error enhancing entrypoints with dependency scores: {e}")

        return unique_entrypoints

    def _build_dependency_graph(self, project_path: str) -> None:
        """Build the project's dependency graph."""
        if (
            not self.dependency_graph
            or self.dependency_graph.graph.number_of_nodes() > 0
        ):
            return

        logger.debug("Building dependency graph for entrypoint enhancement...")
        try:
            project_imports = self.import_analyzer.analyze_project_imports(project_path)
            self.dependency_graph.build_graph(project_imports)
        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")

    def _enhance_with_dependency_scores(
        self, entrypoints: List[Entrypoint]
    ) -> List[Entrypoint]:
        """Enhance entrypoint scores with dependency centrality."""
        if (
            not self.dependency_graph
            or self.dependency_graph.graph.number_of_nodes() == 0
        ):
            return entrypoints

        logger.info("Enhancing entrypoints with dependency scores...")
        try:
            # Use injected centrality calculator instance
            calculator = self.centrality_calculator
            centrality_scores = calculator.calculate_composite_importance()

            for entrypoint in entrypoints:
                file_path = str(entrypoint.location)
                if file_path in centrality_scores:
                    centrality_boost = centrality_scores[file_path] * 0.2
                    entrypoint.score = min(1.0, entrypoint.score + centrality_boost)

            entrypoints.sort(key=lambda x: x.score, reverse=True)
        except Exception as e:
            logger.error(f"Error during dependency score enhancement: {e}")

        return entrypoints

    def _initialize_dependency_components(self, project_path: str) -> None:
        """Initialize dependency analysis components."""
        # Components are now initialized in __init__, but we can set project_root if needed
        if hasattr(self.import_analyzer, "project_root"):
            self.import_analyzer.project_root = project_path

    def _get_project_symbols(self, project_path: str) -> List[Dict[str, Any]]:
        """Get all project symbols using existing infrastructure.

        Args:
            project_path: Project path to analyze

        Returns:
            List of symbol dictionaries
        """
        try:
            # Use existing repo_map to get symbols
            if self.repo_map and hasattr(self.repo_map, "get_tags"):
                symbol_strings = self.repo_map.get_tags()
                # Convert strings to dictionaries
                symbols = [{"identifier": s, "type": "unknown"} for s in symbol_strings]
                logger.debug(f"Retrieved {len(symbols)} symbols from repo_map")
                return symbols

            # Fallback: try to get symbols from search engine
            elif (
                self.repo_map
                and hasattr(self.repo_map, "search_engine")
                and self.repo_map.search_engine
            ):
                # This would need to be implemented based on existing search engine
                logger.debug("Using search engine fallback for symbol discovery")
                return []

            else:
                logger.warning("No symbol discovery method available in repo_map")
                return []

        except Exception as e:
            logger.error(f"Failed to get project symbols: {e}")
            return []

    def _discover_semantic_entrypoints(
        self, intent: str, symbols: List[Dict[str, Any]], project_path: str
    ) -> List[Entrypoint]:
        """Discover entrypoints using semantic matching.

        Args:
            intent: User intent description
            symbols: List of project symbols
            project_path: Project path

        Returns:
            List of semantically relevant entrypoints
        """
        entrypoints = []

        try:
            # Get semantic matches from the repo_map instance
            if not self.repo_map:
                return []
            semantic_matches = self.repo_map.semantic_search(intent)

            for match in semantic_matches:
                if match["score"] > self.semantic_threshold:
                    entrypoints.append(
                        self._create_entrypoint_from_symbol(
                            symbol_info=match["symbol"],
                            score=match["score"],
                            file_path=match["symbol"]["file_path"],
                        )
                    )
        except Exception as e:
            logger.error(f"Error in semantic entrypoint discovery: {e}")

        return entrypoints

    def _discover_fuzzy_entrypoints(
        self, intent: str, symbols: List[Dict[str, Any]], project_path: str
    ) -> List[Entrypoint]:
        """Discover entrypoints using fuzzy matching.

        Args:
            intent: User intent description
            symbols: List of project symbols (strings)
            project_path: Project path

        Returns:
            List of fuzzy-matched entrypoints
        """
        entrypoints = []

        try:
            if not self.repo_map:
                return []
            fuzzy_matches = self.repo_map.fuzzy_search(intent)

            for match in fuzzy_matches:
                if match.score > self.fuzzy_threshold:
                    entrypoints.append(
                        self._create_entrypoint_from_symbol(
                            symbol_info=match.symbol,
                            score=match.score,
                            file_path=match.symbol["file_path"],
                        )
                    )
        except Exception as e:
            logger.error(f"Error in fuzzy entrypoint discovery: {e}")

        return entrypoints

    def _create_entrypoint_from_symbol(
        self, symbol_info: Dict[str, Any], score: float, file_path: Path
    ) -> Entrypoint:
        """Create an Entrypoint from a symbol dictionary."""
        return Entrypoint(
            identifier=symbol_info.get("identifier", "Unknown"),
            file_path=file_path,
            score=score,
            structural_context={
                "line_number": symbol_info.get("line_number", 0),
                "type": symbol_info.get("type", "Unknown"),
            },
        )

    def _deduplicate_entrypoints(
        self, entrypoints: List[Entrypoint]
    ) -> List[Entrypoint]:
        """Remove duplicate entrypoints based on identifier and location.

        Args:
            entrypoints: List of entrypoints to deduplicate

        Returns:
            List of unique entrypoints
        """
        seen = set()
        unique = []

        for entrypoint in entrypoints:
            # Create unique key from identifier and location
            key = (entrypoint.identifier, entrypoint.location)

            if key not in seen:
                seen.add(key)
                unique.append(entrypoint)
            else:
                # Keep the one with higher score
                existing = next(
                    ep for ep in unique if (ep.identifier, ep.location) == key
                )
                if entrypoint.score > existing.score:
                    unique.remove(existing)
                    unique.append(entrypoint)

        return unique

    def _enhance_entrypoints_with_dependencies(
        self, entrypoints: List[Entrypoint], project_path: str
    ) -> None:
        """Enhance entrypoints with dependency analysis information.

        Args:
            entrypoints: List of entrypoints to enhance
            project_path: Project path for dependency analysis
        """
        try:
            logger.info("Enhancing entrypoints with dependency analysis")

            # Build dependency graph for the project
            self._build_project_dependency_graph(project_path)

            # Use injected dependencies - no fallback allowed
            if self.centrality_calculator is None:
                raise ValueError(
                    "CentralityCalculator must be injected - no fallback allowed"
                )
            if self.impact_analyzer is None:
                raise ValueError(
                    "ImpactAnalyzer must be injected - no fallback allowed"
                )

            # Enhance each entrypoint with dependency metrics
            for entrypoint in entrypoints:
                self._enhance_single_entrypoint(entrypoint, project_path)

            logger.info(
                f"Enhanced {len(entrypoints)} entrypoints with dependency information"
            )

        except Exception as e:
            logger.error(f"Error enhancing entrypoints with dependencies: {e}")

    def _build_project_dependency_graph(self, project_path: str) -> None:
        """Build dependency graph for the entire project.

        Args:
            project_path: Project path to analyze
        """
        try:
            logger.debug(f"Building dependency graph for project: {project_path}")

            # Get project files first
            from repomap_tool.core.file_scanner import get_project_files

            project_files = get_project_files(project_path, verbose=False)

            # Analyze project imports
            project_imports = self.import_analyzer.analyze_project_imports(project_path)

            # Build dependency graph
            self.dependency_graph.build_graph(project_imports)

            logger.debug(
                f"Built dependency graph with {len(self.dependency_graph.nodes)} nodes and {len(self.dependency_graph.graph.edges)} edges"
            )

        except Exception as e:
            logger.error(f"Error building dependency graph: {e}")

    def _enhance_single_entrypoint(
        self, entrypoint: Entrypoint, project_path: str
    ) -> None:
        """Enhance a single entrypoint with dependency metrics.

        Args:
            entrypoint: Entrypoint to enhance
            project_path: Project path for context
        """
        try:
            # Extract file path from location
            file_path = self._extract_file_path_from_location(
                str(entrypoint.location), project_path
            )
            if not file_path:
                return

            # Get dependency centrality score
            if self.centrality_calculator is not None:
                centrality_scores = (
                    self.centrality_calculator.calculate_composite_importance()
                )
            else:
                centrality_scores = {}
            if file_path in centrality_scores:
                entrypoint.dependency_centrality = centrality_scores[file_path]

            # Get import and dependency counts
            dependents = self.dependency_graph.get_dependents(file_path)
            dependencies = self.dependency_graph.get_dependencies(file_path)

            entrypoint.import_count = len(dependents)
            entrypoint.dependency_count = len(dependencies)

            # Calculate impact risk
            if self.impact_analyzer is not None:
                impact_report = self.impact_analyzer.analyze_change_impact(file_path)
            else:
                impact_report = None
            if impact_report:
                entrypoint.impact_risk = impact_report.overall_risk_score

                # Calculate refactoring priority based on impact risk and centrality
                if entrypoint.dependency_centrality is not None:
                    entrypoint.refactoring_priority = (
                        entrypoint.impact_risk * 0.4
                        + entrypoint.dependency_centrality * 0.6
                    )

        except Exception as e:
            logger.debug(f"Error enhancing entrypoint {entrypoint.identifier}: {e}")

    def _extract_file_path_from_location(
        self, location: str, project_path: str
    ) -> Optional[str]:
        """Extract file path from entrypoint location.

        Args:
            location: Entrypoint location (e.g., "src/file.py:123")
            project_path: Project root path

        Returns:
            Absolute file path or None if extraction fails
        """
        try:
            # Handle location format: "file.py:123" or "src/file.py:123"
            if ":" in location:
                file_part = location.split(":")[0]
            else:
                file_part = location

            # Construct absolute path
            absolute_path = os.path.join(project_path, file_part)

            # Normalize path
            normalized_path = os.path.normpath(absolute_path)

            # Verify file exists
            if os.path.isfile(normalized_path):
                return normalized_path

            return None

        except Exception as e:
            logger.debug(f"Error extracting file path from location '{location}': {e}")
            return None
