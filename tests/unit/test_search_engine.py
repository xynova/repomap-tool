#!/usr/bin/env python3
"""
Unit tests for search engine functions.

This module tests the core search functions that currently have no unit tests:
- fuzzy_search()
- semantic_search() 
- hybrid_search()
- basic_search()
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Set

from repomap_tool.core.search_engine import (
    fuzzy_search,
    semantic_search,
    hybrid_search,
    basic_search,
)
from repomap_tool.models import MatchResult


class TestFuzzySearch:
    """Test fuzzy search functionality."""

    def test_fuzzy_search_with_valid_matcher(self):
        """Test fuzzy search with a valid fuzzy matcher."""
        # Arrange
        query = "test"
        identifiers = ["test_function", "example_test", "unrelated_function"]
        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = [
            ("test_function", 95),
            ("example_test", 85),
        ]
        limit = 5

        # Act
        results = fuzzy_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 2
        assert results[0].identifier == "test_function"
        assert results[0].score == 0.95  # 95/100
        assert results[0].strategy == "fuzzy_match"
        assert results[0].match_type == "fuzzy"
        assert results[1].identifier == "example_test"
        assert results[1].score == 0.85  # 85/100

    def test_fuzzy_search_with_no_matcher(self):
        """Test fuzzy search when matcher is not available."""
        # Arrange
        query = "test"
        identifiers = ["test_function", "example_test"]
        limit = 5

        # Act
        results = fuzzy_search(query, identifiers, None, limit)

        # Assert
        assert len(results) == 0

    def test_fuzzy_search_with_exception(self):
        """Test fuzzy search when matcher throws an exception."""
        # Arrange
        query = "test"
        identifiers = ["test_function"]
        mock_matcher = Mock()
        mock_matcher.match_identifiers.side_effect = Exception("Test error")
        limit = 5

        # Act
        results = fuzzy_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 0

    def test_fuzzy_search_respects_limit(self):
        """Test that fuzzy search respects the result limit."""
        # Arrange
        query = "test"
        identifiers = ["test1", "test2", "test3", "test4", "test5", "test6"]
        mock_matcher = Mock()
        mock_matcher.match_identifiers.return_value = [
            ("test1", 100),
            ("test2", 95),
            ("test3", 90),
            ("test4", 85),
            ("test5", 80),
            ("test6", 75),
        ]
        limit = 3

        # Act
        results = fuzzy_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 3
        assert results[0].identifier == "test1"
        assert results[1].identifier == "test2"
        assert results[2].identifier == "test3"


class TestSemanticSearch:
    """Test semantic search functionality."""

    def test_semantic_search_with_valid_matcher(self):
        """Test semantic search with a valid semantic matcher."""
        # Arrange
        query = "data processing"
        identifiers = ["data_processor", "file_handler", "data_analyzer"]
        mock_matcher = Mock()
        mock_matcher.find_semantic_matches.return_value = [
            ("data_processor", 85),
            ("data_analyzer", 75),
        ]
        limit = 5

        # Act
        results = semantic_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 2
        assert results[0].identifier == "data_processor"
        assert results[0].score == 0.85  # 85/100
        assert results[0].strategy == "semantic_match"
        assert results[0].match_type == "semantic"
        assert results[1].identifier == "data_analyzer"
        assert results[1].score == 0.75  # 75/100

    def test_semantic_search_with_no_matcher(self):
        """Test semantic search when matcher is not available."""
        # Arrange
        query = "data processing"
        identifiers = ["data_processor", "file_handler"]
        limit = 5

        # Act
        results = semantic_search(query, identifiers, None, limit)

        # Assert
        assert len(results) == 0

    def test_semantic_search_fallback_to_basic(self):
        """Test semantic search falls back to basic search when no results."""
        # Arrange
        query = "data"
        identifiers = ["data_processor", "file_handler"]
        mock_matcher = Mock()
        mock_matcher.find_semantic_matches.return_value = []
        limit = 5

        # Act
        results = semantic_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) > 0
        assert all(r.strategy == "semantic_fallback" for r in results)
        assert all(r.match_type == "semantic" for r in results)

    def test_semantic_search_with_exception_fallback(self):
        """Test semantic search falls back to basic search when exception occurs."""
        # Arrange
        query = "data"
        identifiers = ["data_processor", "file_handler"]
        mock_matcher = Mock()
        mock_matcher.find_semantic_matches.side_effect = Exception("Test error")
        limit = 5

        # Act
        results = semantic_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) > 0
        assert all(r.strategy == "semantic_fallback" for r in results)
        assert all(r.match_type == "semantic" for r in results)


class TestHybridSearch:
    """Test hybrid search functionality."""

    def test_hybrid_search_with_valid_matcher(self):
        """Test hybrid search with a valid hybrid matcher."""
        # Arrange
        query = "data"
        identifiers = ["data_processor", "file_handler", "data_analyzer"]
        mock_matcher = Mock()
        mock_matcher.build_tfidf_model = Mock()
        mock_matcher.match_identifiers.return_value = [
            ("data_processor", 90),
            ("data_analyzer", 80),
        ]
        limit = 5

        # Act
        results = hybrid_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 2
        assert results[0].identifier == "data_processor"
        assert results[0].score == 0.90  # 90/100
        assert results[0].strategy == "hybrid_match"
        assert results[0].match_type == "hybrid"
        assert results[1].identifier == "data_analyzer"
        assert results[1].score == 0.80  # 80/100

    def test_hybrid_search_with_no_matcher(self):
        """Test hybrid search when matcher is not available."""
        # Arrange
        query = "data"
        identifiers = ["data_processor", "file_handler"]
        limit = 5

        # Act
        results = hybrid_search(query, identifiers, None, limit)

        # Assert
        assert len(results) == 0

    def test_hybrid_search_builds_tfidf_model(self):
        """Test that hybrid search builds TF-IDF model when needed."""
        # Arrange
        query = "data"
        identifiers = ["data_processor", "file_handler"]
        mock_matcher = Mock()
        mock_matcher.build_tfidf_model = Mock()
        mock_matcher.match_identifiers.return_value = [("data_processor", 90)]
        limit = 5

        # Act
        results = hybrid_search(query, identifiers, mock_matcher, limit)

        # Assert
        mock_matcher.build_tfidf_model.assert_called_once()
        assert len(results) == 1

    def test_hybrid_search_with_exception(self):
        """Test hybrid search when matcher throws an exception."""
        # Arrange
        query = "data"
        identifiers = ["data_processor"]
        mock_matcher = Mock()
        mock_matcher.build_tfidf_model = Mock()
        mock_matcher.match_identifiers.side_effect = Exception("Test error")
        limit = 5

        # Act
        results = hybrid_search(query, identifiers, mock_matcher, limit)

        # Assert
        assert len(results) == 0


class TestBasicSearch:
    """Test basic search functionality."""

    def test_basic_search_finds_substring_matches(self):
        """Test basic search finds substring matches."""
        # Arrange
        query = "test"
        identifiers = ["test_function", "example_test", "unrelated_function"]
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 2
        assert results[0].identifier == "test_function"
        assert results[0].score == 1.0  # Prefix match gets higher score
        assert results[0].strategy == "basic_string_match"
        assert results[0].match_type == "fuzzy"
        assert results[1].identifier == "example_test"
        assert results[1].score == 0.8  # Substring match gets base score

    def test_basic_search_finds_prefix_matches(self):
        """Test basic search finds prefix matches with higher score."""
        # Arrange
        query = "test"
        identifiers = ["test_function", "testing", "unrelated_function"]
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 2
        # test_function should have higher score (prefix match)
        assert results[0].identifier == "test_function"
        assert results[0].score == 1.0  # Higher score for prefix matches
        assert results[1].identifier == "testing"
        assert results[1].score == 1.0  # Higher score for prefix matches

    def test_basic_search_case_insensitive(self):
        """Test basic search is case insensitive."""
        # Arrange
        query = "TEST"
        identifiers = ["test_function", "unrelated_function"]
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 1
        assert results[0].identifier == "test_function"

    def test_basic_search_respects_limit(self):
        """Test that basic search respects the result limit."""
        # Arrange
        query = "test"
        identifiers = ["test1", "test2", "test3", "test4", "test5", "test6"]
        limit = 3

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 3

    def test_basic_search_no_matches(self):
        """Test basic search returns empty list when no matches."""
        # Arrange
        query = "nonexistent"
        identifiers = ["test_function", "example_function"]
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 0

    def test_basic_search_empty_query(self):
        """Test basic search handles empty query."""
        # Arrange
        query = ""
        identifiers = ["test_function", "example_function"]
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        # Empty query matches everything (empty string is in every string)
        assert len(results) == 2

    def test_basic_search_empty_identifiers(self):
        """Test basic search handles empty identifiers list."""
        # Arrange
        query = "test"
        identifiers = []
        limit = 5

        # Act
        results = basic_search(query, identifiers, limit)

        # Assert
        assert len(results) == 0


class TestSearchEngineIntegration:
    """Integration tests for search engine functions."""

    def test_all_search_functions_return_match_results(self):
        """Test that all search functions return MatchResult objects."""
        # Arrange
        query = "test"
        identifiers = ["test_function", "example_test"]
        limit = 5

        # Create mock matchers
        mock_fuzzy_matcher = Mock()
        mock_fuzzy_matcher.match_identifiers.return_value = [("test_function", 90)]

        mock_semantic_matcher = Mock()
        mock_semantic_matcher.find_semantic_matches.return_value = [("test_function", 85)]

        mock_hybrid_matcher = Mock()
        mock_hybrid_matcher.build_tfidf_model = Mock()
        mock_hybrid_matcher.match_identifiers.return_value = [("test_function", 88)]

        # Act & Assert
        fuzzy_results = fuzzy_search(query, identifiers, mock_fuzzy_matcher, limit)
        assert all(isinstance(r, MatchResult) for r in fuzzy_results)

        semantic_results = semantic_search(query, identifiers, mock_semantic_matcher, limit)
        assert all(isinstance(r, MatchResult) for r in semantic_results)

        hybrid_results = hybrid_search(query, identifiers, mock_hybrid_matcher, limit)
        assert all(isinstance(r, MatchResult) for r in hybrid_results)

        basic_results = basic_search(query, identifiers, limit)
        assert all(isinstance(r, MatchResult) for r in basic_results)
