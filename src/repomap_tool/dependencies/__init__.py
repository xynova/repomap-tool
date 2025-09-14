"""
Dependency Analysis Package for RepoMap Tool.

This package provides intelligent dependency graph analysis to understand code relationships,
file importance, and impact scope for better repomap generation.

Core Components:
- ImportAnalyzer: Analyzes import statements across all files
- CallGraphBuilder: Builds function call graphs within and across files
- DependencyGraph: Main dependency graph representation
- CentralityCalculator: Calculates importance scores for files and functions
- ImpactAnalyzer: Analyzes impact scope of potential changes
- AdvancedDependencyGraph: Enhanced graph with call graph integration
"""

# Lazy loading for advanced features
# Core models - always available
from .models import (
    Import,
    FileImports,
    ProjectImports,
    ImportType,
    FunctionCall,
    CallGraph,
    DependencyNode,
    ImpactReport,
    BreakingChangeRisk,
    RefactoringOpportunity,
    FileAnalysisResult,
    CrossFileRelationship,
    AnalysisFormat,
    FileImpactAnalysis,
    FileCentralityAnalysis,
)

# Core classes - always available for basic functionality
from .import_analyzer import ImportAnalyzer
from .dependency_graph import DependencyGraph
from .ast_file_analyzer import ASTFileAnalyzer


# Lazy loading for advanced features
def get_call_graph_builder() -> type:
    """Get CallGraphBuilder class (lazy loaded)."""
    from .call_graph_builder import CallGraphBuilder

    return CallGraphBuilder


def get_centrality_calculator() -> type:
    """Get CentralityCalculator class (lazy loaded)."""
    from .centrality_calculator import CentralityCalculator

    return CentralityCalculator


def get_impact_analyzer() -> type:
    """Get ImpactAnalyzer class (lazy loaded)."""
    from .impact_analyzer import ImpactAnalyzer

    return ImpactAnalyzer


def get_advanced_dependency_graph() -> type:
    """Get AdvancedDependencyGraph class (lazy loaded)."""
    from .advanced_dependency_graph import AdvancedDependencyGraph

    return AdvancedDependencyGraph


def get_llm_file_analyzer() -> type:
    """Get LLMFileAnalyzer class (lazy loaded)."""
    from .llm_file_analyzer import LLMFileAnalyzer

    return LLMFileAnalyzer


def get_impact_analysis_engine() -> type:
    """Get ImpactAnalysisEngine class (lazy loaded)."""
    from .impact_analysis_engine import ImpactAnalysisEngine

    return ImpactAnalysisEngine


def get_centrality_analysis_engine() -> type:
    """Get CentralityAnalysisEngine class (lazy loaded)."""
    from .centrality_analysis_engine import CentralityAnalysisEngine

    return CentralityAnalysisEngine


def get_path_resolver() -> type:
    """Get PathResolver class (lazy loaded)."""
    from .path_resolver import PathResolver

    return PathResolver


__all__ = [
    # Core classes (always available)
    "ImportAnalyzer",
    "DependencyGraph",
    "ASTFileAnalyzer",
    # Data models (always available)
    "FileImports",
    "ProjectImports",
    "Import",
    "DependencyNode",
    "CallGraph",
    "FunctionCall",
    "ImpactReport",
    "BreakingChangeRisk",
    "FileAnalysisResult",
    "CrossFileRelationship",
    "FileImpactAnalysis",
    "FileCentralityAnalysis",
    "AnalysisFormat",
    "ImportType",
    "RefactoringOpportunity",
    # Lazy loading functions
    "get_call_graph_builder",
    "get_centrality_calculator",
    "get_impact_analyzer",
    "get_advanced_dependency_graph",
    "get_llm_file_analyzer",
    "get_impact_analysis_engine",
    "get_centrality_analysis_engine",
    "get_path_resolver",
]

__version__ = "0.1.0"
