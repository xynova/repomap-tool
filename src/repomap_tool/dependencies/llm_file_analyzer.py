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
                resolved_path = os.path.join(self.project_root, file_path)
                resolved_paths.append(resolved_path)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for reverse dependency analysis
        all_files = self._get_all_project_files()

        # Analyze each file
        impact_analyses = []
        for file_path in file_paths:
            impact_analysis = self._analyze_single_file_impact(
                file_path, ast_results[file_path], all_files
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
                resolved_path = os.path.join(self.project_root, file_path)
                resolved_paths.append(resolved_path)

        # Perform AST analysis for all files
        ast_results = self.ast_analyzer.analyze_multiple_files(resolved_paths)

        # Get all files in project for comprehensive analysis
        all_files = self._get_all_project_files()

        # Analyze each file
        centrality_analyses = []
        for file_path in file_paths:
            centrality_analysis = self._analyze_single_file_centrality(
                file_path, ast_results[file_path], all_files
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
        # Calculate centrality score
        centrality_score = 0.0
        rank = 1
        all_scores = {}
        if self.centrality_calculator:
            all_scores = (
                self.centrality_calculator.calculate_composite_importance()
            )
            centrality_score = all_scores.get(file_path, 0.0)

            # Calculate rank
            sorted_scores = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
            for i, (fpath, score) in enumerate(sorted_scores, 1):
                if fpath == file_path:
                    rank = i
                    break

        # Dependency analysis
        dependency_analysis = {
            "direct_imports": len(ast_result.imports),
            "reverse_dependencies": len(
                self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
            ),
            "total_connections": len(ast_result.imports)
            + len(self.ast_analyzer.find_reverse_dependencies(file_path, all_files)),
        }

        # Function call analysis
        function_call_analysis = {
            "total_calls": len(ast_result.function_calls),
            "defined_functions": len(ast_result.defined_functions),
            "most_called_function": self._find_most_called_function(
                ast_result.function_calls
            ),
            "most_used_class": self._find_most_used_class(ast_result.imports),
        }

        # Centrality breakdown (simplified)
        centrality_breakdown = {
            "degree_centrality": centrality_score * 0.4,  # Simplified calculation
            "betweenness_centrality": centrality_score * 0.3,
            "pagerank": centrality_score * 0.3,
        }

        # Structural impact
        structural_impact = {
            "if_file_changes": len(
                self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
            ),
            "if_functions_change": len(ast_result.defined_functions),
            "if_classes_change": len(ast_result.defined_classes),
        }

        return FileCentralityAnalysis(
            file_path=file_path,
            centrality_score=centrality_score,
            rank=rank,
            total_files=len(all_files),
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
        all_direct_deps = set()
        all_reverse_deps = set()

        for analysis in analyses:
            for dep in analysis.direct_dependencies:
                all_direct_deps.add(dep["file"])
            for dep in analysis.reverse_dependencies:
                all_reverse_deps.add(Path(dep["file"]).name)

        output.append("COMBINED DEPENDENCIES:")
        for dep in list(all_direct_deps)[:10]:
            output.append(f"├── {dep}")
        if len(all_direct_deps) > 10:
            output.append(f"└── ... and {len(all_direct_deps) - 10} more")
        output.append("")

        output.append("COMBINED REVERSE DEPENDENCIES:")
        for dep in list(all_reverse_deps)[:10]:
            output.append(f"├── {dep}")
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
            f"CENTRALITY SCORE: {analysis.centrality_score:.3f} (Rank: {analysis.rank}/{analysis.total_files})"
        )
        output.append("")

        # Dependency analysis
        output.append("DEPENDENCY ANALYSIS:")
        output.append(
            f"├── Direct imports: {analysis.dependency_analysis['direct_imports']} files"
        )
        output.append(
            f"├── Direct dependents: {analysis.dependency_analysis['reverse_dependencies']} files"
        )
        output.append(
            f"└── Total connections: {analysis.dependency_analysis['total_connections']}"
        )
        output.append("")

        # Function call analysis
        output.append("FUNCTION CALL ANALYSIS:")
        output.append(
            f"├── Total function calls: {analysis.function_call_analysis['total_calls']}"
        )
        output.append(
            f"├── Defined functions: {analysis.function_call_analysis['defined_functions']}"
        )
        if analysis.function_call_analysis["most_called_function"]:
            output.append(
                f"└── Most called function: {analysis.function_call_analysis['most_called_function']}"
            )
        output.append("")

        # Centrality breakdown
        output.append("CENTRALITY BREAKDOWN:")
        for metric, score in analysis.centrality_breakdown.items():
            output.append(f"├── {metric}: {score:.3f}")
        output.append(f"└── Composite score: {analysis.centrality_score:.3f}")
        output.append("")

        # Structural impact
        output.append("STRUCTURAL IMPACT:")
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

        call_counts = {}
        for call in function_calls:
            func_name = call.callee
            call_counts[func_name] = call_counts.get(func_name, 0) + 1

        return max(call_counts.items(), key=lambda x: x[1])[0] if call_counts else None

    def _find_most_used_class(self, imports: List[Any]) -> Optional[str]:
        """Find the most frequently imported class."""
        if not imports:
            return None

        class_counts = {}
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
