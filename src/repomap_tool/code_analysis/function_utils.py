"""
Function call analysis utilities for LLM file analysis.

This module provides utilities for analyzing function calls, categorizing them,
and extracting meaningful insights from code analysis results.
"""

import logging
from ..core.config_service import get_config
from ..core.logging_service import get_logger
from typing import Any, Dict, List, Optional, Tuple
from collections import Counter
from repomap_tool.code_analysis.models import CodeTag
from .ast_file_analyzer import ASTFileAnalyzer

logger = get_logger(__name__)


def find_most_called_function(function_calls: List[Any]) -> Optional[str]:
    """Find the most frequently called function."""
    if not function_calls:
        return None

    call_counts: Dict[str, int] = {}
    for call in function_calls:
        func_name = call.callee
        call_counts[func_name] = call_counts.get(func_name, 0) + 1

    return max(call_counts.items(), key=lambda x: x[1])[0] if call_counts else None


def get_top_called_functions(
    function_calls: List[Any], limit: int = get_config("DEFAULT_LIMIT", 5)
) -> List[Tuple[str, int]]:
    """Get the top N most frequently called functions with their call counts."""
    if not function_calls:
        return []

    call_counts: Dict[str, int] = {}
    for call in function_calls:
        func_name = call.callee
        call_counts[func_name] = call_counts.get(func_name, 0) + 1

    # Sort by call count (descending) and return top N
    sorted_calls = sorted(call_counts.items(), key=lambda x: x[1], reverse=True)
    return sorted_calls[:limit]


def smart_categorize_function_calls(
    function_calls: List[Any],
    defined_functions: List[str],
    imports: List[Any],
    limit: int = get_config("DEFAULT_LIMIT", 5),
) -> Dict[str, Any]:
    """Smart categorization that infers sources rather than hardcoding them."""
    if not function_calls:
        return {
            "internal": [],
            "external": [],
            "internal_count": 0,
            "external_count": 0,
            "external_with_sources": [],
        }

    internal_counts: Dict[str, int] = {}
    external_counts: Dict[str, int] = {}

    # Convert defined_functions to a set for faster lookup
    defined_funcs_set = set(defined_functions)

    # Build import mapping
    import_sources: Dict[str, str] = {}
    for imp in imports:
        if hasattr(imp, "symbols") and imp.symbols:
            for symbol in imp.symbols:
                import_sources[symbol] = imp.module
        if hasattr(imp, "module"):
            module_name = imp.module.split("/")[-1] if "/" in imp.module else imp.module
            import_sources[module_name] = imp.module

    # Categorize calls
    for call in function_calls:
        func_name = call.callee
        if func_name in defined_funcs_set:
            internal_counts[func_name] = internal_counts.get(func_name, 0) + 1
        else:
            external_counts[func_name] = external_counts.get(func_name, 0) + 1

    # Sort and limit
    internal_sorted = sorted(internal_counts.items(), key=lambda x: x[1], reverse=True)[
        :limit
    ]
    external_sorted = sorted(external_counts.items(), key=lambda x: x[1], reverse=True)[
        :limit
    ]

    # Smart source detection for external functions
    external_with_sources = []
    for func_name, count in external_sorted:
        source = infer_function_source(func_name, import_sources)
        external_with_sources.append((func_name, count, source))

    return {
        "internal": internal_sorted,
        "external": external_sorted,
        "internal_count": sum(internal_counts.values()),
        "external_count": sum(external_counts.values()),
        "external_with_sources": external_with_sources,
    }


def infer_function_source(func_name: str, import_sources: Dict[str, str]) -> str:
    """Language-agnostic function source inference based on imports and patterns."""

    # 1. EXPLICIT IMPORTS (Most reliable - works for any language)
    if func_name in import_sources:
        return import_sources[func_name]

    # 2. FUZZY IMPORT MATCHING (Language-agnostic)
    # Check if function name is contained in any imported module/symbol
    for symbol, module in import_sources.items():
        # Direct substring match
        if func_name.lower() in symbol.lower() or symbol.lower() in func_name.lower():
            return f"{module} (via {symbol})"

        # Module name matching (e.g., 'log' from imported 'console')
        module_base = module.split("/")[-1].split(".")[0]  # Extract base name
        if (
            func_name.lower() in module_base.lower()
            or module_base.lower() in func_name.lower()
        ):
            return f"{module} (module method)"

    # 3. NAMING PATTERN ANALYSIS (Language-agnostic)

    # Common cross-language patterns
    if any(
        pattern in func_name.lower()
        for pattern in ["log", "print", "debug", "warn", "error"]
    ):
        return "logging/output"

    if any(
        pattern in func_name.lower() for pattern in ["push", "add", "append", "insert"]
    ):
        return "collection mutation"

    if any(
        pattern in func_name.lower()
        for pattern in ["map", "filter", "reduce", "transform"]
    ):
        return "collection processing"

    if any(
        pattern in func_name.lower() for pattern in ["get", "fetch", "retrieve", "find"]
    ):
        return "data access"

    if any(
        pattern in func_name.lower()
        for pattern in ["set", "update", "modify", "change"]
    ):
        return "data mutation"

    if any(
        pattern in func_name.lower()
        for pattern in ["emit", "trigger", "fire", "dispatch"]
    ):
        return "event system"

    if any(
        pattern in func_name.lower()
        for pattern in ["async", "await", "promise", "future"]
    ):
        return "async/concurrency"

    if any(
        pattern in func_name.lower()
        for pattern in ["parse", "serialize", "stringify", "encode", "decode"]
    ):
        return "data serialization"

    if any(
        pattern in func_name.lower()
        for pattern in ["validate", "check", "verify", "test"]
    ):
        return "validation/testing"

    # 4. CAPITALIZATION PATTERNS (Language-agnostic)

    # Constructor pattern (PascalCase)
    # Ensure func_name is a string before calling string methods
    func_name_str = func_name.name if isinstance(func_name, CodeTag) else str(func_name)
    if (
        func_name_str
        and len(func_name_str) > 0
        and func_name_str[0].isupper()
        and not func_name_str.isupper()
    ):
        return "constructor/class"

    # Constant pattern (UPPER_CASE)
    if func_name_str and func_name_str.isupper() and "_" in func_name_str:
        return "constant/enum"

    # Method pattern (camelCase starting with lowercase)
    if (
        func_name_str
        and len(func_name_str) > 0
        and func_name_str[0].islower()
        and any(c.isupper() for c in func_name_str)
    ):
        return "method/function"

    # 5. STRUCTURAL PATTERNS

    # Compound names suggest external libraries
    if (
        len(func_name_str.split("_")) > 2
        or len([c for c in func_name_str if c.isupper()]) > 2
    ):
        return "external library"

    # Short names often indicate built-ins or common utilities
    if len(func_name_str) <= 3:
        return "built-in/utility"

    # 6. FALLBACK - Unknown but categorized
    return "external (unknown)"


def filter_business_relevant_calls(
    external_with_sources: List[Tuple[str, int, str]],
) -> List[Tuple[str, int, str]]:
    """Filter external function calls to show only business-relevant ones."""

    # Define patterns for low-level utility calls to filter out
    utility_patterns = {
        # Basic logging/debugging
        "log",
        "warn",
        "error",
        "info",
        "debug",
        "trace",
        "console",
        # Basic data types and constructors
        "Error",
        "Date",
        "Array",
        "Object",
        "Map",
        "Set",
        "Promise",
        "RegExp",
        # Primitive operations
        "now",
        "getTime",
        "toString",
        "valueOf",
        "hasOwnProperty",
        "push",
        "pop",
        "slice",
        "join",
        "split",
        "trim",
        "length",
        # Basic serialization
        "stringify",
        "parse",
        "JSON",
        # Basic math/comparison
        "Math",
        "ceil",
        "floor",
        "round",
        "abs",
        "max",
        "min",
        # Basic control flow utilities
        "setTimeout",
        "setInterval",
        "clearTimeout",
        "clearInterval",
        # Basic type checking
        "isNaN",
        "isFinite",
        "parseInt",
        "parseFloat",
        # Basic string operations
        "substring",
        "indexOf",
        "replace",
        "toLowerCase",
        "toUpperCase",
        # Basic validation/guards
        "assert",
        "check",
        "validate",  # Only if very generic
    }

    # Additional filtering based on source
    def is_business_relevant(func_name: str, source: str) -> bool:
        # Always include if it's from an explicit import (not a built-in)
        if "built-in" not in source and "external (unknown)" not in source:
            # But still filter out obvious utility functions even from imports
            if func_name.lower() in utility_patterns:
                return False
            return True

        # For built-ins and unknowns, be more selective
        if func_name.lower() in utility_patterns:
            return False

        # Keep functions that suggest business logic
        business_keywords = [
            "task",
            "message",
            "command",
            "execute",
            "process",
            "handle",
            "create",
            "update",
            "delete",
            "save",
            "load",
            "fetch",
            "send",
            "validate",
            "transform",
            "generate",
            "analyze",
            "calculate",
            "request",
            "response",
            "session",
            "user",
            "auth",
            "config",
            "emit",
            "trigger",
            "dispatch",
            "subscribe",
            "publish",
            "start",
            "stop",
            "pause",
            "resume",
            "cancel",
            "complete",
            "migrate",
            "backup",
            "restore",
            "sync",
            "connect",
            "disconnect",
        ]

        func_lower = func_name.lower()
        if any(keyword in func_lower for keyword in business_keywords):
            return True

        # Keep functions with meaningful names (longer than 3 chars, not all lowercase)
        if len(func_name) > 3 and not func_name.islower():
            return True

        return False

    # Filter the calls
    filtered_calls = []
    for func_name, count, source in external_with_sources:
        if is_business_relevant(func_name, source):
            filtered_calls.append((func_name, count, source))

    return filtered_calls


def get_functions_called_from_file(
    ast_analyzer: ASTFileAnalyzer, calling_file: str, target_file: str
) -> List[str]:
    """Get list of functions that calling_file calls from target_file."""
    try:
        # Import here to avoid circular imports
        from .ast_file_analyzer import AnalysisType

        # Analyze the calling file to find function calls
        result = ast_analyzer.analyze_file(calling_file, AnalysisType.ALL)
        if not result or not result.function_calls:
            return []

        # Get functions defined in target file for reference
        target_result = ast_analyzer.analyze_file(target_file, AnalysisType.ALL)
        if not target_result or not target_result.defined_functions:
            return []

        target_functions = set(target_result.defined_functions)

        # Find calls that match functions defined in target file
        called_functions = []
        for call in result.function_calls:
            if hasattr(call, "callee") and call.callee in target_functions:
                called_functions.append(call.callee)

        # Count and return most frequently called functions
        call_counts = Counter(called_functions)
        return [func for func, count in call_counts.most_common(5)]

    except Exception as e:
        # Silently fail to avoid disrupting main analysis
        logger.debug(f"Error analyzing function calls between files: {e}")
        return []


def find_most_used_class(imports: List[Any]) -> Optional[str]:
    """Find the most frequently imported class."""
    if not imports:
        return None

    class_counts: Dict[str, int] = {}
    for import_obj in imports:
        # Check if any imported symbols are classes (start with uppercase)
        if import_obj.symbols:
            for symbol_item in import_obj.symbols:
                # Ensure symbol is a string before calling string methods
                symbol_str = (
                    symbol_item.name
                    if isinstance(symbol_item, CodeTag)
                    else str(symbol_item)
                )
                if symbol_str and len(symbol_str) > 0 and symbol_str[0].isupper():
                    class_counts[symbol_str] = class_counts.get(symbol_str, 0) + 1
        elif (
            import_obj.alias
            and len(import_obj.alias) > 0
            # Ensure alias is a string before calling string methods
            and (
                import_obj.alias.name
                if isinstance(import_obj.alias, CodeTag)
                else str(import_obj.alias)
            )[0].isupper()
        ):
            alias_str = (
                import_obj.alias.name
                if isinstance(import_obj.alias, CodeTag)
                else str(import_obj.alias)
            )
            class_counts[alias_str] = class_counts.get(alias_str, 0) + 1

    return max(class_counts.items(), key=lambda x: x[1])[0] if class_counts else None
