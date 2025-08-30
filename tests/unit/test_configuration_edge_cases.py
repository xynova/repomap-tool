#!/usr/bin/env python3
"""
Configuration Edge Case Tests

This module tests configuration validation edge cases to identify gaps and improve error handling.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

from repomap_tool.models import (
    RepoMapConfig,
    FuzzyMatchConfig,
    SemanticMatchConfig,
    SearchRequest,
    SearchResponse,
    MatchResult,
    ProjectInfo,
    HealthCheck,
    ErrorResponse,
    create_config_from_dict,
    config_to_dict,
    validate_search_request,
    create_error_response,
)


class TestRepoMapConfigEdgeCases:
    """Test edge cases for RepoMapConfig validation."""

    def test_config_with_nonexistent_project_root(self):
        """Test configuration with nonexistent project root."""
        # Arrange
        nonexistent_paths = [
            "/nonexistent/path",
            "/tmp/nonexistent_" + str(os.getpid()),
            "relative/nonexistent/path",
        ]

        for path in nonexistent_paths:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError, match="Project root does not exist"):
                RepoMapConfig(project_root=path)

    def test_config_with_file_as_project_root(self):
        """Test configuration with file as project root (should be directory)."""
        # Arrange
        with tempfile.NamedTemporaryFile() as temp_file:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError, match="Project root must be a directory"):
                RepoMapConfig(project_root=temp_file.name)

    def test_config_with_empty_project_root(self):
        """Test configuration with empty project root."""
        # Arrange
        empty_paths = ["   ", "\t", "\n"]  # Empty string resolves to current dir

        for path in empty_paths:
            # Act & Assert - Should raise validation error for whitespace-only paths
            with pytest.raises((ValueError, Exception), match="Project root cannot be empty or whitespace only"):
                RepoMapConfig(project_root=path)

    def test_config_with_empty_string_project_root(self):
        """Test configuration with empty string project root (should be rejected)."""
        # Act & Assert - Empty string should be rejected
        with pytest.raises((ValueError, Exception), match="Project root cannot be empty or whitespace only"):
            RepoMapConfig(project_root="")

    def test_config_with_malicious_project_root(self):
        """Test configuration with malicious project root paths."""
        # Arrange
        malicious_paths = [
            "../../../etc/passwd",  # Path traversal
            "test\x00.py",  # Null byte
            "test\n.py",  # Newline
            "test<script>.py",  # Script tags
            "test'; DROP TABLE files; --.py",  # SQL injection
            "a" * 10000,  # Very long path
        ]

        for path in malicious_paths:
            # Act & Assert - Should handle malicious paths gracefully
            try:
                with pytest.raises(ValueError):
                    RepoMapConfig(project_root=path)
            except Exception as e:
                # Should not crash with unexpected exceptions
                assert "Project root does not exist" in str(e) or "Project root must be a directory" in str(e)

    def test_config_with_extreme_map_tokens(self):
        """Test configuration with extreme map_tokens values."""
        # Arrange
        extreme_values = [
            {"map_tokens": 0},  # Below minimum
            {"map_tokens": 8193},  # Above maximum
            {"map_tokens": -1},  # Negative
            {"map_tokens": 1000000},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(project_root=".", **extreme_value)

    def test_config_with_extreme_max_results(self):
        """Test configuration with extreme max_results values."""
        # Arrange
        extreme_values = [
            {"max_results": 0},  # Below minimum
            {"max_results": 1001},  # Above maximum
            {"max_results": -1},  # Negative
            {"max_results": 1000000},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(project_root=".", **extreme_value)

    def test_config_with_invalid_log_level(self):
        """Test configuration with invalid log levels."""
        # Arrange
        invalid_levels = [
            "DEBUGGING",  # Invalid level
            "FATAL",  # Invalid level
            "",  # Empty
            "   ",  # Whitespace
            "123",  # Numbers
            "🎉",  # Emoji
        ]

        for level in invalid_levels:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(project_root=".", log_level=level)

    def test_config_with_coercible_log_levels(self):
        """Test configuration with log levels that can be coerced."""
        # Arrange
        coercible_levels = [
            "info",  # Lowercase (should be converted to uppercase)
        ]

        for level in coercible_levels:
            # Act & Assert - Should handle type coercion gracefully
            try:
                config = RepoMapConfig(project_root=".", log_level=level)
                assert config.log_level in ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"]
            except Exception as e:
                pytest.fail(f"Log level coercion failed: {e}")

    def test_config_with_invalid_log_level_abbreviations(self):
        """Test configuration with invalid log level abbreviations."""
        # Arrange
        invalid_abbreviations = [
            "WARN",  # Abbreviated (should fail)
        ]

        for level in invalid_abbreviations:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(project_root=".", log_level=level)

    def test_config_with_invalid_output_format(self):
        """Test configuration with invalid output formats."""
        # Arrange
        invalid_formats = [
            "xml",  # Invalid format
            "yaml",  # Invalid format
            "csv",  # Invalid format
            "",  # Empty
            "JSON",  # Uppercase
            "json ",  # Trailing space
        ]

        for format_type in invalid_formats:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                RepoMapConfig(project_root=".", output_format=format_type)

    def test_config_with_malicious_cache_dir(self):
        """Test configuration with malicious cache directory paths."""
        # Arrange
        malicious_paths = [
            "../../../etc/passwd",  # Path traversal
            "test\x00",  # Null byte
            "test\n",  # Newline
            "test<script>",  # Script tags
            "test'; DROP TABLE cache; --",  # SQL injection
        ]

        for path in malicious_paths:
            # Act & Assert - Should handle malicious paths gracefully
            try:
                config = RepoMapConfig(project_root=".", cache_dir=path)
                # Should not crash, but cache_dir should be resolved
                assert config.cache_dir is not None
            except Exception as e:
                # Should not crash with unexpected exceptions
                assert any(msg in str(e) for msg in [
                    "Project root does not exist",
                    "Project root must be a directory", 
                    "Cache directory cannot contain null bytes",
                    "Cache directory path too long",
                    "Invalid cache directory"
                ])

    def test_config_with_none_values(self):
        """Test configuration with None values."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Act & Assert - Should handle None values gracefully
            config = RepoMapConfig(
                project_root=temp_dir,
                cache_dir=None,  # This is allowed
            )
            
            assert config.cache_dir is None
            assert config.verbose is True  # Default value
            assert config.refresh_cache is False  # Default value

    def test_config_with_none_boolean_values(self):
        """Test configuration with None boolean values (should raise error)."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            # Act & Assert - Should raise validation error for None booleans
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(
                    project_root=temp_dir,
                    verbose=None,  # Should raise error
                )
            
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(
                    project_root=temp_dir,
                    refresh_cache=None,  # Should raise error
                )

    def test_config_with_invalid_types(self):
        """Test configuration with invalid types."""
        # Arrange
        invalid_configs = [
            {"project_root": 123},  # Integer instead of string
            {"project_root": 3.14},  # Float instead of string
            {"project_root": True},  # Boolean instead of string
            {"project_root": []},  # List instead of string
            {"project_root": {}},  # Dict instead of string
        ]

        for invalid_config in invalid_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, TypeError)):
                RepoMapConfig(project_root=".", **invalid_config)

    def test_config_with_coercible_types(self):
        """Test configuration with types that can be coerced."""
        # Arrange
        coercible_configs = [
            {"map_tokens": "100"},  # String to integer (should work)
            {"verbose": "true"},  # String to boolean (should work)
        ]

        for config in coercible_configs:
            # Act & Assert - Should handle type coercion gracefully
            try:
                result = RepoMapConfig(project_root=".", **config)
                assert result is not None
            except Exception as e:
                pytest.fail(f"Type coercion failed: {e}")

    def test_config_with_non_coercible_types(self):
        """Test configuration with types that cannot be coerced."""
        # Arrange
        non_coercible_configs = [
            {"max_results": 3.14},  # Float to integer (should fail)
        ]

        for config in non_coercible_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                RepoMapConfig(project_root=".", **config)


class TestFuzzyMatchConfigEdgeCases:
    """Test edge cases for FuzzyMatchConfig validation."""

    def test_fuzzy_config_with_extreme_thresholds(self):
        """Test fuzzy config with extreme threshold values."""
        # Arrange
        extreme_values = [
            {"threshold": -1},  # Below minimum
            {"threshold": 101},  # Above maximum
            {"threshold": -1000},  # Way below minimum
            {"threshold": 1000},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                FuzzyMatchConfig(**extreme_value)

    def test_fuzzy_config_with_invalid_strategies(self):
        """Test fuzzy config with invalid strategies."""
        # Arrange
        invalid_strategies = [
            ["invalid_strategy"],
            ["prefix", "invalid"],
            ["levenshtein", "sql_injection"],
            ["<script>alert('xss')</script>"],
            ["test'; DROP TABLE strategies; --"],
            [""],  # Empty strategy
            ["   "],  # Whitespace strategy
        ]

        for strategies in invalid_strategies:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError, match="Invalid strategies"):
                FuzzyMatchConfig(strategies=strategies)

    def test_fuzzy_config_with_empty_strategies(self):
        """Test fuzzy config with empty strategies list."""
        # Act & Assert - Should handle empty list gracefully
        config = FuzzyMatchConfig(strategies=[])
        assert config.strategies == []

    def test_fuzzy_config_with_duplicate_strategies(self):
        """Test fuzzy config with duplicate strategies."""
        # Act & Assert - Should handle duplicates gracefully
        config = FuzzyMatchConfig(strategies=["prefix", "prefix", "substring"])
        assert "prefix" in config.strategies
        assert "substring" in config.strategies

    def test_fuzzy_config_with_invalid_types(self):
        """Test fuzzy config with invalid types."""
        # Arrange
        invalid_configs = [
            {"strategies": "prefix"},  # String instead of list (should fail)
        ]

        for invalid_config in invalid_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                FuzzyMatchConfig(**invalid_config)

    def test_fuzzy_config_with_coercible_types(self):
        """Test fuzzy config with types that can be coerced."""
        # Arrange
        coercible_configs = [
            {"threshold": "70"},  # String to integer (should work)
            {"enabled": "true"},  # String to boolean (should work)
            {"cache_results": 1},  # Integer to boolean (should work)
        ]

        for config in coercible_configs:
            # Act & Assert - Should handle type coercion gracefully
            try:
                result = FuzzyMatchConfig(**config)
                assert result is not None
            except Exception as e:
                pytest.fail(f"Type coercion failed: {e}")


class TestSemanticMatchConfigEdgeCases:
    """Test edge cases for SemanticMatchConfig validation."""

    def test_semantic_config_with_extreme_thresholds(self):
        """Test semantic config with extreme threshold values."""
        # Arrange
        extreme_values = [
            {"threshold": -0.1},  # Below minimum
            {"threshold": 1.1},  # Above maximum
            {"threshold": -1000.0},  # Way below minimum
            {"threshold": 1000.0},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                SemanticMatchConfig(**extreme_value)

    def test_semantic_config_with_extreme_min_word_length(self):
        """Test semantic config with extreme min_word_length values."""
        # Arrange
        extreme_values = [
            {"min_word_length": -1},  # Negative (should fail)
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                SemanticMatchConfig(**extreme_value)

    def test_semantic_config_with_valid_extreme_values(self):
        """Test semantic config with extreme but valid values."""
        # Arrange
        valid_extreme_values = [
            {"min_word_length": 1},  # Minimum value (should work)
            {"min_word_length": 1000000},  # Very large (should work)
        ]

        for config in valid_extreme_values:
            # Act & Assert - Should handle extreme values gracefully
            try:
                result = SemanticMatchConfig(**config)
                assert result is not None
            except Exception as e:
                pytest.fail(f"Valid extreme value failed: {e}")

    def test_semantic_config_with_invalid_minimum_values(self):
        """Test semantic config with invalid minimum values."""
        # Arrange
        invalid_minimum_values = [
            {"min_word_length": 0},  # Below minimum (should fail)
        ]

        for config in invalid_minimum_values:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                SemanticMatchConfig(**config)

    def test_semantic_config_with_invalid_types(self):
        """Test semantic config with invalid types."""
        # Arrange
        invalid_configs = [
            {"min_word_length": 3.14},  # Float instead of integer (should fail)
        ]

        for invalid_config in invalid_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises((ValueError, Exception)):
                SemanticMatchConfig(**invalid_config)

    def test_semantic_config_with_coercible_types(self):
        """Test semantic config with types that can be coerced."""
        # Arrange
        coercible_configs = [
            {"threshold": "0.1"},  # String to float (should work)
            {"enabled": "true"},  # String to boolean (should work)
            {"use_tfidf": 1},  # Integer to boolean (should work)
        ]

        for config in coercible_configs:
            # Act & Assert - Should handle type coercion gracefully
            try:
                result = SemanticMatchConfig(**config)
                assert result is not None
            except Exception as e:
                pytest.fail(f"Type coercion failed: {e}")


class TestSearchRequestEdgeCases:
    """Test edge cases for SearchRequest validation."""

    def test_search_request_with_empty_query(self):
        """Test search request with empty query."""
        # Arrange
        empty_queries = [
            "",  # Empty string
            "   ",  # Whitespace only
            "\t\n\r",  # Control characters only
        ]

        for query in empty_queries:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError, match="Query cannot be empty"):
                SearchRequest(query=query)

    def test_search_request_with_extreme_thresholds(self):
        """Test search request with extreme threshold values."""
        # Arrange
        extreme_values = [
            {"threshold": -0.1},  # Below minimum
            {"threshold": 1.1},  # Above maximum
            {"threshold": -1000.0},  # Way below minimum
            {"threshold": 1000.0},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                SearchRequest(query="test", **extreme_value)

    def test_search_request_with_extreme_max_results(self):
        """Test search request with extreme max_results values."""
        # Arrange
        extreme_values = [
            {"max_results": 0},  # Below minimum
            {"max_results": 101},  # Above maximum
            {"max_results": -1},  # Negative
            {"max_results": 1000000},  # Way above maximum
        ]

        for extreme_value in extreme_values:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                SearchRequest(query="test", **extreme_value)

    def test_search_request_with_invalid_match_type(self):
        """Test search request with invalid match types."""
        # Arrange
        invalid_types = [
            "exact",  # Invalid type
            "regex",  # Invalid type
            "EXACT",  # Uppercase
            "fuzzy ",  # Trailing space
            "",  # Empty
        ]

        for match_type in invalid_types:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                SearchRequest(query="test", match_type=match_type)

    def test_search_request_with_malicious_query(self):
        """Test search request with malicious queries."""
        # Arrange
        malicious_queries = [
            "test\x00injection",  # Null byte injection
            "test<script>alert('xss')</script>",  # XSS attempt
            "test'; DROP TABLE identifiers; --",  # SQL injection
            "a" * 10000,  # Very long query
            "🎉🎊🎈",  # Emojis
            "测试",  # Chinese characters
        ]

        for query in malicious_queries:
            # Act & Assert - Should handle malicious queries gracefully
            try:
                request = SearchRequest(query=query)
                assert request.query == query
            except Exception as e:
                pytest.fail(f"Malicious query '{query}' broke the system: {e}")

    def test_search_request_with_invalid_types(self):
        """Test search request with invalid types."""
        # Arrange
        invalid_configs = [
            {"query": 123},  # Integer instead of string
            {"query": 3.14},  # Float instead of string
            {"query": True},  # Boolean instead of string
            {"threshold": "0.7"},  # String instead of float
            {"max_results": "10"},  # String instead of integer
            {"include_context": "true"},  # String instead of boolean
        ]

        for invalid_config in invalid_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                SearchRequest(**invalid_config)


class TestMatchResultEdgeCases:
    """Test edge cases for MatchResult validation."""

    def test_match_result_with_extreme_scores(self):
        """Test match result with extreme score values."""
        # Arrange
        extreme_scores = [
            -0.1,  # Below minimum
            1.1,  # Above maximum
            -1000.0,  # Way below minimum
            1000.0,  # Way above maximum
        ]

        for score in extreme_scores:
            # Act & Assert - Should raise validation error for invalid scores
            with pytest.raises((ValueError, Exception)):
                MatchResult(
                    identifier="test",
                    score=score,
                    strategy="test",
                    match_type="fuzzy"
                )

    def test_match_result_with_valid_scores(self):
        """Test match result with valid score values."""
        # Arrange
        valid_scores = [0.0, 0.5, 1.0]

        for score in valid_scores:
            # Act & Assert - Should accept valid scores
            result = MatchResult(
                identifier="test",
                score=score,
                strategy="test",
                match_type="fuzzy"
            )
            
            # Score should be exactly as provided
            assert result.score == score

    def test_match_result_with_invalid_line_number(self):
        """Test match result with invalid line numbers."""
        # Arrange
        invalid_line_numbers = [
            0,  # Below minimum
            -1,  # Negative
            -1000,  # Way below minimum
        ]

        for line_number in invalid_line_numbers:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                MatchResult(
                    identifier="test",
                    score=0.5,
                    strategy="test",
                    match_type="fuzzy",
                    line_number=line_number
                )

    def test_match_result_with_invalid_match_type(self):
        """Test match result with invalid match types."""
        # Arrange
        invalid_types = [
            "exact",  # Invalid type
            "regex",  # Invalid type
            "EXACT",  # Uppercase
            "fuzzy ",  # Trailing space
            "",  # Empty
        ]

        for match_type in invalid_types:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                MatchResult(
                    identifier="test",
                    score=0.5,
                    strategy="test",
                    match_type=match_type
                )

    def test_match_result_with_malicious_identifier(self):
        """Test match result with malicious identifiers."""
        # Arrange
        malicious_identifiers = [
            "test\x00injection",  # Null byte injection
            "test<script>alert('xss')</script>",  # XSS attempt
            "test'; DROP TABLE identifiers; --",  # SQL injection
            "a" * 10000,  # Very long identifier
            "🎉🎊🎈",  # Emojis
            "测试",  # Chinese characters
        ]

        for identifier in malicious_identifiers:
            # Act & Assert - Should handle malicious identifiers gracefully
            try:
                result = MatchResult(
                    identifier=identifier,
                    score=0.5,
                    strategy="test",
                    match_type="fuzzy"
                )
                assert result.identifier == identifier
            except Exception as e:
                pytest.fail(f"Malicious identifier '{identifier}' broke the system: {e}")


class TestUtilityFunctionEdgeCases:
    """Test edge cases for utility functions."""

    def test_create_config_from_dict_with_invalid_data(self):
        """Test create_config_from_dict with invalid data."""
        # Arrange
        invalid_configs = [
            {},  # Empty dict
            {"invalid_key": "value"},  # Invalid key
            {"project_root": 123},  # Invalid type
            None,  # None
        ]

        for invalid_config in invalid_configs:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                create_config_from_dict(invalid_config)

    def test_validate_search_request_with_invalid_data(self):
        """Test validate_search_request with invalid data."""
        # Arrange
        invalid_requests = [
            {},  # Empty dict
            {"invalid_key": "value"},  # Invalid key
            {"query": 123},  # Invalid type
            None,  # None
        ]

        for invalid_request in invalid_requests:
            # Act & Assert - Should raise validation error
            with pytest.raises(ValueError):
                validate_search_request(invalid_request)

    def test_create_error_response_with_malicious_data(self):
        """Test create_error_response with malicious data."""
        # Arrange
        malicious_data = [
            ("test\x00injection", "ValidationError"),
            ("test<script>alert('xss')</script>", "ValidationError"),
            ("test'; DROP TABLE errors; --", "ValidationError"),
            ("a" * 10000, "ValidationError"),  # Very long error
        ]

        for error, error_type in malicious_data:
            # Act & Assert - Should handle malicious data gracefully
            try:
                response = create_error_response(error, error_type)
                assert response.error == error
                assert response.error_type == error_type
            except Exception as e:
                pytest.fail(f"Malicious error data broke the system: {e}")


class TestConfigurationIntegrationEdgeCases:
    """Test integration edge cases for configuration."""

    def test_full_config_with_all_edge_cases(self):
        """Test full configuration with all edge cases."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            edge_case_config = {
                "project_root": temp_dir,
                "map_tokens": 4096,
                "max_results": 50,
                "log_level": "INFO",
                "output_format": "json",
                "fuzzy_match": {
                    "enabled": True,
                    "threshold": 70,
                    "strategies": ["prefix", "substring"],
                    "cache_results": True
                },
                "semantic_match": {
                    "enabled": True,
                    "threshold": 0.1,
                    "use_tfidf": True,
                    "min_word_length": 3,
                    "cache_results": True
                }
            }

            # Act & Assert - Should handle edge case config gracefully
            try:
                config = RepoMapConfig(**edge_case_config)
                # Use resolve() to handle symlink differences on macOS
                assert config.project_root.resolve() == Path(temp_dir).resolve()
                assert config.fuzzy_match.enabled is True
                assert config.semantic_match.enabled is True
            except Exception as e:
                pytest.fail(f"Edge case config broke the system: {e}")

    def test_config_serialization_edge_cases(self):
        """Test configuration serialization with edge cases."""
        # Arrange
        with tempfile.TemporaryDirectory() as temp_dir:
            config = RepoMapConfig(project_root=temp_dir)

            # Act & Assert - Should handle serialization gracefully
            try:
                config_dict = config_to_dict(config)
                assert isinstance(config_dict, dict)
                assert "project_root" in config_dict
                
                # Test round-trip serialization
                new_config = create_config_from_dict(config_dict)
                assert new_config.project_root == config.project_root
            except Exception as e:
                pytest.fail(f"Config serialization broke the system: {e}")
