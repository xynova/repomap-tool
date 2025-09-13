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

# Lazy imports to reduce coupling and improve startup time
def _lazy_import(module_name: str, class_name: str):
    """Lazy import helper to reduce coupling."""
    def _import():
        module = __import__(f"repomap_tool.dependencies.{module_name}", fromlist=[class_name])
        return getattr(module, class_name)
    return _import

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
def get_call_graph_builder():
    """Get CallGraphBuilder class (lazy loaded)."""
    from .call_graph_builder import CallGraphBuilder
    return CallGraphBuilder

def get_centrality_calculator():
    """Get CentralityCalculator class (lazy loaded)."""
    from .centrality_calculator import CentralityCalculator
    return CentralityCalculator

def get_impact_analyzer():
    """Get ImpactAnalyzer class (lazy loaded)."""
    from .impact_analyzer import ImpactAnalyzer
    return ImpactAnalyzer

def get_advanced_dependency_graph():
    """Get AdvancedDependencyGraph class (lazy loaded)."""
    from .advanced_dependency_graph import AdvancedDependencyGraph
    return AdvancedDependencyGraph

def get_llm_file_analyzer():
    """Get LLMFileAnalyzer class (lazy loaded)."""
    from .llm_file_analyzer import LLMFileAnalyzer
    return LLMFileAnalyzer

def get_impact_analysis_engine():
    """Get ImpactAnalysisEngine class (lazy loaded)."""
    from .impact_analysis_engine import ImpactAnalysisEngine
    return ImpactAnalysisEngine

def get_centrality_analysis_engine():
    """Get CentralityAnalysisEngine class (lazy loaded)."""
    from .centrality_analysis_engine import CentralityAnalysisEngine
    return CentralityAnalysisEngine

def get_path_resolver():
    """Get PathResolver class (lazy loaded)."""
    from .path_resolver import PathResolver
    return PathResolver

def get_js_ts_analyzer():
    """Get JavaScriptTypeScriptAnalyzer class (lazy loaded)."""
    from .js_ts_analyzer import JavaScriptTypeScriptAnalyzer
    return JavaScriptTypeScriptAnalyzer

def get_import_utils():
    """Get ImportUtils class (lazy loaded)."""
    from .import_utils import ImportUtils
    return ImportUtils

def get_ast_visitors():
    """Get AST visitor functions (lazy loaded)."""
    from .ast_visitors import create_visitor, AnalysisContext
    return create_visitor, AnalysisContext

def get_file_utils():
    """Get file utility functions (lazy loaded)."""
    from .file_utils import get_all_project_files, suggest_test_files
    return get_all_project_files, suggest_test_files

def get_function_utils():
    """Get function utility functions (lazy loaded)."""
    from .function_utils import (
        find_most_called_function,
        get_top_called_functions,
        smart_categorize_function_calls,
        filter_business_relevant_calls,
        get_functions_called_from_file,
        find_most_used_class,
    )
    return (
        find_most_called_function,
        get_top_called_functions,
        smart_categorize_function_calls,
        filter_business_relevant_calls,
        get_functions_called_from_file,
        find_most_used_class,
    )

def get_format_utils():
    """Get format utility functions (lazy loaded)."""
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
    return (
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
    "get_js_ts_analyzer",
    "get_import_utils",
    "get_ast_visitors",
    "get_file_utils",
    "get_function_utils",
    "get_format_utils",
]

__version__ = "0.1.0"
