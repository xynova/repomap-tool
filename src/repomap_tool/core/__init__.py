"""
Core functionality for repomap-tool.

This package contains the main components for code analysis and search functionality.
"""

from .repo_map import DockerRepoMap
from .file_scanner import parse_gitignore, should_ignore_file
from .cache_manager import CacheManager

__all__ = ["DockerRepoMap", "parse_gitignore", "should_ignore_file", "CacheManager"]
