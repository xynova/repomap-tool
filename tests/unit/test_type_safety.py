"""
Unit tests for type safety improvements.

Tests protocols, type validation, and runtime type checking.
"""

import pytest
from repomap_tool.protocols import ProjectMap, Tag, FileData, IdentifierSet, MatchResult
from repomap_tool.utils.type_validator import (
    validate_project_map,
    validate_identifier_set,
    validate_cache_stats,
    validate_match_result,
    safe_validate_project_map,
    safe_validate_identifier_set,
)


class TestTypeSafety:
    """Test cases for type safety improvements."""

    def test_project_map_validation(self):
        """Test ProjectMap validation."""
        # Valid project map
        valid_data = {
            "tags": [
                {
                    "name": "test_function",
                    "type": "function",
                    "file": "test.py",
                    "line": 10,
                }
            ],
            "identifiers": ["test_function", "test_class"],
            "files": {
                "test.py": {
                    "identifiers": ["test_function"],
                    "tags": [{"name": "test_function", "type": "function"}],
                    "content": "def test_function(): pass",
                }
            },
        }

        result = validate_project_map(valid_data)
        assert isinstance(result, dict)
        assert result["tags"] is not None
        assert result["identifiers"] is not None
        assert result["files"] is not None
        assert len(result["tags"]) == 1
        assert result["tags"][0]["name"] == "test_function"

    def test_project_map_validation_invalid(self):
        """Test ProjectMap validation with invalid data."""
        # Invalid data - tags should be list
        invalid_data = {"tags": "not_a_list", "identifiers": ["test"]}

        with pytest.raises(ValueError, match="Tags must be a list"):
            validate_project_map(invalid_data)

    def test_safe_project_map_validation(self):
        """Test safe ProjectMap validation with graceful degradation."""
        # Invalid data
        invalid_data = {"tags": "not_a_list", "identifiers": ["test"]}

        # Should not raise exception, should return empty structure
        result = safe_validate_project_map(invalid_data)
        assert isinstance(result, dict)
        assert result["tags"] is None
        assert result["identifiers"] is None
        assert result["files"] is None

    def test_identifier_set_validation(self):
        """Test identifier set validation."""
        # Valid identifiers
        valid_identifiers = ["func1", "func2", "class1"]
        result = validate_identifier_set(valid_identifiers)
        assert result == ["func1", "func2", "class1"]

        # Single string
        result = validate_identifier_set("single_func")
        assert result == ["single_func"]

        # Set
        result = validate_identifier_set({"func1", "func2"})
        assert set(result) == {"func1", "func2"}

    def test_identifier_set_validation_invalid(self):
        """Test identifier set validation with invalid data."""
        # Invalid data
        with pytest.raises(ValueError, match="Identifiers must be"):
            validate_identifier_set(123)

    def test_safe_identifier_set_validation(self):
        """Test safe identifier set validation."""
        # Invalid data
        result = safe_validate_identifier_set(123)
        assert result == []

    def test_cache_stats_validation(self):
        """Test cache statistics validation."""
        valid_stats = {
            "cache_size": 10,
            "hits": 5,
            "misses": 3,
            "hit_rate_percent": 62.5,
            "evictions": 1,
            "expirations": 0,
            "total_requests": 8,
        }

        result = validate_cache_stats(valid_stats)
        assert result == valid_stats

    def test_cache_stats_validation_missing_keys(self):
        """Test cache statistics validation with missing keys."""
        invalid_stats = {
            "cache_size": 10,
            "hits": 5,
            # Missing required keys
        }

        with pytest.raises(ValueError, match="missing required key"):
            validate_cache_stats(invalid_stats)

    def test_match_result_validation(self):
        """Test match result validation."""
        valid_match = ("test_function", 85)
        result = validate_match_result(valid_match)
        assert result == ("test_function", 85)

        # List format
        valid_match_list = ["test_function", 85]
        result = validate_match_result(valid_match_list)
        assert result == ("test_function", 85)

    def test_match_result_validation_invalid(self):
        """Test match result validation with invalid data."""
        # Wrong number of elements
        with pytest.raises(ValueError, match="must be a tuple or list with 2 elements"):
            validate_match_result(("single_element",))

        # Wrong types
        with pytest.raises(ValueError, match="Match identifier must be a string"):
            validate_match_result((123, 85))

        with pytest.raises(ValueError, match="Match score must be a number"):
            validate_match_result(("test", "not_a_number"))

    def test_protocol_types(self):
        """Test that protocol types are properly defined."""
        # Test ProjectMap TypedDict
        project_map: ProjectMap = {
            "tags": [
                {"name": "test", "type": "function", "file": "test.py", "line": 1}
            ],
            "identifiers": ["test"],
            "files": {
                "test.py": {
                    "identifiers": ["test"],
                    "tags": [
                        {
                            "name": "test",
                            "type": "function",
                            "file": "test.py",
                            "line": 1,
                        }
                    ],
                    "content": "def test(): pass",
                }
            },
        }

        assert isinstance(project_map, dict)
        assert project_map["tags"] is not None
        assert project_map["identifiers"] is not None
        assert project_map["files"] is not None

    def test_tag_typeddict(self):
        """Test Tag TypedDict."""
        tag: Tag = {
            "name": "test_function",
            "type": "function",
            "file": "test.py",
            "line": 10,
        }

        assert isinstance(tag, dict)
        assert tag["name"] == "test_function"
        assert tag["type"] == "function"

    def test_filedata_typeddict(self):
        """Test FileData TypedDict."""
        file_data: FileData = {
            "identifiers": ["test_function"],
            "tags": [
                {
                    "name": "test_function",
                    "type": "function",
                    "file": "test.py",
                    "line": 10,
                }
            ],
            "content": "def test_function(): pass",
        }

        assert isinstance(file_data, dict)
        assert file_data["identifiers"] is not None
        assert file_data["tags"] is not None
        assert file_data["content"] is not None

    def test_none_handling(self):
        """Test handling of None values."""
        # None project map
        result = validate_project_map(None)
        assert result["tags"] is None
        assert result["identifiers"] is None
        assert result["files"] is None

        # None identifiers
        result = validate_identifier_set(None)
        assert result == []

    def test_type_aliases(self):
        """Test that type aliases work correctly."""
        # Test IdentifierSet alias
        identifiers: IdentifierSet = {"func1", "func2", "class1"}
        assert isinstance(identifiers, set)
        assert all(isinstance(ident, str) for ident in identifiers)

        # Test MatchResult alias
        match: MatchResult = ("test_function", 85)
        assert isinstance(match, tuple)
        assert len(match) == 2
        assert isinstance(match[0], str)
        assert isinstance(match[1], int)
