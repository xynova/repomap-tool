"""
Centrality Controller for CLI.

This controller orchestrates centrality analysis operations,
coordinating between code_analysis, code_exploration, and code_search services.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from ...code_analysis.models import AnalysisFormat, FileCentralityAnalysis
from .base_controller import BaseController
from .view_models import (
    CentralityViewModel,
    FileAnalysisViewModel,
    SymbolViewModel,
    ControllerConfig,
    AnalysisType,
)


logger = logging.getLogger(__name__)


class CentralityController(BaseController):
    """Controller for centrality analysis operations.

    This controller orchestrates the analysis of file centrality,
    coordinating between different domain services to provide
    LLM-optimized centrality analysis results.
    """

    def __init__(
        self,
        code_analysis_service: Optional[Any] = None,
        code_exploration_service: Optional[Any] = None,
        code_search_service: Optional[Any] = None,
        token_optimizer: Optional[Any] = None,
        context_selector: Optional[Any] = None,
        config: Optional[ControllerConfig] = None,
    ):
        """Initialize the CentralityController.

        Args:
            code_analysis_service: Service for code analysis operations
            code_exploration_service: Service for code exploration operations
            code_search_service: Service for code search operations
            token_optimizer: Service for token optimization
            context_selector: Service for context selection
            config: Controller configuration
        """
        super().__init__(config)

        # Validate dependencies
        if code_analysis_service is None:
            raise ValueError(
                "code_analysis_service must be injected - no fallback allowed"
            )
        if token_optimizer is None:
            raise ValueError("token_optimizer must be injected - no fallback allowed")
        if context_selector is None:
            raise ValueError("context_selector must be injected - no fallback allowed")

        self.code_analysis_service = code_analysis_service
        self.code_exploration = code_exploration_service
        self.code_search = code_search_service
        self.token_optimizer = token_optimizer
        self.context_selector = context_selector

    def execute(self, file_paths: List[str]) -> CentralityViewModel:
        """Execute centrality analysis for the specified files.

        Args:
            file_paths: List of file paths to analyze

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
        """Get structured centrality data from code_analysis service.

        Args:
            file_paths: List of file paths to analyze

        Returns:
            List of FileCentralityAnalysis objects
        """
        # Use LLM analyzer to get structured centrality analysis
        centrality_analyses = (
            self.code_analysis_service.analyze_file_centrality_structured(
                file_paths=file_paths
            )
        )

        return centrality_analyses  # type: ignore[no-any-return]

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

        for analysis in centrality_analyses:
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

            # Create ranking entry
            rankings.append(
                {
                    "rank": analysis.rank,
                    "file_path": analysis.file_path,
                    "centrality_score": analysis.centrality_score,
                    "total_files": analysis.total_files,
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
            max_tokens=self.config.max_tokens if self.config else 4000,
            compression_level=(
                self.config.compression_level if self.config else "medium"
            ),
        )

    # Note: Exploration context methods removed - Controllers focus on LLM analysis

    def _optimize_for_tokens(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize data for token budget.

        Args:
            data: Data to optimize

        Returns:
            Token-optimized data
        """
        # Use token optimizer to optimize the data
        optimized_data = self.token_optimizer.optimize_for_token_budget(
            data, self.config.max_tokens if self.config else 4000
        )

        return optimized_data  # type: ignore[no-any-return]

    def _select_optimal_context(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Select optimal context based on token budget.

        Args:
            data: Data to select context from

        Returns:
            Selected context data
        """
        # Use context selector to select optimal context
        selected_context = self.context_selector.select_optimal_context(
            data,
            self.config.max_tokens if self.config else 4000,
            strategy=(
                self.config.context_selection if self.config else "centrality_based"
            ),
        )

        return selected_context  # type: ignore[no-any-return]

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
            max_tokens=self.config.max_tokens if self.config else 4000,
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
