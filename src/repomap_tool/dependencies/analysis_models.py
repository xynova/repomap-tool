"""
Data models for LLM file analysis.

This module contains the data structures used by the LLM file analyzer
and its modular components, separated to avoid circular imports.
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum


class AnalysisFormat(str, Enum):
    """Output formats for analysis results."""

    TEXT = "text"
    JSON = "json"
    TABLE = "table"
    LLM_OPTIMIZED = "llm_optimized"


@dataclass
class FileImpactAnalysis:
    """Comprehensive impact analysis for a file."""

    file_path: str
    direct_dependencies: List[Dict[str, Any]]
    reverse_dependencies: List[Dict[str, Any]]
    function_call_analysis: List[Dict[str, Any]]
    structural_impact: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    suggested_tests: List[str]


@dataclass
class FileCentralityAnalysis:
    """Comprehensive centrality analysis for a file."""

    file_path: str
    centrality_score: float
    rank: int
    total_files: int
    dependency_analysis: Dict[str, Any]
    function_call_analysis: Dict[str, Any]
    centrality_breakdown: Optional[Dict[str, float]]
    structural_impact: Dict[str, Any]
