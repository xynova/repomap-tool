"""
JavaScript and TypeScript file analyzer.

This module provides regex-based analysis for JavaScript and TypeScript files
to extract imports, function calls, and other relationships.
"""

import re
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass

from .models import Import, ImportType, FunctionCall, FileAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class JSAnalysisContext:
    """Context for JavaScript/TypeScript analysis."""

    file_path: str
    content: str


class JavaScriptTypeScriptAnalyzer:
    """Analyzer for JavaScript and TypeScript files using regex patterns."""

    def __init__(self) -> None:
        """Initialize the JavaScript/TypeScript analyzer."""
        # Compile regex patterns once for better performance
        self.import_patterns = {
            # Pattern 1: Named imports: import { name1, name2 } from 'module'
            "named_imports": re.compile(
                r"import\s*\{\s*([^}]+)\s*\}\s*from\s*['\"]([^'\"]+)['\"]"
            ),
            # Pattern 2: Default imports: import name from 'module'
            "default_imports": re.compile(
                r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
            ),
            # Pattern 3: Namespace imports: import * as name from 'module'
            "namespace_imports": re.compile(
                r"import\s+\*\s+as\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]"
            ),
            # Pattern 4: CommonJS require: require('module')
            "require_calls": re.compile(r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)"),
        }

        self.function_patterns = {
            # Function declarations: function name() {}
            "function_declarations": re.compile(r"function\s+(\w+)\s*\("),
            # Arrow functions: const name = () => {}
            "arrow_functions": re.compile(r"const\s+(\w+)\s*=\s*\("),
            # Method definitions: name() {}
            "method_definitions": re.compile(r"(\w+)\s*\(\s*[^)]*\)\s*\{"),
        }

        self.class_patterns = {
            # Class declarations: class Name {}
            "class_declarations": re.compile(r"class\s+(\w+)"),
            # Class expressions: const Name = class {}
            "class_expressions": re.compile(r"const\s+(\w+)\s*=\s*class"),
        }

    def analyze_file(self, context: JSAnalysisContext) -> FileAnalysisResult:
        """Analyze a JavaScript/TypeScript file.

        Args:
            context: Analysis context with file path and content

        Returns:
            FileAnalysisResult with extracted information
        """
        imports = []
        function_calls = []
        defined_functions = []
        defined_classes = []
        used_classes: List[str] = []
        used_variables: List[str] = []

        try:
            # Extract imports
            imports = self._extract_imports(context.content, context.file_path)

            # Extract function definitions
            defined_functions = self._extract_function_definitions(context.content)

            # Extract class definitions
            defined_classes = self._extract_class_definitions(context.content)

            # Extract function calls (basic pattern matching)
            function_calls = self._extract_function_calls(
                context.content, context.file_path
            )

        except Exception as e:
            logger.error(
                f"Error analyzing JavaScript/TypeScript file {context.file_path}: {e}"
            )

        return FileAnalysisResult(
            file_path=context.file_path,
            imports=imports,
            function_calls=function_calls,
            defined_functions=defined_functions,
            defined_classes=defined_classes,
            used_classes=used_classes,
            used_variables=used_variables,
            line_count=len(context.content.splitlines()),
            analysis_errors=[],
        )

    def _extract_imports(self, content: str, file_path: str) -> List[Import]:
        """Extract import statements from JavaScript/TypeScript content."""
        imports = []

        try:
            # Pattern 1: Named imports: import { name1, name2 } from 'module'
            named_import_pattern = self.import_patterns["named_imports"]
            for match in named_import_pattern.finditer(content):
                symbols_str = match.group(1)
                module = match.group(2)

                # Parse symbols (handle commas and whitespace)
                symbols = [s.strip() for s in symbols_str.split(",")]

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
                        line_number=self._get_line_number(content, match.start()),
                    )
                )

            # Pattern 2: Default imports: import name from 'module'
            default_import_pattern = self.import_patterns["default_imports"]
            for match in default_import_pattern.finditer(content):
                symbol = match.group(1)
                module = match.group(2)

                imports.append(
                    Import(
                        module=module,
                        symbols=[symbol],
                        is_relative=module.startswith("."),
                        import_type=(
                            ImportType.RELATIVE
                            if module.startswith(".")
                            else ImportType.ABSOLUTE
                        ),
                        line_number=self._get_line_number(content, match.start()),
                    )
                )

            # Pattern 3: Namespace imports: import * as name from 'module'
            namespace_import_pattern = self.import_patterns["namespace_imports"]
            for match in namespace_import_pattern.finditer(content):
                namespace = match.group(1)
                module = match.group(2)

                imports.append(
                    Import(
                        module=module,
                        symbols=[namespace],
                        is_relative=module.startswith("."),
                        import_type=(
                            ImportType.RELATIVE
                            if module.startswith(".")
                            else ImportType.ABSOLUTE
                        ),
                        line_number=self._get_line_number(content, match.start()),
                    )
                )

            # Pattern 4: CommonJS require: require('module')
            require_pattern = self.import_patterns["require_calls"]
            for match in require_pattern.finditer(content):
                imports.append(
                    Import(
                        module=match.group(1),
                        symbols=[],
                        is_relative=match.group(1).startswith("."),
                        import_type=(
                            ImportType.RELATIVE
                            if match.group(1).startswith(".")
                            else ImportType.ABSOLUTE
                        ),
                        line_number=self._get_line_number(content, match.start()),
                    )
                )

        except Exception as e:
            logger.error(f"Error extracting imports from {file_path}: {e}")

        return imports

    def _extract_function_definitions(self, content: str) -> List[str]:
        """Extract function definitions from JavaScript/TypeScript content."""
        functions = []

        try:
            # Function declarations: function name() {}
            function_pattern = self.function_patterns["function_declarations"]
            for match in function_pattern.finditer(content):
                functions.append(match.group(1))

            # Arrow functions: const name = () => {}
            arrow_pattern = self.function_patterns["arrow_functions"]
            for match in arrow_pattern.finditer(content):
                functions.append(match.group(1))

        except Exception as e:
            logger.error(f"Error extracting function definitions: {e}")

        return functions

    def _extract_class_definitions(self, content: str) -> List[str]:
        """Extract class definitions from JavaScript/TypeScript content."""
        classes = []

        try:
            # Class declarations: class Name {}
            class_pattern = self.class_patterns["class_declarations"]
            for match in class_pattern.finditer(content):
                classes.append(match.group(1))

            # Class expressions: const Name = class {}
            class_expr_pattern = self.class_patterns["class_expressions"]
            for match in class_expr_pattern.finditer(content):
                classes.append(match.group(1))

        except Exception as e:
            logger.error(f"Error extracting class definitions: {e}")

        return classes

    def _extract_function_calls(
        self, content: str, file_path: str
    ) -> List[FunctionCall]:
        """Extract function calls from JavaScript/TypeScript content."""
        function_calls = []

        try:
            # Basic function call pattern: name(args)
            # This is a simplified approach - a full implementation would need
            # more sophisticated parsing
            call_pattern = r"(\w+)\s*\("
            for match in re.finditer(call_pattern, content):
                function_name = match.group(1)

                # Skip common keywords that might match
                if function_name in [
                    "if",
                    "for",
                    "while",
                    "switch",
                    "catch",
                    "function",
                ]:
                    continue

                function_calls.append(
                    FunctionCall(
                        caller="unknown",
                        callee=function_name,
                        file_path=file_path,
                        line_number=self._get_line_number(content, match.start()),
                        is_method_call=False,
                        object_name=None,
                    )
                )

        except Exception as e:
            logger.error(f"Error extracting function calls: {e}")

        return function_calls

    def _get_line_number(self, content: str, position: int) -> int:
        """Get line number for a given position in content."""
        try:
            return content[:position].count("\n") + 1
        except Exception:
            return 1
