"""
Path resolution utilities for file operations.

This module provides utilities for resolving file paths, handling
absolute/relative path conversion, and project file enumeration.
"""

import os
from typing import List, Optional
from pathlib import Path

from .file_utils import get_all_project_files


class PathResolver:
    """Utility class for resolving file paths and project operations."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the path resolver.

        Args:
            project_root: Root path of the project
        """
        self.project_root = project_root

    def resolve_file_paths(self, file_paths: List[str]) -> List[str]:
        """Resolve file paths relative to project root.

        Args:
            file_paths: List of file paths to resolve

        Returns:
            List of resolved file paths
        """
        resolved_paths = []
        for file_path in file_paths:
            if os.path.isabs(file_path):
                resolved_paths.append(file_path)
            else:
                if self.project_root is None:
                    resolved_paths.append(file_path)
                else:
                    resolved_path = os.path.join(self.project_root, file_path)
                    resolved_paths.append(resolved_path)
        return resolved_paths

    def get_all_project_files(self) -> List[str]:
        """Get all files in the project.

        Returns:
            List of all project files
        """
        return get_all_project_files(self.project_root) if self.project_root else []

    def convert_to_relative_path(self, file_path: str) -> str:
        """Convert absolute path to relative path.

        Args:
            file_path: File path to convert

        Returns:
            Relative file path
        """
        if os.path.isabs(file_path) and self.project_root:
            try:
                return os.path.relpath(file_path, self.project_root)
            except ValueError:
                # If paths are on different drives (Windows), use the original path
                return file_path
        return file_path
