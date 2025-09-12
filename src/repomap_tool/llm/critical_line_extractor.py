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


# DEPRECATED: Use AiderBasedExtractor instead
# This analyzer used 31+ regex patterns when aider already provides tree-sitter
class JavaScriptCriticalAnalyzer(LanguageAnalyzer):
    """DEPRECATED: Use AiderBasedExtractor for tree-sitter-based analysis."""

    def __init__(self) -> None:
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """DEPRECATED: Use aider's tree-sitter parsing instead."""
        self.code = code
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in JavaScript code using enhanced pattern recognition."""
        # Enhanced pattern matching for JavaScript/TypeScript
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s+if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s*{?", 0.85, "conditional_logic"),
            (r"throw\s+[^;]+;", 0.85, "error_handling"),
            (r"try\s*{", 0.80, "error_handling"),
            (r"catch\s*\([^)]+\)\s*{", 0.80, "error_handling"),
            (r"finally\s*{", 0.75, "error_handling"),
            (r"function\s+\w+\s*\([^)]*\)\s*{", 0.80, "function_definition"),
            (r"const\s+\w+\s*=\s*\([^)]*\)\s*=>", 0.80, "arrow_function"),
            (r"let\s+\w+\s*=\s*\([^)]*\)\s*=>", 0.80, "arrow_function"),
            (r"class\s+\w+\s*(?:extends\s+\w+)?\s*{", 0.85, "class_definition"),
            (r"async\s+function\s+\w+\s*\([^)]*\)\s*{", 0.85, "async_function"),
            (r"await\s+[^;]+;", 0.80, "await_statement"),
            (r"Promise\.(resolve|reject|all|race)\s*\(", 0.80, "promise_handling"),
            (r"\.then\s*\(", 0.75, "promise_handling"),
            (r"\.catch\s*\(", 0.75, "promise_handling"),
            (r"console\.(log|error|warn|info|debug)\s*\(", 0.70, "logging"),
            (
                r"export\s+(?:default\s+)?(?:const|let|var|function|class)",
                0.75,
                "export_statement",
            ),
            (r"import\s+.*from\s+['\"][^'\"]+['\"]", 0.70, "import_statement"),
            (r"require\s*\(['\"][^'\"]+['\"]\)", 0.70, "require_statement"),
            (r"switch\s*\([^)]+\)\s*{", 0.80, "switch_statement"),
            (r"case\s+[^:]+:", 0.75, "case_statement"),
            (r"default\s*:", 0.70, "default_case"),
            (r"for\s*\([^)]*\)\s*{", 0.80, "for_loop"),
            (r"for\s+\([^)]*\)\s+of\s+", 0.80, "for_of_loop"),
            (r"for\s+\([^)]*\)\s+in\s+", 0.80, "for_in_loop"),
            (r"while\s*\([^)]+\)\s*{", 0.80, "while_loop"),
            (r"do\s*{", 0.80, "do_while_loop"),
            (r"break\s*;", 0.70, "break_statement"),
            (r"continue\s*;", 0.70, "continue_statement"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if (
                not line_stripped
                or line_stripped.startswith("//")
                or line_stripped.startswith("/*")
            ):
                continue

            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line_stripped):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line_stripped,
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class GoCriticalAnalyzer(LanguageAnalyzer):
    """Go language critical line analyzer."""

    def __init__(self) -> None:
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Go code with enhanced pattern recognition."""
        self.code = code  # Store code for later use
        # Enhanced regex-based parsing for Go language constructs
        # In production, would use proper Go parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Go code using enhanced pattern recognition."""
        patterns = [
            (r"return\s+[^}]+", 0.95, "return_statement"),
            (r"if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"else\s+if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"else\s*{", 0.85, "conditional_logic"),
            (r"for\s+[^{]+{", 0.85, "for_loop"),
            (r"for\s*{", 0.80, "infinite_loop"),
            (r"range\s+[^{]+{", 0.85, "range_loop"),
            (r"func\s+\w+\([^)]*\)\s*[^{]*{", 0.80, "function_definition"),
            (r"func\s*\([^)]*\)\s+\w+\([^)]*\)\s*[^{]*{", 0.85, "method_definition"),
            (r"type\s+\w+\s+(?:struct|interface|func)\s*{", 0.85, "type_definition"),
            (r"panic\s*\([^)]*\)", 0.85, "error_handling"),
            (r"defer\s+[^}]+", 0.75, "defer_statement"),
            (r"go\s+[^}]+", 0.80, "goroutine"),
            (r"select\s*{", 0.80, "select_statement"),
            (r"case\s+[^:]+:", 0.75, "case_statement"),
            (r"default:", 0.70, "default_case"),
            (r"chan\s+[^=]+", 0.80, "channel_declaration"),
            (r"make\s*\([^)]+\)", 0.75, "make_function"),
            (r"new\s*\([^)]+\)", 0.75, "new_function"),
            (r"interface\s*{", 0.80, "interface_definition"),
            (r"struct\s*{", 0.80, "struct_definition"),
            (r"const\s+[^=]+=", 0.70, "constant_declaration"),
            (r"var\s+[^=]+=", 0.70, "variable_declaration"),
            (r"import\s+[^;]+", 0.70, "import_statement"),
            (r"package\s+\w+", 0.75, "package_declaration"),
            (r"switch\s+[^{]+{", 0.80, "switch_statement"),
            (r"fallthrough", 0.70, "fallthrough_statement"),
            (r"break", 0.70, "break_statement"),
            (r"continue", 0.70, "continue_statement"),
            (r"goto\s+\w+", 0.70, "goto_statement"),
            (r"map\s*\[[^\]]+\][^{]+{", 0.75, "map_literal"),
            (r"\[\]\w+\s*{", 0.75, "slice_literal"),
            (r"\.\.\.", 0.70, "variadic_parameter"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if (
                not line_stripped
                or line_stripped.startswith("//")
                or line_stripped.startswith("/*")
            ):
                continue

            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line_stripped):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line_stripped,
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class JavaCriticalAnalyzer(LanguageAnalyzer):
    """Java language critical line analyzer."""

    def __init__(self) -> None:
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Java code with enhanced pattern recognition."""
        self.code = code  # Store code for later use
        # Enhanced regex-based parsing for Java language constructs
        # In production, would use proper Java parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Java code using enhanced pattern recognition."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s+if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s*{", 0.85, "conditional_logic"),
            (r"for\s*\([^)]*\)\s*{?", 0.85, "for_loop"),
            (r"while\s*\([^)]*\)\s*{?", 0.85, "while_loop"),
            (r"do\s*{", 0.85, "do_while_loop"),
            (r"switch\s*\([^)]+\)\s*{", 0.80, "switch_statement"),
            (r"case\s+[^:]+:", 0.75, "case_statement"),
            (r"default:", 0.70, "default_case"),
            (
                r"public\s+(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"private\s+(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"protected\s+(?:static\s+)?(?:final\s+)?(?:class|interface|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"public\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (
                r"private\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (
                r"protected\s+(?:static\s+)?(?:final\s+)?(?:abstract\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (r"throw\s+new\s+\w+Exception[^;]*;", 0.85, "error_handling"),
            (r"throw\s+[^;]+;", 0.85, "error_handling"),
            (r"try\s*{", 0.80, "try_block"),
            (r"catch\s*\([^)]+\)\s*{", 0.80, "catch_block"),
            (r"finally\s*{", 0.75, "finally_block"),
            (r"synchronized\s*\([^)]+\)\s*{", 0.80, "synchronized_block"),
            (r"@\w+", 0.70, "annotation"),
            (r"@Override", 0.75, "override_annotation"),
            (r"@Deprecated", 0.75, "deprecated_annotation"),
            (r"@SuppressWarnings", 0.70, "suppress_warnings_annotation"),
            (r"import\s+[^;]+;", 0.70, "import_statement"),
            (r"package\s+[^;]+;", 0.75, "package_declaration"),
            (r"extends\s+\w+", 0.80, "inheritance"),
            (r"implements\s+[^{]+{", 0.80, "interface_implementation"),
            (r"new\s+\w+\s*\([^)]*\)", 0.75, "object_instantiation"),
            (r"super\s*\([^)]*\)", 0.80, "super_constructor_call"),
            (r"this\s*\([^)]*\)", 0.80, "this_constructor_call"),
            (r"break\s*;", 0.70, "break_statement"),
            (r"continue\s*;", 0.70, "continue_statement"),
            (r"assert\s+[^;]+;", 0.75, "assertion"),
            (r"volatile\s+", 0.75, "volatile_keyword"),
            (r"transient\s+", 0.70, "transient_keyword"),
            (r"native\s+", 0.75, "native_method"),
            (r"strictfp\s+", 0.70, "strictfp_keyword"),
            (r"enum\s+\w+\s*{", 0.80, "enum_definition"),
            (r"interface\s+\w+\s*{", 0.80, "interface_definition"),
            (r"abstract\s+class\s+\w+", 0.85, "abstract_class"),
            (r"final\s+class\s+\w+", 0.80, "final_class"),
            (r"static\s+class\s+\w+", 0.80, "static_class"),
            (r"inner\s+class", 0.75, "inner_class"),
            (r"anonymous\s+class", 0.75, "anonymous_class"),
            (r"lambda\s*\([^)]*\)\s*->", 0.80, "lambda_expression"),
            (r"Stream\s*\.", 0.75, "stream_api"),
            (r"Optional\s*\.", 0.75, "optional_api"),
            (r"CompletableFuture\s*\.", 0.80, "completable_future"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if (
                not line_stripped
                or line_stripped.startswith("//")
                or line_stripped.startswith("/*")
            ):
                continue

            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line_stripped):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line_stripped,
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class CSharpCriticalAnalyzer(LanguageAnalyzer):
    """C# language critical line analyzer."""

    def __init__(self) -> None:
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse C# code with enhanced pattern recognition."""
        self.code = code  # Store code for later use
        # Enhanced regex-based parsing for C# language constructs
        # In production, would use proper C# parser
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in C# code using enhanced pattern recognition."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s+if\s*\([^)]+\)\s*{?", 0.90, "conditional_logic"),
            (r"else\s*{", 0.85, "conditional_logic"),
            (r"for\s*\([^)]*\)\s*{?", 0.85, "for_loop"),
            (r"foreach\s*\([^)]*\)\s*{?", 0.85, "foreach_loop"),
            (r"while\s*\([^)]*\)\s*{?", 0.85, "while_loop"),
            (r"do\s*{", 0.85, "do_while_loop"),
            (r"switch\s*\([^)]+\)\s*{", 0.80, "switch_statement"),
            (r"case\s+[^:]+:", 0.75, "case_statement"),
            (r"default:", 0.70, "default_case"),
            (
                r"public\s+(?:static\s+)?(?:sealed\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"private\s+(?:static\s+)?(?:sealed\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"protected\s+(?:static\s+)?(?:sealed\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"internal\s+(?:static\s+)?(?:sealed\s+)?(?:abstract\s+)?(?:class|interface|struct|enum)\s+\w+",
                0.80,
                "class_definition",
            ),
            (
                r"public\s+(?:static\s+)?(?:virtual\s+)?(?:abstract\s+)?(?:override\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (
                r"private\s+(?:static\s+)?(?:virtual\s+)?(?:abstract\s+)?(?:override\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (
                r"protected\s+(?:static\s+)?(?:virtual\s+)?(?:abstract\s+)?(?:override\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (
                r"internal\s+(?:static\s+)?(?:virtual\s+)?(?:abstract\s+)?(?:override\s+)?\w+\s+\w+\s*\([^)]*\)",
                0.80,
                "method_definition",
            ),
            (r"throw\s+new\s+\w+Exception[^;]*;", 0.85, "error_handling"),
            (r"throw\s+[^;]+;", 0.85, "error_handling"),
            (r"try\s*{", 0.80, "try_block"),
            (r"catch\s*\([^)]+\)\s*{", 0.80, "catch_block"),
            (r"finally\s*{", 0.75, "finally_block"),
            (r"using\s+[^;]+;", 0.70, "using_statement"),
            (r"using\s+[^{]+{", 0.75, "using_block"),
            (r"namespace\s+\w+", 0.75, "namespace_declaration"),
            (r"\[[^\]]+\]", 0.70, "attribute"),
            (r"async\s+\w+\s+\w+\s*\([^)]*\)", 0.80, "async_method"),
            (r"await\s+[^;]+;", 0.75, "await_statement"),
            (r"Task\s*<[^>]+>", 0.80, "task_type"),
            (r"async\s+Task\s*<[^>]+>", 0.85, "async_task_method"),
            (r"var\s+\w+\s*=", 0.70, "var_declaration"),
            (r"const\s+\w+\s*=", 0.70, "const_declaration"),
            (r"readonly\s+", 0.75, "readonly_keyword"),
            (r"sealed\s+", 0.75, "sealed_keyword"),
            (r"virtual\s+", 0.75, "virtual_keyword"),
            (r"override\s+", 0.80, "override_keyword"),
            (r"abstract\s+", 0.80, "abstract_keyword"),
            (r"static\s+", 0.70, "static_keyword"),
            (r"partial\s+", 0.70, "partial_keyword"),
            (r"unsafe\s+", 0.75, "unsafe_keyword"),
            (r"volatile\s+", 0.75, "volatile_keyword"),
            (r"extern\s+", 0.75, "extern_keyword"),
            (r"fixed\s+", 0.75, "fixed_keyword"),
            (r"checked\s*{", 0.75, "checked_block"),
            (r"unchecked\s*{", 0.75, "unchecked_block"),
            (r"lock\s*\([^)]+\)\s*{", 0.80, "lock_statement"),
            (r"yield\s+return", 0.80, "yield_return"),
            (r"yield\s+break", 0.80, "yield_break"),
            (r"LINQ\s*\.", 0.75, "linq_extension"),
            (r"\.Where\s*\(", 0.75, "linq_where"),
            (r"\.Select\s*\(", 0.75, "linq_select"),
            (r"\.FirstOrDefault\s*\(", 0.75, "linq_first_or_default"),
            (r"\.Any\s*\(", 0.75, "linq_any"),
            (r"\.All\s*\(", 0.75, "linq_all"),
            (r"\.Count\s*\(", 0.75, "linq_count"),
            (r"\.Sum\s*\(", 0.75, "linq_sum"),
            (r"\.Average\s*\(", 0.75, "linq_average"),
            (r"\.Max\s*\(", 0.75, "linq_max"),
            (r"\.Min\s*\(", 0.75, "linq_min"),
            (r"\.OrderBy\s*\(", 0.75, "linq_order_by"),
            (r"\.GroupBy\s*\(", 0.75, "linq_group_by"),
            (r"\.Join\s*\(", 0.75, "linq_join"),
            (r"\.Distinct\s*\(", 0.75, "linq_distinct"),
            (r"\.Skip\s*\(", 0.75, "linq_skip"),
            (r"\.Take\s*\(", 0.75, "linq_take"),
            (r"\.ToList\s*\(", 0.75, "linq_to_list"),
            (r"\.ToArray\s*\(", 0.75, "linq_to_array"),
            (r"\.ToDictionary\s*\(", 0.75, "linq_to_dictionary"),
            (r"\.ToLookup\s*\(", 0.75, "linq_to_lookup"),
            (r"\.Aggregate\s*\(", 0.75, "linq_aggregate"),
            (r"\.Zip\s*\(", 0.75, "linq_zip"),
            (r"\.Union\s*\(", 0.75, "linq_union"),
            (r"\.Intersect\s*\(", 0.75, "linq_intersect"),
            (r"\.Except\s*\(", 0.75, "linq_except"),
            (r"\.Concat\s*\(", 0.75, "linq_concat"),
            (r"\.Reverse\s*\(", 0.75, "linq_reverse"),
            (r"\.DefaultIfEmpty\s*\(", 0.75, "linq_default_if_empty"),
            (r"\.OfType\s*<[^>]+>\s*\(", 0.75, "linq_of_type"),
            (r"\.Cast\s*<[^>]+>\s*\(", 0.75, "linq_cast"),
            (r"\.AsEnumerable\s*\(", 0.75, "linq_as_enumerable"),
            (r"\.AsQueryable\s*\(", 0.75, "linq_as_queryable"),
            (r"\.AsParallel\s*\(", 0.75, "linq_as_parallel"),
            (r"\.AsSequential\s*\(", 0.75, "linq_as_sequential"),
            (r"\.AsOrdered\s*\(", 0.75, "linq_as_ordered"),
            (r"\.AsUnordered\s*\(", 0.75, "linq_as_unordered"),
            (
                r"\.WithDegreeOfParallelism\s*\(",
                0.75,
                "linq_with_degree_of_parallelism",
            ),
            (r"\.WithExecutionMode\s*\(", 0.75, "linq_with_execution_mode"),
            (r"\.WithMergeOptions\s*\(", 0.75, "linq_with_merge_options"),
            (r"\.WithCancellation\s*\(", 0.75, "linq_with_cancellation"),
            (
                r"\.WithDegreeOfParallelism\s*\(",
                0.75,
                "linq_with_degree_of_parallelism",
            ),
            (r"\.WithExecutionMode\s*\(", 0.75, "linq_with_execution_mode"),
            (r"\.WithMergeOptions\s*\(", 0.75, "linq_with_merge_options"),
            (r"\.WithCancellation\s*\(", 0.75, "linq_with_cancellation"),
        ]

        critical_nodes = []
        lines = self.code.split("\n")

        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if (
                not line_stripped
                or line_stripped.startswith("//")
                or line_stripped.startswith("/*")
            ):
                continue

            for pattern, importance, pattern_type in patterns:
                if re.search(pattern, line_stripped):
                    critical_nodes.append(
                        {
                            "line_number": line_num,
                            "content": line_stripped,
                            "importance": importance,
                            "pattern_type": pattern_type,
                        }
                    )
                    break

        return critical_nodes


class RustCriticalAnalyzer(LanguageAnalyzer):
    """Rust language critical line analyzer."""

    def __init__(self) -> None:
        self.code = ""

    def parse_code(self, code: str) -> ast.AST:
        """Parse Rust code with enhanced pattern recognition."""
        self.code = code  # Store code for later use
        # Enhanced regex-based parsing for Rust language constructs
        # In production, would use proper Rust parser like syn
        return ast.Module(body=[], type_ignores=[])

    def find_critical_nodes(self, tree: ast.AST) -> List[Dict]:
        """Find critical nodes in Rust code using regex patterns."""
        patterns = [
            (r"return\s+[^;]+;", 0.95, "return_statement"),
            (r"if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"else\s+if\s+[^{]+{", 0.90, "conditional_logic"),
            (r"else\s*{", 0.85, "conditional_logic"),
            (r"for\s+[^{]+{", 0.85, "for_loop"),
            (r"while\s+[^{]+{", 0.85, "while_loop"),
            (r"loop\s*{", 0.85, "infinite_loop"),
            (r"fn\s+\w+\([^)]*\)\s*[^{]*{", 0.80, "function_definition"),
            (r"pub\s+(?:struct|enum|trait|impl)\s+\w+", 0.80, "type_definition"),
            (r"struct\s+\w+\s*{", 0.80, "struct_definition"),
            (r"enum\s+\w+\s*{", 0.80, "enum_definition"),
            (r"trait\s+\w+\s*{", 0.80, "trait_definition"),
            (r"impl\s+\w+\s*{", 0.80, "implementation_block"),
            (r"impl\s+\w+\s+for\s+\w+\s*{", 0.85, "trait_implementation"),
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
            (r"#\[derive\s*\([^)]+\)\]", 0.75, "derive_attribute"),
            (r"#\[cfg\s*\([^)]+\)\]", 0.70, "cfg_attribute"),
            (r"#\[test\]", 0.75, "test_attribute"),
            (r"#\[bench\]", 0.75, "bench_attribute"),
            (r"#\[allow\s*\([^)]+\)\]", 0.70, "allow_attribute"),
            (r"#\[deny\s*\([^)]+\)\]", 0.70, "deny_attribute"),
            (r"#\[warn\s*\([^)]+\)\]", 0.70, "warn_attribute"),
            (r"#\[forbid\s*\([^)]+\)\]", 0.70, "forbid_attribute"),
            (r"#\[inline\]", 0.70, "inline_attribute"),
            (r"#\[no_std\]", 0.70, "no_std_attribute"),
            (r"#\[no_mangle\]", 0.70, "no_mangle_attribute"),
            (r"#\[repr\s*\([^)]+\)\]", 0.70, "repr_attribute"),
            (r"#\[derive\s*\([^)]+\)\]", 0.75, "derive_attribute"),
            (r"#\[cfg\s*\([^)]+\)\]", 0.70, "cfg_attribute"),
            (r"#\[test\]", 0.75, "test_attribute"),
            (r"#\[bench\]", 0.75, "bench_attribute"),
            (r"#\[allow\s*\([^)]+\)\]", 0.70, "allow_attribute"),
            (r"#\[deny\s*\([^)]+\)\]", 0.70, "deny_attribute"),
            (r"#\[warn\s*\([^)]+\)\]", 0.70, "warn_attribute"),
            (r"#\[forbid\s*\([^)]+\)\]", 0.70, "forbid_attribute"),
            (r"#\[inline\]", 0.70, "inline_attribute"),
            (r"#\[no_std\]", 0.70, "no_std_attribute"),
            (r"#\[no_mangle\]", 0.70, "no_mangle_attribute"),
            (r"#\[repr\s*\([^)]+\)\]", 0.70, "repr_attribute"),
            (r"let\s+\w+\s*=", 0.70, "variable_declaration"),
            (r"let\s+mut\s+\w+\s*=", 0.75, "mutable_variable_declaration"),
            (r"const\s+\w+\s*=", 0.70, "constant_declaration"),
            (r"static\s+\w+\s*=", 0.70, "static_declaration"),
            (r"static\s+mut\s+\w+\s*=", 0.75, "mutable_static_declaration"),
            (r"use\s+[^;]+;", 0.70, "use_statement"),
            (r"mod\s+\w+", 0.75, "module_declaration"),
            (r"extern\s+\"C\"\s*{", 0.80, "extern_c_block"),
            (r"extern\s+crate\s+\w+", 0.70, "extern_crate"),
            (r"crate\s+", 0.70, "crate_keyword"),
            (r"super\s+", 0.70, "super_keyword"),
            (r"self\s+", 0.70, "self_keyword"),
            (r"Self\s+", 0.70, "Self_keyword"),
            (r"async\s+fn\s+\w+", 0.85, "async_function"),
            (r"await\s+", 0.80, "await_keyword"),
            (r"async\s+move\s*{", 0.85, "async_move_block"),
            (r"move\s*{", 0.80, "move_block"),
            (r"Box\s*<[^>]+>", 0.75, "box_type"),
            (r"Rc\s*<[^>]+>", 0.75, "rc_type"),
            (r"Arc\s*<[^>]+>", 0.75, "arc_type"),
            (r"RefCell\s*<[^>]+>", 0.75, "refcell_type"),
            (r"Mutex\s*<[^>]+>", 0.75, "mutex_type"),
            (r"RwLock\s*<[^>]+>", 0.75, "rwlock_type"),
            (r"Cell\s*<[^>]+>", 0.75, "cell_type"),
            (r"UnsafeCell\s*<[^>]+>", 0.75, "unsafecell_type"),
            (r"PhantomData\s*<[^>]+>", 0.75, "phantomdata_type"),
            (r"PhantomPinned", 0.75, "phantompinned_type"),
            (r"ManuallyDrop\s*<[^>]+>", 0.75, "manuallydrop_type"),
            (r"MaybeUninit\s*<[^>]+>", 0.75, "maybeuninit_type"),
            (r"NonNull\s*<[^>]+>", 0.75, "nonnull_type"),
            (r"NonZero\s*<[^>]+>", 0.75, "nonzero_type"),
            (r"Wrapping\s*<[^>]+>", 0.75, "wrapping_type"),
            (r"Saturating\s*<[^>]+>", 0.75, "saturating_type"),
            (r"Checked\s*<[^>]+>", 0.75, "checked_type"),
            (r"Overflowing\s*<[^>]+>", 0.75, "overflowing_type"),
            (r"DivEuclid\s*<[^>]+>", 0.75, "diveuclid_type"),
            (r"RemEuclid\s*<[^>]+>", 0.75, "remeuclid_type"),
            (r"DivFloor\s*<[^>]+>", 0.75, "divfloor_type"),
            (r"DivCeil\s*<[^>]+>", 0.75, "divceil_type"),
            (r"RemFloor\s*<[^>]+>", 0.75, "remfloor_type"),
            (r"RemCeil\s*<[^>]+>", 0.75, "remceil_type"),
            (r"DivRound\s*<[^>]+>", 0.75, "divround_type"),
            (r"RemRound\s*<[^>]+>", 0.75, "remround_type"),
            (r"DivTrunc\s*<[^>]+>", 0.75, "divtrunc_type"),
            (r"RemTrunc\s*<[^>]+>", 0.75, "remtrunc_type"),
            (r"DivExact\s*<[^>]+>", 0.75, "divexact_type"),
            (r"RemExact\s*<[^>]+>", 0.75, "remexact_type"),
            (r"DivMod\s*<[^>]+>", 0.75, "divmod_type"),
            (r"DivRem\s*<[^>]+>", 0.75, "divrem_type"),
            (r"DivModFloor\s*<[^>]+>", 0.75, "divmodfloor_type"),
            (r"DivRemFloor\s*<[^>]+>", 0.75, "divremfloor_type"),
            (r"DivModCeil\s*<[^>]+>", 0.75, "divmodceil_type"),
            (r"DivRemCeil\s*<[^>]+>", 0.75, "divremceil_type"),
            (r"DivModRound\s*<[^>]+>", 0.75, "divmodround_type"),
            (r"DivRemRound\s*<[^>]+>", 0.75, "divremround_type"),
            (r"DivModTrunc\s*<[^>]+>", 0.75, "divmodtrunc_type"),
            (r"DivRemTrunc\s*<[^>]+>", 0.75, "divremtrunc_type"),
            (r"DivModExact\s*<[^>]+>", 0.75, "divmodexact_type"),
            (r"DivRemExact\s*<[^>]+>", 0.75, "divremexact_type"),
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

    def __init__(self) -> None:
        self.language_analyzers = {
            "python": PythonCriticalAnalyzer(),
            "javascript": JavaScriptCriticalAnalyzer(),
            "typescript": JavaScriptCriticalAnalyzer(),  # Enhanced JS/TS pattern recognition
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
