#!/usr/bin/env python3
"""
Tests for the custom exception hierarchy and error handling utilities.
"""

import pytest
from repomap_tool.exceptions import (
    RepoMapError,
    ConfigurationError,
    FileAccessError,
    TagExtractionError,
    MatcherError,
    CacheError,
    ValidationError,
    SearchError,
    ProjectAnalysisError,
    RepoMapMemoryError,
    NetworkError,
    RepoMapTimeoutError,
    safe_operation,
    handle_errors,
)


class TestExceptionHierarchy:
    """Test the custom exception hierarchy."""

    def test_base_exception_creation(self):
        """Test creating base RepoMapError."""
        error = RepoMapError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.context == {}

    def test_exception_with_context(self):
        """Test creating exception with context."""
        context = {"file": "test.py", "line": 42}
        error = RepoMapError("Test error", context)
        assert "Context: file=test.py, line=42" in str(error)
        assert error.context == context

    def test_specific_exceptions(self):
        """Test creating specific exception types."""
        exceptions = [
            ConfigurationError("Config error"),
            FileAccessError("File error"),
            TagExtractionError("Tag error"),
            MatcherError("Matcher error"),
            CacheError("Cache error"),
            ValidationError("Validation error"),
            SearchError("Search error"),
            ProjectAnalysisError("Analysis error"),
            RepoMapMemoryError("Memory error"),
            NetworkError("Network error"),
            RepoMapTimeoutError("Timeout error"),
        ]

        for exc in exceptions:
            assert isinstance(exc, RepoMapError)
            assert exc.message in str(exc)

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from RepoMapError."""
        error = ConfigurationError("Test")
        assert isinstance(error, RepoMapError)
        assert isinstance(error, Exception)


class TestSafeOperationDecorator:
    """Test the safe_operation decorator."""

    def test_successful_operation(self):
        """Test that successful operations work normally."""

        @safe_operation("test_operation")
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_file_not_found_error(self):
        """Test that FileNotFoundError is converted to FileAccessError."""

        @safe_operation("test_operation")
        def file_not_found_func():
            raise FileNotFoundError("test.py")

        with pytest.raises(FileAccessError) as exc_info:
            file_not_found_func()

        assert "File not found during test_operation" in str(exc_info.value)
        assert exc_info.value.context["file_path"] == "test.py"

    def test_permission_error(self):
        """Test that PermissionError is converted to FileAccessError."""

        @safe_operation("test_operation")
        def permission_error_func():
            raise PermissionError("test.py")

        with pytest.raises(FileAccessError) as exc_info:
            permission_error_func()

        assert "Permission denied during test_operation" in str(exc_info.value)
        assert exc_info.value.context["file_path"] == "test.py"

    def test_memory_error(self):
        """Test that MemoryError is converted to our RepoMapMemoryError."""

        @safe_operation("test_operation")
        def memory_error_func():
            raise MemoryError("Out of memory")

        with pytest.raises(RepoMapMemoryError) as exc_info:
            memory_error_func()

        assert "Memory limit exceeded during test_operation" in str(exc_info.value)

    def test_timeout_error(self):
        """Test that TimeoutError is converted to our RepoMapTimeoutError."""

        @safe_operation("test_operation")
        def timeout_error_func():
            raise TimeoutError("Operation timed out")

        with pytest.raises(RepoMapTimeoutError) as exc_info:
            timeout_error_func()

        assert "Operation timed out during test_operation" in str(exc_info.value)

    def test_custom_exception_preserved(self):
        """Test that our custom exceptions are preserved."""

        @safe_operation("test_operation")
        def custom_error_func():
            raise SearchError("Custom search error")

        with pytest.raises(SearchError) as exc_info:
            custom_error_func()

        assert "Custom search error" in str(exc_info.value)

    def test_unexpected_exception_wrapped(self):
        """Test that unexpected exceptions are wrapped."""

        @safe_operation("test_operation")
        def unexpected_error_func():
            raise ValueError("Unexpected value error")

        with pytest.raises(RepoMapError) as exc_info:
            unexpected_error_func()

        assert "Unexpected error during test_operation" in str(exc_info.value)
        assert "Unexpected value error" in str(exc_info.value)

    def test_safe_operation_with_context(self):
        """Test safe_operation with custom context."""

        @safe_operation("test_operation", {"custom": "context"})
        def error_func():
            raise FileNotFoundError("test.py")

        with pytest.raises(FileAccessError) as exc_info:
            error_func()

        assert exc_info.value.context["custom"] == "context"


class TestHandleErrorsDecorator:
    """Test the handle_errors decorator."""

    def test_successful_operation(self):
        """Test that successful operations work normally."""

        @handle_errors
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_custom_exception_preserved(self):
        """Test that our custom exceptions are preserved."""

        @handle_errors
        def custom_error_func():
            raise SearchError("Custom search error")

        with pytest.raises(SearchError) as exc_info:
            custom_error_func()

        assert "Custom search error" in str(exc_info.value)

    def test_unexpected_exception_wrapped(self):
        """Test that unexpected exceptions are wrapped."""

        @handle_errors
        def unexpected_error_func():
            raise ValueError("Unexpected value error")

        with pytest.raises(RepoMapError) as exc_info:
            unexpected_error_func()

        assert "Error in unexpected_error_func" in str(exc_info.value)
        assert "Unexpected value error" in str(exc_info.value)


class TestExceptionContext:
    """Test exception context functionality."""

    def test_context_preservation(self):
        """Test that context is preserved in exceptions."""
        context = {"operation": "test", "file": "test.py", "line": 42, "user_id": 123}

        error = FileAccessError("Test error", context)

        assert error.context["operation"] == "test"
        assert error.context["file"] == "test.py"
        assert error.context["line"] == 42
        assert error.context["user_id"] == 123

    def test_context_string_representation(self):
        """Test that context is included in string representation."""
        context = {"file": "test.py", "line": 42}
        error = TagExtractionError("Failed to extract tags", context)

        error_str = str(error)
        assert "Failed to extract tags" in error_str
        assert "Context: file=test.py, line=42" in error_str

    def test_empty_context(self):
        """Test that empty context doesn't affect string representation."""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.context == {}
