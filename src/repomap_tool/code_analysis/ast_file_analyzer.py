"""
Tree-sitter-based file analyzer for detailed file-level dependency analysis.

This module provides comprehensive tree-sitter-based analysis of individual files using
aider's RepoMap functionality to extract imports, function calls, class usage, and other
relationships for LLM-optimized impact and centrality analysis.
"""

import logging
from ..core.logging_service import get_logger
import os
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

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the tree-sitter file analyzer.

        Args:
            project_root: Root path of the project for resolving relative imports
        """
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None
        self._repo_map = None
        self._io = None
        self.analysis_cache: Dict[str, FileAnalysisResult] = {}
        self.cache_enabled = True

        logger.info(
            f"ASTFileAnalyzer initialized with tree-sitter for project: {self.project_root}"
        )

    def analyze_file(
        self, file_path: str, analysis_type: AnalysisType = AnalysisType.ALL
    ) -> FileAnalysisResult:
        """Analyze a single file using aider's tree-sitter.

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

            # Get aider's RepoMap for tree-sitter parsing
            repo_map = self._get_repo_map()

            # Get relative path for aider
            rel_path = self._get_relative_path(full_path)

            # Use aider's tree-sitter to get tags
            tags = repo_map.get_tags(full_path, rel_path)

            # Extract information from tags
            imports = self._extract_imports_from_tags(tags, full_path)
            defined_functions = self._extract_functions_from_tags(tags)
            defined_classes = self._extract_classes_from_tags(tags)
            function_calls = self._extract_function_calls_from_tags(tags, full_path)

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
                analysis_errors=[],
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

    def _get_repo_map(self) -> Any:
        """Get or create aider's RepoMap instance."""
        if self._repo_map is None:
            try:
                from aider.repomap import RepoMap
                from aider.io import InputOutput

                self._io = InputOutput()
                self._repo_map = RepoMap(io=self._io, root=self.project_root or "/")
                logger.debug("Created aider RepoMap instance for tree-sitter parsing")
            except ImportError as e:
                logger.error(f"Failed to import aider modules: {e}")
                raise RuntimeError(
                    "aider modules not available for tree-sitter parsing"
                )

        return self._repo_map

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for aider's RepoMap."""
        if self.project_root and file_path.startswith(self.project_root):
            return os.path.relpath(file_path, self.project_root)
        return os.path.basename(file_path)

    def _extract_imports_from_tags(
        self, tags: List[Any], file_path: str
    ) -> List[Import]:
        """Extract imports from aider tags."""
        imports = []

        # For now, we'll extract imports from the file content since aider tags
        # don't directly provide import information. This is a simplified approach.
        # TODO: Enhance this to use aider's more detailed parsing if available

        try:
            # Read file content to extract imports (temporary approach)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple import extraction for now - can be enhanced later
            import_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip().startswith("import ") or "require(" in line
            ]

            for line_num, line in enumerate(import_lines, 1):
                if line.startswith("import "):
                    # Basic ES6 import parsing
                    if " from " in line:
                        parts = line.split(" from ")
                        if len(parts) == 2:
                            module = parts[1].strip().strip("'\"")
                            imports.append(
                                Import(
                                    module=module,
                                    symbols=[],
                                    is_relative=module.startswith("."),
                                    import_type=(
                                        ImportType.RELATIVE
                                        if module.startswith(".")
                                        else ImportType.ABSOLUTE
                                    ),
                                    line_number=line_num,
                                )
                            )
                elif "require(" in line:
                    # Basic CommonJS require parsing
                    start = line.find("require(") + 8
                    end = line.find(")", start)
                    if start < end:
                        module = line[start:end].strip().strip("'\"")
                        imports.append(
                            Import(
                                module=module,
                                symbols=[],
                                is_relative=module.startswith("."),
                                import_type=(
                                    ImportType.RELATIVE
                                    if module.startswith(".")
                                    else ImportType.ABSOLUTE
                                ),
                                line_number=line_num,
                            )
                        )

        except Exception as e:
            logger.warning(f"Could not extract imports from {file_path}: {e}")

        return imports

    def _extract_functions_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract function names from aider tags."""
        functions = []

        for tag in tags:
            if tag.kind in ["def", "function"]:
                functions.append(tag.name)

        return functions

    def _extract_classes_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract class names from aider tags."""
        classes = []

        for tag in tags:
            if tag.kind in ["class"]:
                classes.append(tag.name)

        return classes

    def _extract_function_calls_from_tags(
        self, tags: List[Any], file_path: str
    ) -> List[FunctionCall]:
        """Extract function calls from aider tags."""
        calls = []

        # For now, we'll create basic function calls from tag references
        # This is a simplified approach - can be enhanced with more detailed parsing
        for tag in tags:
            if tag.kind in ["ref"]:  # References to functions
                calls.append(
                    FunctionCall(
                        caller="unknown",
                        callee=tag.name,
                        file_path=file_path,
                        line_number=tag.line,
                        is_method_call=False,
                        object_name=None,
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
    ) -> List[str]:
        """Find files that import the given file (reverse dependencies)."""
        reverse_deps: List[str] = []

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
                            reverse_deps.append(other_file)
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
