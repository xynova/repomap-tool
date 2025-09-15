"""
LLM-optimized file analyzer for impact and centrality analysis.

This module provides comprehensive file-level analysis optimized for LLM consumption,
combining AST analysis with dependency graph analysis to provide detailed insights
about file relationships and impact.
"""

import logging
import os
from typing import List, Dict, Set, Optional, Any, Tuple, TYPE_CHECKING
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

if TYPE_CHECKING:
    from .llm_analyzer_config import LLMAnalyzerConfig, LLMAnalyzerDependencies
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
        config: "LLMAnalyzerConfig",
        dependencies: "LLMAnalyzerDependencies",
    ):
        """Initialize the LLM file analyzer with configuration and dependencies.

        Args:
            config: LLM analyzer configuration
            dependencies: Injected dependencies container
        """
        # Store configuration
        self.config = config
        self.max_tokens = config.max_tokens
        self.enable_impact_analysis = config.enable_impact_analysis
        self.enable_centrality_analysis = config.enable_centrality_analysis
        self.enable_code_snippets = config.enable_code_snippets
        self.max_snippets_per_file = config.max_snippets_per_file
        self.snippet_max_lines = config.snippet_max_lines
        self.analysis_timeout = config.analysis_timeout
        self.cache_results = config.cache_results
        self.verbose = config.verbose

        # Store dependencies container
        self.dependencies = dependencies

        # Store core dependencies
        self.dependency_graph = dependencies.dependency_graph
        self.project_root = dependencies.project_root

        # Store injected dependencies
        self.ast_analyzer = dependencies.ast_analyzer
        self.token_optimizer = dependencies.token_optimizer
        self.context_selector = dependencies.context_selector
        self.hierarchical_formatter = dependencies.hierarchical_formatter
        self.path_resolver = dependencies.path_resolver
        self.centrality_calculator = dependencies.centrality_calculator
        self.centrality_engine = dependencies.centrality_engine
        self.impact_engine = dependencies.impact_engine

        logger.info("LLMFileAnalyzer initialized with configuration and injected dependencies")

        # Impact analyzer is now injected via DI container
        # No need for manual instantiation
        self.impact_analyzer = None  # Will be set by DI container if needed

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
