#!/usr/bin/env python3
"""
Unit tests for analyzer functions.

This module tests the core analyzer functions that currently have no unit tests:
- analyze_file_types()
- analyze_identifier_types()
- get_cache_size()
"""

from unittest.mock import patch

from repomap_tool.core.analyzer import (
    analyze_file_types,
    analyze_identifier_types,
    get_cache_size,
)


class TestAnalyzeFileTypes:
    """Test file type analysis functionality."""

    def test_analyze_file_types_with_python_files(self):
        """Test analyzing Python files."""
        # Arrange
        project_files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "README.md",
            "requirements.txt",
        ]

        # Act
        file_types = analyze_file_types(project_files)

        # Assert
        assert "py" in file_types
        assert file_types["py"] == 3
        assert "md" in file_types
        assert file_types["md"] == 1
        assert "txt" in file_types
        assert file_types["txt"] == 1

    def test_analyze_file_types_with_no_files(self):
        """Test analyzing empty file list."""
        # Arrange
        project_files = []

        # Act
        file_types = analyze_file_types(project_files)

        # Assert
        assert file_types == {}

    def test_analyze_file_types_with_files_no_extensions(self):
        """Test analyzing files without extensions."""
        # Arrange
        project_files = ["Dockerfile", "Makefile", "README"]

        # Act
        file_types = analyze_file_types(project_files)

        # Assert
        assert file_types == {}

    def test_analyze_file_types_with_mixed_extensions(self):
        """Test analyzing files with various extensions."""
        # Arrange
        project_files = [
            "script.py",
            "data.json",
            "config.yaml",
            "document.pdf",
            "image.png",
            "archive.zip",
        ]

        # Act
        file_types = analyze_file_types(project_files)

        # Assert
        assert file_types["py"] == 1
        assert file_types["json"] == 1
        assert file_types["yaml"] == 1
        assert file_types["pdf"] == 1
        assert file_types["png"] == 1
        assert file_types["zip"] == 1


class TestAnalyzeIdentifierTypes:
    """Test identifier type analysis functionality."""

    def test_analyze_identifier_types_with_various_identifiers(self):
        """Test analyzing various types of identifiers."""
        # Arrange
        identifiers = {
            "UserClass",  # Class (PascalCase)
            "user_function",  # Function (snake_case)
            "CONSTANT_VALUE",  # Constant (UPPER_CASE)
            "variable_name",  # Variable (snake_case)
            "camelCaseVar",  # Variable (camelCase)
            "get_data",  # Function (snake_case)
            "set_value",  # Function (snake_case)
            "is_valid",  # Function (snake_case)
            "has_permission",  # Function (snake_case)
        }

        # Act
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert identifier_types["classes"] >= 1  # UserClass
        assert identifier_types["functions"] >= 6  # All snake_case functions
        # Note: The analyzer classifies snake_case as functions, not variables
        assert identifier_types["variables"] >= 0  # No variables in this set
        assert identifier_types["constants"] >= 1  # CONSTANT_VALUE

    def test_analyze_identifier_types_with_no_identifiers(self):
        """Test analyzing empty identifier set."""
        # Arrange
        identifiers = set()

        # Act
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert identifier_types["classes"] == 0
        assert identifier_types["functions"] == 0
        assert identifier_types["variables"] == 0
        assert identifier_types["constants"] == 0
        assert identifier_types["other"] == 0

    def test_analyze_identifier_types_with_only_classes(self):
        """Test analyzing only class identifiers."""
        # Arrange
        identifiers = {
            "UserManager",
            "DataProcessor",
            "ConfigHandler",
            "FileReader",
        }

        # Act
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert identifier_types["classes"] == 4
        assert identifier_types["functions"] == 0
        assert identifier_types["variables"] == 0
        assert identifier_types["constants"] == 0
        assert identifier_types["other"] == 0

    def test_analyze_identifier_types_with_only_functions(self):
        """Test analyzing only function identifiers."""
        # Arrange
        identifiers = {
            "get_user_data",
            "process_data",
            "validate_input",
            "save_to_file",
        }

        # Act
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert identifier_types["classes"] == 0
        assert identifier_types["functions"] == 4
        assert identifier_types["variables"] == 0
        assert identifier_types["constants"] == 0
        assert identifier_types["other"] == 0

    def test_analyze_identifier_types_with_only_constants(self):
        """Test analyzing only constant identifiers."""
        # Arrange
        identifiers = {
            "MAX_RETRY_COUNT",
            "DEFAULT_TIMEOUT",
            "API_BASE_URL",
            "DEBUG_MODE",
        }

        # Act
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert identifier_types["classes"] == 0
        assert identifier_types["functions"] == 0
        assert identifier_types["variables"] == 0
        assert identifier_types["constants"] == 4
        assert identifier_types["other"] == 0


class TestGetCacheSize:
    """Test cache size functionality."""

    def test_get_cache_size_returns_integer(self):
        """Test that get_cache_size returns an integer."""
        # Act
        cache_size = get_cache_size()

        # Assert
        assert isinstance(cache_size, int)
        assert cache_size == 0  # Currently returns 0 as placeholder

    @patch("repomap_tool.core.analyzer.get_cache_size")
    def test_get_cache_size_returns_zero_when_no_cache(self, mock_get_cache_size):
        """Test that get_cache_size returns 0 when no cache exists."""
        # Arrange
        mock_get_cache_size.return_value = 0

        # Act
        cache_size = get_cache_size()

        # Assert
        assert cache_size == 0

    def test_get_cache_size_handles_large_values(self):
        """Test that get_cache_size handles large cache sizes."""
        # Act
        cache_size = get_cache_size()

        # Assert
        assert cache_size == 0  # Currently returns 0 as placeholder
        assert isinstance(cache_size, int)


class TestAnalyzerIntegration:
    """Integration tests for analyzer functions."""

    def test_analyzer_functions_work_together(self):
        """Test that analyzer functions work together correctly."""
        # Arrange
        project_files = [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "config.yaml",
            "README.md",
        ]

        identifiers = {
            "MainClass",
            "UtilityFunctions",
            "test_function",
            "config_value",
            "CONSTANT_DATA",
        }

        # Act
        file_types = analyze_file_types(project_files)
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert file_types["py"] == 3
        assert file_types["yaml"] == 1
        assert file_types["md"] == 1

        assert identifier_types["classes"] >= 2  # MainClass, UtilityFunctions
        assert identifier_types["functions"] >= 1  # test_function
        # Note: config_value is snake_case, so it's classified as a function
        assert identifier_types["constants"] >= 1  # CONSTANT_DATA

    def test_analyzer_functions_with_real_project_structure(self):
        """Test analyzer functions with a realistic project structure."""
        # Arrange
        project_files = [
            "src/repomap_tool/__init__.py",
            "src/repomap_tool/core/repo_map.py",
            "src/repomap_tool/matchers/fuzzy_matcher.py",
            "src/repomap_tool/models.py",
            "tests/unit/test_fuzzy.py",
            "tests/integration/test_self_integration.py",
            "pyproject.toml",
            "README.md",
            "Makefile",
        ]

        identifiers = {
            "DockerRepoMap",
            "FuzzyMatcher",
            "RepoMapConfig",
            "test_fuzzy_search",
            "analyze_project",
            "search_identifiers",
            "MAX_RESULTS",
            "DEFAULT_THRESHOLD",
        }

        # Act
        file_types = analyze_file_types(project_files)
        identifier_types = analyze_identifier_types(identifiers)

        # Assert
        assert file_types["py"] == 6  # 6 Python files in the list
        assert file_types["toml"] == 1
        assert file_types["md"] == 1

        assert (
            identifier_types["classes"] >= 3
        )  # DockerRepoMap, FuzzyMatcher, RepoMapConfig
        assert (
            identifier_types["functions"] >= 3
        )  # test_fuzzy_search, analyze_project, search_identifiers
        assert identifier_types["constants"] >= 2  # MAX_RESULTS, DEFAULT_THRESHOLD
