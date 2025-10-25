"""
Impact Controller for CLI.

This controller orchestrates impact analysis operations,
coordinating between code_analysis, code_exploration, and code_search services.
"""

from __future__ import annotations

import logging
from repomap_tool.core.config_service import get_config
from repomap_tool.core.logging_service import get_logger
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from ...code_analysis.models import AnalysisFormat, FileImpactAnalysis
from ...code_analysis.dependency_graph import DependencyGraph
from ...code_analysis.impact_analyzer import ImpactAnalyzer
from ...code_analysis.impact_analysis_engine import ImpactAnalysisEngine
from ...code_analysis.ast_file_analyzer import ASTFileAnalyzer
from ...code_analysis.path_resolver import PathResolver
from .base_controller import BaseController
from .view_models import (
    ImpactViewModel,
    FileAnalysisViewModel,
    ControllerConfig,
    AnalysisType,
)

if TYPE_CHECKING:
    from repomap_tool.models import SymbolViewModel

logger = get_logger(__name__)


class ImpactController(BaseController):
    """Controller for impact analysis operations.

    This controller orchestrates the analysis of change impact,
    coordinating between different domain services to provide
    LLM-optimized impact analysis results.
    """

    def __init__(
        self,
        dependency_graph: DependencyGraph,
        impact_analyzer: ImpactAnalyzer,
        impact_engine: ImpactAnalysisEngine,
        ast_analyzer: ASTFileAnalyzer,
        path_resolver: PathResolver,
        config: Optional[ControllerConfig] = None,
    ):
        """Initialize the ImpactController.

        Args:
            dependency_graph: Dependency graph for impact analysis
            impact_analyzer: Impact analysis service
            impact_engine: Impact analysis engine
            ast_analyzer: AST analysis service
            path_resolver: Path resolution service
            config: Controller configuration
        """
        super().__init__(config)

        # All dependencies are required and injected via DI container

        self.dependency_graph = dependency_graph
        self.impact_analyzer = impact_analyzer
        self.impact_engine = impact_engine
        self.ast_analyzer = ast_analyzer
        self.path_resolver = path_resolver

    def execute(self, changed_files: List[str]) -> ImpactViewModel:
        """Execute impact analysis for the specified changed files.

        Args:
            changed_files: List of files that have changed

        Returns:
            ImpactViewModel with analysis results
        """
        if self.config is None:
            raise ValueError(
                "ControllerConfig must be set before executing - use controller.config = config"
            )

        # Type assertion for MyPy - we know config is not None after the check above
        config = self.config

        self._log_operation("impact_analysis", {"changed_files": changed_files})

        try:
            # 1. Get structured impact data from code_analysis service
            impact_analyses = self._get_impact_data(changed_files)

            # 2. Build ViewModel from structured data
            view_model = self._build_simple_view_model(impact_analyses, changed_files)

            self._log_operation(
                "impact_analysis_complete",
                {
                    "changed_files": len(changed_files),
                    "affected_files": view_model.total_affected,
                    "token_count": view_model.token_count,
                },
            )

            return view_model

        except Exception as e:
            self.logger.error(f"Impact analysis failed: {e}")
            raise

    def _get_impact_data(self, changed_files: List[str]) -> List[FileImpactAnalysis]:
        """Get structured impact data by performing analysis directly.

        Args:
            changed_files: List of files that have changed

        Returns:
            List of FileImpactAnalysis objects
        """
        # Resolve file paths relative to project root
        resolved_paths = self.path_resolver.resolve_file_paths(changed_files)

        # Get all files in project for comprehensive analysis
        all_files = self.path_resolver.get_all_project_files()
        # Validate that all file paths are absolute (architectural requirement)
        all_files = self.path_resolver.resolve_file_paths(all_files)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Create a mapping for O(1) lookups instead of O(n) list.index() calls
        resolved_paths_map = dict(zip(changed_files, resolved_paths))

        # Analyze each file for impact
        impact_analyses = []
        for file_path in changed_files:
            try:
                # Find the resolved path for this file using the map
                resolved_path = resolved_paths_map[file_path]
                impact_analysis = self.impact_engine.analyze_file_impact(
                    file_path, ast_results[resolved_path], all_files
                )
                impact_analyses.append(impact_analysis)
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                # Create a minimal impact analysis for this file
                impact_analysis = FileImpactAnalysis(
                    file_path=file_path,
                    impact_score=0.0,
                    affected_files=[],
                    dependency_chain_length=0,
                    risk_level="low",
                    impact_categories=[],
                    suggested_tests=[],
                    direct_dependencies=[],
                    reverse_dependencies=[],
                    function_call_analysis=None,
                    structural_impact={},
                    risk_factors=[],
                    mitigation_suggestions=[],
                    risk_assessment={},
                )
                impact_analyses.append(impact_analysis)

        return impact_analyses

    # Note: Related symbols methods removed - Controllers focus on LLM analysis

    # Note: Symbol relationship methods removed - Controllers focus on LLM analysis

    # Note: All symbol analysis methods removed - Controllers focus on LLM analysis

    # Note: All remaining methods removed - Controllers focus on LLM analysis

    # Note: All remaining methods removed - Controllers focus on LLM analysis

    # Note: Token optimization methods removed - Controllers focus on LLM analysis

    # Note: Context selection methods removed - Controllers focus on LLM analysis

    # Note: All ViewModel building methods removed - Controllers focus on LLM analysis

    # Note: All remaining methods removed - Controllers focus on LLM analysis

    def _build_simple_view_model(
        self, impact_analyses: List[FileImpactAnalysis], changed_files: List[str]
    ) -> ImpactViewModel:
        """Build ImpactViewModel from structured impact analysis data.

        Args:
            impact_analyses: List of FileImpactAnalysis objects
            changed_files: Original changed files

        Returns:
            ImpactViewModel instance
        """
        # Create affected files list from structured data
        affected_files = []
        all_affected_files = set()

        for analysis in impact_analyses:
            # Create FileAnalysisViewModel from structured data
            file_analysis = FileAnalysisViewModel(
                file_path=analysis.file_path,
                line_count=0,  # Not available in FileImpactAnalysis
                symbols=[],  # Not available in FileImpactAnalysis
                imports=[],  # Not available in FileImpactAnalysis
                dependencies=[],  # Not available in FileImpactAnalysis
                impact_risk=analysis.impact_score,  # Use impact score as impact risk
                analysis_type=AnalysisType.IMPACT,
            )
            affected_files.append(file_analysis)

            # Collect all affected files
            all_affected_files.update(analysis.affected_files)

        # Calculate impact scope from structured data
        impact_scores = [analysis.impact_score for analysis in impact_analyses]
        high_impact = len([s for s in impact_scores if s >= 0.7])
        medium_impact = len([s for s in impact_scores if 0.3 <= s < 0.7])
        low_impact = len([s for s in impact_scores if s < 0.3])

        impact_scope = {
            "total_affected_files": len(all_affected_files),
            "total_related_symbols": sum(
                len(analysis.impact_categories) if analysis.impact_categories else 0
                for analysis in impact_analyses
            ),
            "impact_depth": (
                max(
                    analysis.dependency_chain_length or 0
                    for analysis in impact_analyses
                )
                if impact_analyses
                else 1
            ),
            "scope_categories": {
                "high_impact": high_impact,
                "medium_impact": medium_impact,
                "low_impact": low_impact,
            },
        }

        # Create risk assessment from structured data
        risk_levels = [analysis.risk_level for analysis in impact_analyses]
        overall_risk = (
            "high"
            if "high" in risk_levels
            else "medium" if "medium" in risk_levels else "low"
        )

        risk_assessment = {
            "overall_risk_level": overall_risk,
            "risk_factors": [
                f"Impact score: {analysis.impact_score:.2f}"
                for analysis in impact_analyses
            ],
            "mitigation_suggestions": [
                suggestion
                for analysis in impact_analyses
                for suggestion in (analysis.suggested_tests or [])
            ],
            "confidence_score": (
                sum(analysis.impact_score for analysis in impact_analyses)
                / len(impact_analyses)
                if impact_analyses
                else 0.5
            ),
        }

        return ImpactViewModel(
            changed_files=changed_files,
            affected_files=affected_files,
            impact_scope=impact_scope,
            risk_assessment=risk_assessment,
            total_affected=len(all_affected_files),
            token_count=len(str(impact_analyses)),
            max_tokens=get_config("MAX_TOKENS", 4000),
            compression_level=(
                self.config.compression_level if self.config else "medium"
            ),
        )

    # Note: All remaining methods removed - Controllers focus on LLM analysis

    def _calculate_max_impact_depth(self, affected_files: List[Dict[str, Any]]) -> int:
        """Calculate maximum impact depth.

        Args:
            affected_files: List of affected files

        Returns:
            Maximum impact depth
        """
        return max(
            [file_data.get("impact_depth", 1) for file_data in affected_files],
            default=1,
        )

    def _categorize_impact_scope(
        self, affected_files: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Categorize impact scope.

        Args:
            affected_files: List of affected files

        Returns:
            Impact scope categories
        """
        categories = {"high_impact": 0, "medium_impact": 0, "low_impact": 0}

        for file_data in affected_files:
            impact_level = file_data.get("impact_level", "low_impact")
            categories[impact_level] = categories.get(impact_level, 0) + 1

        return categories

    def _build_risk_assessment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build risk assessment.

        Args:
            context: Analysis context

        Returns:
            Risk assessment dictionary
        """
        risk_data = context.get("risk_assessment", {})

        return {
            "overall_risk_level": risk_data.get("overall_risk", "low"),
            "risk_factors": risk_data.get("risk_factors", []),
            "mitigation_suggestions": risk_data.get("mitigation_suggestions", []),
            "confidence_score": risk_data.get("confidence_score", 0.0),
        }
