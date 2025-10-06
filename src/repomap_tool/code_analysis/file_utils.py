"""
File utilities for project analysis.

This module contains simple file system utilities that can be used
across different analysis components.
"""

import logging
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def get_all_project_files(
    project_root: str, max_files: Optional[int] = None
) -> List[str]:
    """Get all analyzable files in the project for analysis.

    Args:
        project_root: Root path of the project
        max_files: Maximum number of files to return (for performance)

    Returns:
        List of file paths for supported languages (Python, TypeScript, JavaScript, etc.)
    """
    if not project_root:
        return []

    # Ensure project_root is always a string, not a ConfigurationOption
    project_path = Path(str(project_root))

    # Use centralized file filtering
    from .file_filter import FileFilter

    all_files = []

    for file_path in project_path.rglob("*"):
        if not any(part.startswith(".") for part in file_path.parts):
            if file_path.is_file():
                # Use centralized filtering
                if FileFilter.is_code_file(str(file_path)) and not FileFilter.should_exclude_file(str(file_path)):
                    # Convert to relative path from project root
                    try:
                        rel_path = file_path.relative_to(project_path)
                        all_files.append(str(rel_path))

                        # Stop if we've reached the maximum number of files (only if limit is specified)
                        if max_files is not None and len(all_files) >= max_files:
                            logger.info(
                                f"Reached maximum file limit ({max_files}), stopping file discovery"
                            )
                            break

                    except ValueError:
                        # File is not relative to project root, skip it
                        continue

    logger.info(
        f"Found {len(all_files)} files for analysis"
        + (f" (limit: {max_files})" if max_files else "")
    )
    return all_files


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
