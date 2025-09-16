"""
Path normalization utilities for consistent file path handling.

This module provides utilities to normalize file paths consistently across
the entire system to prevent key mismatches in dependency analysis.
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class PathNormalizer:
    """Normalizes file paths to ensure consistency across the system."""

    def __init__(self, project_root: str):
        """Initialize the path normalizer with a project root.

        Args:
            project_root: The root directory of the project
        """
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = Path(str(project_root)).resolve()
        logger.debug(
            f"PathNormalizer initialized with project root: {self.project_root}"
        )

    def normalize_path(self, file_path: str) -> str:
        """Normalize a file path to a consistent relative format.

        Args:
            file_path: The file path to normalize (can be absolute or relative)

        Returns:
            Normalized relative path from project root

        Examples:
            >>> normalizer = PathNormalizer("/workspace")
            >>> normalizer.normalize_path("CODE_OF_CONDUCT.md")
            "CODE_OF_CONDUCT.md"
            >>> normalizer.normalize_path("/workspace/src/core/task/Task.ts")
            "src/core/task/Task.ts"
            >>> normalizer.normalize_path("webview-ui/vitest.setup.ts")
            "webview-ui/vitest.setup.ts"
        """
        try:
            # Convert to Path object
            path = Path(file_path)

            # If it's already relative and doesn't start with project root, use as-is
            if not path.is_absolute():
                # Check if it's already a relative path from project root
                if not str(path).startswith(str(self.project_root)):
                    return str(path)

            # Convert absolute path to relative path from project root
            if path.is_absolute():
                try:
                    relative_path = path.relative_to(self.project_root)
                    return str(relative_path)
                except ValueError:
                    # Path is not relative to project root, return as-is
                    logger.warning(
                        f"Path {file_path} is not relative to project root {self.project_root}"
                    )
                    return str(path)

            # Already relative, return as-is
            return str(path)

        except Exception as e:
            logger.error(f"Error normalizing path {file_path}: {e}")
            return file_path

    def normalize_paths(self, file_paths: list[str]) -> list[str]:
        """Normalize a list of file paths.

        Args:
            file_paths: List of file paths to normalize

        Returns:
            List of normalized file paths
        """
        return [self.normalize_path(path) for path in file_paths]

    def is_normalized(self, file_path: str) -> bool:
        """Check if a file path is already normalized.

        Args:
            file_path: The file path to check

        Returns:
            True if the path is normalized, False otherwise
        """
        normalized = self.normalize_path(file_path)
        return file_path == normalized


def normalize_file_path(file_path: str, project_root: str) -> str:
    """Convenience function to normalize a single file path.

    Args:
        file_path: The file path to normalize
        project_root: The project root directory

    Returns:
        Normalized file path
    """
    normalizer = PathNormalizer(project_root)
    return normalizer.normalize_path(file_path)


def normalize_file_paths(file_paths: list[str], project_root: str) -> list[str]:
    """Convenience function to normalize a list of file paths.

    Args:
        file_paths: List of file paths to normalize
        project_root: The project root directory

    Returns:
        List of normalized file paths
    """
    normalizer = PathNormalizer(project_root)
    return normalizer.normalize_paths(file_paths)
