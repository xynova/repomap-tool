"""
Impact analysis engine for file-level impact assessment.

This module provides comprehensive impact analysis for files, including
direct dependencies, reverse dependencies, function call analysis,
structural impact, and risk assessment.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from .ast_file_analyzer import ASTFileAnalyzer, FileAnalysisResult
from .file_utils import suggest_test_files
from .models import FileImpactAnalysis

logger = logging.getLogger(__name__)


class ImpactAnalysisEngine:
    """Engine for analyzing file impact and dependencies."""

    def __init__(self, ast_analyzer: ASTFileAnalyzer):
        """Initialize the impact analysis engine.

        Args:
            ast_analyzer: AST file analyzer instance
        """
        self.ast_analyzer = ast_analyzer

    def analyze_file_impact(
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
        direct_dependencies = self._analyze_direct_dependencies(ast_result.imports)

        # Reverse dependencies (what imports this file)
        reverse_dependencies = self._analyze_reverse_dependencies(file_path, all_files)

        # Function call analysis
        function_call_analysis = self._analyze_function_calls(ast_result.function_calls)

        # Structural impact
        structural_impact = self._calculate_structural_impact(ast_result)

        # Risk assessment
        risk_assessment = self._assess_risk(ast_result, reverse_dependencies)

        # Suggested tests
        suggested_tests = suggest_test_files(file_path)

        return FileImpactAnalysis(
            file_path=file_path,
            direct_dependencies=direct_dependencies,
            reverse_dependencies=reverse_dependencies,
            function_call_analysis=function_call_analysis,
            structural_impact=structural_impact,
            risk_assessment=risk_assessment,
            suggested_tests=suggested_tests,
        )

    def _analyze_direct_dependencies(self, imports: List[Any]) -> List[Dict[str, Any]]:
        """Analyze direct dependencies from imports.

        Args:
            imports: List of import objects

        Returns:
            List of dependency dictionaries
        """
        direct_dependencies = []
        for import_obj in imports:
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
        return direct_dependencies

    def _analyze_reverse_dependencies(
        self, file_path: str, all_files: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze reverse dependencies (what imports this file).

        Args:
            file_path: Path to the file
            all_files: List of all files in the project

        Returns:
            List of reverse dependency dictionaries
        """
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
        return reverse_dependencies

    def _analyze_function_calls(
        self, function_calls: List[Any]
    ) -> List[Dict[str, Any]]:
        """Analyze function calls in the file.

        Args:
            function_calls: List of function call objects

        Returns:
            List of function call analysis dictionaries
        """
        function_call_analysis = []
        for func_call in function_calls:
            function_call_analysis.append(
                {
                    "function": func_call.callee,
                    "line": func_call.line_number,
                    "is_method_call": func_call.is_method_call,
                    "object_name": func_call.object_name,
                }
            )
        return function_call_analysis

    def _calculate_structural_impact(
        self, ast_result: FileAnalysisResult
    ) -> Dict[str, Any]:
        """Calculate structural impact metrics.

        Args:
            ast_result: AST analysis result

        Returns:
            Structural impact dictionary
        """
        return {
            "total_imports": len(ast_result.imports),
            "total_function_calls": len(ast_result.function_calls),
            "defined_functions": len(ast_result.defined_functions),
            "defined_classes": len(ast_result.defined_classes),
            "line_count": ast_result.line_count,
        }

    def _assess_risk(
        self, ast_result: FileAnalysisResult, reverse_dependencies: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Assess risk factors for the file.

        Args:
            ast_result: AST analysis result
            reverse_dependencies: List of reverse dependencies

        Returns:
            Risk assessment dictionary
        """
        return {
            "high_import_count": len(ast_result.imports) > 10,
            "complex_function_calls": len(ast_result.function_calls) > 20,
            "many_dependents": len(reverse_dependencies) > 5,
            "analysis_errors": len(ast_result.analysis_errors) > 0,
        }
