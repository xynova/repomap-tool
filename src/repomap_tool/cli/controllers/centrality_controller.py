"""
Centrality Controller for CLI.

This controller orchestrates centrality analysis operations,
coordinating between code_analysis, code_exploration, and code_search services.
"""

from __future__ import annotations

import logging
from repomap_tool.core.config_service import get_config
from repomap_tool.core.logging_service import get_logger
from typing import List, Dict, Any, Optional

from ...code_analysis.models import AnalysisFormat, FileCentralityAnalysis
from .base_controller import BaseController
from .view_models import (
    CentralityViewModel,
    FileAnalysisViewModel,
    ControllerConfig,
    AnalysisType,
)
from repomap_tool.models import SymbolViewModel


logger = get_logger(__name__)


class CentralityController(BaseController):
    """Controller for centrality analysis operations.

    This controller orchestrates the analysis of file centrality,
    coordinating between different domain services to provide
    LLM-optimized centrality analysis results.
    """

    def __init__(
        self,
        dependency_graph: Optional[Any] = None,
        centrality_calculator: Optional[Any] = None,
        centrality_engine: Optional[Any] = None,
        ast_analyzer: Optional[Any] = None,
        path_resolver: Optional[Any] = None,
        config: Optional[ControllerConfig] = None,
    ):
        """Initialize the CentralityController.

        Args:
            dependency_graph: Dependency graph for centrality analysis
            centrality_calculator: Centrality calculation service
            centrality_engine: Centrality analysis engine
            ast_analyzer: AST analysis service
            path_resolver: Path resolution service
            config: Controller configuration
        """
        super().__init__(config)

        # Validate dependencies
        if dependency_graph is None:
            raise ValueError("dependency_graph must be injected - no fallback allowed")
        if centrality_calculator is None:
            raise ValueError(
                "centrality_calculator must be injected - no fallback allowed"
            )
        if centrality_engine is None:
            raise ValueError("centrality_engine must be injected - no fallback allowed")
        if ast_analyzer is None:
            raise ValueError("ast_analyzer must be injected - no fallback allowed")
        if path_resolver is None:
            raise ValueError("path_resolver must be injected - no fallback allowed")

        self.dependency_graph = dependency_graph
        self.centrality_calculator = centrality_calculator
        self.centrality_engine = centrality_engine
        self.ast_analyzer = ast_analyzer
        self.path_resolver = path_resolver

    def execute(self, file_paths: Optional[List[str]] = None) -> CentralityViewModel:
        """Execute centrality analysis for the specified files.

        Args:
            file_paths: List of file paths to analyze (optional, will use all code files if not provided)

        Returns:
            CentralityViewModel with analysis results
        """
        if self.config is None:
            raise ValueError(
                "ControllerConfig must be set before executing - use controller.config = config"
            )

        # Type assertion for MyPy - we know config is not None after the check above
        config = self.config

        self._log_operation("centrality_analysis", {"files": file_paths})

        try:
            # Use centralized file discovery if no files provided
            if file_paths is None:
                from ...code_analysis.file_discovery_service import (
                    create_file_discovery_service,
                )

                file_discovery = create_file_discovery_service(
                    self.path_resolver.project_root
                )
                file_paths = file_discovery.get_code_files(exclude_tests=True)
                logger.debug(
                    f"Using {len(file_paths)} code files from centralized discovery"
                )

            # 1. Get structured centrality data from code_analysis service
            centrality_analyses = self._get_centrality_data(file_paths)

            # 2. Build ViewModel from structured data
            view_model = self._build_simple_view_model(centrality_analyses, file_paths)

            self._log_operation(
                "centrality_analysis_complete",
                {
                    "files_analyzed": len(file_paths),
                    "token_count": view_model.token_count,
                },
            )

            return view_model

        except Exception as e:
            self.logger.error(f"Centrality analysis failed: {e}")
            raise

    def _get_centrality_data(
        self, file_paths: List[str]
    ) -> List[FileCentralityAnalysis]:
        """Get structured centrality data by performing analysis directly.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of FileCentralityAnalysis objects
        """
        # Filter to only code files for centrality analysis
        from ...code_analysis.file_filter import FileFilter

        code_files = FileFilter.filter_code_files(file_paths, exclude_tests=True)

        if len(code_files) != len(file_paths):
            logger.info(
                f"Filtered {len(file_paths)} files to {len(code_files)} code files "
                f"for centrality analysis"
            )

        # Build dependency graph if it's empty
        if self.dependency_graph.graph.number_of_nodes() == 0:
            logger.debug("Building dependency graph for centrality analysis")
            self._build_dependency_graph()

        # Resolve file paths relative to project root
        resolved_paths = self.path_resolver.resolve_file_paths(code_files)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for comprehensive analysis
        # Use the same file list that was used to build the dependency graph
        # to ensure consistency between centrality calculation and analysis
        all_files = self.path_resolver.get_all_project_files()

        # If we have a dependency graph, use its file list for consistency
        if self.dependency_graph and self.dependency_graph.graph.number_of_nodes() > 0:
            # Get files from dependency graph to ensure consistency
            graph_files = list(self.dependency_graph.graph.nodes())
            if graph_files:
                all_files = graph_files
                logger.debug(
                    f"Using {len(all_files)} files from dependency graph for consistency"
                )

        # Sort files by centrality score (highest first) to process most important files first
        if len(code_files) > 1:
            # Get centrality scores for all files to sort them
            centrality_scores = (
                self.centrality_calculator.calculate_composite_importance()
            )
            file_scores = [(fp, centrality_scores.get(fp, 0.0)) for fp in code_files]
            sorted_file_scores = sorted(file_scores, key=lambda x: x[1], reverse=True)
            sorted_file_paths = [fp for fp, _ in sorted_file_scores]
        else:
            sorted_file_paths = code_files

        # Create a mapping for O(1) lookups instead of O(n) list.index() calls
        resolved_paths_map = dict(zip(code_files, resolved_paths))

        # Analyze each file in order of importance
        centrality_analyses = []
        for file_path in sorted_file_paths:
            try:
                # Find the resolved path for this file using the map
                resolved_path = resolved_paths_map[file_path]
                centrality_analysis = self.centrality_engine.analyze_file_centrality(
                    file_path, ast_results[resolved_path], all_files
                )
                centrality_analyses.append(centrality_analysis)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                # Create a minimal centrality analysis for this file
                centrality_analysis = FileCentralityAnalysis(
                    file_path=file_path,
                    centrality_score=0.0,
                    rank=1,
                    total_files=len(code_files),
                    dependency_analysis={
                        "total_connections": 0,
                        "incoming_connections": 0,
                        "outgoing_connections": 0,
                        "connection_ratio": 0.0,
                        "direct_imports": 0,
                        "reverse_dependencies": 0,
                    },
                    function_call_analysis={
                        "defined_functions": 0,
                        "called_functions": 0,
                        "external_calls": 0,
                        "internal_calls": 0,
                    },
                    centrality_breakdown={
                        "degree_centrality": 0.0,
                        "betweenness_centrality": 0.0,
                        "pagerank": 0.0,
                        "eigenvector_centrality": 0.0,
                        "closeness_centrality": 0.0,
                    },
                    structural_impact={
                        "complexity_score": 0.0,
                        "maintainability_score": 0.0,
                        "testability_score": 0.0,
                        "documentation_score": 0.0,
                    },
                )
                centrality_analyses.append(centrality_analysis)

        return centrality_analyses

    # Note: Exploration context methods removed - Controllers focus on LLM analysis

    def _build_simple_view_model(
        self, centrality_analyses: List[FileCentralityAnalysis], file_paths: List[str]
    ) -> CentralityViewModel:
        """Build CentralityViewModel from structured centrality analysis data.

        Args:
            centrality_analyses: List of FileCentralityAnalysis objects
            file_paths: Original file paths

        Returns:
            CentralityViewModel instance
        """
        # Create file analysis list from structured data
        file_analyses = []
        rankings = []

        # Sort analyses by centrality score to calculate proper rankings
        sorted_analyses = sorted(
            centrality_analyses, key=lambda x: x.centrality_score, reverse=True
        )

        for rank, analysis in enumerate(sorted_analyses, 1):
            # Create FileAnalysisViewModel from structured data
            file_analysis = FileAnalysisViewModel(
                file_path=analysis.file_path,
                line_count=0,  # Not available in FileCentralityAnalysis
                symbols=[],  # Not available in FileCentralityAnalysis
                imports=[],  # Not available in FileCentralityAnalysis
                dependencies=[],  # Not available in FileCentralityAnalysis
                impact_risk=analysis.centrality_score,  # Use centrality score as impact risk
                analysis_type=AnalysisType.CENTRALITY,
            )
            file_analyses.append(file_analysis)

            # Create ranking entry with additional data and proper rank
            rankings.append(
                {
                    "rank": rank,  # Use calculated rank instead of analysis.rank
                    "file_path": analysis.file_path,  # Use original path without cleaning to preserve special chars like [id]
                    "centrality_score": analysis.centrality_score,
                    "total_files": analysis.total_files,
                    "connections": analysis.dependency_analysis.get(
                        "total_connections", 0
                    ),
                    "imports": analysis.dependency_analysis.get("direct_imports", 0),
                    "reverse_dependencies": analysis.dependency_analysis.get(
                        "reverse_dependencies", 0
                    ),
                    "functions": analysis.function_call_analysis.get(
                        "defined_functions", 0
                    ),
                }
            )

        # Calculate summary statistics from structured data
        centrality_scores = [
            analysis.centrality_score for analysis in centrality_analyses
        ]
        high_centrality = len([s for s in centrality_scores if s >= 0.7])
        medium_centrality = len([s for s in centrality_scores if 0.3 <= s < 0.7])
        low_centrality = len([s for s in centrality_scores if s < 0.3])

        centrality_summary = {
            "analysis_type": "centrality",
            "total_files": len(centrality_analyses),
            "high_centrality_files": high_centrality,
            "medium_centrality_files": medium_centrality,
            "low_centrality_files": low_centrality,
            "average_centrality": (
                sum(centrality_scores) / len(centrality_scores)
                if centrality_scores
                else 0.0
            ),
            "max_centrality": max(centrality_scores) if centrality_scores else 0.0,
            "min_centrality": min(centrality_scores) if centrality_scores else 0.0,
            "token_optimization": True,
        }

        return CentralityViewModel(
            files=file_analyses,
            rankings=rankings,
            total_files=len(centrality_analyses),
            analysis_summary=centrality_summary,
            token_count=len(str(centrality_analyses)),
            max_tokens=get_config("MAX_TOKENS", 4000),
            compression_level=(
                self.config.compression_level if self.config else "medium"
            ),
        )

    # Note: Exploration context methods removed - Controllers focus on LLM analysis

    def _build_view_model(
        self, selected_context: Dict[str, Any], file_paths: List[str]
    ) -> CentralityViewModel:
        """Build CentralityViewModel from selected context.

        Args:
            selected_context: Selected context data
            file_paths: Original file paths

        Returns:
            CentralityViewModel instance
        """
        # Build file analysis view models
        file_view_models = []
        for file_path in file_paths:
            file_analysis = self._build_file_analysis_view_model(
                file_path, selected_context
            )
            file_view_models.append(file_analysis)

        # Build rankings
        rankings = self._build_rankings(selected_context)

        # Build analysis summary
        analysis_summary = self._build_analysis_summary(selected_context, file_paths)

        return CentralityViewModel(
            files=file_view_models,
            rankings=rankings,
            total_files=len(file_paths),
            analysis_summary=analysis_summary,
            token_count=self._estimate_tokens(selected_context),
            max_tokens=get_config("MAX_TOKENS", 4000),
            compression_level=(
                self.config.compression_level if self.config else "medium"
            ),
        )

    def _build_file_analysis_view_model(
        self, file_path: str, context: Dict[str, Any]
    ) -> FileAnalysisViewModel:
        """Build FileAnalysisViewModel for a single file.

        Args:
            file_path: Path to the file
            context: Analysis context

        Returns:
            FileAnalysisViewModel instance
        """
        # Get file-specific data from context
        file_data = context.get("files", {}).get(file_path, {})

        # Build symbol view models
        symbols = []
        for symbol_data in file_data.get("symbols", []):
            symbol = SymbolViewModel(
                name=symbol_data.get("name", ""),
                file_path=file_path,
                line_number=symbol_data.get("line_number", 0),
                symbol_type=symbol_data.get("type", "unknown"),
                signature=symbol_data.get("signature"),
                centrality_score=symbol_data.get("centrality_score"),
                importance_score=symbol_data.get("importance_score"),
            )
            symbols.append(symbol)

        return FileAnalysisViewModel(
            file_path=file_path,
            line_count=file_data.get("line_count", 0),
            symbols=symbols,
            imports=file_data.get("imports", []),
            dependencies=file_data.get("dependencies", []),
            centrality_score=file_data.get("centrality_score"),
            analysis_type=AnalysisType.CENTRALITY,
        )

    def _build_rankings(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build centrality rankings.

        Args:
            context: Analysis context

        Returns:
            List of ranking dictionaries
        """
        centrality_scores = context.get("centrality_scores", {})

        # Sort files by centrality score
        sorted_files = sorted(
            centrality_scores.items(), key=lambda x: x[1], reverse=True
        )

        rankings = []
        for rank, (file_path, score) in enumerate(sorted_files, 1):
            rankings.append(
                {
                    "rank": rank,
                    "file_path": file_path,
                    "centrality_score": score,
                    "relative_importance": (
                        score / max(centrality_scores.values())
                        if centrality_scores
                        else 0
                    ),
                }
            )

        return rankings

    def _build_analysis_summary(
        self, context: Dict[str, Any], file_paths: List[str]
    ) -> Dict[str, Any]:
        """Build analysis summary.

        Args:
            context: Analysis context
            file_paths: Original file paths

        Returns:
            Analysis summary dictionary
        """
        centrality_scores = context.get("centrality_scores", {})

        return {
            "total_files_analyzed": len(file_paths),
            "average_centrality": (
                sum(centrality_scores.values()) / len(centrality_scores)
                if centrality_scores
                else 0
            ),
            "max_centrality": (
                max(centrality_scores.values()) if centrality_scores else 0
            ),
            "min_centrality": (
                min(centrality_scores.values()) if centrality_scores else 0
            ),
            "analysis_type": "centrality",
            "compression_applied": (
                self.config.compression_level if self.config else "medium"
            ),
            "token_optimization": True,
        }

    def _build_dependency_graph(self) -> None:
        """Build the dependency graph if it's empty."""
        try:
            # Get project root from path resolver
            project_root = self.path_resolver.project_root

            # Use import analyzer to get project imports
            from repomap_tool.code_analysis.import_analyzer import ImportAnalyzer

            import_analyzer = ImportAnalyzer(project_root=project_root)

            # Analyze project imports
            project_imports = import_analyzer.analyze_project_imports(project_root)

            # Use all files for dependency analysis (no artificial limits)

            # Build the dependency graph
            self.dependency_graph.build_graph(project_imports)

            logger.debug(
                f"Built dependency graph with {self.dependency_graph.graph.number_of_nodes()} nodes"
            )

        except Exception as e:
            logger.error(f"Failed to build dependency graph: {e}")
            # Continue with empty graph - centrality analysis will handle it gracefully
