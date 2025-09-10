"""
File scanning and gitignore functionality.

This module handles project file discovery and gitignore pattern matching.
"""

import fnmatch
import logging
from pathlib import Path
from typing import List


def parse_gitignore(gitignore_path: Path) -> List[str]:
    """
    Parse a .gitignore file and return list of patterns.

    Args:
        gitignore_path: Path to .gitignore file

    Returns:
        List of gitignore patterns
    """
    patterns: List[str] = []
    if not gitignore_path.exists():
        return patterns

    try:
        with open(gitignore_path, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.append(line)
    except (IOError, OSError) as e:
        logging.warning(f"Failed to read .gitignore file {gitignore_path}: {e}")

    return patterns


def should_ignore_file(
    file_path: Path, gitignore_patterns: List[str], project_root: Path
) -> bool:
    """
    Check if a file should be ignored based on .gitignore patterns.

    Args:
        file_path: Path to the file to check
        gitignore_patterns: List of .gitignore patterns
        project_root: Root directory of the project

    Returns:
        True if file should be ignored, False otherwise
    """
    if not gitignore_patterns:
        return False

    # Get relative path from project root
    try:
        rel_path = file_path.relative_to(project_root)
    except ValueError:
        # File is not under project root
        return False

    rel_path_str = str(rel_path)
    is_ignored = False

    for pattern in gitignore_patterns:
        # Skip empty patterns
        if not pattern or pattern.isspace():
            continue

        # Handle negation patterns (starting with !)
        if pattern.startswith("!"):
            # Remove the ! prefix
            negated_pattern = pattern[1:]
            # Check if this negation pattern matches
            if _pattern_matches(rel_path_str, negated_pattern):
                # Negation pattern matches, so don't ignore this file
                is_ignored = False
            continue

        # Check if this pattern matches
        if _pattern_matches(rel_path_str, pattern):
            is_ignored = True

    return is_ignored


def _pattern_matches(rel_path_str: str, pattern: str) -> bool:
    """
    Check if a gitignore pattern matches a relative path.

    Args:
        rel_path_str: Relative path string to check
        pattern: Gitignore pattern to match against

    Returns:
        True if pattern matches, False otherwise
    """
    # Handle double wildcard patterns (**)
    if "**" in pattern:
        # Handle different ** patterns
        if pattern.startswith("**/"):
            # **/pattern -> matches pattern at any depth
            pattern = pattern[3:]
            if pattern.endswith("/"):
                pattern = pattern[:-1]
            # Check if any directory in the path matches the pattern
            path_parts = rel_path_str.split("/")
            for i in range(len(path_parts)):
                sub_path = "/".join(path_parts[: i + 1])
                if fnmatch.fnmatch(sub_path, pattern) or sub_path == pattern:
                    return True
                # Also check individual path parts
                if path_parts[i] == pattern:
                    return True
            return False

        elif pattern.endswith("/**"):
            # pattern/** -> matches pattern and anything under it
            pattern = pattern[:-3]
            if rel_path_str.startswith(pattern + "/") or rel_path_str == pattern:
                return True
            return False

        elif "/**/" in pattern:
            # pattern/**/suffix -> matches pattern, then any directories, then suffix
            prefix, suffix = pattern.split("/**/", 1)
            if rel_path_str.startswith(prefix + "/"):
                remaining_path = rel_path_str[len(prefix) + 1 :]
                # Check if suffix appears anywhere in the remaining path
                if suffix in remaining_path:
                    return True
                # Check if suffix is at the end
                if remaining_path.endswith("/" + suffix) or remaining_path == suffix:
                    return True
            return False

        return False

    # Handle directory patterns (ending with /)
    if pattern.endswith("/"):
        dir_pattern = pattern[:-1]
        if rel_path_str.startswith(dir_pattern + "/") or rel_path_str == dir_pattern:
            return True

    # Handle patterns with wildcards (anywhere in the pattern)
    elif "*" in pattern or "?" in pattern:
        # Use fnmatch for any pattern containing wildcards
        if fnmatch.fnmatch(rel_path_str, pattern):
            return True
    else:
        # Exact match or prefix match
        if rel_path_str == pattern or rel_path_str.startswith(pattern + "/"):
            return True

    return False


def get_project_files(project_root: str, verbose: bool = False) -> List[str]:
    """
    Get list of project files, respecting .gitignore patterns.

    Args:
        project_root: Root directory of the project
        verbose: Whether to enable verbose logging

    Returns:
        List of file paths relative to project root
    """
    import os

    # Parse .gitignore file
    gitignore_path = Path(project_root) / ".gitignore"
    gitignore_patterns = parse_gitignore(gitignore_path)

    if gitignore_patterns and verbose:
        logging.info(f"Loaded {len(gitignore_patterns)} .gitignore patterns")

    files = []
    for root, dirs, filenames in os.walk(project_root):
        # Filter out ignored directories
        dirs[:] = [
            d
            for d in dirs
            if not should_ignore_file(
                Path(root) / d,
                gitignore_patterns,
                Path(project_root),
            )
        ]

        for filename in filenames:
            file_path = Path(root) / filename

            # Always ignore .gitignore file itself
            if filename == ".gitignore":
                if verbose:
                    logging.debug(f"Ignoring .gitignore file: {file_path}")
                continue

            # Check if file should be ignored
            if should_ignore_file(file_path, gitignore_patterns, Path(project_root)):
                if verbose:
                    logging.debug(f"Ignoring file (gitignore): {file_path}")
                continue

            # Get relative path from project root
            rel_path = file_path.relative_to(Path(project_root))
            files.append(str(rel_path))

    return files
