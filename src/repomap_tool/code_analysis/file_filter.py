"""
Centralized file filtering system for RepoMap-Tool.

This module provides a single source of truth for file filtering logic,
consolidating all the scattered filtering rules across the codebase.
"""

import logging
from ..core.logging_service import get_logger
from typing import List, Set, Optional
from pathlib import Path

logger = get_logger(__name__)


class FileFilter:
    """Centralized file filtering system."""

    # Core code file extensions supported by RepoMap-Tool
    CODE_EXTENSIONS: Set[str] = {
        ".py",  # Python
        ".ts",  # TypeScript
        ".tsx",  # TypeScript React
        ".js",  # JavaScript
        ".jsx",  # JavaScript React
        ".java",  # Java
        ".go",  # Go
        ".cs",  # C#
        ".cpp",  # C++
        ".c",  # C
        ".h",  # C Header
        ".hpp",  # C++ Header
    }

    # Extensions that can be parsed for imports/analysis but are not "core code"
    # Note: These should match the language parser keys (without dots)
    ANALYZABLE_EXTENSIONS: Set[str] = {
        "py",
        "ts",
        "tsx",
        "js",
        "jsx",
        "java",
        "go",
        "cs",
    }

    # File patterns to exclude from analysis
    EXCLUDE_PATTERNS: Set[str] = {
        "node_modules",
        ".git",
        ".vscode",
        "dist",
        "build",
        "coverage",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "*.min.js",
        "*.bundle.js",
        "*.d.ts",
        "*.spec.ts",
        "*.test.ts",
        "*.test.js",
        "*.spec.py",
        "*.test.py",
        "__test__",
        "test_",
    }

    # Test file patterns (more specific than exclude patterns)
    TEST_PATTERNS: Set[str] = {
        ".spec.",
        ".test.",
        "__test__",
        "test_",
        ".min.",
        ".bundle.",
        ".d.ts",
    }

    @classmethod
    def is_code_file(cls, file_path: str) -> bool:
        """Check if a file is a code file that should be included in centrality analysis.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file is a code file
        """
        return any(file_path.endswith(ext) for ext in cls.CODE_EXTENSIONS)

    @classmethod
    def is_analyzable_file(cls, file_path: str) -> bool:
        """Check if a file can be analyzed for imports/dependencies.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file can be analyzed
        """
        return any(file_path.endswith(f".{ext}") for ext in cls.ANALYZABLE_EXTENSIONS)

    @classmethod
    def is_test_file(cls, file_path: str) -> bool:
        """Check if a file is a test file.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file is a test file
        """
        file_path_lower = file_path.lower()
        return any(pattern in file_path_lower for pattern in cls.TEST_PATTERNS)

    @classmethod
    def should_exclude_file(cls, file_path: str) -> bool:
        """Check if a file should be excluded from analysis.

        Args:
            file_path: Path to the file to check

        Returns:
            True if the file should be excluded
        """
        file_path_str = str(file_path)

        # Check exclude patterns
        if any(pattern in file_path_str for pattern in cls.EXCLUDE_PATTERNS):
            return True

        # Check if it's a test file
        if cls.is_test_file(file_path_str):
            return True

        return False

    @classmethod
    def filter_code_files(
        cls, file_paths: List[str], exclude_tests: bool = True
    ) -> List[str]:
        """Filter a list of files to only include code files.

        Args:
            file_paths: List of file paths to filter
            exclude_tests: Whether to exclude test files

        Returns:
            List of filtered code files
        """
        filtered_files = []

        for file_path in file_paths:
            # Check if it's a code file
            if not cls.is_code_file(file_path):
                continue

            # Check if it should be excluded
            if cls.should_exclude_file(file_path):
                continue

            # Check if it's a test file (if we're excluding tests)
            if exclude_tests and cls.is_test_file(file_path):
                continue

            filtered_files.append(file_path)

        logger.debug(
            f"Filtered {len(file_paths)} files to {len(filtered_files)} code files"
        )
        return filtered_files

    @classmethod
    def is_python_file(cls, file_path: str) -> bool:
        """Check if the file is a Python file."""
        return file_path.endswith(".py")

    @classmethod
    def filter_analyzable_files(
        cls, file_paths: List[str], exclude_tests: bool = True
    ) -> List[str]:
        """Filter a list of files to only include analyzable files.

        Args:
            file_paths: List of file paths to filter
            exclude_tests: Whether to exclude test files

        Returns:
            List of filtered analyzable files
        """
        filtered_files = []

        for file_path in file_paths:
            # Temporarily enable all languages for debugging
            # if not cls.is_python_file(file_path):
            #     continue

            # Revert to original behavior: filter out non-python files (temporarily for debugging other language queries)
            if not cls.is_python_file(file_path):
                continue

            # Check if it should be excluded
            if cls.should_exclude_file(file_path):
                continue

            # Check if it's a test file (if we're excluding tests)
            if exclude_tests and cls.is_test_file(file_path):
                continue

            filtered_files.append(file_path)

        logger.debug(
            f"Filtered {len(file_paths)} files to {len(filtered_files)} analyzable files"
        )
        return filtered_files

    @classmethod
    def get_code_extensions(cls) -> Set[str]:
        """Get the set of code file extensions.

        Returns:
            Set of code file extensions
        """
        return cls.CODE_EXTENSIONS.copy()

    @classmethod
    def get_analyzable_extensions(cls) -> Set[str]:
        """Get the set of analyzable file extensions.

        Returns:
            Set of analyzable file extensions
        """
        return cls.ANALYZABLE_EXTENSIONS.copy()

    @classmethod
    def get_exclude_patterns(cls) -> Set[str]:
        """Get the set of exclude patterns.

        Returns:
            Set of exclude patterns
        """
        return cls.EXCLUDE_PATTERNS.copy()

    @classmethod
    def get_test_patterns(cls) -> Set[str]:
        """Get the set of test file patterns.

        Returns:
            Set of test file patterns
        """
        return cls.TEST_PATTERNS.copy()


# Convenience functions for backward compatibility
def is_code_file(file_path: str) -> bool:
    """Check if a file is a code file."""
    return FileFilter.is_code_file(file_path)


def is_analyzable_file(file_path: str) -> bool:
    """Check if a file can be analyzed."""
    return FileFilter.is_analyzable_file(file_path)


def filter_code_files(file_paths: List[str], exclude_tests: bool = True) -> List[str]:
    """Filter files to only include code files."""
    return FileFilter.filter_code_files(file_paths, exclude_tests)


def filter_analyzable_files(
    file_paths: List[str], exclude_tests: bool = True
) -> List[str]:
    """Filter files to only include analyzable files."""
    filtered_files = []
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        # Temporarily only include Python files to bypass JS/TS parsing issues
        if FileFilter.is_python_file(str(file_path)):
            if exclude_tests and FileFilter.is_test_file(str(file_path)):
                continue
            filtered_files.append(file_path_str)
    return filtered_files
