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
        project_root: Optional[str] = None,
        tree_sitter_parser: Optional[Any] = None,
    ):
        """Initialize the tree-sitter file analyzer.

        Args:
            project_root: Root path of the project for resolving relative imports
            tree_sitter_parser: TreeSitterParser instance (required dependency)
        """
        # Validate required dependency
        if tree_sitter_parser is None:
            raise ValueError("TreeSitterParser must be injected - no fallback allowed")
        
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
        """Extract imports from file content since tree-sitter tags don't include imports."""
        imports = []

        try:
            # Read file content to extract imports
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Handle Python imports
                if line.startswith("import ") and " from " not in line:
                    # Standard import: import module
                    module = line[7:].strip()  # Remove "import "
                    # Handle multiple imports: import os, sys
                    for module_name in module.split(","):
                        module_name = module_name.strip()
                        if module_name:
                            imports.append(
                                Import(
                                    module=module_name,
                                    symbols=[],
                                    is_relative=module_name.startswith("."),
                                    import_type=(
                                        ImportType.RELATIVE
                                        if module_name.startswith(".")
                                        else ImportType.ABSOLUTE
                                    ),
                                    line_number=line_num,
                                )
                            )
                elif line.startswith("from "):
                    # From import: from module import symbol
                    if " import " in line:
                        parts = line.split(" import ")
                        if len(parts) == 2:
                            from_part = parts[0].strip()  # "from module"
                            import_part = parts[1].strip()  # "symbol"

                            if from_part.startswith("from "):
                                module = from_part[5:].strip()  # Remove "from "
                                symbols = []

                                # Handle multiple symbols: import os, sys
                                for symbol in import_part.split(","):
                                    symbol = symbol.strip()
                                    if symbol:
                                        symbols.append(symbol)

                                imports.append(
                                    Import(
                                        module=module,
                                        symbols=symbols,
                                        is_relative=module.startswith("."),
                                        import_type=(
                                            ImportType.RELATIVE
                                            if module.startswith(".")
                                            else ImportType.ABSOLUTE
                                        ),
                                        line_number=line_num,
                                    )
                                )

                # Handle JavaScript/TypeScript imports
                elif line.startswith("import ") and (
                    " from " in line or " = require(" in line
                ):
                    if " from " in line:
                        # ES6 import: import { symbol } from 'module'
                        parts = line.split(" from ")
                        if len(parts) == 2:
                            symbols_part = parts[0].strip()
                            module = parts[1].strip().strip("'\"")

                            symbols = []
                            if symbols_part.startswith("import "):
                                symbols_str = symbols_part[
                                    7:
                                ].strip()  # Remove "import "
                                if symbols_str.startswith("{") and symbols_str.endswith(
                                    "}"
                                ):
                                    # Named imports: { symbol1, symbol2 }
                                    symbols_str = symbols_str[1:-1]  # Remove braces
                                    for symbol in symbols_str.split(","):
                                        symbol = symbol.strip()
                                        if symbol:
                                            symbols.append(symbol)
                                elif symbols_str == "*":
                                    # Namespace import: import * as name
                                    symbols = ["*"]
                                else:
                                    # Default import: import name
                                    symbols = [symbols_str]

                            imports.append(
                                Import(
                                    module=module,
                                    symbols=symbols,
                                    is_relative=module.startswith("."),
                                    import_type=(
                                        ImportType.RELATIVE
                                        if module.startswith(".")
                                        else ImportType.ABSOLUTE
                                    ),
                                    line_number=line_num,
                                )
                            )
                    elif " = require(" in line:
                        # CommonJS require: const module = require('module')
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
        """Extract function names from tree-sitter tags."""
        functions = []

        for tag in tags:
            if tag.kind in ["def", "function"]:
                # Filter out false positives - tree-sitter sometimes tags variable assignments as 'def'
                # We can identify these by checking if the name appears to be a variable assignment
                # in the context of the file content
                if not self._is_likely_variable_assignment(
                    tag
                ) and not self._is_likely_class_definition(tag):
                    functions.append(tag.name)

        return functions

    def _is_likely_variable_assignment(self, tag: Any) -> bool:
        """Check if a tag is likely a variable assignment rather than a function definition."""
        # This is a heuristic to filter out false positives from tree-sitter parsing
        # Variable assignments that tree-sitter incorrectly tags as 'def' often have these characteristics:

        # 1. Single word names that are common variable names
        common_variable_names = {
            "result",
            "obj",
            "message",
            "counts",
            "data",
            "value",
            "item",
            "items",
            "response",
            "request",
            "config",
            "settings",
            "options",
            "params",
            "args",
            "kwargs",
            "self",
            "cls",
            "var",
            "temp",
            "tmp",
            "file",
            "path",
            "url",
            "name",
            "id",
            "key",
            "val",
            "content",
            "text",
            "string",
            "number",
            "list",
            "dict",
            "tuple",
            "set",
            "bool",
        }

        if tag.name.lower() in common_variable_names:
            return True

        # 2. Names that are very short (1-3 characters) and lowercase
        if len(tag.name) <= 3 and tag.name.islower():
            return True

        # 3. Names that are common variable patterns but not function patterns
        # Functions typically have descriptive names, variables are often short/generic
        # But we need to be careful not to filter out legitimate short function names
        if (
            tag.name.islower()
            and len(tag.name) <= 6
            and not any(
                word in tag.name
                for word in [
                    "get",
                    "set",
                    "is",
                    "has",
                    "can",
                    "should",
                    "will",
                    "do",
                    "make",
                    "create",
                    "build",
                    "process",
                    "handle",
                    "manage",
                    "parse",
                    "format",
                    "validate",
                    "check",
                    "find",
                    "search",
                    "load",
                    "save",
                    "delete",
                    "update",
                    "add",
                    "remove",
                    "init",
                    "method",
                    "test",
                    "run",
                    "call",
                    "exec",
                    "eval",
                ]
            )
        ):
            return True

        return False

    def _extract_classes_from_tags(self, tags: List[Any]) -> List[str]:
        """Extract class names from tree-sitter tags."""
        classes = []

        for tag in tags:
            if tag.kind in ["class"]:
                classes.append(tag.name)
            elif tag.kind == "def" and self._is_likely_class_definition(tag):
                # Tree-sitter sometimes tags class definitions as 'def'
                classes.append(tag.name)

        return classes

    def _is_likely_class_definition(self, tag: Any) -> bool:
        """Check if a tag is likely a class definition rather than a function."""
        # Class names typically follow PascalCase convention
        if tag.name[0].isupper() and tag.name[1:].islower():
            return True

        # Class names that are all uppercase (constants/enums)
        if tag.name.isupper():
            return True

        # Class names with multiple uppercase letters (PascalCase)
        if any(c.isupper() for c in tag.name[1:]):
            return True

        return False

    def _extract_function_calls_from_tags(
        self, tags: List[Any], file_path: str
    ) -> List[FunctionCall]:
        """Extract function calls from tree-sitter tags."""
        calls = []

        # For now, we'll create basic function calls from tag references
        # This is a simplified approach - can be enhanced with more detailed parsing
        for tag in tags:
            if tag.kind in ["ref"]:  # References to functions
                calls.append(
                    FunctionCall(
                        name=tag.name,
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
