"""
Centralized tag kind constants and utilities.

This module provides constants and helper functions for working with tree-sitter tag kinds,
eliminating magic strings scattered throughout the codebase.

Tag kinds follow a hierarchical structure:
- name.definition.* - Definitions (classes, functions, methods, variables)
- name.reference.* - References (imports, calls, usage)
- call.* - Function/method calls
- import.* - Import statements
"""

from typing import Set


# ============================================================================
# Tag Kind Patterns (for matching)
# ============================================================================

# Definition patterns
DEFINITION_CLASS = "definition.class"
DEFINITION_FUNCTION = "definition.function"
DEFINITION_METHOD = "definition.method"
DEFINITION_ASYNC_FUNCTION = "definition.async_function"
DEFINITION_ASYNC_METHOD = "definition.async_method"
DEFINITION_VARIABLE = "definition.variable"
DEFINITION_PARAMETER = "definition.parameter"
DEFINITION_IMPORT_ALIAS = "definition.import_alias"

# Reference patterns
REFERENCE_IMPORT = "reference.import"
REFERENCE_CALL = "reference.call"
REFERENCE_NAME = "reference.name"

# Call patterns
CALL_NAME = "call.name"
CALL_NAME_ATTRIBUTE = "call.name.attribute"

# Import patterns
IMPORT_RELATIVE_PREFIX = "import.relative_prefix"
IMPORT_ITEM = "reference.import.item"


# ============================================================================
# Helper Functions
# ============================================================================


def is_class_definition(tag_kind: str) -> bool:
    """Check if tag kind represents a class, interface, or enum definition."""
    tag_kind_lower = tag_kind.lower()
    return any(
        pattern in tag_kind_lower
        for pattern in ["class", "interface", "enum", "type", "record"]
        if pattern != "definition"  # Avoid matching "definition" substring
    )


def is_function_definition(tag_kind: str) -> bool:
    """Check if tag kind represents a function definition (not a method)."""
    tag_kind_lower = tag_kind.lower()
    # Must contain "definition.function" or "definition.async_function" but not "method" or "call"
    has_function = (
        DEFINITION_FUNCTION in tag_kind_lower
        or DEFINITION_ASYNC_FUNCTION in tag_kind_lower
    )
    not_method = "method" not in tag_kind_lower
    not_call = "call" not in tag_kind_lower
    return has_function and not_method and not_call


def is_method_definition(tag_kind: str) -> bool:
    """Check if tag kind represents a method definition."""
    tag_kind_lower = tag_kind.lower()
    return "method" in tag_kind_lower or "constructor" in tag_kind_lower


def is_variable_definition(tag_kind: str) -> bool:
    """Check if tag kind represents a variable definition."""
    tag_kind_lower = tag_kind.lower()
    return (
        any(
            pattern in tag_kind_lower
            for pattern in ["variable", "field", "property", "parameter"]
        )
        and "call" not in tag_kind_lower
    )  # Exclude call-related tags


def is_import(tag_kind: str) -> bool:
    """Check if tag kind represents an import statement."""
    tag_kind_lower = tag_kind.lower()
    return any(pattern in tag_kind_lower for pattern in ["import", "require", "export"])


def is_function_call(tag_kind: str) -> bool:
    """Check if tag kind represents a function or method call."""
    tag_kind_lower = tag_kind.lower()
    return "call" in tag_kind_lower


def is_import_from_statement(tag_kind: str) -> bool:
    """Check if tag kind represents an import-from statement."""
    tag_kind_lower = tag_kind.lower()
    return "import_from" in tag_kind_lower or "import.from" in tag_kind_lower


def matches_any_pattern(tag_kind: str, patterns: Set[str]) -> bool:
    """Check if tag kind matches any of the provided patterns."""
    tag_kind_lower = tag_kind.lower()
    return any(pattern.lower() in tag_kind_lower for pattern in patterns)


def get_tag_category(tag_kind: str) -> str:
    """
    Get the high-level category of a tag kind.

    Returns one of: 'class', 'function', 'method', 'variable', 'import', 'call', or 'unknown'
    """
    if is_class_definition(tag_kind):
        return "class"
    elif is_method_definition(tag_kind):
        return "method"
    elif is_function_definition(tag_kind):
        return "function"
    elif is_variable_definition(tag_kind):
        return "variable"
    elif is_import(tag_kind):
        return "import"
    elif is_function_call(tag_kind):
        return "call"
    else:
        return "unknown"
