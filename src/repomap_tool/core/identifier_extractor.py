"""
Identifier extraction functionality.

This module handles extracting identifiers from project maps and code files.
"""

import re
from typing import Union
from ..protocols import ProjectMap, IdentifierSet
from ..utils.type_validator import safe_validate_project_map


def extract_identifiers(project_map: Union[ProjectMap, str, None]) -> IdentifierSet:
    """
    Extract all identifiers from the project map.

    This method handles multiple project map formats:
    - String: Real aider RepoMap returns a formatted string
    - Dictionary: Mock/standalone implementation returns structured data
    - None/Empty: Handle gracefully

    Args:
        project_map: Project map from RepoMap or other source

    Returns:
        Set of extracted identifiers
    """
    identifiers: IdentifierSet = set()

    # Handle None or empty project_map
    if not project_map:
        return identifiers

    # Handle string format (real aider RepoMap)
    if isinstance(project_map, str):
        # Extract identifiers from the string using regex
        # Look for function/class definitions and variable names
        patterns = [
            r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
            r"class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]",
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^=]",  # Variable assignments
            r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)",  # Function calls
        ]

        for pattern in patterns:
            matches = re.findall(pattern, project_map)
            identifiers.update(matches)

        return identifiers

    # Handle dictionary format (mock/standalone implementation)
    if isinstance(project_map, dict):
        # Use type validation for structured data
        validated_map = safe_validate_project_map(project_map)  # type: ignore

        # Extract identifiers from validated structure
        if validated_map["tags"]:
            for tag in validated_map["tags"]:
                if tag["name"]:
                    identifiers.add(tag["name"])

        if validated_map["identifiers"]:
            identifiers.update(validated_map["identifiers"])

        if validated_map["files"]:
            for file_data in validated_map["files"].values():
                if file_data["identifiers"]:
                    identifiers.update(file_data["identifiers"])

    return identifiers
