"""
Path resolution utilities for file operations.

This module provides utilities for resolving file paths, handling
absolute/relative path conversion, and project file enumeration.
"""

import os
from typing import List, Optional
from pathlib import Path

from ..core.file_scanner import get_project_files


class PathResolver:
    """Utility class for resolving file paths and project operations."""

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the path resolver.

        Args:
            project_root: Root path of the project
        """
        # Ensure project_root is always a string, not a ConfigurationOption
        self.project_root = str(project_root) if project_root is not None else None

    def resolve_file_paths(self, file_paths: List[str]) -> List[str]:
        """Validate that all file paths are absolute (architectural requirement).

        Args:
            file_paths: List of file paths to validate

        Returns:
            List of validated absolute file paths

        Raises:
            ValueError: If any path is not absolute
        """
        validated_paths = []
        for file_path in file_paths:
            if not os.path.isabs(file_path):
                raise ValueError(
                    f"All file paths must be absolute (architectural requirement). Got relative path: {file_path}"
                )
            validated_paths.append(file_path)
        return validated_paths

    def get_all_project_files(self, max_files: Optional[int] = None) -> List[str]:
        """Get all files in the project.

        Args:
            max_files: Maximum number of files to return (for performance)

        Returns:
            List of all project files
        """
        if not self.project_root:
            return []

        # Use centralized file discovery service
        from .file_discovery_service import create_file_discovery_service

        file_discovery = create_file_discovery_service(self.project_root)
        code_files = file_discovery.get_code_files(exclude_tests=True)

        # Apply file limit for performance (only if specified)
        if max_files is not None and len(code_files) > max_files:
            # Sort by importance (prioritize main files)
            important_files = []
            other_files = []

            for file_path in code_files:
                # Prioritize main entry points and core files
                if any(
                    priority in file_path.lower()
                    for priority in ["main.", "index.", "app.", "core/", "src/"]
                ):
                    important_files.append(file_path)
                else:
                    other_files.append(file_path)

            # Take important files first, then other files
            selected_files = important_files[:max_files]
            if len(selected_files) < max_files:
                remaining_slots = max_files - len(selected_files)
                selected_files.extend(other_files[:remaining_slots])

            return selected_files

        return code_files

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
