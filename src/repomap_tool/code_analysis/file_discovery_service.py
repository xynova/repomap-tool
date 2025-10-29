"""
Centralized file discovery service for RepoMap-Tool.

This service provides a single source of truth for file discovery,
eliminating the need for components to ask for file paths separately.
"""

import logging
from ..core.logging_service import get_logger
from typing import List, Optional, Dict, Any
from pathlib import Path

from .file_filter import FileFilter
from ..core.file_scanner import get_project_files

logger = get_logger(__name__)


class FileDiscoveryService:
    """Centralized service for file discovery and filtering."""

    def __init__(self, project_root: str):
        """Initialize the file discovery service.

        Args:
            project_root: Root path of the project
        """
        # Always normalize to absolute path to ensure consistency with cache
        self.project_root = str(Path(project_root).resolve())
        self._all_files_cache: Optional[List[str]] = None
        self._code_files_cache: Optional[List[str]] = None
        self._analyzable_files_cache: Optional[List[str]] = None

        logger.debug(f"FileDiscoveryService initialized for project: {project_root}")

    def get_all_files(self, use_cache: bool = True) -> List[str]:
        """Get all files in the project (raw discovery, no filtering).

        Args:
            use_cache: Whether to use cached results

        Returns:
            List of all project files (absolute paths)
        """
        if use_cache and self._all_files_cache is not None:
            return self._all_files_cache

        logger.debug("Discovering all project files")
        all_files = get_project_files(self.project_root, verbose=False)

        if use_cache:
            self._all_files_cache = all_files

        logger.debug(f"Discovered {len(all_files)} total files")
        return all_files

    def get_code_files(
        self, exclude_tests: bool = True, use_cache: bool = True
    ) -> List[str]:
        """Get code files for centrality analysis.

        Args:
            exclude_tests: Whether to exclude test files
            use_cache: Whether to use cached results

        Returns:
            List of code files (absolute paths)
        """
        cache_key = f"code_files_{exclude_tests}"
        if use_cache and self._code_files_cache is not None:
            return self._code_files_cache

        logger.debug(f"Filtering code files (exclude_tests={exclude_tests})")
        all_files = self.get_all_files(use_cache=use_cache)
        code_files = FileFilter.filter_code_files(
            all_files, exclude_tests=exclude_tests
        )

        if use_cache:
            self._code_files_cache = code_files

        logger.debug(f"Filtered to {len(code_files)} code files")
        return code_files

    def get_analyzable_files(
        self, exclude_tests: bool = True, use_cache: bool = True
    ) -> List[str]:
        """Get analyzable files for import analysis.

        Args:
            exclude_tests: Whether to exclude test files
            use_cache: Whether to use cached results

        Returns:
            List of analyzable files (absolute paths)
        """
        if use_cache and self._analyzable_files_cache is not None:
            return self._analyzable_files_cache

        logger.debug(f"Filtering analyzable files (exclude_tests={exclude_tests})")
        all_files = self.get_all_files(use_cache=use_cache)
        analyzable_files = FileFilter.filter_analyzable_files(
            all_files, exclude_tests=exclude_tests
        )

        if use_cache:
            self._analyzable_files_cache = analyzable_files

        logger.debug(f"Filtered to {len(analyzable_files)} analyzable files")
        return analyzable_files

    def get_files_for_analysis(
        self, analysis_type: str, exclude_tests: bool = True
    ) -> List[str]:
        """Get files appropriate for a specific analysis type.

        Args:
            analysis_type: Type of analysis ('centrality', 'impact', 'imports', etc.)
            exclude_tests: Whether to exclude test files

        Returns:
            List of files appropriate for the analysis type
        """
        if analysis_type in ["centrality", "impact"]:
            return self.get_code_files(exclude_tests=exclude_tests)
        elif analysis_type in ["imports", "dependencies"]:
            return self.get_analyzable_files(exclude_tests=exclude_tests)
        else:
            # Default to code files
            return self.get_code_files(exclude_tests=exclude_tests)

    def get_tree_sitter_supported_files(
        self, tree_sitter_parser: Any, exclude_tests: bool = True
    ) -> List[str]:
        """Get files that are supported by tree-sitter parser.

        Args:
            tree_sitter_parser: Tree-sitter parser instance to check language support
            exclude_tests: Whether to exclude test files

        Returns:
            List of files that can be parsed by tree-sitter
        """
        all_files = self.get_all_files(use_cache=True)

        # Filter files based on tree-sitter language support
        supported_files = []
        for file_path in all_files:
            if tree_sitter_parser.is_language_supported(file_path):
                supported_files.append(file_path)

        # Apply additional filtering if needed
        if exclude_tests:
            supported_files = FileFilter.filter_code_files(
                supported_files, exclude_tests=True
            )

        return supported_files

    def clear_cache(self) -> None:
        """Clear all cached file lists."""
        self._all_files_cache = None
        self._code_files_cache = None
        self._analyzable_files_cache = None
        logger.debug("Cleared file discovery cache")

    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about discovered files.

        Returns:
            Dictionary with file statistics
        """
        all_files = self.get_all_files()
        code_files = self.get_code_files(exclude_tests=True)
        analyzable_files = self.get_analyzable_files(exclude_tests=True)

        return {
            "total_files": len(all_files),
            "code_files": len(code_files),
            "analyzable_files": len(analyzable_files),
            "test_files_excluded": len(all_files) - len(code_files),
            "project_root": self.project_root,
        }


# Service factory function (no singleton - each project needs its own instance)
def create_file_discovery_service(project_root: str) -> FileDiscoveryService:
    """Create a new file discovery service instance for a project.

    Args:
        project_root: Project root path

    Returns:
        FileDiscoveryService instance
    """
    return FileDiscoveryService(project_root)
