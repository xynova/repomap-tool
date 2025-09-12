"""
Critical line extractor for LLM optimization.

This module provides the CriticalLine dataclass and Python-specific analyzer.
All other language analysis is now handled by AiderBasedExtractor using tree-sitter.
"""

import ast
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CriticalLine:
    """Represents a critical line of code with importance scoring."""

    line_number: int
    content: str
    importance: float
    pattern_type: str
    context: Optional[str] = None


class LanguageAnalyzer:
    """Base class for language-specific code analysis."""

    def parse_code(self, code: str) -> ast.AST:
        """Parse code into AST representation."""
        raise NotImplementedError("Subclasses must implement parse_code")

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in the AST."""
        raise NotImplementedError("Subclasses must implement find_critical_nodes")


class PythonCriticalAnalyzer(LanguageAnalyzer):
    """Python-specific critical line analyzer using AST."""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Python code into AST."""
        try:
            return ast.parse(code)
        except SyntaxError as e:
            logger.warning(f"Failed to parse Python code: {e}")
            return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Python AST."""
        critical_nodes = []

        for node in ast.walk(tree):
            critical_node = self._analyze_node(node)
            if critical_node:
                critical_nodes.append(critical_node)

        return critical_nodes

    def _analyze_node(self, node: ast.AST) -> Optional[Dict]:
        """Analyze a single AST node for criticality."""
        if isinstance(node, ast.FunctionDef):
            return {
                "line_number": node.lineno,
                "content": f"def {node.name}({', '.join(arg.arg for arg in node.args.args)})",
                "importance": 0.9,
                "pattern_type": "function_definition",
            }
        elif isinstance(node, ast.ClassDef):
            return {
                "line_number": node.lineno,
                "content": f"class {node.name}",
                "importance": 0.85,
                "pattern_type": "class_definition",
            }
        elif isinstance(node, ast.Return):
            return {
                "line_number": node.lineno,
                "content": "return statement",
                "importance": 0.8,
                "pattern_type": "return_statement",
            }
        elif isinstance(node, ast.Import):
            return {
                "line_number": node.lineno,
                "content": f"import {', '.join(alias.name for alias in node.names)}",
                "importance": 0.7,
                "pattern_type": "import_statement",
            }
        elif isinstance(node, ast.ImportFrom):
            return {
                "line_number": node.lineno,
                "content": f"from {node.module} import {', '.join(alias.name for alias in node.names)}",
                "importance": 0.7,
                "pattern_type": "import_from_statement",
            }
        elif isinstance(node, ast.Assign):
            # Check if it's an important assignment (class/function assignment)
            if (
                len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, (ast.Call, ast.Lambda))
            ):
                return {
                    "line_number": node.lineno,
                    "content": f"{node.targets[0].id} = ...",
                    "importance": 0.75,
                    "pattern_type": "important_assignment",
                }

        return None


# All other language analyzers (Go, Java, C#, Rust) have been removed.
# They used 300+ regex patterns and are now replaced by AiderBasedExtractor
# which uses tree-sitter for proper AST parsing across all languages.
