"""
AST-based file analyzer for detailed file-level dependency analysis.

This module provides comprehensive AST-based analysis of individual files to extract
imports, function calls, class usage, and other relationships for LLM-optimized
impact and centrality analysis.
"""

import ast
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from .models import (
    Import,
    ImportType,
    FunctionCall,
    FileAnalysisResult,
    CrossFileRelationship,
)
from .ast_visitors import create_visitor, AnalysisContext
from .js_ts_analyzer import JavaScriptTypeScriptAnalyzer, JSAnalysisContext
from .import_utils import ImportUtils

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of AST analysis to perform."""

    IMPORTS = "imports"
    FUNCTION_CALLS = "function_calls"
    CLASS_USAGE = "class_usage"
    VARIABLE_USAGE = "variable_usage"
    ALL = "all"


class ASTFileAnalyzer:
    """AST-based analyzer for individual files and cross-file relationships."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the AST file analyzer.

        Args:
            project_root: Root path of the project for resolving relative imports
        """
        self.project_root = project_root
        self.analysis_cache: Dict[str, FileAnalysisResult] = {}
        self.cache_enabled = True

        # Initialize extracted components
        self.import_utils = ImportUtils(project_root)
        self.js_ts_analyzer = JavaScriptTypeScriptAnalyzer()

        logger.info(f"ASTFileAnalyzer initialized for project: {self.project_root}")

    def analyze_file(
        self, file_path: str, analysis_type: AnalysisType = AnalysisType.ALL
    ) -> FileAnalysisResult:
        """Analyze a single file using AST parsing.

        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform

        Returns:
            FileAnalysisResult with comprehensive analysis
        """
        # Check cache first
        cache_key = f"{file_path}:{analysis_type.value}"
        if self.cache_enabled and cache_key in self.analysis_cache:
            logger.debug(f"Using cached analysis for {file_path}")
            return self.analysis_cache[cache_key]

        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check file extension to determine parsing method
            file_ext = Path(file_path).suffix.lower()
            if file_ext == ".py":
                # Use Python AST for Python files
                tree = ast.parse(content, filename=file_path)
                result = self._analyze_ast_tree(tree, file_path, content, analysis_type)
            elif file_ext in [".ts", ".js", ".tsx", ".jsx"]:
                # Use extracted JavaScript/TypeScript analyzer
                js_context = JSAnalysisContext(file_path=file_path, content=content)
                result = self.js_ts_analyzer.analyze_file(js_context)
            else:
                # For other file types, return empty result with analysis error
                logger.debug(
                    f"Skipping analysis for unsupported file type: {file_path}"
                )
                return FileAnalysisResult(
                    file_path=file_path,
                    imports=[],
                    function_calls=[],
                    defined_functions=[],
                    defined_classes=[],
                    used_classes=[],
                    used_variables=[],
                    line_count=len(content.splitlines()),
                    analysis_errors=[f"Analysis not supported for {file_ext} files"],
                )

            # Result is already obtained from the appropriate parser above

            # Cache result
            if self.cache_enabled:
                self.analysis_cache[cache_key] = result

            logger.debug(
                f"AST analysis complete for {file_path}: {len(result.imports)} imports, {len(result.function_calls)} calls"
            )
            return result

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
            return FileAnalysisResult(
                file_path=file_path,
                imports=[],
                function_calls=[],
                defined_functions=[],
                defined_classes=[],
                used_classes=[],
                used_variables=[],
                line_count=0,
                analysis_errors=[f"Syntax error: {e}"],
            )
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return FileAnalysisResult(
                file_path=file_path,
                imports=[],
                function_calls=[],
                defined_functions=[],
                defined_classes=[],
                used_classes=[],
                used_variables=[],
                line_count=0,
                analysis_errors=[f"Analysis error: {e}"],
            )

    def analyze_multiple_files(
        self, file_paths: List[str], analysis_type: AnalysisType = AnalysisType.ALL
    ) -> Dict[str, FileAnalysisResult]:
        """Analyze multiple files and return results.

        Args:
            file_paths: List of file paths to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Dictionary mapping file paths to analysis results
        """
        results = {}

        for file_path in file_paths:
            try:
                results[file_path] = self.analyze_file(file_path, analysis_type)
            except Exception as e:
                logger.error(f"Failed to analyze {file_path}: {e}")
                results[file_path] = FileAnalysisResult(
                    file_path=file_path,
                    imports=[],
                    function_calls=[],
                    defined_functions=[],
                    defined_classes=[],
                    used_classes=[],
                    used_variables=[],
                    line_count=0,
                    analysis_errors=[f"Failed to analyze: {e}"],
                )

        return results

    def find_direct_dependencies(self, file_path: str) -> List[Import]:
        """Find all direct dependencies (imports) for a file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of Import objects representing direct dependencies
        """
        result = self.analyze_file(file_path, AnalysisType.IMPORTS)
        return result.imports

    def find_reverse_dependencies(
        self, file_path: str, all_files: List[str]
    ) -> List[CrossFileRelationship]:
        """Find all files that import or use the specified file.

        Args:
            file_path: Path to the file to find reverse dependencies for
            all_files: List of all files in the project to search

        Returns:
            List of CrossFileRelationship objects
        """
        reverse_deps = []

        # Analyze all files to find references to the target file
        for other_file in all_files:
            if other_file == file_path:
                continue

            try:
                result = self.analyze_file(other_file, AnalysisType.ALL)

                # Check imports
                for import_obj in result.imports:
                    if self.import_utils.is_import_of_file(import_obj, file_path):
                        reverse_deps.append(
                            CrossFileRelationship(
                                source_file=other_file,
                                target_file=file_path,
                                relationship_type="imports",
                                line_number=import_obj.line_number or 0,
                                details=f"imports {import_obj.module}",
                            )
                        )

                # Check function calls (if the file defines functions that are called)
                # This would require more sophisticated analysis

            except Exception as e:
                logger.debug(
                    f"Error checking reverse dependencies in {other_file}: {e}"
                )
                continue

        return reverse_deps

    def find_function_call_relationships(
        self, file_path: str, all_files: List[str]
    ) -> List[CrossFileRelationship]:
        """Find function call relationships for a file.

        Args:
            file_path: Path to the file to analyze
            all_files: List of all files in the project

        Returns:
            List of CrossFileRelationship objects for function calls
        """
        relationships = []
        result = self.analyze_file(file_path, AnalysisType.FUNCTION_CALLS)

        # For each function call in the file, try to find where it's defined
        for func_call in result.function_calls:
            # This is a simplified approach - in practice, you'd need more sophisticated
            # analysis to determine which file defines the function
            relationships.append(
                CrossFileRelationship(
                    source_file=file_path,
                    target_file="unknown",  # Would need more analysis to determine
                    relationship_type="calls_function",
                    line_number=func_call.line_number or 0,
                    details=f"calls {func_call.callee}",
                )
            )

        return relationships

    def _analyze_ast_tree(
        self, tree: ast.AST, file_path: str, content: str, analysis_type: AnalysisType
    ) -> FileAnalysisResult:
        """Analyze an AST tree and extract relevant information.

        Args:
            tree: Parsed AST tree
            file_path: Path to the file being analyzed
            content: File content for line counting
            analysis_type: Type of analysis to perform

        Returns:
            FileAnalysisResult with extracted information
        """
        # Create analysis context
        context = AnalysisContext(
            file_path=file_path, content=content, analysis_type=analysis_type.value
        )

        # Create appropriate visitor
        visitor = create_visitor(analysis_type.value, context)

        # Visit the AST tree
        visitor.visit(tree)

        # Count lines
        line_count = len(content.splitlines())

        return FileAnalysisResult(
            file_path=file_path,
            imports=visitor.imports,
            function_calls=visitor.function_calls,
            defined_functions=visitor.defined_functions,
            defined_classes=visitor.defined_classes,
            used_classes=visitor.used_classes,
            used_variables=visitor.used_variables,
            line_count=line_count,
            analysis_errors=visitor.analysis_errors,
        )

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        logger.info("AST analysis cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": self.cache_enabled,
            "cache_size": len(self.analysis_cache),
            "cached_files": list(self.analysis_cache.keys()),
        }

    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return 1
