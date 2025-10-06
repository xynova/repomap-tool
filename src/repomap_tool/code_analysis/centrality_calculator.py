"""
Centrality calculator for dependency analysis.

This module calculates various centrality measures for files in the dependency graph
to determine their importance and influence within the codebase.
"""

import logging
import networkx as nx
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict

from .dependency_graph import DependencyGraph
from ..core.config_service import get_config
from ..core.logging_service import get_logger

logger = get_logger(__name__)


class CentralityCalculator:
    """Calculates centrality measures for files in the dependency graph."""

    def __init__(self, dependency_graph: DependencyGraph):
        """Initialize the centrality calculator.

        Args:
            dependency_graph: DependencyGraph instance to analyze
        """
        self.graph = dependency_graph
        self.cache: Dict[str, Any] = {}
        self.cache_enabled = True

        logger.info("CentralityCalculator initialized")

    def calculate_degree_centrality(self) -> Dict[str, float]:
        """Calculate degree centrality for all files.

        Degree centrality measures how many connections (imports + imported_by) a file has.
        Higher values indicate files that are more connected to the rest of the codebase.

        Returns:
            Dictionary mapping file paths to degree centrality scores (0-1)
        """
        cache_key = "degree_centrality"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached degree centrality scores")
            return self.cache[cache_key]  # type: ignore

        try:
            # Use NetworkX's degree centrality
            degree_scores: Dict[str, float] = nx.degree_centrality(self.graph.graph)

            # Validate scores
            self._validate_centrality_scores(degree_scores)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = degree_scores

            logger.info(f"Calculated degree centrality for {len(degree_scores)} files")
            return degree_scores

        except Exception as e:
            logger.error(f"Error calculating degree centrality: {e}")
            return {}

    def calculate_betweenness_centrality(self) -> Dict[str, float]:
        """Calculate betweenness centrality for all files.

        Betweenness centrality measures how often a file lies on shortest paths
        between other files. Higher values indicate files that act as bridges.

        Returns:
            Dictionary mapping file paths to betweenness centrality scores (0-1)
        """
        cache_key = "betweenness_centrality"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached betweenness centrality scores")
            return self.cache[cache_key]  # type: ignore

        try:
            # Check if graph is empty
            if self.graph.graph.number_of_nodes() == 0:
                logger.warning("Empty centrality scores dictionary")
                logger.error(
                    "Error calculating betweenness centrality: cannot compute centrality for the null graph"
                )
                return {}

            # Use NetworkX's betweenness centrality
            betweenness_scores: Dict[str, float] = nx.betweenness_centrality(
                self.graph.graph
            )

            # Validate scores
            self._validate_centrality_scores(betweenness_scores)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = betweenness_scores

            logger.info(
                f"Calculated betweenness centrality for {len(betweenness_scores)} files"
            )
            return betweenness_scores

        except Exception as e:
            logger.error(f"Error calculating betweenness centrality: {e}")
            return {}

    def calculate_pagerank_centrality(
        self, alpha: Optional[float] = None, max_iter: Optional[int] = None
    ) -> Dict[str, float]:
        """Calculate PageRank centrality for all files.

        PageRank centrality measures the importance of files based on the importance
        of files that import them. Higher values indicate more important files.

        Args:
            alpha: Damping parameter (default: from config)
            max_iter: Maximum iterations for convergence (default: from config)

        Returns:
            Dictionary mapping file paths to PageRank scores (0-1)
        """
        # Use config defaults if not provided
        if alpha is None:
            alpha = get_config("PAGERANK_ALPHA", 0.85))
        if max_iter is None:
            max_iter = get_config("PAGERANK_MAX_ITER", 100))
            
        cache_key = f"pagerank_centrality_{alpha}_{max_iter}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached PageRank centrality scores")
            return self.cache[cache_key]  # type: ignore

        try:
            # Check if graph is empty
            if self.graph.graph.number_of_nodes() == 0:
                logger.warning("Empty centrality scores dictionary")
                logger.error(
                    "Error calculating PageRank centrality: cannot compute centrality for the null graph"
                )
                return {}

            # Use NetworkX's PageRank
            pagerank_scores: Dict[str, float] = nx.pagerank(
                self.graph.graph, alpha=alpha, max_iter=max_iter
            )

            # Validate scores
            self._validate_centrality_scores(pagerank_scores)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = pagerank_scores

            logger.info(
                f"Calculated PageRank centrality for {len(pagerank_scores)} files"
            )
            return pagerank_scores

        except Exception as e:
            logger.error(f"Error calculating PageRank centrality: {e}")
            return {}

    def calculate_hub_authority_scores(
        self,
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Calculate HITS algorithm scores (Hub and Authority).

        HITS algorithm identifies:
        - Hubs: Files that import many other important files
        - Authorities: Files that are imported by many important files

        Returns:
            Tuple of (hub_scores, authority_scores) dictionaries
        """
        cache_key = "hits_scores"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached HITS scores")
            cached: Dict[str, Dict[str, float]] = self.cache[cache_key]
            return cached["hub"], cached["authority"]

        try:
            # Use NetworkX's HITS algorithm
            hub_scores: Dict[str, float]
            authority_scores: Dict[str, float]
            hub_scores, authority_scores = nx.hits(self.graph.graph)

            # Validate scores
            self._validate_centrality_scores(hub_scores)
            self._validate_centrality_scores(authority_scores)

            # Cache results
            if self.cache_enabled:
                cache_data: Dict[str, Dict[str, float]] = {
                    "hub": hub_scores,
                    "authority": authority_scores,
                }
                self.cache[cache_key] = cache_data

            logger.info(f"Calculated HITS scores for {len(hub_scores)} files")
            return hub_scores, authority_scores

        except Exception as e:
            logger.error(f"Error calculating HITS scores: {e}")
            return {}, {}

    def calculate_eigenvector_centrality(self) -> Dict[str, float]:
        """Calculate eigenvector centrality for all files.

        Eigenvector centrality measures the importance of a file based on the
        importance of its neighbors (files it imports or is imported by).

        Returns:
            Dictionary mapping file paths to eigenvector centrality scores (0-1)
        """
        cache_key = "eigenvector_centrality"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached eigenvector centrality scores")
            return self.cache[cache_key]  # type: ignore

        try:
            # Check if graph is empty
            if self.graph.graph.number_of_nodes() == 0:
                logger.warning("Empty centrality scores dictionary")
                logger.error(
                    "Error calculating eigenvector centrality: cannot compute centrality for the null graph"
                )
                return {}

            # Use NetworkX's eigenvector centrality
            max_iter = get_config("EIGENVECTOR_MAX_ITER", 1000)
            eigenvector_scores: Dict[str, float] = nx.eigenvector_centrality(
                self.graph.graph, max_iter=max_iter
            )

            # Validate scores
            self._validate_centrality_scores(eigenvector_scores)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = eigenvector_scores

            logger.info(
                f"Calculated eigenvector centrality for {len(eigenvector_scores)} files"
            )
            return eigenvector_scores

        except Exception as e:
            logger.warning("Empty centrality scores dictionary")
            logger.error(f"Error calculating eigenvector centrality: {e}")
            return {}

    def calculate_closeness_centrality(self) -> Dict[str, float]:
        """Calculate closeness centrality for all files.

        Closeness centrality measures how close a file is to all other files
        in the dependency graph. Higher values indicate files that are well-connected.

        Returns:
            Dictionary mapping file paths to closeness centrality scores (0-1)
        """
        cache_key = "closeness_centrality"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug("Using cached closeness centrality scores")
            return self.cache[cache_key]  # type: ignore

        try:
            # Check if graph is empty
            if self.graph.graph.number_of_nodes() == 0:
                logger.warning("Empty centrality scores dictionary")
                logger.error(
                    "Error calculating closeness centrality: cannot compute centrality for the null graph"
                )
                return {}

            # Use NetworkX's closeness centrality
            closeness_scores: Dict[str, float] = nx.closeness_centrality(
                self.graph.graph
            )

            # Validate scores
            self._validate_centrality_scores(closeness_scores)

            # Cache results
            if self.cache_enabled:
                self.cache[cache_key] = closeness_scores

            logger.info(
                f"Calculated closeness centrality for {len(closeness_scores)} files"
            )
            return closeness_scores

        except Exception as e:
            logger.error(f"Error calculating closeness centrality: {e}")
            return {}

    def calculate_composite_importance(
        self, weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate composite importance score using multiple centrality measures.

        Args:
            weights: Optional dictionary specifying weights for each centrality measure.
                    Default weights: degree (0.3), betweenness (0.25), pagerank (0.25),
                    eigenvector (0.1), closeness (0.1)

        Returns:
            Dictionary mapping file paths to composite importance scores (0-1)
        """
        if weights is None:
            weights = {
                "degree": 0.3,
                "betweenness": 0.25,
                "pagerank": 0.25,
                "eigenvector": 0.1,
                "closeness": 0.1,
            }

        # Validate weights sum to 1.0
        total_weight = sum(weights.values())
        if abs(total_weight - 1.0) > 0.001:
            logger.warning(f"Weights sum to {total_weight}, normalizing to 1.0")
            weights = {k: v / total_weight for k, v in weights.items()}

        try:
            # Check if graph is empty
            if self.graph.graph.number_of_nodes() == 0:
                logger.warning("Empty centrality scores dictionary")
                logger.error(
                    "Error calculating composite importance: cannot compute centrality for the null graph"
                )
                return {}

            # Calculate all centrality measures
            centrality_scores = {}

            if "degree" in weights:
                degree_scores = self.calculate_degree_centrality()
                centrality_scores["degree"] = degree_scores

            if "betweenness" in weights:
                betweenness_scores = self.calculate_betweenness_centrality()
                centrality_scores["betweenness"] = betweenness_scores

            if "pagerank" in weights:
                pagerank_scores = self.calculate_pagerank_centrality()
                centrality_scores["pagerank"] = pagerank_scores

            if "eigenvector" in weights:
                eigenvector_scores = self.calculate_eigenvector_centrality()
                centrality_scores["eigenvector"] = eigenvector_scores

            if "closeness" in weights:
                closeness_scores = self.calculate_closeness_centrality()
                centrality_scores["closeness"] = closeness_scores

            # Calculate composite scores
            composite_scores = {}
            all_files: Set[str] = set()
            for scores in centrality_scores.values():
                all_files.update(scores.keys())

            for file_path in all_files:
                composite_score = 0.0
                for measure, scores in centrality_scores.items():
                    if file_path in scores:
                        composite_score += scores[file_path] * weights[measure]

                composite_scores[file_path] = composite_score

            # Validate composite scores
            self._validate_centrality_scores(composite_scores)

            logger.info(
                f"Calculated composite importance for {len(composite_scores)} files"
            )
            return composite_scores

        except Exception as e:
            logger.error(f"Error calculating composite importance: {e}")
            return {}

    def get_top_central_files(
        self, centrality_type: str = "composite", top_n: int = 10
    ) -> List[Tuple[str, float]]:
        """Get the top N most central files by a specific centrality measure.

        Args:
            centrality_type: Type of centrality to use ('degree', 'betweenness', 'pagerank', etc.)
            top_n: Number of top files to return

        Returns:
            List of (file_path, score) tuples, sorted by score descending
        """
        try:
            if centrality_type == "composite":
                scores = self.calculate_composite_importance()
            elif centrality_type == "degree":
                scores = self.calculate_degree_centrality()
            elif centrality_type == "betweenness":
                scores = self.calculate_betweenness_centrality()
            elif centrality_type == "pagerank":
                scores = self.calculate_pagerank_centrality()
            elif centrality_type == "eigenvector":
                scores = self.calculate_eigenvector_centrality()
            elif centrality_type == "closeness":
                scores = self.calculate_closeness_centrality()
            else:
                logger.error(f"Unknown centrality type: {centrality_type}")
                return []

            # Sort by score and return top N
            sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            return sorted_files[:top_n]

        except Exception as e:
            logger.error(f"Error getting top central files: {e}")
            return []

    def get_centrality_ranking(
        self, centrality_type: str = "composite"
    ) -> List[Tuple[str, float, int]]:
        """Get a complete ranking of files by centrality with rank positions.

        Args:
            centrality_type: Type of centrality to use

        Returns:
            List of (file_path, score, rank) tuples, sorted by score descending
        """
        try:
            if centrality_type == "composite":
                scores = self.calculate_composite_importance()
            elif centrality_type == "degree":
                scores = self.calculate_degree_centrality()
            elif centrality_type == "betweenness":
                scores = self.calculate_betweenness_centrality()
            elif centrality_type == "pagerank":
                scores = self.calculate_pagerank_centrality()
            elif centrality_type == "eigenvector":
                scores = self.calculate_eigenvector_centrality()
            elif centrality_type == "closeness":
                scores = self.calculate_closeness_centrality()
            else:
                logger.error(f"Unknown centrality type: {centrality_type}")
                return []

            # Sort by score and add rank
            sorted_files = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            ranking = [
                (file_path, score, rank + 1)
                for rank, (file_path, score) in enumerate(sorted_files)
            ]

            return ranking

        except Exception as e:
            logger.error(f"Error getting centrality ranking: {e}")
            return []

    def get_centrality_percentile(
        self, file_path: str, centrality_type: str = "composite"
    ) -> float:
        """Get the percentile rank of a file's centrality score.

        Args:
            file_path: Path to the file
            centrality_type: Type of centrality to use

        Returns:
            Percentile rank (0-100), where 100 is the most central
        """
        try:
            if centrality_type == "composite":
                scores = self.calculate_composite_importance()
            elif centrality_type == "degree":
                scores = self.calculate_degree_centrality()
            elif centrality_type == "betweenness":
                scores = self.calculate_betweenness_centrality()
            elif centrality_type == "pagerank":
                scores = self.calculate_pagerank_centrality()
            elif centrality_type == "eigenvector":
                scores = self.calculate_eigenvector_centrality()
            elif centrality_type == "closeness":
                scores = self.calculate_closeness_centrality()
            else:
                logger.error(f"Unknown centrality type: {centrality_type}")
                return 0.0

            if file_path not in scores:
                return 0.0

            file_score = scores[file_path]
            all_scores = list(scores.values())
            all_scores.sort()

            # Calculate percentile
            rank = 0
            for score in all_scores:
                if score <= file_score:
                    rank += 1

            percentile = (rank / len(all_scores)) * 100
            return percentile

        except Exception as e:
            logger.error(f"Error calculating centrality percentile: {e}")
            return 0.0

    def _validate_centrality_scores(self, scores: Dict[str, float]) -> None:
        """Validate that centrality scores are reasonable.

        Args:
            scores: Dictionary of centrality scores to validate
        """
        if not scores:
            logger.warning("Empty centrality scores dictionary")
            return

        # Check for reasonable score ranges
        min_score = min(scores.values())
        max_score = max(scores.values())

        if min_score < 0 or max_score > 1:
            logger.warning(
                f"Centrality scores outside expected range [0,1]: min={min_score}, max={max_score}"
            )

        # Check for all-zero or all-one scores (likely calculation error)
        unique_scores = set(scores.values())
        if len(unique_scores) == 1:
            logger.warning(
                f"All centrality scores are identical: {list(unique_scores)[0]}"
            )

        # Check for NaN or infinite values
        for file_path, score in scores.items():
            if not isinstance(score, (int, float)) or score != score:  # NaN check
                logger.error(f"Invalid centrality score for {file_path}: {score}")

    def clear_cache(self) -> None:
        """Clear the centrality calculation cache."""
        self.cache.clear()
        logger.info("Centrality calculation cache cleared")

    def disable_cache(self) -> None:
        """Disable caching for centrality calculations."""
        self.cache_enabled = False
        logger.info("Centrality calculation caching disabled")

    def enable_cache(self) -> None:
        """Enable caching for centrality calculations."""
        self.cache_enabled = True
        logger.info("Centrality calculation caching enabled")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about the centrality calculation cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.cache),
            "cached_measures": list(self.cache.keys()),
            "total_cached_scores": sum(len(scores) for scores in self.cache.values()),
        }
