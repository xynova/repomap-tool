"""
Signature enhancer for LLM optimization.

This module enhances function signatures with type information,
call patterns, and usage examples to improve LLM understanding.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EnhancedSignature:
    """Enhanced function signature with additional information."""

    original_signature: str
    enhanced_signature: str
    parameter_types: Dict[str, str]
    return_type: Optional[str]
    usage_examples: List[str]
    error_cases: List[str]
    complexity_score: float


class TypeInferenceEngine:
    """Infers types for function parameters and return values."""

    def __init__(self):
        self.common_patterns = self._load_common_patterns()
        self.type_hints = self._load_type_hints()

    def infer_missing_types(
        self, symbol_content: str, language: str = "python"
    ) -> Dict[str, str]:
        """Infer types for parameters and return values.

        Args:
            symbol_content: Raw code content
            language: Programming language

        Returns:
            Dictionary mapping parameter names to inferred types
        """
        if language.lower() == "python":
            return self._infer_python_types(symbol_content)
        elif language.lower() in ["javascript", "typescript", "js"]:
            return self._infer_javascript_types(symbol_content)
        else:
            return {}

    def _infer_python_types(self, content: str) -> Dict[str, str]:
        """Infer types for Python code."""
        type_mapping = {}

        # Look for type hints in the code
        type_hint_patterns = [
            r"def\s+\w+\s*\([^)]*\)\s*->\s*([^:]+):",  # Return type hints
            r"(\w+):\s*([^,)]+)",  # Parameter type hints
        ]

        for pattern in type_hint_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    param_name, type_name = match
                    type_mapping[param_name] = self._normalize_type(type_name)

        # Infer from usage patterns
        usage_patterns = {
            r'(\w+)\s*=\s*["\']': "str",
            r"(\w+)\s*=\s*\d+": "int",
            r"(\w+)\s*=\s*\d+\.\d+": "float",
            r"(\w+)\s*=\s*\[": "list",
            r"(\w+)\s*=\s*\{": "dict",
            r"(\w+)\s*=\s*True|\w+\s*=\s*False": "bool",
        }

        for pattern, inferred_type in usage_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in type_mapping:
                    type_mapping[match] = inferred_type

        return type_mapping

    def _infer_javascript_types(self, content: str) -> Dict[str, str]:
        """Infer types for JavaScript/TypeScript code."""
        type_mapping = {}

        # Look for JSDoc or TypeScript type annotations
        jsdoc_patterns = [
            r"@param\s*\{([^}]+)\}\s*(\w+)",  # JSDoc param types
            r"@returns?\s*\{([^}]+)\}",  # JSDoc return types
        ]

        for pattern in jsdoc_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple) and len(match) == 2:
                    type_name, param_name = match
                    type_mapping[param_name] = self._normalize_type(type_name)
                else:
                    # Return type
                    type_mapping["return"] = self._normalize_type(match)

        # Infer from usage patterns
        usage_patterns = {
            r'(\w+)\s*=\s*["\']': "string",
            r"(\w+)\s*=\s*\d+": "number",
            r"(\w+)\s*=\s*\[": "array",
            r"(\w+)\s*=\s*\{": "object",
            r"(\w+)\s*=\s*true|\w+\s*=\s*false": "boolean",
        }

        for pattern, inferred_type in usage_patterns.items():
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in type_mapping:
                    type_mapping[match] = inferred_type

        return type_mapping

    def _normalize_type(self, type_name: str) -> str:
        """Normalize type names to standard format."""
        type_name = type_name.strip().lower()

        # Python type normalization
        python_mapping = {
            "str": "str",
            "string": "str",
            "int": "int",
            "integer": "int",
            "float": "float",
            "double": "float",
            "bool": "bool",
            "boolean": "bool",
            "list": "list",
            "array": "list",
            "dict": "dict",
            "dictionary": "dict",
            "tuple": "tuple",
            "set": "set",
            "none": "None",
            "null": "None",
        }

        # JavaScript type normalization
        js_mapping = {
            "string": "string",
            "str": "string",
            "number": "number",
            "num": "number",
            "int": "number",
            "integer": "number",
            "float": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "array": "array",
            "list": "array",
            "object": "object",
            "obj": "object",
            "dict": "object",
            "function": "function",
            "func": "function",
            "void": "void",
            "undefined": "undefined",
        }

        # Check Python first, then JavaScript
        if type_name in python_mapping:
            return python_mapping[type_name]
        elif type_name in js_mapping:
            return js_mapping[type_name]
        else:
            # Return original if no mapping found
            return type_name

    def _load_common_patterns(self) -> Dict[str, List[str]]:
        """Load common parameter patterns for type inference."""
        return {
            "python": [
                "username",
                "password",
                "email",
                "user_id",
                "file_path",
                "data",
                "config",
                "options",
                "kwargs",
                "args",
            ],
            "javascript": [
                "username",
                "password",
                "email",
                "userId",
                "filePath",
                "data",
                "config",
                "options",
                "callback",
                "params",
            ],
        }

    def _load_type_hints(self) -> Dict[str, str]:
        """Load common type hints for parameter names."""
        return {
            "username": "str",
            "password": "str",
            "email": "str",
            "user_id": "int",
            "file_path": "str",
            "data": "dict",
            "config": "dict",
            "options": "dict",
            "callback": "callable",
            "params": "dict",
        }


class SignatureEnhancer:
    """Enhances function signatures with type information and usage patterns."""

    def __init__(self):
        self.type_inference = TypeInferenceEngine()
        self.signature_patterns = self._load_signature_patterns()

    def _load_signature_patterns(self) -> Dict[str, Any]:
        """Load signature patterns for different languages."""
        return {
            "python": {
                "function_def": r"def\s+(\w+)\s*\([^)]*\)",
                "class_def": r"class\s+(\w+)",
                "type_hint": r"(\w+):\s*([^,)]+)",
                "return_hint": r"->\s*([^:]+):",
            },
            "javascript": {
                "function_def": r"function\s+(\w+)\s*\([^)]*\)",
                "arrow_func": r"(\w+)\s*[:=]\s*\([^)]*\)\s*=>",
                "method_def": r"(\w+)\s*\([^)]*\)\s*\{",
            },
        }

    def enhance_function_signature(
        self, symbol_content: str, language: str = "python"
    ) -> EnhancedSignature:
        """Enhance function signature with type information.

        Args:
            symbol_content: Raw code content
            language: Programming language

        Returns:
            EnhancedSignature object with additional information
        """
        try:
            # Extract original signature
            original_signature = self._extract_original_signature(
                symbol_content, language
            )

            # Infer types
            parameter_types = self.type_inference.infer_missing_types(
                symbol_content, language
            )

            # Create enhanced signature
            enhanced_signature = self._create_enhanced_signature(
                original_signature, parameter_types, language
            )

            # Generate usage examples
            usage_examples = self._generate_usage_examples(
                symbol_content, parameter_types, language
            )

            # Identify error cases
            error_cases = self._identify_error_cases(symbol_content, language)

            # Calculate complexity score
            complexity_score = self._calculate_complexity_score(
                symbol_content, language
            )

            return EnhancedSignature(
                original_signature=original_signature,
                enhanced_signature=enhanced_signature,
                parameter_types=parameter_types,
                return_type=self._infer_return_type(symbol_content, language),
                usage_examples=usage_examples,
                error_cases=error_cases,
                complexity_score=complexity_score,
            )

        except Exception as e:
            logger.error(f"Error enhancing signature: {e}")
            # Return basic signature if enhancement fails
            return EnhancedSignature(
                original_signature=(
                    symbol_content[:100] + "..."
                    if len(symbol_content) > 100
                    else symbol_content
                ),
                enhanced_signature=(
                    symbol_content[:100] + "..."
                    if len(symbol_content) > 100
                    else symbol_content
                ),
                parameter_types={},
                return_type=None,
                usage_examples=[],
                error_cases=[],
                complexity_score=0.5,
            )

    def _extract_original_signature(self, content: str, language: str) -> str:
        """Extract the original function signature from code."""
        if language.lower() == "python":
            # Python function definition
            match = re.search(r"def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*[^:]+)?:", content)
            if match:
                return match.group(0).rstrip(":")
        elif language.lower() in ["javascript", "typescript", "js"]:
            # JavaScript function definition
            patterns = [
                r"function\s+(\w+)\s*\([^)]*\)\s*\{?",
                r"(\w+)\s*[:=]\s*function\s*\([^)]*\)\s*\{?",
                r"(\w+)\s*[:=]\s*\([^)]*\)\s*=>\s*\{?",
            ]

            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(0).rstrip("{")

        # Fallback: return first line
        return content.split("\n")[0].strip()

    def _create_enhanced_signature(
        self, original: str, parameter_types: Dict[str, str], language: str
    ) -> str:
        """Create enhanced signature with type information."""
        if not parameter_types:
            return original

        enhanced = original

        # Add type hints to parameters
        for param_name, param_type in parameter_types.items():
            if param_name != "return":
                # Find parameter in signature and add type hint
                pattern = rf"\b{re.escape(param_name)}\b"
                replacement = f"{param_name}: {param_type}"
                enhanced = re.sub(pattern, replacement, enhanced, count=1)

        return enhanced

    def _generate_usage_examples(
        self, content: str, parameter_types: Dict[str, str], language: str
    ) -> List[str]:
        """Generate usage examples for the function."""
        examples = []

        # Look for existing usage patterns in the code
        if language.lower() == "python":
            # Find function calls
            function_name = self._extract_function_name(content)
            if function_name:
                call_patterns = [
                    rf"{re.escape(function_name)}\s*\([^)]*\)",
                    rf"{re.escape(function_name)}\s*\([^)]*\)\s*#.*",
                ]

                for pattern in call_patterns:
                    matches = re.findall(pattern, content)
                    for match in matches[:2]:  # Limit to 2 examples
                        examples.append(match.strip())

        # Generate synthetic examples if none found
        if not examples and parameter_types:
            example = self._create_synthetic_example(parameter_types, language)
            if example:
                examples.append(example)

        return examples[:3]  # Limit to 3 examples

    def _create_synthetic_example(
        self, parameter_types: Dict[str, str], language: str
    ) -> str:
        """Create a synthetic usage example based on parameter types."""
        if not parameter_types:
            return ""

        # Generate example values based on types
        example_values = []
        for param_name, param_type in parameter_types.items():
            if param_name == "return":
                continue

            if param_type in ["str", "string"]:
                example_values.append(f'"{param_name}_example"')
            elif param_type in ["int", "number"]:
                example_values.append("42")
            elif param_type in ["float", "number"]:
                example_values.append("3.14")
            elif param_type in ["bool", "boolean"]:
                example_values.append("True")
            elif param_type in ["list", "array"]:
                example_values.append("[]")
            elif param_type in ["dict", "object"]:
                example_values.append("{}")
            else:
                example_values.append(f"{param_name}_value")

        # Create example call
        if language.lower() == "python":
            return f"function_name({', '.join(example_values)})"
        else:
            return f"functionName({', '.join(example_values)})"

    def _identify_error_cases(self, content: str, language: str) -> List[str]:
        """Identify potential error cases in the function."""
        error_cases = []

        # Look for error handling patterns
        if language.lower() == "python":
            error_patterns = [
                r"raise\s+(\w+Error)",
                r"except\s+(\w+Error)",
                r"if\s+not\s+(\w+)",
                r"if\s+(\w+)\s+is\s+None",
            ]
        else:
            error_patterns = [
                r"throw\s+new\s+(\w+Error)",
                r"catch\s*\((\w+Error)",
                r"if\s*\(\s*!(\w+)",
                r"if\s*\(\s*(\w+)\s*===\s*null",
            ]

        for pattern in error_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match not in error_cases:
                    error_cases.append(match)

        return error_cases[:5]  # Limit to 5 error cases

    def _calculate_complexity_score(self, content: str, language: str) -> float:
        """Calculate complexity score for the function."""
        score = 0.0

        # Count lines of code
        lines = content.split("\n")
        non_empty_lines = [
            line for line in lines if line.strip() and not line.strip().startswith("#")
        ]

        # Base complexity from line count
        if len(non_empty_lines) <= 5:
            score += 0.2
        elif len(non_empty_lines) <= 15:
            score += 0.5
        else:
            score += 0.8

        # Complexity from control structures
        control_patterns = {
            "if": r"\bif\b",
            "for": r"\bfor\b",
            "while": r"\bwhile\b",
            "try": r"\btry\b",
            "except": r"\bexcept\b",
            "catch": r"\bcatch\b",
        }

        for structure, pattern in control_patterns.items():
            count = len(re.findall(pattern, content, re.IGNORECASE))
            if count > 0:
                score += min(0.3, count * 0.1)

        # Complexity from function calls
        call_count = len(re.findall(r"\w+\s*\(", content))
        score += min(0.2, call_count * 0.05)

        return min(1.0, score)

    def _extract_function_name(self, content: str) -> Optional[str]:
        """Extract function name from content."""
        # Python function
        match = re.search(r"def\s+(\w+)", content)
        if match:
            return match.group(1)

        # JavaScript function
        js_patterns = [
            r"function\s+(\w+)",
            r"(\w+)\s*[:=]\s*function",
            r"(\w+)\s*[:=]\s*\([^)]*\)\s*=>",
        ]

        for pattern in js_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _infer_return_type(self, content: str, language: str) -> Optional[str]:
        """Infer return type from function content."""
        if language.lower() == "python":
            # Look for return type hints
            match = re.search(r"->\s*([^:]+):", content)
            if match:
                return self.type_inference._normalize_type(match.group(1))

            # Look for return statements to infer type
            return_patterns = [
                r'return\s+["\']',  # String return
                r"return\s+\d+",  # Number return
                r"return\s+True|\s+False",  # Boolean return
                r"return\s+\[",  # List return
                r"return\s+\{",  # Dict return
            ]

            for pattern in return_patterns:
                if re.search(pattern, content):
                    if "[\"']" in pattern:
                        return "str"
                    elif "\d+" in pattern:
                        return "int"
                    elif "True|False" in pattern:
                        return "bool"
                    elif "\[" in pattern:
                        return "list"
                    elif "\{" in pattern:
                        return "dict"

        return None

    def add_call_patterns(self, symbol_content: str) -> List[str]:
        """Add common call patterns for this function."""
        patterns = []

        # Extract function name
        function_name = self._extract_function_name(symbol_content)
        if not function_name:
            return patterns

        # Look for existing call patterns
        call_matches = re.findall(
            rf"{re.escape(function_name)}\s*\([^)]*\)", symbol_content
        )

        for match in call_matches[:3]:  # Limit to 3 patterns
            patterns.append(match.strip())

        return patterns
