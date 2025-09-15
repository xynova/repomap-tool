"""
Impact analysis engine for file-level impact assessment.

This module provides comprehensive impact analysis for files, including
direct dependencies, reverse dependencies, function call analysis,
structural impact, and risk assessment.
"""

import logging
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from .ast_file_analyzer import ASTFileAnalyzer, FileAnalysisResult
from .file_utils import suggest_test_files
from .models import FileImpactAnalysis

logger = logging.getLogger(__name__)


class ImpactAnalysisEngine:
    """Engine for analyzing file impact and dependencies."""

    def __init__(self, ast_analyzer: ASTFileAnalyzer, dependency_graph: Optional[Any] = None, path_normalizer: Optional[Any] = None):
        """Initialize the impact analysis engine.

        Args:
            ast_analyzer: AST file analyzer instance
            dependency_graph: Dependency graph for reverse dependency analysis
            path_normalizer: Path normalizer for consistent path resolution
        """
        self.ast_analyzer = ast_analyzer
        self.dependency_graph = dependency_graph
        self.path_normalizer = path_normalizer

    def analyze_file_impact(
        self, file_path: str, ast_result: FileAnalysisResult, all_files: List[str], dependency_graph: Optional[Any] = None
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
        # Use the passed dependency graph if available, otherwise fall back to the injected one
        graph_to_use = dependency_graph if dependency_graph is not None else self.dependency_graph
        reverse_dependencies = self._analyze_reverse_dependencies(file_path, all_files, graph_to_use)

        # Function call analysis
        function_call_analysis = self._analyze_function_calls(ast_result.function_calls, ast_result.imports)

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
        self, file_path: str, all_files: List[str], dependency_graph: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """Analyze reverse dependencies (what imports this file).

        Args:
            file_path: Path to the file
            all_files: List of all files in the project

        Returns:
            List of reverse dependency dictionaries
        """
        reverse_dependencies = []
        
        # Try to use dependency graph first if available (same approach as centrality analysis)
        graph_to_use = dependency_graph if dependency_graph is not None else self.dependency_graph
        if (
            graph_to_use
            and hasattr(graph_to_use, "nodes")
            and len(graph_to_use.nodes) > 0  # Ensure graph is populated
        ):
            try:
                # Convert file path to relative path for dependency graph lookup
                relative_path = self._get_relative_path(file_path)
                
                if relative_path in graph_to_use.nodes:
                    node = graph_to_use.nodes[relative_path]
                    if hasattr(node, 'imported_by') and node.imported_by:
                        for importing_file in node.imported_by:
                            reverse_dependencies.append(
                                {
                                    "file": importing_file,
                                    "line": 0,  # Line number not available from graph
                                    "relationship": "imports",
                                    "details": f"imports {relative_path}",
                                }
                            )
                        return reverse_dependencies
            except Exception as e:
                logger.debug(f"Error using dependency graph for reverse deps: {e}")
        
        # Fallback to AST analysis
        try:
            reverse_deps = self.ast_analyzer.find_reverse_dependencies(file_path, all_files)
            for dep in reverse_deps:
                reverse_dependencies.append(
                    {
                        "file": dep.source_file,
                        "line": dep.line_number,
                        "relationship": dep.relationship_type,
                        "details": dep.details,
                    }
                )
        except Exception as e:
            logger.debug(f"Error in AST reverse dependency analysis: {e}")
        
        return reverse_dependencies

    def _get_relative_path(self, file_path: str) -> str:
        """Convert absolute file path to relative path for dependency graph lookup."""
        try:
            # Use path normalizer if available (same as centrality analysis)
            if self.path_normalizer:
                return self.path_normalizer.normalize_path(file_path)
            
            # Fallback to simple path resolution
            if not os.path.isabs(file_path):
                return file_path
            
            # Try to make it relative to project root
            if hasattr(self, 'project_root') and self.project_root:
                project_root = str(self.project_root)
                if file_path.startswith(project_root):
                    return os.path.relpath(file_path, project_root)
            
            # Fallback: return the filename
            return os.path.basename(file_path)
        except Exception:
            return file_path

    def _analyze_function_calls(
        self, function_calls: List[Any], imports: List[Any] = None
    ) -> List[Dict[str, Any]]:
        """Analyze function calls in the file.

        Args:
            function_calls: List of function call objects
            imports: List of import objects for source resolution

        Returns:
            List of function call analysis dictionaries
        """
        # Build a mapping of imported names to their sources
        import_map = {}
        if imports:
            for imp in imports:
                # Handle direct imports: import module as alias
                if hasattr(imp, 'alias') and imp.alias and hasattr(imp, 'module'):
                    import_map[imp.alias] = imp.module
                # Handle symbol imports: from module import symbol1, symbol2
                elif hasattr(imp, 'symbols') and imp.symbols and hasattr(imp, 'module'):
                    for symbol in imp.symbols:
                        import_map[symbol] = imp.module
                # Handle module imports: import module (use module name itself)
                elif hasattr(imp, 'module') and imp.module:
                    # Extract the last part of the module name for direct usage
                    module_name = imp.module.split('.')[-1]
                    import_map[module_name] = imp.module

        function_call_analysis = []
        for func_call in function_calls:
            # Try to determine the source of the function call
            source_info = self._determine_function_source(func_call, import_map)
            
            function_call_analysis.append(
                {
                    "function": func_call.callee,
                    "line": func_call.line_number,
                    "is_method_call": func_call.is_method_call,
                    "object_name": func_call.object_name,
                    "source": source_info,
                    "resolved_callee": getattr(func_call, 'resolved_callee', None),
                }
            )
        return function_call_analysis

    def _determine_function_source(self, func_call: Any, import_map: Dict[str, str] = None) -> str:
        """Determine where a function call comes from.
        
        Args:
            func_call: FunctionCall object
            import_map: Mapping of imported names to their source modules
            
        Returns:
            Source information string
        """
        try:
            # If we have resolved callee information, use it
            if hasattr(func_call, 'resolved_callee') and func_call.resolved_callee:
                return f"from {func_call.resolved_callee}"
            
            # If it's a method call, try to determine the object source
            if func_call.is_method_call and func_call.object_name:
                # Check if object_name is an imported module
                if import_map and func_call.object_name in import_map:
                    return f"method of {func_call.object_name} (from {import_map[func_call.object_name]})"
                # Check if object_name looks like a built-in
                elif func_call.object_name in ['console', 'document', 'window', 'process']:
                    return f"built-in {func_call.object_name}"
                elif func_call.object_name.startswith('_'):
                    return f"private {func_call.object_name}"
                else:
                    return f"method of {func_call.object_name}"
            
            # Check if the function name is directly imported
            if import_map and func_call.callee in import_map:
                return f"from {import_map[func_call.callee]}"
            
            # Check if it's a common built-in function
            built_ins = [
                'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set',
                'range', 'enumerate', 'zip', 'map', 'filter', 'sorted',
                'max', 'min', 'sum', 'abs', 'round', 'type', 'isinstance',
                'hasattr', 'getattr', 'setattr', 'delattr', 'dir', 'vars',
                'locals', 'globals', 'eval', 'exec', 'compile', 'open',
                'input', 'raw_input', 'reload', 'help', 'exit', 'quit'
            ]
            
            if func_call.callee in built_ins:
                return "built-in function"
            
            # Check if it looks like a test function
            test_functions = [
                'describe', 'it', 'test', 'beforeEach', 'afterEach', 'beforeAll', 'afterAll',
                'expect', 'assert', 'mock', 'spy', 'stub', 'sinon', 'jest'
            ]
            
            if func_call.callee in test_functions:
                return "test framework"
            
            # Default to unknown source
            return "unknown source"
            
        except Exception as e:
            logger.debug(f"Error determining function source: {e}")
            return "unknown source"

    def _calculate_structural_impact(
        self, ast_result: FileAnalysisResult
    ) -> Dict[str, Any]:
        """Calculate structural impact metrics.

        Args:
            ast_result: AST analysis result

        Returns:
            Structural impact dictionary
        """
        # Calculate impact score based on various factors
        impact_score = self._calculate_impact_score(ast_result)
        
        return {
            "total_imports": len(ast_result.imports),
            "total_function_calls": len(ast_result.function_calls),
            "defined_functions": len(ast_result.defined_functions),
            "defined_classes": len(ast_result.defined_classes),
            "line_count": ast_result.line_count,
            "impact_score": impact_score,
        }

    def _calculate_impact_score(self, ast_result: FileAnalysisResult) -> float:
        """Calculate impact score based on file complexity and structure.

        Args:
            ast_result: AST analysis result

        Returns:
            Impact score between 0.0 and 1.0
        """
        try:
            # Base score from file size
            line_count = ast_result.line_count
            size_score = min(line_count / 1000.0, 0.3)  # Cap at 0.3 for large files

            # Score from number of imports (more imports = more dependencies)
            import_count = len(ast_result.imports)
            import_score = min(import_count / 50.0, 0.2)  # Cap at 0.2

            # Score from function calls (more calls = more complexity)
            function_calls = len(ast_result.function_calls)
            call_score = min(function_calls / 200.0, 0.2)  # Cap at 0.2

            # Score from defined functions/classes (more definitions = more impact)
            defined_functions = len(ast_result.defined_functions)
            defined_classes = len(ast_result.defined_classes)
            definition_score = min((defined_functions + defined_classes * 2) / 20.0, 0.3)  # Classes weighted more

            # Combine scores
            total_score = size_score + import_score + call_score + definition_score
            
            # Normalize to 0.0-1.0 range
            return min(total_score, 1.0)
            
        except Exception as e:
            logger.error(f"Error calculating impact score: {e}")
            return 0.0

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
