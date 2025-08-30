"""
Identifier extraction functionality.

This module handles extracting identifiers from project maps and code files.
"""

import re
from typing import Set, Any


def extract_identifiers(project_map: Any) -> Set[str]:
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
    identifiers: Set[str] = set()

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
        # Handle Tag objects from aider (new format)
        if "tags" in project_map and project_map["tags"] is not None:
            for tag in project_map["tags"]:
                if hasattr(tag, "name") and tag.name:
                    identifiers.add(tag.name)

        # Check if project_map has top-level identifiers key
        if "identifiers" in project_map and project_map["identifiers"] is not None:
            # Ensure identifiers is iterable
            if isinstance(project_map["identifiers"], (list, set, tuple)):
                identifiers.update(project_map["identifiers"])
            else:
                # Log warning but don't fail
                pass

        # Also check for file-based identifiers (complex structure)
        for file_path, file_data in project_map.items():
            if isinstance(file_data, dict) and "identifiers" in file_data:
                if isinstance(file_data["identifiers"], (list, set, tuple)):
                    identifiers.update(file_data["identifiers"])

    return identifiers
