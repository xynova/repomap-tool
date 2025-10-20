"""
Tree-sitter-based file analyzer for detailed file-level dependency analysis.

This module provides comprehensive tree-sitter-based analysis of individual files using
TreeSitterParser to extract imports, function calls, class usage, and other
relationships for LLM-optimized impact and centrality analysis.
"""

import logging
from ..core.logging_service import get_logger
import os
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

from .tree_sitter_parser import TreeSitterParser
from .models import (
    Import,
    ImportType,
    FunctionCall,
    FileAnalysisResult,
    CrossFileRelationship,
)

logger = get_logger(__name__)


class AnalysisType(str, Enum):
    """Types of analysis to perform."""

    IMPORTS = "imports"
    FUNCTION_CALLS = "function_calls"
    CLASS_USAGE = "class_usage"
    VARIABLE_USAGE = "variable_usage"
    ALL = "all"


class ASTFileAnalyzer:
    """Tree-sitter-based analyzer for individual files and cross-file relationships."""

    def __init__(
        self,
        tree_sitter_parser: TreeSitterParser,
        project_root: Optional[str] = None,
    ):
        """Initialize the tree-sitter file analyzer.

        Args:
            project_root: Root path of the project for resolving relative imports
            tree_sitter_parser: TreeSitterParser instance (required dependency)
        """
        # All dependencies are required and injected via DI container

        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None
        # Removed aider dependencies - using TreeSitterParser directly
        self.analysis_cache: Dict[str, FileAnalysisResult] = {}
        self.cache_enabled = True

        # Use injected tree-sitter parser
        self.tree_sitter_parser = tree_sitter_parser

        logger.debug(
            f"ASTFileAnalyzer initialized with tree-sitter for project: {self.project_root}"
        )

    def analyze_file(
        self, file_path: str, analysis_type: AnalysisType = AnalysisType.ALL
    ) -> FileAnalysisResult:
        """Analyze a single file using tree-sitter.

        Args:
            file_path: Path to the file to analyze
            analysis_type: Type of analysis to perform

        Returns:
            FileAnalysisResult with extracted information
        """
        # Check cache first
        cache_key = f"{file_path}:{analysis_type}"
        if self.cache_enabled and cache_key in self.analysis_cache:
            logger.debug(f"Using cached analysis for {file_path}")
            return self.analysis_cache[cache_key]

        try:
            # Resolve file path
            full_path = self._resolve_file_path(file_path)

            # Check for syntax errors first
            analysis_errors = []
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to parse Python files for syntax errors
                if full_path.endswith(".py"):
                    try:
                        compile(content, full_path, "exec")
                    except SyntaxError as e:
                        analysis_errors.append(
                            f"Syntax error at line {e.lineno}: {e.msg}"
                        )
                    except Exception as e:
                        analysis_errors.append(f"Parse error: {str(e)}")
            except Exception as e:
                analysis_errors.append(f"File read error: {str(e)}")

            # Use TreeSitterParser directly for tag extraction
            tags = self.tree_sitter_parser.get_tags(full_path, use_cache=True)

            # Extract information from tags
            imports = self._extract_imports_from_tags(tags, full_path)
            defined_functions = self._extract_functions_from_tags(tags)
            defined_classes = self._extract_classes_from_tags(tags)
            function_calls = self._extract_function_calls_from_tags(tags, full_path)
            defined_methods = self._extract_methods_from_tags(tags)

            # Create result
            result = FileAnalysisResult(
                file_path=full_path,
                imports=imports,
                function_calls=function_calls,
                defined_functions=defined_functions,
                defined_classes=defined_classes,
                used_classes=[],  # TODO: Extract from tags if needed
                used_variables=[],  # TODO: Extract from tags if needed
                line_count=self._get_line_count(full_path),
                analysis_errors=analysis_errors,
                defined_methods=defined_methods, # Added defined_methods to result
            )

            # Cache the result
            if self.cache_enabled:
                self.analysis_cache[cache_key] = result

            logger.debug(
                f"Tree-sitter analysis complete for {full_path}: "
                f"{len(imports)} imports, {len(defined_functions)} functions, "
                f"{len(defined_classes)} classes, {len(function_calls)} calls"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing file {file_path} with tree-sitter: {e}")
            # Return empty result on error
            return FileAnalysisResult(
                file_path=file_path,
                imports=[],
                function_calls=[],
                defined_functions=[],
                defined_classes=[],
                used_classes=[],
                used_variables=[],
                line_count=0,
                analysis_errors=[str(e)],
            )

    def _resolve_file_path(self, file_path: str) -> str:
        """Resolve file path to absolute path."""
        if os.path.isabs(file_path):
            return file_path

        if self.project_root:
            return os.path.join(self.project_root, file_path)

        return file_path

    def _extract_imports_from_tags(
        self, tags: List[Any], file_path: str
    ) -> List[Import]:
        """Extract imports from tree-sitter tags."""
        imports = []

        for tag in tags:
            if tag.kind in ["import", "import_from"]:
                module = getattr(tag, "module", tag.name) # Use module if available, otherwise name
                symbols = getattr(tag, "symbols", []) # Get symbols if available
                is_relative = module.startswith(".") # Determine if relative based on module name

                # Determine import type more robustly based on tag kind and module name
                if tag.kind == "import_from":
                    import_type = ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE
                else: # tag.kind == "import"
                    import_type = ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE

                imports.append(
                    Import(
                        module=module,
                        symbols=symbols,
                        is_relative=is_relative,
                        import_type=import_type,
                        line_number=tag.line,
                    )
                )

        return imports

    def _extract_functions_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract function names from tree-sitter tags, filtering out methods."""
        functions = []

        for tag in tags:
            # Only include if it's a function definition and not a method
            if tag.kind in ["def", "function"] and "method" not in tag.kind:
                functions.append(tag.name)

        return functions

    def _extract_methods_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract method names from tree-sitter tags."""
        methods = []
        for tag in tags:
            if "method" in tag.kind:
                methods.append(tag.name)
        return methods

    def _is_likely_variable_assignment(self, tag: Any) -> bool:
        """Check if a tag is likely a variable assignment rather than a function definition."""
        # This heuristic is no longer needed if we rely on explicit tag kinds
        return False # Always return False as we no longer filter based on this

    def _extract_classes_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract class names from tree-sitter tags."""
        classes = []

        for tag in tags:
            if tag.kind in ["class", "interface", "enum"]:
                classes.append(tag.name)

        return classes

    def _extract_function_calls_from_tags(
        self, tags: List[Any], file_path: str
    ) -> List[FunctionCall]:
        """Extract function calls from tree-sitter tags."""
        calls = []

        for tag in tags:
            if tag.kind in ["call", "method_call", "function_call"]:
                # Determine if it's a method call or a direct function call
                is_method_call = False
                object_name = None
                callee = tag.callee if hasattr(tag, "callee") else tag.name

                if "." in callee:
                    parts = callee.split(".", 1)
                    object_name = parts[0]
                    is_method_call = True

                calls.append(
                    FunctionCall(
                        name=tag.name,
                        caller=getattr(tag, "caller", "unknown"),
                        callee=callee,
                        file_path=file_path,
                        line_number=tag.line,
                        is_method_call=is_method_call,
                        object_name=object_name,
                    )
                )

        return calls

    def _get_line_count(self, file_path: str) -> int:
        """Get line count of a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return len(f.readlines())
        except Exception:
            return 0

    def analyze_multiple_files(
        self, file_paths: List[str], analysis_type: AnalysisType = AnalysisType.ALL
    ) -> Dict[str, FileAnalysisResult]:
        """Analyze multiple files using tree-sitter.

        Args:
            file_paths: List of file paths to analyze
            analysis_type: Type of analysis to perform

        Returns:
            Dictionary mapping file paths to analysis results
        """
        results = {}

        for file_path in file_paths:
            try:
                result = self.analyze_file(file_path, analysis_type)
                results[file_path] = result
            except Exception as e:
                logger.error(f"Error analyzing file {file_path}: {e}")
                # Add empty result for failed files
                results[file_path] = FileAnalysisResult(
                    file_path=file_path,
                    imports=[],
                    function_calls=[],
                    defined_functions=[],
                    defined_classes=[],
                    used_classes=[],
                    used_variables=[],
                    line_count=0,
                    analysis_errors=[str(e)],
                )

        return results

    def find_reverse_dependencies(
        self, file_path: str, all_files: List[str]
    ) -> List[CrossFileRelationship]:
        """Find files that import the given file (reverse dependencies)."""
        reverse_deps: List[CrossFileRelationship] = []

        try:
            # Get the module name for the target file
            target_module = self._file_path_to_module_name(file_path)
            if not target_module:
                return reverse_deps

            # Check each file to see if it imports the target module
            for other_file in all_files:
                if other_file == file_path:
                    continue

                try:
                    result = self.analyze_file(other_file, AnalysisType.IMPORTS)
                    for import_stmt in result.imports:
                        if (
                            import_stmt.module == target_module
                            or import_stmt.module.endswith(f".{target_module}")
                        ):
                            reverse_deps.append(
                                CrossFileRelationship(
                                    source_file=other_file,
                                    target_file=file_path,
                                    relationship_type="imports",
                                    strength=1.0,
                                    line_number=import_stmt.line_number or 0,
                                    details=f"Imports {import_stmt.module}",
                                )
                            )
                            break
                except Exception as e:
                    logger.debug(
                        f"Could not analyze {other_file} for reverse deps: {e}"
                    )
                    continue

        except Exception as e:
            logger.error(f"Error finding reverse dependencies for {file_path}: {e}")

        return reverse_deps

    def _file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert file path to module name."""
        try:
            if not self.project_root:
                return None

            # Get relative path from project root
            rel_path = os.path.relpath(file_path, self.project_root)

            # Remove .py extension and convert path separators to dots
            if rel_path.endswith(".py"):
                rel_path = rel_path[:-3]
            elif rel_path.endswith((".ts", ".tsx", ".js", ".jsx")):
                rel_path = rel_path.rsplit(".", 1)[0]

            # Convert path separators to module separators
            module_name = rel_path.replace(os.sep, ".")

            # Remove __init__ suffix if present
            if module_name.endswith(".__init__"):
                module_name = module_name[:-9]

            return module_name if module_name else None

        except Exception as e:
            logger.debug(f"Could not convert {file_path} to module name: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the analysis cache."""
        self.analysis_cache.clear()
        logger.debug("Analysis cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.analysis_cache),
            "cache_enabled": self.cache_enabled,
        }
