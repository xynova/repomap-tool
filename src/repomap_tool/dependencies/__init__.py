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
from .import_analyzer import ImportAnalyzer
from .dependency_graph import DependencyGraph
from .call_graph_builder import CallGraphBuilder
from .centrality_calculator import CentralityCalculator
from .impact_analyzer import ImpactAnalyzer
from .advanced_dependency_graph import AdvancedDependencyGraph
from .ast_file_analyzer import ASTFileAnalyzer
from .ast_visitors import create_visitor, AnalysisContext
from .js_ts_analyzer import JavaScriptTypeScriptAnalyzer
from .import_utils import ImportUtils
from .impact_analysis_engine import ImpactAnalysisEngine
from .centrality_analysis_engine import CentralityAnalysisEngine
from .path_resolver import PathResolver
from .llm_file_analyzer import LLMFileAnalyzer
from .file_utils import get_all_project_files, suggest_test_files
from .function_utils import (
    find_most_called_function,
    get_top_called_functions,
    smart_categorize_function_calls,
    filter_business_relevant_calls,
    get_functions_called_from_file,
    find_most_used_class,
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

__all__ = [
    # Core classes
    "ImportAnalyzer",
    "DependencyGraph",
    "CallGraphBuilder",
    "CentralityCalculator",
    "ImpactAnalyzer",
    "AdvancedDependencyGraph",
    "ASTFileAnalyzer",
    "LLMFileAnalyzer",
    # Analysis engines
    "ImpactAnalysisEngine",
    "CentralityAnalysisEngine",
    "PathResolver",
    # AST analysis components
    "create_visitor",
    "AnalysisContext",
    "JavaScriptTypeScriptAnalyzer",
    "ImportUtils",
    # Data models
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
    # File utilities
    "get_all_project_files",
    "suggest_test_files",
    "find_most_called_function",
    "get_top_called_functions",
    "smart_categorize_function_calls",
    "filter_business_relevant_calls",
    "get_functions_called_from_file",
    "find_most_used_class",
    # Format utilities
    "format_llm_optimized_impact",
    "format_llm_optimized_centrality",
    "format_json_impact",
    "format_json_centrality",
    "format_table_impact",
    "format_table_centrality",
    "format_text_impact",
    "format_text_centrality",
]

__version__ = "0.1.0"
