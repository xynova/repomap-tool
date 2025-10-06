"""
Call graph builder for dependency analysis.

This module analyzes function calls within and across files to build a comprehensive
call graph that shows how functions depend on each other.
"""

import ast
import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .models import FunctionCall, CallGraph

logger = get_logger(__name__)


class CallAnalyzer:
    """Base class for language-specific call analyzers."""

    def extract_calls(self, file_content: str, file_path: str) -> List[FunctionCall]:
        """Extract function calls from file content.

        Args:
            file_content: Raw file content
            file_path: Path to the file for context

        Returns:
            List of FunctionCall objects
        """
        raise NotImplementedError("Subclasses must implement extract_calls")


class PythonCallAnalyzer(CallAnalyzer):
    """Parser for Python function calls using AST."""

    def extract_calls(self, file_content: str, file_path: str) -> List[FunctionCall]:
        """Extract Python function calls using AST parsing."""
        calls = []

        try:
            tree = ast.parse(file_content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Handle function calls
                    call_info = self._analyze_call_node(node, file_path)
                    if call_info:
                        calls.append(call_info)

        except SyntaxError as e:
            logger.warning(f"Syntax error parsing Python file {file_path}: {e}")
        except Exception as e:
            logger.error(f"Error parsing Python file {file_path}: {e}")

        return calls

    def _analyze_call_node(
        self, node: ast.Call, file_path: str
    ) -> Optional[FunctionCall]:
        """Analyze a single function call node."""
        try:
            # Get the caller function name (if we can determine it)
            caller = self._get_calling_function_name(node)

            # Get the callee function name
            callee = self._get_called_function_name(node)

            if not callee:
                return None

            # Determine if it's a method call
            is_method_call = False
            object_name = None

            if isinstance(node.func, ast.Attribute):
                is_method_call = True
                if isinstance(node.func.value, ast.Name):
                    object_name = node.func.value.id

            # Create function call object
            call = FunctionCall(
                caller=caller or "unknown",
                callee=callee,
                file_path=file_path,
                line_number=getattr(node, "lineno", 0),
                is_method_call=is_method_call,
                object_name=object_name,
            )

            return call

        except Exception as e:
            logger.debug(f"Error analyzing call node: {e}")
            return None

    def _get_calling_function_name(self, node: ast.Call) -> Optional[str]:
        """Get the name of the function that contains this call."""
        try:
            # Walk up the AST to find the containing function
            current = node
            while hasattr(current, "parent"):
                current = current.parent
                if isinstance(current, ast.FunctionDef):
                    return current.name
                elif isinstance(current, ast.AsyncFunctionDef):
                    return current.name
                elif isinstance(current, ast.ClassDef):
                    return f"{current.name}.__init__"

            return None

        except Exception:
            return None

    def _get_called_function_name(self, node: ast.Call) -> Optional[str]:
        """Get the name of the function being called."""
        try:
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
            elif isinstance(node.func, ast.Call):
                # Handle cases like func()()
                return self._get_called_function_name(node.func)
            else:
                return None

        except Exception:
            return None


class JavaScriptCallAnalyzer(CallAnalyzer):
    """Parser for JavaScript/TypeScript function calls using aider's tree-sitter."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize with project root for aider's RepoMap."""
        super().__init__()
        self.project_root = project_root
        self._repo_map = None

    def extract_calls(self, file_content: str, file_path: str) -> List[FunctionCall]:
        """Extract JavaScript/TypeScript function calls using aider's tree-sitter."""
        calls = []

        try:
            # Get aider's RepoMap for tree-sitter parsing
            repo_map = self._get_repo_map()

            # Get relative path for aider
            rel_path = self._get_relative_path(file_path)

            # Use aider's tree-sitter to get tags
            tags = repo_map.get_tags(file_path, rel_path)

            # Extract function calls from tags
            for tag in tags:
                if tag.kind in ["ref"]:  # References to functions
                    calls.append(
                        FunctionCall(
                            caller="unknown",  # TODO: Extract caller from context
                            callee=tag.name,
                            file_path=file_path,
                            line_number=tag.line,
                            is_method_call=False,  # TODO: Determine if it's a method call
                            object_name=None,
                        )
                    )

            logger.debug(
                f"Tree-sitter extracted {len(calls)} function calls from {file_path}"
            )

        except Exception as e:
            logger.error(
                f"Error extracting function calls from {file_path} with tree-sitter: {e}"
            )

        return calls

    def _get_repo_map(self) -> Any:
        """Get or create aider's RepoMap instance."""
        if self._repo_map is None:
            try:
                from aider.repomap import RepoMap
                from aider.io import InputOutput

                io = InputOutput()
                self._repo_map = RepoMap(io=io, root=self.project_root or "/")
                logger.debug(
                    "Created aider RepoMap instance for JavaScript call analysis"
                )
            except ImportError as e:
                logger.error(f"Failed to import aider modules: {e}")
                raise RuntimeError(
                    "aider modules not available for tree-sitter parsing"
                )

        return self._repo_map

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path for aider's RepoMap."""
        import os

        if self.project_root and file_path.startswith(self.project_root):
            return os.path.relpath(file_path, self.project_root)
        return os.path.basename(file_path)

    def _get_line_number(self, content: str, position: int) -> Optional[int]:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return None

    def _find_calling_function(
        self, function_lines: Dict[int, str], call_line: int
    ) -> Optional[str]:
        """Find the function that contains a call at the given line."""
        try:
            # Find the function declaration that comes before this line
            candidate_functions = [
                (line, func)
                for line, func in function_lines.items()
                if line <= call_line
            ]

            if candidate_functions:
                # Return the function from the closest line before the call
                return max(candidate_functions, key=lambda x: x[0])[1]

            return None

        except Exception:
            return None


class CallGraphBuilder:
    """Main call graph builder that coordinates multi-language analysis."""

    def __init__(self) -> None:
        """Initialize the call graph builder with language analyzers."""
        self.language_analyzers: Dict[str, CallAnalyzer] = {
            "py": PythonCallAnalyzer(),
            "js": JavaScriptCallAnalyzer(),
            "ts": JavaScriptCallAnalyzer(),  # TypeScript uses same analyzer
            "jsx": JavaScriptCallAnalyzer(),
            "tsx": JavaScriptCallAnalyzer(),
        }

        # File extensions that should be analyzed
        from .file_filter import FileFilter

        self.analyzable_extensions = FileFilter.get_analyzable_extensions()

        logger.info(
            f"CallGraphBuilder initialized with {len(self.language_analyzers)} language analyzers"
        )

    def build_call_graph(
        self, project_files: List[str], max_workers: int = get_config("MAX_WORKERS", 4)
    ) -> CallGraph:
        """Build the complete call graph for a project.

        Args:
            project_files: List of file paths to analyze
            max_workers: Maximum number of parallel workers

        Returns:
            CallGraph object with all function calls
        """
        logger.info(f"Building call graph for {len(project_files)} files")

        # Filter to only analyzable files
        from .file_filter import FileFilter

        analyzable_files = FileFilter.filter_analyzable_files(
            project_files, exclude_tests=True
        )

        logger.info(f"Found {len(analyzable_files)} analyzable files for call graph")

        all_calls: List[FunctionCall] = []
        function_locations: Dict[str, str] = {}

        # Use parallel processing for large projects
        if len(analyzable_files) > 10 and max_workers > 1:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_file = {
                    executor.submit(self.analyze_file_calls, file_path): file_path
                    for file_path in analyzable_files
                }

                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        file_calls = future.result()
                        all_calls.extend(file_calls)

                        # Track function locations
                        for call in file_calls:
                            if call.caller != "unknown":
                                function_locations[call.caller] = file_path

                    except Exception as e:
                        logger.error(f"Error analyzing calls in {file_path}: {e}")
        else:
            # Sequential processing for small projects
            for file_path in analyzable_files:
                file_calls = self.analyze_file_calls(file_path)
                all_calls.extend(file_calls)

                # Track function locations
                for call in file_calls:
                    if call.caller != "unknown":
                        function_locations[call.caller] = file_path

        # Build call graph
        call_graph = CallGraph(
            project_path=str(Path(project_files[0]).parent) if project_files else "",
            function_calls=all_calls,
            function_locations=function_locations,
        )

        logger.info(
            f"Call graph built: {len(all_calls)} function calls, {len(function_locations)} functions"
        )
        return call_graph

    def analyze_file_calls(self, file_path: str) -> List[FunctionCall]:
        """Analyze function calls in a single file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            List of FunctionCall objects found in the file
        """
        file_path = str(file_path)
        file_ext = Path(file_path).suffix.lstrip(".")

        # Check if we have an analyzer for this file type
        if file_ext not in self.language_analyzers:
            logger.debug(f"No analyzer for {file_ext}, skipping {file_path}")
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Get the appropriate analyzer
            analyzer = self.language_analyzers[file_ext]
            calls = analyzer.extract_calls(content, file_path)

            logger.debug(f"Analyzed {file_path}: found {len(calls)} function calls")
            return calls

        except UnicodeDecodeError:
            logger.warning(f"Could not decode {file_path} as UTF-8, skipping")
            return []
        except Exception as e:
            logger.error(f"Failed to analyze calls in {file_path}: {e}")
            return []

    def resolve_cross_file_calls(
        self, calls: List[FunctionCall], project_files: List[str]
    ) -> List[FunctionCall]:
        """Resolve function calls that cross file boundaries.

        Args:
            calls: List of FunctionCall objects
            project_files: List of all project files for context

        Returns:
            List of FunctionCall objects with resolved cross-file information
        """
        logger.info("Resolving cross-file function calls")

        # Build a map of function names to their file locations
        function_locations = {}
        for call in calls:
            if call.caller != "unknown":
                function_locations[call.caller] = call.file_path

        # Resolve cross-file calls
        resolved_calls = []
        for call in calls:
            # Check if the callee is defined in a different file
            if call.callee in function_locations:
                callee_file = function_locations[call.callee]
                if callee_file != call.file_path:
                    call.resolved_callee = callee_file

            resolved_calls.append(call)

        logger.info(f"Resolved {len(resolved_calls)} cross-file calls")
        return resolved_calls

    def get_call_statistics(self, call_graph: CallGraph) -> Dict[str, Any]:
        """Get comprehensive statistics about the call graph.

        Args:
            call_graph: CallGraph object to analyze

        Returns:
            Dictionary with call graph statistics
        """
        try:
            stats: Dict[str, Any] = {
                "total_calls": len(call_graph.function_calls),
                "total_functions": len(call_graph.function_locations),
                "unique_callers": len(
                    set(call.caller for call in call_graph.function_calls)
                ),
                "unique_callees": len(
                    set(call.callee for call in call_graph.function_calls)
                ),
                "method_calls": len(
                    [call for call in call_graph.function_calls if call.is_method_call]
                ),
                "function_calls": len(
                    [
                        call
                        for call in call_graph.function_calls
                        if not call.is_method_call
                    ]
                ),
            }

            # Call frequency analysis
            callee_counts: Dict[str, int] = {}
            for call in call_graph.function_calls:
                callee_counts[call.callee] = callee_counts.get(call.callee, 0) + 1

            if callee_counts:
                most_called = max(callee_counts.items(), key=lambda x: x[1])
                stats["most_called_function"] = most_called[0]  # Get the function name
                stats["average_calls_per_function"] = sum(callee_counts.values()) / len(
                    callee_counts
                )

            # File distribution
            file_call_counts: Dict[str, int] = {}
            for call in call_graph.function_calls:
                file_call_counts[call.file_path] = (
                    file_call_counts.get(call.file_path, 0) + 1
                )

            if file_call_counts:
                top_files = sorted(
                    file_call_counts.items(), key=lambda x: x[1], reverse=True
                )[:5]
                stats["files_with_most_calls"] = [
                    file_name for file_name, _ in top_files
                ]

            return stats

        except Exception as e:
            logger.error(f"Error calculating call graph statistics: {e}")
            return {}

    def find_function_dependencies(
        self, call_graph: CallGraph, function_name: str
    ) -> List[str]:
        """Find all functions that a given function depends on.

        Args:
            call_graph: CallGraph object to analyze
            function_name: Name of the function to analyze

        Returns:
            List of function names that the function depends on
        """
        try:
            dependencies = set()

            # Find all calls made by this function
            for call in call_graph.function_calls:
                if call.caller == function_name:
                    dependencies.add(call.callee)

            return list(dependencies)

        except Exception as e:
            logger.error(f"Error finding dependencies for {function_name}: {e}")
            return []

    def find_function_dependents(
        self, call_graph: CallGraph, function_name: str
    ) -> List[str]:
        """Find all functions that depend on a given function.

        Args:
            call_graph: CallGraph object to analyze
            function_name: Name of the function to analyze

        Returns:
            List of function names that depend on the function
        """
        try:
            dependents = set()

            # Find all calls to this function
            for call in call_graph.function_calls:
                if call.callee == function_name:
                    dependents.add(call.caller)

            return list(dependents)

        except Exception as e:
            logger.error(f"Error finding dependents for {function_name}: {e}")
            return []

    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages."""
        return list(self.language_analyzers.keys())

    def add_language_analyzer(self, extension: str, analyzer: CallAnalyzer) -> None:
        """Add support for a new programming language.

        Args:
            extension: File extension (without dot)
            analyzer: CallAnalyzer instance for the language
        """
        self.language_analyzers[extension] = analyzer
        self.analyzable_extensions.add(extension)
        logger.info(f"Added call analyzer for {extension} files")
