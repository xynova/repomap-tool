"""
AST visitor classes for different analysis types.

This module provides specialized AST visitors for extracting different types of
information from Python AST trees, including imports, function calls, and definitions.
"""

import ast
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

from .models import Import, ImportType, FunctionCall

logger = logging.getLogger(__name__)


@dataclass
class AnalysisContext:
    """Context information for AST analysis."""

    file_path: str
    content: str
    analysis_type: str


class BaseASTVisitor(ast.NodeVisitor):
    """Base class for AST visitors with common functionality."""

    def __init__(self, context: AnalysisContext):
        """Initialize the visitor with analysis context."""
        self.context = context
        self.imports: List[Import] = []
        self.function_calls: List[FunctionCall] = []
        self.defined_functions: List[str] = []
        self.defined_classes: List[str] = []
        self.used_classes: List[str] = []
        self.used_variables: List[str] = []
        self.analysis_errors: List[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import nodes."""
        try:
            import_objs = self._extract_imports(node)
            self.imports.extend(import_objs)
        except Exception as e:
            self.analysis_errors.append(
                f"Error processing import at line {getattr(node, 'lineno', 'unknown')}: {e}"
            )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit import from nodes."""
        try:
            import_objs = self._extract_imports(node)
            self.imports.extend(import_objs)
        except Exception as e:
            self.analysis_errors.append(
                f"Error processing import from at line {getattr(node, 'lineno', 'unknown')}: {e}"
            )

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes."""
        try:
            func_call = self._extract_function_call(node)
            if func_call:
                self.function_calls.append(func_call)
        except Exception as e:
            self.analysis_errors.append(
                f"Error processing function call at line {getattr(node, 'lineno', 'unknown')}: {e}"
            )

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes."""
        self.defined_functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes."""
        self.defined_classes.append(node.name)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name nodes."""
        if isinstance(node.ctx, ast.Load):
            self.used_variables.append(node.id)
        self.generic_visit(node)

    def _extract_imports(self, node: ast.Import | ast.ImportFrom) -> List[Import]:
        """Extract import information from an AST node."""
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

    def _extract_function_call(self, node: ast.Call) -> Optional[FunctionCall]:
        """Extract function call information from an AST node."""
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
                file_path=self.context.file_path,
                line_number=node.lineno,
                is_method_call=is_method_call,
                object_name=object_name,
            )

        except Exception as e:
            logger.debug(f"Error extracting function call: {e}")
            return None


class ImportVisitor(BaseASTVisitor):
    """AST visitor specialized for import analysis."""

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import nodes."""
        super().visit_Import(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit import from nodes."""
        super().visit_ImportFrom(node)


class FunctionCallVisitor(BaseASTVisitor):
    """AST visitor specialized for function call analysis."""

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes."""
        super().visit_Call(node)


class DefinitionVisitor(BaseASTVisitor):
    """AST visitor specialized for definition analysis."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes."""
        super().visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes."""
        super().visit_ClassDef(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name nodes."""
        super().visit_Name(node)


class ComprehensiveVisitor(BaseASTVisitor):
    """AST visitor that performs all types of analysis."""

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import nodes."""
        super().visit_Import(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit import from nodes."""
        super().visit_ImportFrom(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call nodes."""
        super().visit_Call(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition nodes."""
        super().visit_FunctionDef(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition nodes."""
        super().visit_ClassDef(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name nodes."""
        super().visit_Name(node)


def create_visitor(analysis_type: str, context: AnalysisContext) -> BaseASTVisitor:
    """Create an appropriate visitor based on analysis type.

    Args:
        analysis_type: Type of analysis to perform
        context: Analysis context

    Returns:
        Appropriate AST visitor instance
    """
    if analysis_type == "imports":
        return ImportVisitor(context)
    elif analysis_type == "function_calls":
        return FunctionCallVisitor(context)
    elif analysis_type == "class_usage":
        return DefinitionVisitor(context)
    elif analysis_type == "variable_usage":
        return DefinitionVisitor(context)
    else:  # "all" or any other type
        return ComprehensiveVisitor(context)
