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

from .models import (
    Import, FileImports, ProjectImports, ImportType,
    FunctionCall, CallGraph, DependencyNode,
    ImpactReport, BreakingChangeRisk, RefactoringOpportunity
)
from .import_analyzer import ImportAnalyzer
from .dependency_graph import DependencyGraph
from .call_graph_builder import CallGraphBuilder
from .centrality_calculator import CentralityCalculator
from .impact_analyzer import ImpactAnalyzer
from .advanced_dependency_graph import AdvancedDependencyGraph

__all__ = [
    # Core classes
    "ImportAnalyzer",
    "DependencyGraph", 
    "CallGraphBuilder",
    "CentralityCalculator",
    "ImpactAnalyzer",
    "AdvancedDependencyGraph",
    
    # Data models
    "FileImports",
    "ProjectImports", 
    "Import",
    "DependencyNode",
    "CallGraph",
    "FunctionCall",
    "ImpactReport",
    "BreakingChangeRisk",
]

__version__ = "0.1.0"
