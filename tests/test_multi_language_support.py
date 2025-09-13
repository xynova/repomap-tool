#!/usr/bin/env python3
"""
Test multi-language support for LLM optimization components.

Note: This test has been updated to reflect the tree-sitter migration.
All language analysis now uses AiderBasedExtractor instead of regex-based analyzers.
"""

import unittest
from unittest.mock import Mock
from src.repomap_tool.llm.aider_based_extractor import (
    CriticalLineExtractor,
    AiderBasedExtractor,
)
from src.repomap_tool.llm.critical_line_extractor import CriticalLine


class TestMultiLanguageSupport(unittest.TestCase):
    """Test critical line extraction for multiple programming languages using tree-sitter."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_repo_map = Mock()
        self.extractor = CriticalLineExtractor(self.mock_repo_map)

    def test_aider_based_extractor_initialization(self):
        """Test that AiderBasedExtractor initializes correctly."""
        aider_extractor = AiderBasedExtractor(self.mock_repo_map)
        self.assertEqual(aider_extractor.repo_map, self.mock_repo_map)

    def test_critical_line_extractor_with_repo_map(self):
        """Test CriticalLineExtractor with repo_map (tree-sitter mode)."""
        extractor = CriticalLineExtractor(self.mock_repo_map)
        self.assertIsNotNone(extractor.aider_extractor)
        self.assertEqual(extractor.repo_map, self.mock_repo_map)

    def test_critical_line_extractor_without_repo_map(self):
        """Test CriticalLineExtractor without repo_map (fallback mode)."""
        extractor = CriticalLineExtractor()
        self.assertIsNone(extractor.aider_extractor)
        self.assertIsNone(extractor.repo_map)

    def test_extract_critical_lines_fallback_mode(self):
        """Test fallback extraction for raw content."""
        extractor = CriticalLineExtractor()  # No repo_map

        sample_code = """
def test_function():
    if condition:
        return result
    import os
"""
        result = extractor.extract_critical_lines(sample_code, "python")

        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        # Check that we get CriticalLine objects
        for line in result:
            self.assertIsInstance(line, CriticalLine)
            self.assertIsInstance(line.line_number, int)
            self.assertIsInstance(line.content, str)
            self.assertIsInstance(line.importance, float)
            self.assertIsInstance(line.pattern_type, str)

    def test_aider_based_extraction_success(self):
        """Test successful extraction using aider's tree-sitter."""
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

        aider_extractor = AiderBasedExtractor(self.mock_repo_map)
        result = aider_extractor.extract_critical_lines("test_file.py")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["line_number"], 10)
        self.assertEqual(result[0]["content"], "authenticate_user")
        self.assertEqual(result[0]["confidence"], 0.9)  # def gets 0.9
        self.assertEqual(result[0]["tag_kind"], "def")

    def test_aider_based_extraction_exception(self):
        """Test extraction with exception handling."""
        self.mock_repo_map.get_tags.side_effect = Exception("Test error")

        aider_extractor = AiderBasedExtractor(self.mock_repo_map)
        result = aider_extractor.extract_critical_lines("test_file.py")

        self.assertEqual(result, [])

    def test_confidence_calculation(self):
        """Test confidence score calculation based on tag kind."""
        aider_extractor = AiderBasedExtractor(self.mock_repo_map)

        # Test different tag kinds
        mock_def_tag = Mock()
        mock_def_tag.kind = "def"
        self.assertEqual(aider_extractor._calculate_confidence(mock_def_tag), 0.9)

        mock_ref_tag = Mock()
        mock_ref_tag.kind = "ref"
        self.assertEqual(aider_extractor._calculate_confidence(mock_ref_tag), 0.7)

        mock_other_tag = Mock()
        mock_other_tag.kind = "other"
        self.assertEqual(aider_extractor._calculate_confidence(mock_other_tag), 0.5)

    def test_reason_from_kind_mapping(self):
        """Test reason mapping from tag kind."""
        aider_extractor = AiderBasedExtractor(self.mock_repo_map)

        # Test known mappings
        self.assertEqual(
            aider_extractor._get_reason_from_kind("def"), "function_or_class_definition"
        )
        self.assertEqual(
            aider_extractor._get_reason_from_kind("class"), "class_definition"
        )
        self.assertEqual(
            aider_extractor._get_reason_from_kind("ref"), "reference_or_call"
        )

        # Test unknown mapping
        self.assertEqual(
            aider_extractor._get_reason_from_kind("unknown"), "unknown_kind_unknown"
        )

    def test_tree_sitter_migration_complete(self):
        """Test that tree-sitter migration is complete."""
        # Verify that the new extractor uses tree-sitter approach
        extractor = CriticalLineExtractor(self.mock_repo_map)
        self.assertIsNotNone(extractor.aider_extractor)

        # Verify that aider's get_tags method is used (tree-sitter)
        mock_tag = Mock()
        mock_tag.line = 1
        mock_tag.name = "test"
        mock_tag.kind = "def"
        self.mock_repo_map.get_tags.return_value = [mock_tag]

        result = extractor.aider_extractor.extract_critical_lines("test.py")
        self.mock_repo_map.get_tags.assert_called_once_with("test.py", "test.py")
        self.assertEqual(len(result), 1)


if __name__ == "__main__":
    unittest.main()
