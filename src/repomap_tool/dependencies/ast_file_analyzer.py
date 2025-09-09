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

from .models import Import, ImportType, FunctionCall

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of AST analysis to perform."""

    IMPORTS = "imports"
    FUNCTION_CALLS = "function_calls"
    CLASS_USAGE = "class_usage"
    VARIABLE_USAGE = "variable_usage"
    ALL = "all"


@dataclass
class FileAnalysisResult:
    """Result of AST analysis for a single file."""

    file_path: str
    imports: List[Import]
    function_calls: List[FunctionCall]
    defined_functions: List[str]
    defined_classes: List[str]
    used_classes: List[str]
    used_variables: List[str]
    line_count: int
    analysis_errors: List[str]


@dataclass
class CrossFileRelationship:
    """Relationship between files based on AST analysis."""

    source_file: str
    target_file: str
    relationship_type: str  # "imports", "calls_function", "uses_class", etc.
    line_number: int
    details: str


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

            # Parse AST
            tree = ast.parse(content, filename=file_path)

            # Perform analysis
            result = self._analyze_ast_tree(tree, file_path, content, analysis_type)

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
                    if self._is_import_of_file(import_obj, file_path):
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
                    details=f"calls {func_call.function_name}",
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
        imports = []
        function_calls = []
        defined_functions = []
        defined_classes = []
        used_classes = []
        used_variables = []
        analysis_errors = []

        # Count lines
        line_count = len(content.splitlines())

        # Visit all nodes in the AST
        for node in ast.walk(tree):
            try:
                if analysis_type in [AnalysisType.IMPORTS, AnalysisType.ALL]:
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        import_objs = self._extract_imports(node, file_path)
                        imports.extend(import_objs)

                if analysis_type in [AnalysisType.FUNCTION_CALLS, AnalysisType.ALL]:
                    if isinstance(node, ast.Call):
                        func_call = self._extract_function_call(node, file_path)
                        if func_call:
                            function_calls.append(func_call)

                if analysis_type in [AnalysisType.ALL]:
                    if isinstance(node, ast.FunctionDef):
                        defined_functions.append(node.name)
                    elif isinstance(node, ast.ClassDef):
                        defined_classes.append(node.name)
                    elif isinstance(node, ast.Name):
                        if isinstance(node.ctx, ast.Load):
                            used_variables.append(node.id)

            except Exception as e:
                analysis_errors.append(
                    f"Error processing node at line {getattr(node, 'lineno', 'unknown')}: {e}"
                )

        return FileAnalysisResult(
            file_path=file_path,
            imports=imports,
            function_calls=function_calls,
            defined_functions=defined_functions,
            defined_classes=defined_classes,
            used_classes=used_classes,
            used_variables=used_variables,
            line_count=line_count,
            analysis_errors=analysis_errors,
        )

    def _extract_imports(
        self, node: Union[ast.Import, ast.ImportFrom], file_path: str
    ) -> List[Import]:
        """Extract import information from an AST node.

        Args:
            node: AST import node
            file_path: Path to the file containing the import

        Returns:
            List of Import objects
        """
        imports = []
        try:
            if isinstance(node, ast.Import):
                # Handle: import module1, module2, module3
                for alias in node.names:
                    imports.append(
                        Import(
                            module=alias.name,
                            alias=alias.asname,
                            is_relative=False,
                            import_type=ImportType.ABSOLUTE,
                            line_number=node.lineno,
                            symbols=[],
                        )
                    )

            elif isinstance(node, ast.ImportFrom):
                # Handle: from module import name1, name2, name3
                module_name = node.module or ""
                is_relative = module_name.startswith(".")

                # Extract all symbols from this import statement
                symbols = []
                for alias in node.names:
                    symbols.append(alias.asname or alias.name)

                imports.append(
                    Import(
                        module=module_name,
                        alias=None,
                        is_relative=is_relative,
                        import_type=(
                            ImportType.RELATIVE if is_relative else ImportType.ABSOLUTE
                        ),
                        line_number=node.lineno,
                        symbols=symbols,
                    )
                )

        except Exception as e:
            logger.debug(f"Error extracting imports: {e}")

        return imports

    def _extract_function_call(
        self, node: ast.Call, file_path: str
    ) -> Optional[FunctionCall]:
        """Extract function call information from an AST node.

        Args:
            node: AST call node
            file_path: Path to the file containing the call

        Returns:
            FunctionCall object or None if extraction fails
        """
        try:
            # Get function name and determine if it's a method call
            is_method_call = False
            object_name = None
            callee = "unknown"

            if isinstance(node.func, ast.Name):
                callee = node.func.id
            elif isinstance(node.func, ast.Attribute):
                callee = node.func.attr
                is_method_call = True
                if isinstance(node.func.value, ast.Name):
                    object_name = node.func.value.id
                else:
                    object_name = "complex_object"
            else:
                callee = "unknown"

            # For now, we don't have caller context, so use "unknown"
            caller = "unknown"

            return FunctionCall(
                caller=caller,
                callee=callee,
                file_path=file_path,
                line_number=node.lineno,
                is_method_call=is_method_call,
                object_name=object_name,
            )

        except Exception as e:
            logger.debug(f"Error extracting function call: {e}")
            return None

    def _get_attr_name(self, node: ast.Attribute) -> str:
        """Get the full attribute name from an AST attribute node.

        Args:
            node: AST attribute node

        Returns:
            Full attribute name string
        """
        if isinstance(node.value, ast.Name):
            return node.value.id
        elif isinstance(node.value, ast.Attribute):
            return f"{self._get_attr_name(node.value)}.{node.attr}"
        else:
            return "unknown"

    def _is_import_of_file(self, import_obj: Import, target_file: str) -> bool:
        """Check if an import refers to a specific file.

        Args:
            import_obj: Import object to check
            target_file: Target file path to check against

        Returns:
            True if the import refers to the target file
        """
        try:
            # Get the module name that the target file represents
            target_module = self._file_path_to_module_name(target_file)
            if not target_module:
                return False

            # Check if the import matches the target module
            import_module = import_obj.module

            # Handle exact matches
            if import_module == target_module:
                return True

            # Handle cases where the import is a parent package of the target
            # e.g., import "my_package" matches file "my_package/__init__.py"
            if target_module.startswith(import_module + "."):
                return True

            # Handle cases where the import is a submodule of the target
            # e.g., import "my_package.utils" matches file "my_package/utils.py"
            if import_module.startswith(target_module + "."):
                return True

            # Handle relative imports
            if import_obj.is_relative:
                # For relative imports, we need to resolve them relative to the importing file
                # This is more complex and would require the importing file context
                # For now, we'll do a simple check
                relative_module = import_module.lstrip(".")
                if relative_module == target_module or target_module.endswith(
                    "." + relative_module
                ):
                    return True

            return False

        except Exception as e:
            logger.debug(f"Error in _is_import_of_file: {e}")
            return False

    def _file_path_to_module_name(self, file_path: str) -> Optional[str]:
        """Convert a file path to its corresponding Python module name.

        Args:
            file_path: Path to the Python file

        Returns:
            Module name or None if conversion fails
        """
        try:
            if not self.project_root:
                # Fallback to simple stem extraction if no project root
                return Path(file_path).stem

            # Convert to absolute path
            abs_file_path = Path(file_path).resolve()
            abs_project_root = Path(self.project_root).resolve()

            # Check if the file is within the project root
            try:
                relative_path = abs_file_path.relative_to(abs_project_root)
            except ValueError:
                # File is not within project root
                return Path(file_path).stem

            # Convert path to module name
            module_parts = []
            is_init_file = False

            for part in relative_path.parts:
                if part == "__init__.py":
                    # Handle __init__.py files - the module is the parent directory
                    is_init_file = True
                    break
                elif part.endswith(".py"):
                    # Remove .py extension
                    module_parts.append(part[:-3])
                else:
                    module_parts.append(part)

            # Join parts with dots
            if is_init_file:
                # For __init__.py files, the module name is the parent directory path
                module_name = ".".join(module_parts)
            else:
                module_name = ".".join(module_parts)

            return module_name if module_name else None

        except Exception as e:
            logger.debug(f"Error converting file path to module name: {e}")
            return None

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
