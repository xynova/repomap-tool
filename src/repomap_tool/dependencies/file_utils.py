"""
File utilities for project analysis.

This module contains simple file system utilities that can be used
across different analysis components.
"""

import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


def get_all_project_files(project_root: str) -> List[str]:
    """Get all Python files in the project for analysis.

    Args:
        project_root: Root path of the project

    Returns:
        List of Python file paths
    """
    if not project_root:
        return []

    # Ensure project_root is always a string, not a ConfigurationOption
    project_path = Path(str(project_root))
    python_files = []

    for py_file in project_path.rglob("*.py"):
        if not any(part.startswith(".") for part in py_file.parts):
            python_files.append(str(py_file))

    return python_files


def suggest_test_files(file_path: str) -> List[str]:
    """Suggest test files for a given file.

    Args:
        file_path: Path to the file to find tests for

    Returns:
        List of suggested test file paths
    """
    file_path_obj = Path(file_path)
    test_files = []

    # Look for test files in common locations
    test_patterns = [
        f"test_{file_path_obj.stem}.py",
        f"{file_path_obj.stem}_test.py",
    ]

    for pattern in test_patterns:
        # Check in tests directory
        test_file = file_path_obj.parent / "tests" / pattern
        if test_file.exists():
            test_files.append(str(test_file))

        # Check in parent tests directory
        test_file = file_path_obj.parent.parent / "tests" / pattern
        if test_file.exists():
            test_files.append(str(test_file))

    return test_files
