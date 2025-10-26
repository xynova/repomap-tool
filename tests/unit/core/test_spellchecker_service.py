"""
Unit tests for SpellCheckerService security functionality.

Tests focus on verifying safe subprocess usage and path resolution
to prevent PATH hijacking vulnerabilities.
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
from typing import Optional, Set
import subprocess

from src.repomap_tool.core.spellchecker_service import SpellCheckerService


class TestSpellCheckerServiceSecurity(unittest.TestCase):
    """Test security aspects of SpellCheckerService."""

    def setUp(self):
        """Set up test fixtures."""
        self.custom_dict: Set[str] = {"custom", "words"}

        # Patch the availability check during initialization to prevent false warnings
        with patch(
            "src.repomap_tool.core.spellchecker_service.SpellCheckerService._check_codespell_availability",
            return_value=True,
        ):
            self.service = SpellCheckerService(self.custom_dict)

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    def test_get_codespell_path_found(self, mock_which):
        """Test _get_codespell_path returns full path when codespell is found."""
        mock_which.return_value = "/usr/bin/codespell"

        result = self.service._get_codespell_path()

        self.assertEqual(result, "/usr/bin/codespell")
        mock_which.assert_called_once_with("codespell")

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    def test_get_codespell_path_not_found(self, mock_which):
        """Test _get_codespell_path returns None when codespell is not found."""
        mock_which.return_value = None

        result = self.service._get_codespell_path()

        self.assertIsNone(result)
        mock_which.assert_called_once_with("codespell")

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    @patch("src.repomap_tool.core.spellchecker_service.subprocess.run")
    def test_check_availability_with_full_path(self, mock_run, mock_which):
        """Test _check_codespell_availability uses full path in subprocess call."""
        mock_which.return_value = "/usr/bin/codespell"
        mock_run.return_value = Mock(returncode=0)

        result = self.service._check_codespell_availability()

        self.assertTrue(result)
        mock_which.assert_called_once_with("codespell")
        mock_run.assert_called_once_with(
            ["/usr/bin/codespell", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    def test_check_availability_not_found(self, mock_which):
        """Test _check_codespell_availability returns False when codespell not found."""
        mock_which.return_value = None

        result = self.service._check_codespell_availability()

        self.assertFalse(result)
        mock_which.assert_called_once_with("codespell")

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    @patch("src.repomap_tool.core.spellchecker_service.subprocess.run")
    def test_run_codespell_with_full_path(self, mock_run, mock_which):
        """Test _run_codespell uses full path in subprocess call."""
        mock_which.return_value = "/usr/bin/codespell"
        mock_run.return_value = Mock(
            stdout="test.txt:1: seach ==> search, each, reach\n", returncode=0
        )

        result = self.service._run_codespell("test text with seach")

        self.assertEqual(result, ["search", "each", "reach"])
        mock_which.assert_called_once_with("codespell")
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        self.assertEqual(call_args[0], "/usr/bin/codespell")  # Full path used

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    def test_run_codespell_not_found(self, mock_which):
        """Test _run_codespell returns empty list when codespell not found."""
        mock_which.return_value = None

        result = self.service._run_codespell("test text")

        self.assertEqual(result, [])
        mock_which.assert_called_once_with("codespell")

    @patch("src.repomap_tool.core.spellchecker_service.shutil.which")
    @patch("src.repomap_tool.core.spellchecker_service.subprocess.run")
    def test_run_codespell_subprocess_failure(self, mock_run, mock_which):
        """Test _run_codespell handles subprocess failures gracefully."""
        mock_which.return_value = "/usr/bin/codespell"
        mock_run.side_effect = subprocess.TimeoutExpired("codespell", 10)

        result = self.service._run_codespell("test text")

        self.assertEqual(result, [])
        mock_which.assert_called_once_with("codespell")
        mock_run.assert_called_once()

    def test_security_no_partial_paths(self):
        """Test that no partial paths are used in subprocess calls (security check)."""
        # This is a security validation test - ensure we never use partial paths
        service_code = open("src/repomap_tool/core/spellchecker_service.py").read()

        # Check that we don't use partial paths in subprocess calls
        self.assertNotIn('["codespell",', service_code)

        # Check that we use the safe path resolution method
        self.assertIn("_get_codespell_path()", service_code)
        self.assertIn("shutil.which", service_code)


if __name__ == "__main__":
    unittest.main()
