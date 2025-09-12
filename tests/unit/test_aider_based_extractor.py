"""
Tests for AiderBasedExtractor functionality.

This module tests the tree-sitter based critical line extraction
that replaces the old regex-based analyzers.
"""

import unittest
from unittest.mock import Mock, patch
from pathlib import Path

from src.repomap_tool.llm.aider_based_extractor import (
    AiderBasedExtractor,
    CriticalLineExtractor,
)
from src.repomap_tool.llm.critical_line_extractor import CriticalLine


class TestAiderBasedExtractor(unittest.TestCase):
    """Test the AiderBasedExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_repo_map = Mock()
        self.extractor = AiderBasedExtractor(self.mock_repo_map)

    def test_initialization(self):
        """Test AiderBasedExtractor initialization."""
        self.assertEqual(self.extractor.repo_map, self.mock_repo_map)

    def test_extract_critical_lines_success(self):
        """Test successful critical line extraction."""
        # Mock aider tags
        mock_tag1 = Mock()
        mock_tag1.line = 10
        mock_tag1.name = "authenticate_user"
        mock_tag1.kind = "def"
        mock_tag1.col = 5

        mock_tag2 = Mock()
        mock_tag2.line = 15
        mock_tag2.name = "return result"
        mock_tag2.kind = "ref"
        mock_tag2.col = 8

        self.mock_repo_map.get_tags.return_value = [mock_tag1, mock_tag2]

        result = self.extractor.extract_critical_lines("test_file.py")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["line_number"], 10)
        self.assertEqual(result[0]["content"], "authenticate_user")
        self.assertEqual(result[0]["confidence"], 0.9)  # def gets 0.9
        self.assertEqual(result[0]["tag_kind"], "def")
        self.assertEqual(result[0]["column"], 5)

        self.assertEqual(result[1]["line_number"], 15)
        self.assertEqual(result[1]["content"], "return result")
        self.assertEqual(result[1]["confidence"], 0.7)  # ref gets 0.7

    def test_extract_critical_lines_exception(self):
        """Test critical line extraction with exception."""
        self.mock_repo_map.get_tags.side_effect = Exception("Test error")

        result = self.extractor.extract_critical_lines("test_file.py")

        self.assertEqual(result, [])

    def test_calculate_confidence(self):
        """Test confidence calculation for different tag kinds."""
        mock_tag_def = Mock()
        mock_tag_def.kind = "def"
        self.assertEqual(self.extractor._calculate_confidence(mock_tag_def), 0.9)

        mock_tag_ref = Mock()
        mock_tag_ref.kind = "ref"
        self.assertEqual(self.extractor._calculate_confidence(mock_tag_ref), 0.7)

        mock_tag_other = Mock()
        mock_tag_other.kind = "other"
        self.assertEqual(self.extractor._calculate_confidence(mock_tag_other), 0.5)

    def test_get_reason_from_kind(self):
        """Test reason mapping for different tag kinds."""
        self.assertEqual(
            self.extractor._get_reason_from_kind("def"), "function_or_class_definition"
        )
        self.assertEqual(
            self.extractor._get_reason_from_kind("class"), "class_definition"
        )
        self.assertEqual(
            self.extractor._get_reason_from_kind("import"), "import_statement"
        )
        self.assertEqual(
            self.extractor._get_reason_from_kind("function"), "function_definition"
        )
        self.assertEqual(
            self.extractor._get_reason_from_kind("unknown"), "unknown_kind_unknown"
        )


class TestCriticalLineExtractor(unittest.TestCase):
    """Test the new CriticalLineExtractor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = CriticalLineExtractor()

    def test_initialization_without_repo_map(self):
        """Test initialization without repo_map."""
        extractor = CriticalLineExtractor()
        self.assertIsNone(extractor.repo_map)
        self.assertIsNone(extractor.aider_extractor)

    def test_initialization_with_repo_map(self):
        """Test initialization with repo_map."""
        mock_repo_map = Mock()
        extractor = CriticalLineExtractor(mock_repo_map)
        self.assertEqual(extractor.repo_map, mock_repo_map)
        self.assertIsNotNone(extractor.aider_extractor)

    def test_extract_critical_lines_fallback(self):
        """Test fallback extraction for raw content."""
        sample_code = """
def test_function():
    if condition:
        return result
    import os
"""
        result = self.extractor.extract_critical_lines(sample_code, "python")

        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        # Check that we get CriticalLine objects
        for line in result:
            self.assertIsInstance(line, CriticalLine)
            self.assertIsInstance(line.line_number, int)
            self.assertIsInstance(line.content, str)
            self.assertIsInstance(line.importance, float)
            self.assertIsInstance(line.pattern_type, str)

    def test_extract_critical_lines_file_path(self):
        """Test extraction with file path."""
        mock_repo_map = Mock()
        mock_tag = Mock()
        mock_tag.line = 5
        mock_tag.name = "test_function"
        mock_tag.kind = "def"
        mock_tag.col = 1

        mock_repo_map.get_tags.return_value = [mock_tag]

        extractor = CriticalLineExtractor(mock_repo_map)

        with patch("pathlib.Path.is_file", return_value=True):
            result = extractor.extract_critical_lines("/path/to/file.py", "python")

        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], CriticalLine)
        self.assertEqual(result[0].line_number, 5)
        self.assertEqual(result[0].content, "test_function")

    def test_get_implementation_essence(self):
        """Test implementation essence extraction."""
        sample_code = """
def authenticate_user(username, password):
    user = User.find_by_username(username)
    if not user:
        return AuthResult(success=False)
    return AuthResult(success=True, user=user)
"""
        essence = self.extractor.get_implementation_essence(sample_code, "python")

        self.assertIsInstance(essence, str)
        self.assertIn("authenticate_user", essence)
        self.assertIn("|", essence)  # Should contain separator

    def test_get_implementation_essence_empty(self):
        """Test implementation essence with no critical lines."""
        essence = self.extractor.get_implementation_essence("", "python")
        self.assertEqual(essence, "Implementation details not available")

    def test_convert_to_critical_lines(self):
        """Test conversion from aider results to CriticalLine objects."""
        aider_results = [
            {
                "line_number": 10,
                "content": "def test():",
                "confidence": 0.9,
                "reason": "function_definition",
                "tag_kind": "def",
            },
            {
                "line_number": 15,
                "content": "return result",
                "confidence": 0.7,
                "reason": "return_statement",
                "tag_kind": "ref",
            },
        ]

        result = self.extractor._convert_to_critical_lines(aider_results)

        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], CriticalLine)
        self.assertEqual(result[0].line_number, 10)
        self.assertEqual(result[0].content, "def test():")
        self.assertEqual(result[0].importance, 0.9)
        self.assertEqual(result[0].pattern_type, "function_definition")
        self.assertEqual(result[0].context, "def")

    def test_fallback_extraction_patterns(self):
        """Test fallback extraction identifies common patterns."""
        sample_code = """
def my_function():
    class MyClass:
        if condition:
            return value
    import os
"""
        result = self.extractor._fallback_extraction(sample_code)

        self.assertTrue(len(result) > 0)

        # Check that we found the expected patterns
        contents = [line.content for line in result]
        self.assertTrue(any("def " in content for content in contents))
        self.assertTrue(any("class " in content for content in contents))
        self.assertTrue(any("return " in content for content in contents))
        self.assertTrue(any("import " in content for content in contents))

    def test_fallback_extraction_empty(self):
        """Test fallback extraction with empty content."""
        result = self.extractor._fallback_extraction("")
        self.assertEqual(result, [])

    def test_fallback_extraction_no_patterns(self):
        """Test fallback extraction with content that has no patterns."""
        result = self.extractor._fallback_extraction("just some text without patterns")
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
