"""
Centrality analysis engine for file-level centrality assessment.

This module provides comprehensive centrality analysis for files, including
centrality scores, rankings, dependency analysis, and structural impact.
"""

import logging
import os
from typing import List, Dict, Any, Optional

from .ast_file_analyzer import ASTFileAnalyzer, FileAnalysisResult
from .centrality_calculator import CentralityCalculator
from .function_utils import (
    smart_categorize_function_calls,
    find_most_called_function,
    get_top_called_functions,
    find_most_used_class,
)
from .models import FileCentralityAnalysis
from ..utils.path_normalizer import PathNormalizer

logger = logging.getLogger(__name__)


class CentralityAnalysisEngine:
    """Engine for analyzing file centrality and importance."""

    def __init__(
        self,
        ast_analyzer: ASTFileAnalyzer,
        centrality_calculator: CentralityCalculator,
        dependency_graph: Any,
        path_normalizer: PathNormalizer,
    ):
        """Initialize the centrality analysis engine.

        Args:
            ast_analyzer: AST file analyzer instance
            centrality_calculator: Centrality calculator instance
            dependency_graph: Dependency graph for analysis
            path_normalizer: Path normalizer for consistent file paths
        """
        self.ast_analyzer = ast_analyzer
        self.centrality_calculator = centrality_calculator
        self.dependency_graph = dependency_graph
        self.path_normalizer = path_normalizer
        
        logger.info("CentralityAnalysisEngine initialized with all required dependencies")

    def analyze_file_centrality(
        self, file_path: str, ast_result: FileAnalysisResult, all_files: List[str]
    ) -> FileCentralityAnalysis:
        """Analyze centrality for a single file.

        Args:
            file_path: Path to the file to analyze
            ast_result: AST analysis result for the file
            all_files: List of all files in the project

        Returns:
            FileCentralityAnalysis object
        """
        try:
            # Convert absolute path to relative path for dependency graph lookup
            relative_file_path = self._resolve_relative_path(file_path)

            # Calculate centrality score and ranking
            centrality_score, rank, total_files = self._calculate_centrality_metrics(
                relative_file_path
            )

            # Dependency analysis
            dependency_analysis = self._analyze_dependencies(
                relative_file_path, ast_result, all_files
            )

            # Function call analysis
            function_call_analysis = self._analyze_function_calls(ast_result)

            # Centrality breakdown
            centrality_breakdown = self._calculate_centrality_breakdown(
                relative_file_path
            )

            # Structural impact
            structural_impact = self._calculate_structural_impact(
                relative_file_path, ast_result, all_files
            )

            return FileCentralityAnalysis(
                file_path=file_path,
                centrality_score=centrality_score,
                rank=rank,
                total_files=total_files,
                dependency_analysis=dependency_analysis,
                function_call_analysis=function_call_analysis,
                centrality_breakdown=centrality_breakdown,
                structural_impact=structural_impact,
            )
        except Exception as e:
            logger.error(f"Error in analyze_file_centrality for {file_path}: {e}")
            raise

    def _resolve_relative_path(self, file_path: str) -> str:
        """Resolve file path to relative path for dependency graph lookup.

        Args:
            file_path: File path to resolve

        Returns:
            Normalized relative file path
        """
        try:
            # Use injected path normalizer
            normalized_path = self.path_normalizer.normalize_path(file_path)
            logger.debug(f"Normalized path: {file_path} -> {normalized_path}")
            return normalized_path
        except Exception as e:
            logger.error(f"Error resolving relative path for {file_path}: {e}")
            return file_path

    def _calculate_centrality_metrics(
        self, relative_file_path: str
    ) -> tuple[float, int, int]:
        """Calculate centrality score, rank, and total files.

        Args:
            relative_file_path: Relative file path

        Returns:
            Tuple of (centrality_score, rank, total_files)
        """
        centrality_score = 0.0
        rank = 1
        total_files = 0
        all_scores = {}

        if self.centrality_calculator:
            all_scores = self.centrality_calculator.calculate_composite_importance()
            centrality_score = all_scores.get(relative_file_path, 0.0)
            total_files = len(all_scores) if all_scores else 0

            # Calculate rank
            if all_scores:
                sorted_scores = sorted(
                    all_scores.items(), key=lambda x: x[1], reverse=True
                )
                for i, (fpath, score) in enumerate(sorted_scores, 1):
                    if fpath == relative_file_path:
                        rank = i
                        break

        # If centrality calculator failed or returned empty results, use fallback
        if total_files == 0:
            if (
                self.dependency_graph
                and hasattr(self.dependency_graph, "nodes")
                and len(self.dependency_graph.nodes) > 0
            ):
                total_files = len(self.dependency_graph.nodes)
            else:
                total_files = 1

        return centrality_score, rank, total_files

    def _analyze_dependencies(
        self,
        relative_file_path: str,
        ast_result: FileAnalysisResult,
        all_files: List[str],
    ) -> Dict[str, Any]:
        """Analyze dependencies for the file.

        Args:
            relative_file_path: Relative file path
            ast_result: AST analysis result
            all_files: List of all files in the project

        Returns:
            Dependency analysis dictionary
        """
        # Use dependency graph data when available
        if (
            self.dependency_graph
            and hasattr(self.dependency_graph, "nodes")
            and relative_file_path in self.dependency_graph.nodes
        ):
            node = self.dependency_graph.nodes[relative_file_path]
            direct_imports = len(node.imports) if node.imports else 0
            reverse_dependencies = len(node.imported_by) if node.imported_by else 0
            # Get actual lists for detailed analysis
            import_list = list(node.imports) if node.imports else []
            reverse_dep_list = list(node.imported_by) if node.imported_by else []
        else:
            # Fallback to AST results for Python files
            direct_imports = len(ast_result.imports)
            reverse_dep_relationships = self.ast_analyzer.find_reverse_dependencies(
                relative_file_path, all_files
            )
            reverse_dependencies = len(reverse_dep_relationships)
            import_list = (
                [imp.module for imp in ast_result.imports] if ast_result.imports else []
            )
            reverse_dep_list = [rel.source_file for rel in reverse_dep_relationships]

        return {
            "direct_imports": direct_imports,
            "reverse_dependencies": reverse_dependencies,
            "total_connections": direct_imports + reverse_dependencies,
            "import_list": import_list[:15],  # Show more for LLM analysis
            "reverse_dep_list": reverse_dep_list,  # Show ALL inbound deps for LLM
            "import_list_truncated": len(import_list) > 15,
            "reverse_dep_list_truncated": False,  # Don't truncate inbound deps
        }

    def _analyze_function_calls(self, ast_result: FileAnalysisResult) -> Dict[str, Any]:
        """Analyze function calls in the file.

        Args:
            ast_result: AST analysis result

        Returns:
            Function call analysis dictionary
        """
        categorized_calls = smart_categorize_function_calls(
            ast_result.function_calls,
            ast_result.defined_functions,
            ast_result.imports,
            limit=5,
        )

        return {
            "total_calls": len(ast_result.function_calls),
            "internal_calls": categorized_calls["internal_count"],
            "external_calls": categorized_calls["external_count"],
            "defined_functions": len(ast_result.defined_functions),
            "most_called_function": find_most_called_function(
                ast_result.function_calls
            ),
            "top_called_functions": get_top_called_functions(
                ast_result.function_calls, limit=5
            ),
            "internal_functions": categorized_calls["internal"],
            "external_functions": categorized_calls["external"],
            "external_with_sources": categorized_calls["external_with_sources"],
            "most_used_class": find_most_used_class(ast_result.imports),
        }

    def _calculate_centrality_breakdown(
        self, relative_file_path: str
    ) -> Optional[Dict[str, float]]:
        """Calculate detailed centrality breakdown.

        Args:
            relative_file_path: Relative file path

        Returns:
            Centrality breakdown dictionary or None
        """
        if not self.centrality_calculator:
            logger.warning(f"Centrality calculator is None for {relative_file_path}")
            return None

        try:
            centrality_breakdown = {}
            logger.info(f"Calculating centrality breakdown for {relative_file_path}")

            # Get individual centrality measures for this file
            degree_scores = self.centrality_calculator.calculate_degree_centrality()
            betweenness_scores = (
                self.centrality_calculator.calculate_betweenness_centrality()
            )
            pagerank_scores = self.centrality_calculator.calculate_pagerank_centrality()
            
            # Log centrality calculation progress
            logger.debug(f"Calculating centrality breakdown for {relative_file_path}")

            # Only include metrics that were successfully calculated
            if degree_scores and relative_file_path in degree_scores:
                centrality_breakdown["degree_centrality"] = degree_scores[relative_file_path]
            if betweenness_scores and relative_file_path in betweenness_scores:
                centrality_breakdown["betweenness_centrality"] = betweenness_scores[
                    relative_file_path
                ]
            if pagerank_scores and relative_file_path in pagerank_scores:
                centrality_breakdown["pagerank"] = pagerank_scores[relative_file_path]
            
            # If no centrality scores were found for this file, return None
            if not centrality_breakdown:
                logger.debug(f"No centrality scores found for {relative_file_path}")
                return None

            # Try to get additional metrics if they work
            try:
                eigenvector_scores = (
                    self.centrality_calculator.calculate_eigenvector_centrality()
                )
                if eigenvector_scores and relative_file_path in eigenvector_scores:
                    centrality_breakdown["eigenvector"] = eigenvector_scores[
                        relative_file_path
                    ]
            except Exception as e:
                logger.debug(f"Eigenvector centrality calculation failed: {e}")

            try:
                closeness_scores = (
                    self.centrality_calculator.calculate_closeness_centrality()
                )
                if closeness_scores and relative_file_path in closeness_scores:
                    centrality_breakdown["closeness"] = closeness_scores[
                        relative_file_path
                    ]
            except Exception as e:
                logger.debug(f"Closeness centrality calculation failed: {e}")

            return centrality_breakdown

        except Exception as e:
            logger.error(f"Error calculating detailed centrality breakdown: {e}")
            return None

    def _calculate_structural_impact(
        self,
        relative_file_path: str,
        ast_result: FileAnalysisResult,
        all_files: List[str],
    ) -> Dict[str, Any]:
        """Calculate structural impact metrics.

        Args:
            relative_file_path: Relative file path
            ast_result: AST analysis result
            all_files: List of all files in the project

        Returns:
            Structural impact dictionary
        """
        # Use dependency graph data when available
        if (
            self.dependency_graph
            and hasattr(self.dependency_graph, "nodes")
            and relative_file_path in self.dependency_graph.nodes
        ):
            node = self.dependency_graph.nodes[relative_file_path]
            files_affected = len(node.imported_by) if node.imported_by else 0
        else:
            # Fallback to AST results for Python files
            files_affected = len(
                self.ast_analyzer.find_reverse_dependencies(
                    relative_file_path, all_files
                )
            )

        return {
            "if_file_changes": files_affected,
            "if_functions_change": len(ast_result.defined_functions),
            "if_classes_change": len(ast_result.defined_classes),
        }
