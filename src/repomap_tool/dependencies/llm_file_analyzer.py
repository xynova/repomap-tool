"""
LLM-optimized file analyzer for impact and centrality analysis.

This module provides comprehensive file-level analysis optimized for LLM consumption,
combining AST analysis with dependency graph analysis to provide detailed insights
about file relationships and impact.
"""

import logging
import os
from typing import List, Dict, Set, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .ast_file_analyzer import (
    AnalysisType,
    ASTFileAnalyzer,
    FileAnalysisResult,
    CrossFileRelationship,
)
from .advanced_dependency_graph import AdvancedDependencyGraph
from .centrality_calculator import CentralityCalculator
from .impact_analyzer import ImpactAnalyzer
from .impact_analysis_engine import ImpactAnalysisEngine
from .centrality_analysis_engine import CentralityAnalysisEngine
from .path_resolver import PathResolver
from .models import (
    AnalysisFormat,
    FileImpactAnalysis,
    FileCentralityAnalysis,
)
from .format_utils import (
    format_llm_optimized_impact,
    format_llm_optimized_centrality,
    format_json_impact,
    format_json_centrality,
    format_table_impact,
    format_table_centrality,
    format_text_impact,
    format_text_centrality,
)
from ..llm.token_optimizer import TokenOptimizer
from ..llm.context_selector import ContextSelector
from ..llm.hierarchical_formatter import HierarchicalFormatter

logger = logging.getLogger(__name__)


class LLMFileAnalyzer:
    """LLM-optimized file analyzer for comprehensive impact and centrality analysis."""

    centrality_calculator: Optional[CentralityCalculator]
    impact_analyzer: Optional[ImpactAnalyzer]

    def __init__(
        self,
        dependency_graph: Optional[AdvancedDependencyGraph] = None,
        project_root: Optional[str] = None,
        max_tokens: int = 4000,
        # Dependency injection parameters
        ast_analyzer: Optional[ASTFileAnalyzer] = None,
        token_optimizer: Optional[TokenOptimizer] = None,
        context_selector: Optional[ContextSelector] = None,
        hierarchical_formatter: Optional[HierarchicalFormatter] = None,
        path_resolver: Optional[PathResolver] = None,
        impact_engine: Optional[ImpactAnalysisEngine] = None,
        centrality_engine: Optional[CentralityAnalysisEngine] = None,
    ):
        """Initialize the LLM file analyzer.

        Args:
            dependency_graph: Advanced dependency graph for analysis
            project_root: Root path of the project
            max_tokens: Maximum tokens for LLM-optimized output
            ast_analyzer: AST analyzer instance (injected)
            token_optimizer: Token optimizer instance (injected)
            context_selector: Context selector instance (injected)
            hierarchical_formatter: Hierarchical formatter instance (injected)
            path_resolver: Path resolver instance (injected)
            impact_engine: Impact analysis engine instance (injected)
            centrality_engine: Centrality analysis engine instance (injected)
        """
        self.dependency_graph = dependency_graph
        self.project_root = project_root
        self.max_tokens = max_tokens

        # Initialize components with dependency injection
        self.ast_analyzer = ast_analyzer or ASTFileAnalyzer(project_root)
        self.token_optimizer = token_optimizer or TokenOptimizer()
        self.context_selector = context_selector or ContextSelector(dependency_graph)
        self.hierarchical_formatter = hierarchical_formatter or HierarchicalFormatter()
        self.path_resolver = path_resolver or PathResolver(project_root)

        # Initialize analysis engines with dependency injection
        self.impact_engine = impact_engine or ImpactAnalysisEngine(self.ast_analyzer)
        self.centrality_engine = centrality_engine or CentralityAnalysisEngine(
            self.ast_analyzer, None, dependency_graph
        )

        # Initialize analysis components if dependency graph is available
        if dependency_graph:
            try:
                self.centrality_calculator = CentralityCalculator(dependency_graph)
            except Exception as e:
                logger.error(f"Failed to initialize centrality calculator: {e}")
                self.centrality_calculator = None

            try:
                self.impact_analyzer = ImpactAnalyzer(dependency_graph)
            except Exception as e:
                logger.error(f"Failed to initialize impact analyzer: {e}")
                self.impact_analyzer = None

            # Update centrality engine with calculator if not already injected
            if not centrality_engine:
                self.centrality_engine = CentralityAnalysisEngine(
                    self.ast_analyzer, self.centrality_calculator, dependency_graph
                )
        else:
            self.centrality_calculator = None
            self.impact_analyzer = None

    def analyze_file_impact(
        self,
        file_paths: List[str],
        format_type: AnalysisFormat = AnalysisFormat.LLM_OPTIMIZED,
    ) -> str:
        """Analyze impact for one or more files.

        Args:
            file_paths: List of file paths to analyze
            format_type: Output format type

        Returns:
            Formatted impact analysis string
        """

        # Resolve file paths relative to project root
        resolved_paths = self.path_resolver.resolve_file_paths(file_paths)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for reverse dependency analysis
        all_files = self.path_resolver.get_all_project_files()

        # Analyze each file
        impact_analyses = []
        for i, file_path in enumerate(file_paths):
            resolved_path = resolved_paths[i]
            impact_analysis = self.impact_engine.analyze_file_impact(
                file_path, ast_results[resolved_path], all_files
            )
            impact_analyses.append(impact_analysis)

        # Format output
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return format_llm_optimized_impact(
                impact_analyses, self.token_optimizer, self.max_tokens
            )
        elif format_type == AnalysisFormat.JSON:
            return format_json_impact(impact_analyses)
        elif format_type == AnalysisFormat.TABLE:
            return format_table_impact(impact_analyses)
        else:
            return format_text_impact(
                impact_analyses, self.token_optimizer, self.max_tokens
            )

    def analyze_file_centrality(
        self,
        file_paths: List[str],
        format_type: AnalysisFormat = AnalysisFormat.LLM_OPTIMIZED,
    ) -> str:
        """Analyze centrality for one or more files.

        Args:
            file_paths: List of file paths to analyze
            format_type: Output format type

        Returns:
            Formatted centrality analysis string
        """

        if not self.centrality_calculator:
            return "Centrality analysis requires dependency graph. Please run dependency analysis first."

        # Resolve file paths relative to project root
        resolved_paths = self.path_resolver.resolve_file_paths(file_paths)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for comprehensive analysis
        all_files = self.path_resolver.get_all_project_files()

        # Analyze each file
        centrality_analyses = []
        for i, file_path in enumerate(file_paths):
            try:
                resolved_path = resolved_paths[i]
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
                    total_files=len(file_paths),
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
                        "dependency_depth": 0,
                        "fan_in": 0,
                        "fan_out": 0,
                    },
                )
                centrality_analyses.append(centrality_analysis)

        # Format output
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return format_llm_optimized_centrality(
                centrality_analyses,
                self.token_optimizer,
                self.max_tokens,
                self.project_root or "",
                self.ast_analyzer,
            )
        elif format_type == AnalysisFormat.JSON:
            return format_json_centrality(centrality_analyses)
        elif format_type == AnalysisFormat.TABLE:
            return format_table_centrality(centrality_analyses)
        else:
            return format_text_centrality(
                centrality_analyses,
                self.token_optimizer,
                self.max_tokens,
                self.project_root or "",
                self.ast_analyzer,
            )

    # Formatting methods moved to format_utils.py

    # File utility methods moved to file_utils.py

    # Function analysis methods moved to function_utils.py
