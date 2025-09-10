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
from ..llm.token_optimizer import TokenOptimizer
from ..llm.context_selector import ContextSelector
from ..llm.hierarchical_formatter import HierarchicalFormatter

logger = logging.getLogger(__name__)


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
    centrality_breakdown: Dict[str, float]
    structural_impact: Dict[str, Any]


class LLMFileAnalyzer:
    """LLM-optimized file analyzer for comprehensive impact and centrality analysis."""

    centrality_calculator: Optional[CentralityCalculator]
    impact_analyzer: Optional[ImpactAnalyzer]

    def __init__(
        self,
        dependency_graph: Optional[AdvancedDependencyGraph] = None,
        project_root: Optional[str] = None,
        max_tokens: int = 4000,
    ):
        """Initialize the LLM file analyzer.

        Args:
            dependency_graph: Advanced dependency graph for analysis
            project_root: Root path of the project
            max_tokens: Maximum tokens for LLM-optimized output
        """
        self.dependency_graph = dependency_graph
        self.project_root = project_root
        self.max_tokens = max_tokens

        # Initialize components
        self.ast_analyzer = ASTFileAnalyzer(project_root)
        self.token_optimizer = TokenOptimizer()
        self.context_selector = ContextSelector(dependency_graph)
        self.hierarchical_formatter = HierarchicalFormatter()

        # Initialize analysis components if dependency graph is available
        if dependency_graph:
            self.centrality_calculator = CentralityCalculator(dependency_graph)
            self.impact_analyzer = ImpactAnalyzer(dependency_graph)
        else:
            self.centrality_calculator = None
            self.impact_analyzer = None

        logger.info(f"LLMFileAnalyzer initialized for project: {project_root}")

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
        logger.info(f"Analyzing impact for {len(file_paths)} files")

        # Resolve file paths relative to project root
        resolved_paths = []
        for file_path in file_paths:
            if os.path.isabs(file_path):
                resolved_paths.append(file_path)
            else:
                if self.project_root is None:
                    resolved_paths.append(file_path)
                else:
                    resolved_path = os.path.join(self.project_root, file_path)
                    resolved_paths.append(resolved_path)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for reverse dependency analysis
        all_files = self._get_all_project_files()

        # Analyze each file
        impact_analyses = []
        for i, file_path in enumerate(file_paths):
            resolved_path = resolved_paths[i]
            impact_analysis = self._analyze_single_file_impact(
                file_path, ast_results[resolved_path], all_files
            )
            impact_analyses.append(impact_analysis)

        # Format output
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return self._format_llm_optimized_impact(impact_analyses)
        elif format_type == AnalysisFormat.JSON:
            return self._format_json_impact(impact_analyses)
        elif format_type == AnalysisFormat.TABLE:
            return self._format_table_impact(impact_analyses)
        else:
            return self._format_text_impact(impact_analyses)

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
        logger.info(f"Analyzing centrality for {len(file_paths)} files")

        if not self.centrality_calculator:
            return "Centrality analysis requires dependency graph. Please run dependency analysis first."

        # Resolve file paths relative to project root
        resolved_paths = []
        for file_path in file_paths:
            if os.path.isabs(file_path):
                resolved_paths.append(file_path)
            else:
                if self.project_root is None:
                    resolved_paths.append(file_path)
                else:
                    resolved_path = os.path.join(self.project_root, file_path)
                    resolved_paths.append(resolved_path)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for comprehensive analysis
        all_files = self._get_all_project_files()

        # Analyze each file
        centrality_analyses = []
        for i, file_path in enumerate(file_paths):
            resolved_path = resolved_paths[i]
            centrality_analysis = self._analyze_single_file_centrality(
                file_path, ast_results[resolved_path], all_files
            )
            centrality_analyses.append(centrality_analysis)

        # Format output
        if format_type == AnalysisFormat.LLM_OPTIMIZED:
            return self._format_llm_optimized_centrality(centrality_analyses)
        elif format_type == AnalysisFormat.JSON:
            return self._format_json_centrality(centrality_analyses)
        elif format_type == AnalysisFormat.TABLE:
            return self._format_table_centrality(centrality_analyses)
        else:
            return self._format_text_centrality(centrality_analyses)

    def _analyze_single_file_impact(
        self, file_path: str, ast_result: FileAnalysisResult, all_files: List[str]
    ) -> FileImpactAnalysis:
        """Analyze impact for a single file.

        Args:
            file_path: Path to the file to analyze
            ast_result: AST analysis result for the file
            all_files: List of all files in the project

        Returns:
            FileImpactAnalysis object
        """
        # Direct dependencies (what this file imports)
        direct_dependencies = []
        for import_obj in ast_result.imports:
            # Determine what was imported
            imported = None
            if import_obj.symbols:
                imported = ", ".join(
                    import_obj.symbols
                )  # from module import symbol1, symbol2
            elif import_obj.alias:
                imported = f"{import_obj.module} as {import_obj.alias}"  # import module as alias
            else:
                imported = import_obj.module  # import module

            direct_dependencies.append(
                {
                    "file": import_obj.module,
                    "line": import_obj.line_number,
                    "imported": imported,
                    "type": import_obj.import_type.value,
                }
            )

        # Reverse dependencies (what imports this file)
        reverse_deps = self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
        reverse_dependencies = []
        for dep in reverse_deps:
            reverse_dependencies.append(
                {
                    "file": dep.source_file,
                    "line": dep.line_number,
                    "relationship": dep.relationship_type,
                    "details": dep.details,
                }
            )

        # Function call analysis
        function_call_analysis = []
        for func_call in ast_result.function_calls:
            function_call_analysis.append(
                {
                    "function": func_call.callee,
                    "line": func_call.line_number,
                    "is_method_call": func_call.is_method_call,
                    "object_name": func_call.object_name,
                }
            )

        # Structural impact
        structural_impact = {
            "total_imports": len(ast_result.imports),
            "total_function_calls": len(ast_result.function_calls),
            "defined_functions": len(ast_result.defined_functions),
            "defined_classes": len(ast_result.defined_classes),
            "line_count": ast_result.line_count,
        }

        # Risk assessment
        risk_assessment = {
            "high_import_count": len(ast_result.imports) > 10,
            "complex_function_calls": len(ast_result.function_calls) > 20,
            "many_dependents": len(reverse_dependencies) > 5,
            "analysis_errors": len(ast_result.analysis_errors) > 0,
        }

        # Suggested tests
        suggested_tests = self._suggest_test_files(file_path)

        return FileImpactAnalysis(
            file_path=file_path,
            direct_dependencies=direct_dependencies,
            reverse_dependencies=reverse_dependencies,
            function_call_analysis=function_call_analysis,
            structural_impact=structural_impact,
            risk_assessment=risk_assessment,
            suggested_tests=suggested_tests,
        )

    def _analyze_single_file_centrality(
        self, file_path: str, ast_result: FileAnalysisResult, all_files: List[str]
    ) -> FileCentralityAnalysis:
        """Analyze centrality for a single file.

        Args:
            file_path: Path to the file to analyze
            ast_result: AST analysis result for the file
            all_files: List of all files in the project

        Returns:
            FileCentralityAnalysis object
        """
        # Convert absolute path to relative path for dependency graph lookup
        if os.path.isabs(file_path) and self.project_root:
            try:
                relative_file_path = os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If paths are on different drives (Windows), use the original path
                relative_file_path = file_path
        else:
            relative_file_path = file_path

        # Calculate centrality score
        centrality_score = 0.0
        rank = 1
        total_files = 0
        all_scores = {}
        if self.centrality_calculator:
            all_scores = self.centrality_calculator.calculate_composite_importance()
            centrality_score = all_scores.get(relative_file_path, 0.0)
            total_files = len(all_scores) if all_scores else 0

            # Calculate rank
            if all_scores:
                sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
                for i, (fpath, score) in enumerate(sorted_scores, 1):
                    if fpath == relative_file_path:
                        rank = i
                        break
        
        # If centrality calculator failed or returned empty results, use fallback
        if total_files == 0:
            if self.dependency_graph and len(self.dependency_graph.nodes) > 0:
                total_files = len(self.dependency_graph.nodes)
            else:
                total_files = len(all_files) if all_files else 1

        # Dependency analysis - use dependency graph data when available
        if self.dependency_graph and relative_file_path in self.dependency_graph.nodes:
            node = self.dependency_graph.nodes[relative_file_path]
            direct_imports = len(node.imports) if node.imports else 0
            reverse_dependencies = len(node.imported_by) if node.imported_by else 0
            # Get actual lists for detailed analysis
            import_list = list(node.imports) if node.imports else []
            reverse_dep_list = list(node.imported_by) if node.imported_by else []
        else:
            # Fallback to AST results for Python files
            direct_imports = len(ast_result.imports)
            reverse_dep_relationships = self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
            reverse_dependencies = len(reverse_dep_relationships)
            import_list = [imp.module for imp in ast_result.imports] if ast_result.imports else []
            reverse_dep_list = [rel.source_file for rel in reverse_dep_relationships]
        
        dependency_analysis = {
            "direct_imports": direct_imports,
            "reverse_dependencies": reverse_dependencies,
            "total_connections": direct_imports + reverse_dependencies,
            "import_list": import_list[:15],  # Show more for LLM analysis
            "reverse_dep_list": reverse_dep_list,  # Show ALL inbound deps for LLM
            "import_list_truncated": len(import_list) > 15,
            "reverse_dep_list_truncated": False,  # Don't truncate inbound deps
        }

        # Function call analysis
        categorized_calls = self._smart_categorize_function_calls(
            ast_result.function_calls, ast_result.defined_functions, ast_result.imports, limit=5
        )
        function_call_analysis = {
            "total_calls": len(ast_result.function_calls),
            "internal_calls": categorized_calls["internal_count"],
            "external_calls": categorized_calls["external_count"],
            "defined_functions": len(ast_result.defined_functions),
            "most_called_function": self._find_most_called_function(
                ast_result.function_calls
            ),
            "top_called_functions": self._get_top_called_functions(
                ast_result.function_calls, limit=5
            ),
            "internal_functions": categorized_calls["internal"],
            "external_functions": categorized_calls["external"],
            "external_with_sources": categorized_calls["external_with_sources"],
            "most_used_class": self._find_most_used_class(ast_result.imports),
        }

        # Get actual centrality breakdown from calculator
        centrality_breakdown = {}
        if self.centrality_calculator:
            try:
                # Get individual centrality measures for this file
                degree_scores = self.centrality_calculator.calculate_degree_centrality()
                betweenness_scores = self.centrality_calculator.calculate_betweenness_centrality() 
                pagerank_scores = self.centrality_calculator.calculate_pagerank_centrality()
                
                # Only include metrics that were successfully calculated
                if degree_scores and relative_file_path in degree_scores:
                    centrality_breakdown["degree"] = degree_scores[relative_file_path]
                if betweenness_scores and relative_file_path in betweenness_scores:
                    centrality_breakdown["betweenness"] = betweenness_scores[relative_file_path]
                if pagerank_scores and relative_file_path in pagerank_scores:
                    centrality_breakdown["pagerank"] = pagerank_scores[relative_file_path]
                    
                # Try to get additional metrics if they work
                try:
                    eigenvector_scores = self.centrality_calculator.calculate_eigenvector_centrality()
                    if eigenvector_scores and relative_file_path in eigenvector_scores:
                        centrality_breakdown["eigenvector"] = eigenvector_scores[relative_file_path]
                except Exception as e:
                    logger.debug(f"Eigenvector centrality calculation failed: {e}")
                    
                try:
                    closeness_scores = self.centrality_calculator.calculate_closeness_centrality()
                    if closeness_scores and relative_file_path in closeness_scores:
                        centrality_breakdown["closeness"] = closeness_scores[relative_file_path]
                except Exception as e:
                    logger.debug(f"Closeness centrality calculation failed: {e}")
                    
            except Exception as e:
                logger.warning(f"Error calculating detailed centrality breakdown: {e}")
                # Fallback to simplified calculation
                centrality_breakdown = {
                    "degree": centrality_score * 0.4,
                    "betweenness": centrality_score * 0.3,
                    "pagerank": centrality_score * 0.3,
                }
        else:
            # Fallback when no centrality calculator available
            centrality_breakdown = {
                "degree": centrality_score * 0.4,
                "betweenness": centrality_score * 0.3, 
                "pagerank": centrality_score * 0.3,
            }

        # Structural impact - use dependency graph data when available
        if self.dependency_graph and relative_file_path in self.dependency_graph.nodes:
            node = self.dependency_graph.nodes[relative_file_path]
            files_affected = len(node.imported_by) if node.imported_by else 0
        else:
            # Fallback to AST results for Python files
            files_affected = len(
                self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
            )
        
        structural_impact = {
            "if_file_changes": files_affected,
            "if_functions_change": len(ast_result.defined_functions),
            "if_classes_change": len(ast_result.defined_classes),
        }

        return FileCentralityAnalysis(
            file_path=file_path,
            centrality_score=centrality_score,
            rank=rank,
            total_files=total_files,
            dependency_analysis=dependency_analysis,
            function_call_analysis=function_call_analysis,
            centrality_breakdown=centrality_breakdown,
            structural_impact=structural_impact,
        )

    def _format_llm_optimized_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis for LLM consumption.

        Args:
            analyses: List of FileImpactAnalysis objects

        Returns:
            LLM-optimized formatted string
        """
        if len(analyses) == 1:
            return self._format_single_file_impact_llm(analyses[0])
        else:
            return self._format_multiple_files_impact_llm(analyses)

    def _format_single_file_impact_llm(self, analysis: FileImpactAnalysis) -> str:
        """Format single file impact analysis for LLM."""
        output = []
        file_name = Path(analysis.file_path).name

        output.append(f"=== Impact Analysis: {file_name} ===")
        output.append("")

        # Direct dependencies
        output.append("DIRECT DEPENDENCIES (what this file imports/calls):")
        for dep in analysis.direct_dependencies[:10]:  # Limit for token budget
            output.append(f"├── {dep['file']}:{dep['line']} (import {dep['imported']})")
        if len(analysis.direct_dependencies) > 10:
            output.append(f"└── ... and {len(analysis.direct_dependencies) - 10} more")
        output.append("")

        # Reverse dependencies
        output.append("REVERSE DEPENDENCIES (what imports/calls this file):")
        for dep in analysis.reverse_dependencies[:10]:  # Limit for token budget
            output.append(
                f"├── {Path(dep['file']).name}:{dep['line']} ({dep['relationship']})"
            )
        if len(analysis.reverse_dependencies) > 10:
            output.append(f"└── ... and {len(analysis.reverse_dependencies) - 10} more")
        output.append("")

        # Function call analysis
        if analysis.function_call_analysis:
            output.append("FUNCTION CALL ANALYSIS:")
            for call in analysis.function_call_analysis[:5]:  # Limit for token budget
                output.append(f"├── {call['function']}() called at line {call['line']}")
            if len(analysis.function_call_analysis) > 5:
                output.append(
                    f"└── ... and {len(analysis.function_call_analysis) - 5} more calls"
                )
            output.append("")

        # Structural impact
        output.append("STRUCTURAL IMPACT (if function signatures change):")
        output.append(
            f"├── If functions change → {analysis.structural_impact['defined_functions']} functions affected"
        )
        output.append(
            f"├── If classes change → {analysis.structural_impact['defined_classes']} classes affected"
        )
        output.append(
            f"└── Total dependents → {len(analysis.reverse_dependencies)} files potentially affected"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_multiple_files_impact_llm(
        self, analyses: List[FileImpactAnalysis]
    ) -> str:
        """Format multiple files impact analysis for LLM."""
        output = []

        output.append(
            f"=== Impact Analysis: {', '.join(Path(a.file_path).name for a in analyses)} ==="
        )
        output.append("")

        output.append("FILES ANALYZED:")
        for analysis in analyses:
            output.append(f"├── {Path(analysis.file_path).name}")
        output.append("")

        # Combined dependencies
        all_direct_deps: Set[str] = set()
        all_reverse_deps: Set[str] = set()

        for analysis in analyses:
            for dep in analysis.direct_dependencies:
                all_direct_deps.add(dep["file"])
            for dep in analysis.reverse_dependencies:
                all_reverse_deps.add(Path(dep["file"]).name)

        output.append("COMBINED DEPENDENCIES:")
        for dep_name in list(all_direct_deps)[:10]:
            output.append(f"├── {dep_name}")
        if len(all_direct_deps) > 10:
            output.append(f"└── ... and {len(all_direct_deps) - 10} more")
        output.append("")

        output.append("COMBINED REVERSE DEPENDENCIES:")
        for dep_name in list(all_reverse_deps)[:10]:
            output.append(f"├── {dep_name}")
        if len(all_reverse_deps) > 10:
            output.append(f"└── ... and {len(all_reverse_deps) - 10} more")

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_llm_optimized_centrality(
        self, analyses: List[FileCentralityAnalysis]
    ) -> str:
        """Format centrality analysis for LLM consumption."""
        if len(analyses) == 1:
            return self._format_single_file_centrality_llm(analyses[0])
        else:
            return self._format_multiple_files_centrality_llm(analyses)

    def _format_single_file_centrality_llm(
        self, analysis: FileCentralityAnalysis
    ) -> str:
        """Format single file centrality analysis for LLM."""
        output = []
        file_name = Path(analysis.file_path).name

        output.append(f"=== Centrality Analysis: {file_name} ===")
        output.append("")

        output.append(
            f"📊 IMPORTANCE SCORE: {analysis.centrality_score:.3f}/1.0 (Rank: {analysis.rank}/{analysis.total_files})"
        )
        output.append("")

        # Dependency analysis
        output.append("🔗 FILE CONNECTIONS:")
        output.append(
            f"├── Files this imports from: {analysis.dependency_analysis['direct_imports']} files"
        )
        output.append(
            f"├── Files that import this: {analysis.dependency_analysis['reverse_dependencies']} files"
        )
        output.append(
            f"└── Total connections: {analysis.dependency_analysis['total_connections']}"
        )
        output.append("")
        
        # Show actual dependency lists if available
        import_list = analysis.dependency_analysis.get('import_list', [])
        reverse_dep_list = analysis.dependency_analysis.get('reverse_dep_list', [])
        
        if import_list:
            output.append("📤 OUTBOUND DEPENDENCIES (imports):")
            for i, dep in enumerate(import_list):
                # Convert to relative path for cleaner display
                dep_display = Path(dep).name if dep else dep
                prefix = "├──" if i < len(import_list) - 1 else "└──"
                output.append(f"│   {prefix} {dep_display}")
            if analysis.dependency_analysis.get('import_list_truncated'):
                output.append(f"│   └── ... and {analysis.dependency_analysis['direct_imports'] - len(import_list)} more")
            output.append("")
            
        if reverse_dep_list:
            output.append("📥 INBOUND DEPENDENCIES (files that import this):")
            
            # Group dependencies by directory for better organization
            deps_by_dir = {}
            for dep in reverse_dep_list:
                # Show relative path with context
                if dep.startswith(self.project_root):
                    dep_relative = os.path.relpath(dep, self.project_root)
                else:
                    dep_relative = dep
                
                # Extract meaningful directory context
                parts = Path(dep_relative).parts
                if len(parts) > 1:
                    dir_path = str(Path(*parts[:-1]))  # Directory path
                    filename = parts[-1]  # Just filename
                else:
                    dir_path = "."
                    filename = dep_relative
                
                if dir_path not in deps_by_dir:
                    deps_by_dir[dir_path] = []
                deps_by_dir[dir_path].append((dep, filename))
            
            # Display grouped dependencies
            dir_count = 0
            total_dirs = len(deps_by_dir)
            
            for dir_path, files in deps_by_dir.items():
                dir_count += 1
                dir_prefix = "├──" if dir_count < total_dirs else "└──"
                
                if len(files) == 1:
                    # Single file in directory - show inline
                    dep, filename = files[0]
                    if dir_path == ".":
                        output.append(f"│   {dir_prefix} {filename}")
                    else:
                        output.append(f"│   {dir_prefix} {dir_path}/{filename}")
                else:
                    # Multiple files in directory - group them
                    output.append(f"│   {dir_prefix} {dir_path}/ ({len(files)} files)")
                    for j, (dep, filename) in enumerate(files):
                        file_prefix = "├──" if j < len(files) - 1 else "└──"
                        output.append(f"│   │   {file_prefix} {filename}")
                        
                        # Add function call details if available (but only for first few to avoid clutter)
                        if j < 3:  # Show function calls for first 3 files per directory
                            called_functions = self._get_functions_called_from_file(dep, analysis.file_path)
                            if called_functions:
                                func_list = ", ".join(called_functions[:2])  # Show top 2 functions
                                if len(called_functions) > 2:
                                    func_list += f" (+{len(called_functions)-2} more)"
                                output.append(f"│   │       └── calls: {func_list}")
            
            output.append("")

        # Function call analysis
        output.append("⚙️ FUNCTION USAGE:")
        
        total_calls = analysis.function_call_analysis['total_calls']
        internal_calls = analysis.function_call_analysis.get('internal_calls', 0)
        external_calls = analysis.function_call_analysis.get('external_calls', 0)
        
        output.append(f"├── Total function calls: {total_calls}")
        output.append(f"├── Internal calls: {internal_calls} ({internal_calls/total_calls*100:.1f}%)" if total_calls > 0 else "├── Internal calls: 0")
        output.append(f"├── External calls: {external_calls} ({external_calls/total_calls*100:.1f}%)" if total_calls > 0 else "├── External calls: 0") 
        output.append(f"├── Functions defined: {analysis.function_call_analysis['defined_functions']}")
        
        # Show internal functions (calls to functions defined in this file)
        internal_functions = analysis.function_call_analysis.get("internal_functions", [])
        external_with_sources = analysis.function_call_analysis.get("external_with_sources", [])
        
        if internal_functions:
            output.append("├── 🏠 Internal calls (business logic):")
            for i, (func_name, count) in enumerate(internal_functions):
                # Calculate importance based on call frequency
                importance = "🔥" if count >= 3 else "⚡" if count >= 2 else "📋"
                prefix = "│   ├──" if i < len(internal_functions) - 1 else "│   └──"
                output.append(f"{prefix} {importance} {func_name} ({count}x)")
        
        if external_with_sources:
            # Filter external calls to focus on business logic
            business_relevant_calls = self._filter_business_relevant_calls(external_with_sources)
            
            if business_relevant_calls:
                is_last_section = not internal_functions
                section_prefix = "└──" if is_last_section else "├──"
                output.append(f"{section_prefix} 🌐 External calls (business logic):")
                
                for i, (func_name, count, source) in enumerate(business_relevant_calls):
                    if is_last_section:
                        prefix = "    ├──" if i < len(business_relevant_calls) - 1 else "    └──"
                    else:
                        prefix = "│   ├──" if i < len(business_relevant_calls) - 1 else "│   └──"
                    
                    # Color-code by dependency type
                    if "(built-in)" in source:
                        dep_type = "🔧"  # Built-in
                    elif "unknown" in source:
                        dep_type = "❓"  # Unknown
                    else:
                        dep_type = "📦"  # Import
                    
                    output.append(f"{prefix} {dep_type} {func_name} ({count}x) → {source}")
                
                # Show summary of filtered calls
                filtered_count = len(external_with_sources) - len(business_relevant_calls)
                if filtered_count > 0:
                    if is_last_section:
                        output.append(f"        └── ({filtered_count} low-level utility calls hidden)")
                    else:
                        output.append(f"│       └── ({filtered_count} low-level utility calls hidden)")
        
        # If no categorized data available, fall back to top functions
        if not internal_functions and not external_with_sources:
            top_functions = analysis.function_call_analysis.get("top_called_functions", [])
            if top_functions:
                output.append("└── Most called functions:")
                for i, (func_name, count) in enumerate(top_functions):
                    prefix = "    ├──" if i < len(top_functions) - 1 else "    └──"
                    output.append(f"{prefix} {func_name} ({count}x)")
        
        output.append("")

        # Centrality breakdown with user-friendly terms
        output.append("📈 IMPORTANCE METRICS (0.0 = low, 1.0 = high):")
        
        # Map technical terms to user-friendly ones with explanations
        metric_info = {
            'degree': ('Connection Count', 'how many files this connects to'),
            'betweenness': ('Bridge Factor', 'how often this file sits between others'), 
            'pagerank': ('Influence Score', 'overall influence in the codebase'),
            'eigenvector': ('Network Authority', 'connections to other important files'),
            'closeness': ('Accessibility', 'how easily reachable from other files')
        }
        
        metric_count = 0
        total_metrics = len(analysis.centrality_breakdown)
        
        for metric, score in analysis.centrality_breakdown.items():
            metric_count += 1
            if metric in metric_info:
                name, explanation = metric_info[metric]
                prefix = "├──" if metric_count < total_metrics else "├──"
                output.append(f"{prefix} {name}: {score:.3f} ({explanation})")
            else:
                # Fallback for any new metrics
                fallback_name = metric.replace('_', ' ').title()
                prefix = "├──" if metric_count < total_metrics else "├──"
                output.append(f"{prefix} {fallback_name}: {score:.3f}")
            
        output.append(f"└── Overall Importance: {analysis.centrality_score:.3f}")
        output.append("")

        # Structural impact
        output.append("💥 CHANGE IMPACT:")
        output.append(
            f"├── If this file changes → {analysis.structural_impact['if_file_changes']} files potentially affected"
        )
        output.append(
            f"├── If functions change → {analysis.structural_impact['if_functions_change']} functions affected"
        )
        output.append(
            f"└── If classes change → {analysis.structural_impact['if_classes_change']} classes affected"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_multiple_files_centrality_llm(
        self, analyses: List[FileCentralityAnalysis]
    ) -> str:
        """Format multiple files centrality analysis for LLM."""
        output = []

        output.append(
            f"=== Centrality Analysis: {', '.join(Path(a.file_path).name for a in analyses)} ==="
        )
        output.append("")

        # Sort by centrality score
        sorted_analyses = sorted(
            analyses, key=lambda x: x.centrality_score, reverse=True
        )

        output.append("CENTRALITY RANKINGS:")
        for i, analysis in enumerate(sorted_analyses, 1):
            file_name = Path(analysis.file_path).name
            output.append(
                f"{i}. {file_name}: {analysis.centrality_score:.3f} (rank {analysis.rank})"
            )
        output.append("")

        # Combined analysis
        total_connections = sum(
            a.dependency_analysis["total_connections"] for a in analyses
        )
        total_functions = sum(
            a.function_call_analysis["defined_functions"] for a in analyses
        )

        output.append("COMBINED ANALYSIS:")
        output.append(f"├── Total connections: {total_connections}")
        output.append(f"├── Total defined functions: {total_functions}")
        output.append(
            f"└── Average centrality: {sum(a.centrality_score for a in analyses) / len(analyses):.3f}"
        )

        # Optimize for token budget
        result = "\n".join(output)
        return self.token_optimizer.optimize_for_token_budget(result, self.max_tokens)

    def _format_json_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as JSON."""
        import json

        data = []
        for analysis in analyses:
            data.append(
                {
                    "file_path": analysis.file_path,
                    "direct_dependencies": analysis.direct_dependencies,
                    "reverse_dependencies": analysis.reverse_dependencies,
                    "function_call_analysis": analysis.function_call_analysis,
                    "structural_impact": analysis.structural_impact,
                    "risk_assessment": analysis.risk_assessment,
                    "suggested_tests": analysis.suggested_tests,
                }
            )
        return json.dumps(data, indent=2)

    def _format_json_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as JSON."""
        import json

        data = []
        for analysis in analyses:
            data.append(
                {
                    "file_path": analysis.file_path,
                    "centrality_score": analysis.centrality_score,
                    "rank": analysis.rank,
                    "total_files": analysis.total_files,
                    "dependency_analysis": analysis.dependency_analysis,
                    "function_call_analysis": analysis.function_call_analysis,
                    "centrality_breakdown": analysis.centrality_breakdown,
                    "structural_impact": analysis.structural_impact,
                }
            )
        return json.dumps(data, indent=2)

    def _format_table_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as table."""
        # This would use Rich tables - simplified for now
        output = []
        for analysis in analyses:
            file_name = Path(analysis.file_path).name
            output.append(f"File: {file_name}")
            output.append(f"  Direct Dependencies: {len(analysis.direct_dependencies)}")
            output.append(
                f"  Reverse Dependencies: {len(analysis.reverse_dependencies)}"
            )
            output.append(f"  Function Calls: {len(analysis.function_call_analysis)}")
            output.append("")
        return "\n".join(output)

    def _format_table_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as table."""
        # This would use Rich tables - simplified for now
        output = []
        for analysis in analyses:
            file_name = Path(analysis.file_path).name
            output.append(f"File: {file_name}")
            output.append(f"  Centrality Score: {analysis.centrality_score:.3f}")
            output.append(f"  Rank: {analysis.rank}/{analysis.total_files}")
            output.append(
                f"  Total Connections: {analysis.dependency_analysis['total_connections']}"
            )
            output.append("")
        return "\n".join(output)

    def _format_text_impact(self, analyses: List[FileImpactAnalysis]) -> str:
        """Format impact analysis as plain text."""
        return self._format_llm_optimized_impact(analyses)

    def _format_text_centrality(self, analyses: List[FileCentralityAnalysis]) -> str:
        """Format centrality analysis as plain text."""
        return self._format_llm_optimized_centrality(analyses)

    def _get_all_project_files(self) -> List[str]:
        """Get all files in the project for analysis."""
        if not self.project_root:
            return []

        project_path = Path(self.project_root)
        python_files = []

        for py_file in project_path.rglob("*.py"):
            if not any(part.startswith(".") for part in py_file.parts):
                python_files.append(str(py_file))

        return python_files

    def _suggest_test_files(self, file_path: str) -> List[str]:
        """Suggest test files for a given file."""
        # Simplified test file suggestion
        file_path_obj = Path(file_path)
        test_files = []

        # Look for test files in common locations
        test_patterns = [
            f"test_{file_path_obj.stem}.py",
            f"{file_path_obj.stem}_test.py",
        ]

        for pattern in test_patterns:
            # Check in tests directory
            test_file = file_path_obj.parent / "tests" / pattern
            if test_file.exists():
                test_files.append(str(test_file))

            # Check in parent tests directory
            test_file = file_path_obj.parent.parent / "tests" / pattern
            if test_file.exists():
                test_files.append(str(test_file))

        return test_files

    def _find_most_called_function(self, function_calls: List[Any]) -> Optional[str]:
        """Find the most frequently called function."""
        if not function_calls:
            return None

        call_counts: Dict[str, int] = {}
        for call in function_calls:
            func_name = call.callee
            call_counts[func_name] = call_counts.get(func_name, 0) + 1

        return max(call_counts.items(), key=lambda x: x[1])[0] if call_counts else None

    def _get_top_called_functions(self, function_calls: List[Any], limit: int = 5) -> List[Tuple[str, int]]:
        """Get the top N most frequently called functions with their call counts."""
        if not function_calls:
            return []

        call_counts: Dict[str, int] = {}
        for call in function_calls:
            func_name = call.callee
            call_counts[func_name] = call_counts.get(func_name, 0) + 1

        # Sort by call count (descending) and return top N
        sorted_calls = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_calls[:limit]

    def _smart_categorize_function_calls(self, function_calls: List[Any], defined_functions: List[str], imports: List[Any], limit: int = 5) -> Dict[str, Any]:
        """Smart categorization that infers sources rather than hardcoding them."""
        if not function_calls:
            return {
                "internal": [], 
                "external": [], 
                "internal_count": 0, 
                "external_count": 0,
                "external_with_sources": []
            }

        internal_counts: Dict[str, int] = {}
        external_counts: Dict[str, int] = {}
        
        # Convert defined_functions to a set for faster lookup
        defined_funcs_set = set(defined_functions)
        
        # Build import mapping
        import_sources: Dict[str, str] = {}
        for imp in imports:
            if hasattr(imp, 'symbols') and imp.symbols:
                for symbol in imp.symbols:
                    import_sources[symbol] = imp.module
            if hasattr(imp, 'module'):
                module_name = imp.module.split('/')[-1] if '/' in imp.module else imp.module
                import_sources[module_name] = imp.module

        # Categorize calls
        for call in function_calls:
            func_name = call.callee
            if func_name in defined_funcs_set:
                internal_counts[func_name] = internal_counts.get(func_name, 0) + 1
            else:
                external_counts[func_name] = external_counts.get(func_name, 0) + 1

        # Sort and limit
        internal_sorted = sorted(internal_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        external_sorted = sorted(external_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        # Smart source detection for external functions
        external_with_sources = []
        for func_name, count in external_sorted:
            source = self._infer_function_source(func_name, import_sources)
            external_with_sources.append((func_name, count, source))

        return {
            "internal": internal_sorted,
            "external": external_sorted,
            "internal_count": sum(internal_counts.values()),
            "external_count": sum(external_counts.values()), 
            "external_with_sources": external_with_sources
        }
    
    def _infer_function_source(self, func_name: str, import_sources: Dict[str, str]) -> str:
        """Language-agnostic function source inference based on imports and patterns."""
        
        # 1. EXPLICIT IMPORTS (Most reliable - works for any language)
        if func_name in import_sources:
            return import_sources[func_name]
        
        # 2. FUZZY IMPORT MATCHING (Language-agnostic)
        # Check if function name is contained in any imported module/symbol
        for symbol, module in import_sources.items():
            # Direct substring match
            if func_name.lower() in symbol.lower() or symbol.lower() in func_name.lower():
                return f"{module} (via {symbol})"
            
            # Module name matching (e.g., 'log' from imported 'console')
            module_base = module.split('/')[-1].split('.')[0]  # Extract base name
            if func_name.lower() in module_base.lower() or module_base.lower() in func_name.lower():
                return f"{module} (module method)"
        
        # 3. NAMING PATTERN ANALYSIS (Language-agnostic)
        
        # Common cross-language patterns
        if any(pattern in func_name.lower() for pattern in ['log', 'print', 'debug', 'warn', 'error']):
            return "logging/output"
        
        if any(pattern in func_name.lower() for pattern in ['push', 'add', 'append', 'insert']):
            return "collection mutation"
            
        if any(pattern in func_name.lower() for pattern in ['map', 'filter', 'reduce', 'transform']):
            return "collection processing"
            
        if any(pattern in func_name.lower() for pattern in ['get', 'fetch', 'retrieve', 'find']):
            return "data access"
            
        if any(pattern in func_name.lower() for pattern in ['set', 'update', 'modify', 'change']):
            return "data mutation"
            
        if any(pattern in func_name.lower() for pattern in ['emit', 'trigger', 'fire', 'dispatch']):
            return "event system"
            
        if any(pattern in func_name.lower() for pattern in ['async', 'await', 'promise', 'future']):
            return "async/concurrency"
            
        if any(pattern in func_name.lower() for pattern in ['parse', 'serialize', 'stringify', 'encode', 'decode']):
            return "data serialization"
            
        if any(pattern in func_name.lower() for pattern in ['validate', 'check', 'verify', 'test']):
            return "validation/testing"
        
        # 4. CAPITALIZATION PATTERNS (Language-agnostic)
        
        # Constructor pattern (PascalCase)
        if func_name and func_name[0].isupper() and not func_name.isupper():
            return "constructor/class"
            
        # Constant pattern (UPPER_CASE)
        if func_name.isupper() and '_' in func_name:
            return "constant/enum"
            
        # Method pattern (camelCase starting with lowercase)
        if func_name and func_name[0].islower() and any(c.isupper() for c in func_name):
            return "method/function"
        
        # 5. STRUCTURAL PATTERNS
        
        # Compound names suggest external libraries
        if len(func_name.split('_')) > 2 or len([c for c in func_name if c.isupper()]) > 2:
            return "external library"
            
        # Short names often indicate built-ins or common utilities
        if len(func_name) <= 3:
            return "built-in/utility"
        
        # 6. FALLBACK - Unknown but categorized
        return "external (unknown)"

    def _filter_business_relevant_calls(self, external_with_sources: List[Tuple[str, int, str]]) -> List[Tuple[str, int, str]]:
        """Filter external function calls to show only business-relevant ones."""
        
        # Define patterns for low-level utility calls to filter out
        utility_patterns = {
            # Basic logging/debugging
            'log', 'warn', 'error', 'info', 'debug', 'trace', 'console',
            
            # Basic data types and constructors
            'Error', 'Date', 'Array', 'Object', 'Map', 'Set', 'Promise', 'RegExp',
            
            # Primitive operations
            'now', 'getTime', 'toString', 'valueOf', 'hasOwnProperty',
            'push', 'pop', 'slice', 'join', 'split', 'trim', 'length',
            
            # Basic serialization
            'stringify', 'parse', 'JSON',
            
            # Basic math/comparison
            'Math', 'ceil', 'floor', 'round', 'abs', 'max', 'min',
            
            # Basic control flow utilities
            'setTimeout', 'setInterval', 'clearTimeout', 'clearInterval',
            
            # Basic type checking
            'isNaN', 'isFinite', 'parseInt', 'parseFloat',
            
            # Basic string operations
            'substring', 'indexOf', 'replace', 'toLowerCase', 'toUpperCase',
            
            # Basic validation/guards
            'assert', 'check', 'validate' # Only if very generic
        }
        
        # Additional filtering based on source
        def is_business_relevant(func_name: str, source: str) -> bool:
            # Always include if it's from an explicit import (not a built-in)
            if "built-in" not in source and "external (unknown)" not in source:
                # But still filter out obvious utility functions even from imports
                if func_name.lower() in utility_patterns:
                    return False
                return True
            
            # For built-ins and unknowns, be more selective
            if func_name.lower() in utility_patterns:
                return False
                
            # Keep functions that suggest business logic
            business_keywords = [
                'task', 'message', 'command', 'execute', 'process', 'handle',
                'create', 'update', 'delete', 'save', 'load', 'fetch', 'send',
                'validate', 'transform', 'generate', 'analyze', 'calculate',
                'request', 'response', 'session', 'user', 'auth', 'config',
                'emit', 'trigger', 'dispatch', 'subscribe', 'publish',
                'start', 'stop', 'pause', 'resume', 'cancel', 'complete',
                'migrate', 'backup', 'restore', 'sync', 'connect', 'disconnect'
            ]
            
            func_lower = func_name.lower()
            if any(keyword in func_lower for keyword in business_keywords):
                return True
                
            # Keep functions with meaningful names (longer than 3 chars, not all lowercase)
            if len(func_name) > 3 and not func_name.islower():
                return True
                
            return False
        
        # Filter the calls
        filtered_calls = []
        for func_name, count, source in external_with_sources:
            if is_business_relevant(func_name, source):
                filtered_calls.append((func_name, count, source))
        
        return filtered_calls

    def _get_functions_called_from_file(self, calling_file: str, target_file: str) -> List[str]:
        """Get list of functions that calling_file calls from target_file."""
        try:
            # Analyze the calling file to find function calls
            result = self.ast_analyzer.analyze_file(calling_file, AnalysisType.ALL)
            if not result or not result.function_calls:
                return []
            
            # Get functions defined in target file for reference
            target_result = self.ast_analyzer.analyze_file(target_file, AnalysisType.ALL)
            if not target_result or not target_result.defined_functions:
                return []
            
            target_functions = set(target_result.defined_functions)
            
            # Find calls that match functions defined in target file
            called_functions = []
            for call in result.function_calls:
                if hasattr(call, 'callee') and call.callee in target_functions:
                    called_functions.append(call.callee)
            
            # Count and return most frequently called functions
            from collections import Counter
            call_counts = Counter(called_functions)
            return [func for func, count in call_counts.most_common(5)]
            
        except Exception as e:
            # Silently fail to avoid disrupting main analysis
            return []

    def _find_most_used_class(self, imports: List[Any]) -> Optional[str]:
        """Find the most frequently imported class."""
        if not imports:
            return None

        class_counts: Dict[str, int] = {}
        for import_obj in imports:
            # Check if any imported symbols are classes (start with uppercase)
            if import_obj.symbols:
                for symbol in import_obj.symbols:
                    if symbol[0].isupper():
                        class_counts[symbol] = class_counts.get(symbol, 0) + 1
            elif import_obj.alias and import_obj.alias[0].isupper():
                class_counts[import_obj.alias] = (
                    class_counts.get(import_obj.alias, 0) + 1
                )

        return (
            max(class_counts.items(), key=lambda x: x[1])[0] if class_counts else None
        )
