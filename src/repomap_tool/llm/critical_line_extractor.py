"""
Critical line extractor for LLM optimization.

This module extracts the most important lines from functions and classes
to provide LLMs with the essence of code implementation without wasting
tokens on less critical details.
"""

import ast
import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from pathlib import Path

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
            # Return empty module if parsing fails
            return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Python AST."""
        critical_nodes = []

        for node in ast.walk(tree):
            node_info = self._analyze_node(node)
            if node_info and node_info["importance"] > 0.0:
                critical_nodes.append(node_info)

        return sorted(critical_nodes, key=lambda x: x["importance"], reverse=True)

    def _analyze_node(self, node: ast.AST) -> Optional[Dict]:
        """Analyze individual AST node for importance."""
        if isinstance(node, ast.Return):
            return {
                "line_number": getattr(node, "lineno", 0),
                "content": ast.unparse(node),
                "importance": 0.95,
                "pattern_type": "return_statement",
            }

        elif isinstance(node, ast.If):
            return {
                "line_number": getattr(node, "lineno", 0),
                "content": f"if {ast.unparse(node.test)}:",
                "importance": 0.90,
                "pattern_type": "conditional_logic",
            }

        elif isinstance(node, ast.Raise):
            return {
                "line_number": getattr(node, "lineno", 0),
                "content": ast.unparse(node),
                "importance": 0.85,
                "pattern_type": "error_handling",
            }

        elif isinstance(node, ast.Call):
            # Check if it's an important method call
            if isinstance(node.func, ast.Attribute):
                method_name = node.func.attr
                if method_name in [
                    "verify_password",
                    "authenticate",
                    "validate",
                    "save",
                    "delete",
                ]:
                    return {
                        "line_number": getattr(node, "lineno", 0),
                        "content": ast.unparse(node),
                        "importance": 0.80,
                        "pattern_type": "important_method_call",
                    }

        elif isinstance(node, ast.Assign):
            # Check for important assignments
            if isinstance(node.targets[0], ast.Name):
                var_name = node.targets[0].id
                if var_name in ["user", "session", "result", "error", "status"]:
                    return {
                        "line_number": getattr(node, "lineno", 0),
                        "content": ast.unparse(node),
                        "importance": 0.75,
                        "pattern_type": "important_assignment",
                    }

        return None


class JavaScriptCriticalAnalyzer(LanguageAnalyzer):
    """JavaScript/TypeScript critical line analyzer."""

    def __init__(self):
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse JavaScript code (simplified for now)."""
        self.code = code  # Store code for later use
        # For now, return a simple structure
        # In production, would use proper JS parser like esprima
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in JavaScript code using regex patterns."""
        # Simplified pattern matching for JavaScript
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"throw\s+[^;]+;", 0.85, "error_handling"),
            (r"console\.(log|error|warn)\s*\([^)]+\)", 0.70, "logging"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line.strip()):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line.strip(),
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class GoCriticalAnalyzer(LanguageAnalyzer):
    """Go language critical line analyzer."""

    def __init__(self):
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Go code (simplified for now)."""
        self.code = code  # Store code for later use
        # For now, return a simple structure
        # In production, would use proper Go parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Go code using regex patterns."""
        patterns = [
            (r"return\s+[^}]+", 0.95, "return_statement"),
            (r"if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"for\s+[^{]+{", 0.85, "loop_structure"),
            (r"func\s+\w+\([^)]*\)\s*[^{]*{", 0.80, "function_definition"),
            (r"panic\s*\([^)]*\)", 0.85, "error_handling"),
            (r"defer\s+[^}]+", 0.75, "defer_statement"),
            (r"go\s+[^}]+", 0.80, "goroutine"),
            (r"select\s*{", 0.80, "select_statement"),
            (r"case\s+[^:]+:", 0.75, "case_statement"),
            (r"default:", 0.70, "default_case"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line.strip()):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line.strip(),
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class JavaCriticalAnalyzer(LanguageAnalyzer):
    """Java language critical line analyzer."""

    def __init__(self):
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Java code (simplified for now)."""
        self.code = code  # Store code for later use
        # For now, return a simple structure
        # In production, would use proper Java parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Java code using regex patterns."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"for\s*\([^)]*\)\s*{?", 0.85, "loop_structure"),
            (r"while\s*\([^)]*\)\s*{?", 0.85, "loop_structure"),
            (
                r"public\s+(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"public\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (r"throw\s+new\s+\w+Exception[^;]*;", 0.85, "error_handling"),
            (r"try\s*{", 0.80, "try_block"),
            (r"catch\s*\([^)]+\)\s*{", 0.80, "catch_block"),
            (r"finally\s*{", 0.75, "finally_block"),
            (r"synchronized\s*\([^)]+\)\s*{", 0.80, "synchronized_block"),
            (r"@\w+", 0.70, "annotation"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line.strip()):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line.strip(),
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class CSharpCriticalAnalyzer(LanguageAnalyzer):
    """C# language critical line analyzer."""

    def __init__(self):
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse C# code (simplified for now)."""
        self.code = code  # Store code for later use
        # For now, return a simple structure
        # In production, would use proper C# parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in C# code using regex patterns."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"for\s*\([^)]*\)\s*{?", 0.85, "loop_structure"),
            (r"foreach\s*\([^)]*\)\s*{?", 0.85, "loop_structure"),
            (r"while\s*\([^)]*\)\s*{?", 0.85, "loop_structure"),
            (
                r"public\s+(?:static\s+)?(?:sealed\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"public\s+(?:static\s+)?(?:virtual\s+)?(?:abstract\s+)?(?:override\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (r"throw\s+new\s+\w+Exception[^;]*;", 0.85, "error_handling"),
            (r"try\s*{", 0.80, "try_block"),
            (r"catch\s*\([^)]+\)\s*{", 0.80, "catch_block"),
            (r"finally\s*{", 0.75, "finally_block"),
            (r"using\s+[^;]+;", 0.70, "using_statement"),
            (r"namespace\s+\w+", 0.75, "namespace_declaration"),
            (r"\[[^\]]+\]", 0.70, "attribute"),
            (r"async\s+\w+\s+\w+\s*\([^)]*\)", 0.80, "async_method"),
            (r"await\s+[^;]+;", 0.75, "await_statement"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line.strip()):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line.strip(),
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class RustCriticalAnalyzer(LanguageAnalyzer):
    """Rust language critical line analyzer."""

    def __init__(self):
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Rust code (simplified for now)."""
        self.code = code  # Store code for later use
        # For now, return a simple structure
        # In production, would use proper Rust parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Rust code using regex patterns."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"for\s+[^{]+{", 0.85, "loop_structure"),
            (r"while\s+[^{]+{", 0.85, "loop_structure"),
            (r"loop\s*{", 0.85, "loop_structure"),
            (r"fn\s+\w+\([^)]*\)\s*[^{]*{", 0.80, "function_definition"),
            (r"pub\s+(?:struct|enum|trait|impl)\s+\w+", 0.80, "type_definition"),
            (r"panic!\s*\([^)]*\)", 0.85, "error_handling"),
            (r"Result<[^>]+>", 0.80, "result_type"),
            (r"Option<[^>]+>", 0.80, "option_type"),
            (r"match\s+[^{]+{", 0.85, "match_statement"),
            (r"Some\s*\([^)]*\)", 0.75, "some_variant"),
            (r"None", 0.75, "none_variant"),
            (r"Ok\s*\([^)]*\)", 0.75, "ok_variant"),
            (r"Err\s*\([^)]*\)", 0.75, "err_variant"),
            (r"unsafe\s*{", 0.85, "unsafe_block"),
            (r"#\[[^\]]+\]", 0.70, "attribute"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line.strip()):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line.strip(),
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class CriticalLineExtractor:
    """Extracts critical lines from code symbols for LLM optimization."""

    def __init__(self):
        self.language_analyzers = {
            "python": PythonCriticalAnalyzer(),
            "javascript": JavaScriptCriticalAnalyzer(),
            "typescript": JavaScriptCriticalAnalyzer(),  # Same as JS for now
            "js": JavaScriptCriticalAnalyzer(),
            "go": GoCriticalAnalyzer(),
            "golang": GoCriticalAnalyzer(),
            "java": JavaCriticalAnalyzer(),
            "csharp": CSharpCriticalAnalyzer(),
            "c#": CSharpCriticalAnalyzer(),
            "cs": CSharpCriticalAnalyzer(),
            "rust": RustCriticalAnalyzer(),
        }
        self.importance_threshold = 0.7

    def extract_critical_lines(
        self, symbol_content: str, language: str = "python"
    ) -> List[CriticalLine]:
        """Extract critical lines from symbol content.

        Args:
            symbol_content: Raw code content
            language: Programming language

        Returns:
            List of CriticalLine objects sorted by importance
        """
        try:
            analyzer = self.language_analyzers.get(language.lower())
            if not analyzer:
                logger.warning(f"No analyzer for language: {language}")
                return self._fallback_extraction(symbol_content)

            # Parse code using language-specific analyzer
            tree = analyzer.parse_code(symbol_content)
            critical_nodes = analyzer.find_critical_nodes(tree)

            # Convert to CriticalLine objects
            critical_lines = []
            for node in critical_nodes:
                if node["importance"] >= self.importance_threshold:
                    critical_line = CriticalLine(
                        line_number=node["line_number"],
                        content=node["content"],
                        importance=node["importance"],
                        pattern_type=node["pattern_type"],
                    )
                    critical_lines.append(critical_line)

            # Sort by importance and limit to top results
            critical_lines.sort(key=lambda x: x.importance, reverse=True)
            return critical_lines[:5]  # Top 5 most critical lines

        except Exception as e:
            logger.error(f"Error extracting critical lines: {e}")
            return self._fallback_extraction(symbol_content)

    def _fallback_extraction(self, content: str) -> List[CriticalLine]:
        """Fallback extraction using simple pattern matching."""
        critical_lines = []
        lines = content.split("\n")

        # Multi-language fallback patterns
        fallback_patterns = [
            # Common patterns across languages
            (r"return\s+", 0.8, "return_statement"),
            (r"if\s+", 0.7, "conditional_logic"),
            (r"for\s+", 0.7, "loop_structure"),
            (r"while\s+", 0.7, "loop_statement"),
            # Python
            (r"def\s+", 0.6, "function_definition"),
            (r"class\s+", 0.6, "class_definition"),
            (r"raise\s+", 0.7, "error_handling"),
            # JavaScript/TypeScript
            (r"function\s+", 0.6, "function_definition"),
            (r"const\s+", 0.5, "variable_declaration"),
            (r"let\s+", 0.5, "variable_declaration"),
            (r"throw\s+", 0.7, "error_handling"),
            # Go
            (r"func\s+", 0.6, "function_definition"),
            (r"panic\s*\(", 0.7, "error_handling"),
            (r"defer\s+", 0.6, "defer_statement"),
            (r"go\s+", 0.6, "goroutine"),
            # Java
            (r"public\s+", 0.6, "access_modifier"),
            (r"private\s+", 0.6, "access_modifier"),
            (r"protected\s+", 0.6, "access_modifier"),
            (r"class\s+", 0.6, "class_definition"),
            (r"interface\s+", 0.6, "interface_definition"),
            (r"throw\s+", 0.7, "error_handling"),
            (r"try\s*{", 0.6, "try_block"),
            (r"catch\s*\(", 0.6, "catch_block"),
            # C#
            (r"public\s+", 0.6, "access_modifier"),
            (r"private\s+", 0.6, "access_modifier"),
            (r"class\s+", 0.6, "class_definition"),
            (r"interface\s+", 0.6, "interface_definition"),
            (r"struct\s+", 0.6, "struct_definition"),
            (r"namespace\s+", 0.6, "namespace_declaration"),
            (r"using\s+", 0.5, "using_statement"),
            (r"throw\s+", 0.7, "error_handling"),
            (r"try\s*{", 0.6, "try_block"),
            (r"catch\s*\(", 0.6, "catch_block"),
            (r"async\s+", 0.6, "async_method"),
            (r"await\s+", 0.6, "await_statement"),
            # Rust
            (r"fn\s+", 0.6, "function_definition"),
            (r"pub\s+", 0.6, "visibility_modifier"),
            (r"struct\s+", 0.6, "struct_definition"),
            (r"enum\s+", 0.6, "enum_definition"),
            (r"trait\s+", 0.6, "trait_definition"),
            (r"impl\s+", 0.6, "implementation_block"),
            (r"panic!\s*\(", 0.7, "error_handling"),
            (r"match\s+", 0.6, "match_statement"),
            (r"Some\s*\(", 0.6, "some_variant"),
            (r"None", 0.6, "none_variant"),
            (r"Ok\s*\(", 0.6, "ok_variant"),
            (r"Err\s*\(", 0.6, "err_variant"),
        ]

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith('"""'):
                continue

            for pattern, importance, pattern_type in fallback_patterns:
                if re.search(pattern, line):
                    critical_lines.append(
                        CriticalLine(
                            line_number=line_num,
                            content=line,
                            importance=importance,
                            pattern_type=pattern_type,
                        )
                    )
                    break

        return critical_lines[:3]  # Top 3 for fallback

    def get_implementation_essence(
        self, symbol_content: str, language: str = "python"
    ) -> str:
        """Get a concise summary of what the symbol does.

        Args:
            symbol_content: Raw code content
            language: Programming language

        Returns:
            Concise description of the symbol's purpose
        """
        critical_lines = self.extract_critical_lines(symbol_content, language)

        if not critical_lines:
            return "Implementation details not available"

        # Create essence from critical lines
        essence_parts = []
        for line in critical_lines[:2]:  # Use top 2 lines
            if line.pattern_type == "return_statement":
                essence_parts.append("Returns value")
            elif line.pattern_type == "conditional_logic":
                essence_parts.append("Has conditional logic")
            elif line.pattern_type == "error_handling":
                essence_parts.append("Handles errors")
            elif line.pattern_type == "important_method_call":
                essence_parts.append("Calls important methods")

        if not essence_parts:
            essence_parts.append("Contains business logic")

        return "; ".join(essence_parts)

    def rank_line_importance(
        self, lines: List[str], symbol_type: str = "function"
    ) -> List[float]:
        """Rank lines by importance for LLM understanding.

        Args:
            lines: List of code lines
            symbol_type: Type of symbol (function, class, etc.)

        Returns:
            List of importance scores for each line
        """
        importance_scores = []

        for line in lines:
            line = line.strip()
            if not line:
                importance_scores.append(0.0)
                continue

            # Base importance based on symbol type
            base_score = 0.5 if symbol_type == "function" else 0.4

            # Boost for important patterns
            if re.search(r"return\s+", line):
                base_score += 0.3
            elif re.search(r"if\s+", line):
                base_score += 0.25
            elif re.search(r"raise\s+", line):
                base_score += 0.25
            elif re.search(r"def\s+", line):
                base_score += 0.2
            elif re.search(r"class\s+", line):
                base_score += 0.2

            # Penalize comments and empty lines
            if line.startswith("#") or line.startswith('"""'):
                base_score -= 0.1

            importance_scores.append(min(1.0, max(0.0, base_score)))

        return importance_scores
