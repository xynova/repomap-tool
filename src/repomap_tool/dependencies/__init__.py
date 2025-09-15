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
]

__version__ = "0.1.0"
